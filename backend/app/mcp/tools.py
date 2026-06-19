"""MCP tool implementations. They call the local REST backend (do not touch the DB directly)."""
import json
import os
from urllib.parse import urlencode
from typing import Any, Dict

import requests


def _base_url() -> str:
    return os.environ.get("APC_BASE_URL", "http://127.0.0.1:8765").rstrip("/")


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json; charset=utf-8"}
    token = os.environ.get("APC_MCP_TOKEN", "")
    if token:
        h["Authorization"] = f"Bearer {token}"
    h["X-APC-Actor"] = os.environ.get("APC_AGENT_NAME", "mcp-agent")
    return h


class McpError(Exception):
    pass


def _request(method: str, path: str, **kwargs) -> Any:
    url = _base_url() + path
    try:
        resp = requests.request(method, url, headers=_headers(), timeout=30, **kwargs)
    except requests.RequestException as e:
        raise McpError(f"backend not reachable at {url}: {e}")
    if resp.status_code >= 400:
        try:
            data = resp.json()
            msg = data.get("message") or data.get("error") or resp.text
        except Exception:
            msg = resp.text
        raise McpError(f"backend error {resp.status_code}: {msg}")
    if not resp.content:
        return {}
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text}


# ---- Tool implementations ----

def get_projects(args: dict) -> Any:
    return _request("GET", "/api/projects")


def get_project_tree(args: dict) -> Any:
    pid = args["project_id"]
    include_done = "true" if args.get("include_done", True) else "false"
    return _request("GET", f"/api/projects/{pid}/tree?include_done={include_done}")


def create_node(args: dict) -> Any:
    return _request("POST", "/api/nodes", json=args)


def update_node(args: dict) -> Any:
    nid = args.pop("node_id")
    return _request("PATCH", f"/api/nodes/{nid}", json=args)


def update_status(args: dict) -> Any:
    nid = args.pop("node_id")
    return _request("POST", f"/api/nodes/{nid}/status", json=args)


def add_evidence(args: dict) -> Any:
    nid = args.pop("node_id")
    return _request("POST", f"/api/nodes/{nid}/evidence", json=args)


def add_artifact(args: dict) -> Any:
    nid = args.pop("node_id")
    return _request("POST", f"/api/nodes/{nid}/artifacts", json=args)


def report_blocker(args: dict) -> Any:
    nid = args.pop("node_id")
    return _request("POST", f"/api/nodes/{nid}/blocker", json=args)


def resolve_blocker(args: dict) -> Any:
    nid = args.pop("node_id")
    return _request("POST", f"/api/nodes/{nid}/blocker/resolve", json=args)


def create_checkpoint(args: dict) -> Any:
    pid = args.pop("project_id")
    return _request("POST", f"/api/projects/{pid}/checkpoints", json=args)


def move_node(args: dict) -> Any:
    nid = args.pop("node_id")
    return _request("POST", f"/api/nodes/{nid}/move", json=args)


def search_nodes(args: dict) -> Any:
    pid = args["project_id"]
    params = urlencode(
        {
            "q": args.get("query", ""),
            "status": ",".join(args.get("status") or []),
            "tags": ",".join(args.get("tags") or []),
        }
    )
    return _request(
        "GET",
        f"/api/projects/{pid}/search?{params}",
    )


def set_current_focus(args: dict) -> Any:
    pid = args.pop("project_id")
    return _request("POST", f"/api/projects/{pid}/focus", json=args)


TOOL_DISPATCH = {
    "get_projects": get_projects,
    "get_project_tree": get_project_tree,
    "create_node": create_node,
    "update_node": update_node,
    "update_status": update_status,
    "add_evidence": add_evidence,
    "add_artifact": add_artifact,
    "report_blocker": report_blocker,
    "resolve_blocker": resolve_blocker,
    "create_checkpoint": create_checkpoint,
    "move_node": move_node,
    "search_nodes": search_nodes,
    "set_current_focus": set_current_focus,
}
