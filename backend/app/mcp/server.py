"""MCP STDIO server for Agent Project Console.

Implements a minimal Model Context Protocol server over JSON-RPC 2.0 on
stdin/stdout. Compatible with Cline, Claude Code, Codex CLI and any client
that speaks the MCP STDIO transport.

Run: python -m app.mcp.server

Environment:
- APC_BASE_URL (default http://127.0.0.1:8765)
- APC_MCP_TOKEN (required for write operations)
- APC_AGENT_NAME (optional, used as actor in activity log)
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any, Dict

from .schemas import TOOL_SCHEMAS
from .tools import TOOL_DISPATCH, McpError


PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {
    "name": "agent-project-console",
    "version": "0.1.0",
}


def _configure_stdio_encoding() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def _log(msg: str) -> None:
    # MCP stdio: stdout is reserved for JSON-RPC. Logs go to stderr.
    sys.stderr.write(f"[apc-mcp] {msg}\n")
    sys.stderr.flush()


def _send(message: Dict[str, Any]) -> None:
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8") + b"\n"
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def _ok(req_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    e: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": e}


def handle_initialize(req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return _ok(
        req_id,
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
                "logging": {},
            },
            "serverInfo": SERVER_INFO,
            "instructions": (
                "Agent Project Console MCP server. Use get_project_tree before working, "
                "set_current_focus + update_status(in_progress) before a Step, "
                "add_evidence + update_status(done) after, report_blocker on blockers, "
                "and create_checkpoint after each Phase."
            ),
        },
    )


def handle_tools_list(req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    return _ok(req_id, {"tools": TOOL_SCHEMAS})


def handle_tools_call(req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
    name = params.get("name", "")
    args = params.get("arguments", {}) or {}
    if name not in TOOL_DISPATCH:
        return _err(req_id, -32601, f"unknown tool: {name}")
    try:
        result = TOOL_DISPATCH[name](dict(args))
    except McpError as e:
        # Return as a tool error result so the LLM can see the message
        return _ok(
            req_id,
            {
                "isError": True,
                "content": [{"type": "text", "text": f"ERROR: {str(e)}"}],
            },
        )
    except Exception as e:  # pragma: no cover
        _log(f"tool {name} raised: {e}\n{traceback.format_exc()}")
        return _ok(
            req_id,
            {
                "isError": True,
                "content": [{"type": "text", "text": f"INTERNAL ERROR: {e}"}],
            },
        )
    text = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    return _ok(
        req_id,
        {
            "content": [{"type": "text", "text": text}],
            "isError": False,
        },
    )


HANDLERS = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}


def handle_message(msg: Dict[str, Any]) -> Dict[str, Any] | None:
    method = msg.get("method")
    req_id = msg.get("id")
    params = msg.get("params") or {}

    # Notifications (no id) -> no response
    if req_id is None:
        if method == "notifications/initialized":
            _log("client initialized")
        return None

    if method in HANDLERS:
        try:
            return HANDLERS[method](req_id, params)
        except Exception as e:  # pragma: no cover
            _log(f"handler {method} failed: {e}\n{traceback.format_exc()}")
            return _err(req_id, -32603, f"internal error: {e}")

    if method == "ping":
        return _ok(req_id, {})

    return _err(req_id, -32601, f"method not found: {method}")


def main() -> None:
    _configure_stdio_encoding()
    _log(f"starting MCP STDIO server, base_url={os.environ.get('APC_BASE_URL', 'http://127.0.0.1:8765')}")
    if not os.environ.get("APC_MCP_TOKEN"):
        _log("warning: APC_MCP_TOKEN is not set. Write operations will fail. Create a token in the Settings page.")
    while True:
        try:
            raw_line = sys.stdin.buffer.readline()
        except KeyboardInterrupt:
            break
        if not raw_line:
            break
        line = raw_line.decode("utf-8", errors="replace")
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            _log(f"invalid JSON: {e}: {line[:200]}")
            continue
        # Handle batch
        if isinstance(msg, list):
            for sub in msg:
                resp = handle_message(sub)
                if resp is not None:
                    _send(resp)
            continue
        resp = handle_message(msg)
        if resp is not None:
            _send(resp)


if __name__ == "__main__":
    main()
