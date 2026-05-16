# MCP Setup

The MCP server runs locally and talks to the Flask backend via HTTP. It does not touch the database directly.

## Prerequisites

1. Backend is running on `http://127.0.0.1:8765`.
2. You created an MCP token in the Web UI Settings page (or via `python scripts/create_mcp_token.py <name>`). Copy it once — the database stores only a hash.

## How the MCP server is invoked

```bash
python -m app.mcp.server
```

It must be run from the `backend/` directory (so that `app.mcp.server` is importable).

It expects three environment variables:

* `APC_BASE_URL=http://127.0.0.1:8765`
* `APC_MCP_TOKEN=<paste your token>`
* `APC_AGENT_NAME=cline`  (optional; appears in activity log)

## Cline (VS Code extension)

Open the Cline settings JSON (Command Palette → "Cline: Edit MCP Servers") and add:

```jsonc
{
  "mcpServers": {
    "agent-project-console": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "f:\\projects\\tree_for_agents\\agent-project-console\\backend",
      "env": {
        "APC_BASE_URL": "http://127.0.0.1:8765",
        "APC_MCP_TOKEN": "apc_xxxxxxxxxxxxxxxxxxxx",
        "APC_AGENT_NAME": "cline"
      }
    }
  }
}
```

On Linux/macOS, change `cwd` to your absolute path. After saving, restart Cline. The tools (`get_projects`, `get_project_tree`, `update_status`, …) appear in Cline's tool list.

## Claude Code (Anthropic CLI)

Edit `~/.config/claude/mcp.json` (Linux/macOS) or `%APPDATA%\Claude\mcp.json` (Windows):

```jsonc
{
  "mcpServers": {
    "agent-project-console": {
      "command": "python",
      "args": ["-m", "app.mcp.server"],
      "cwd": "/absolute/path/to/agent-project-console/backend",
      "env": {
        "APC_BASE_URL": "http://127.0.0.1:8765",
        "APC_MCP_TOKEN": "apc_xxxxxxxxxxxxxxxxxxxx",
        "APC_AGENT_NAME": "claude-code"
      }
    }
  }
}
```

Restart Claude Code. Verify with `claude mcp list`.

## Codex CLI

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.agent-project-console]
command = "python"
args = ["-m", "app.mcp.server"]
cwd = "/absolute/path/to/agent-project-console/backend"

[mcp_servers.agent-project-console.env]
APC_BASE_URL = "http://127.0.0.1:8765"
APC_MCP_TOKEN = "apc_xxxxxxxxxxxxxxxxxxxx"
APC_AGENT_NAME = "codex"
```

Or, if your Codex install uses JSON, add the same `agent-project-console` block under `mcpServers`.

## Available tools

| Tool | Purpose |
|------|--------|
| `get_projects` | list all projects |
| `get_project_tree` | full Part/Phase/Step tree for one project |
| `create_node` | create a Part / Phase / Step (hierarchy enforced) |
| `update_node` | edit a node's title, description, priority, etc. |
| `update_status` | change node status; `done` requires `evidence_summary`; `blocked` requires `blocker_reason` and `next_action` |
| `add_evidence` | attach file_path / commit_hash / command_output / test_result / screenshot_path / url / note |
| `add_artifact` | attach a deliverable (doc, build, source, package) |
| `report_blocker` | mark a node blocked with reason / impact / next action |
| `resolve_blocker` | move a blocked node back to in_progress with a resolution note |
| `create_checkpoint` | snapshot of completed / in_progress / next / blockers / risks |
| `move_node` | move a node to a new parent (hierarchy enforced) |
| `search_nodes` | search by query, status, tags |
| `set_current_focus` | mark which Step the agent is currently working on |

See `docs/API.md` for the underlying REST endpoints and `skills/agent-project-console/SKILL.md` for usage rules.

## Verifying the connection

After configuring your client:

1. Ask the agent to call `get_projects`. It should return whatever you created in the Web UI (or an empty list).
2. The Web UI Settings page will show the token's "last used" timestamp updating.
3. The Activity page on a project shows incoming `node_created`, `status_changed`, `evidence_added`, etc. events with the agent name as actor.

If the agent reports `backend not reachable at ...`, the Flask backend is not running. Start it via `python run.py`.

If you get `invalid token`, regenerate one in Settings and update the MCP client config.
