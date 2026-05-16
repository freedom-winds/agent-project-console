# Running Agent Project Console

This guide covers Windows (PowerShell / cmd) and Linux/macOS.

## Prerequisites

- Python 3.11 or newer (`python --version`)
- Node.js 18 or newer (`node --version`)
- npm

## One-time setup

### Backend

```bash
cd agent-project-console/backend
python -m pip install -r requirements.txt
```

### Frontend

```bash
cd agent-project-console/frontend
npm install
```

## Start the backend

Default address: `http://127.0.0.1:8765`. Default DB: SQLite at `backend/instance/apc.sqlite3`.

### Linux / macOS

```bash
cd agent-project-console/backend
python run.py
```

### Windows (PowerShell)

```powershell
cd agent-project-console\backend
python run.py
```

### Windows (cmd)

```cmd
cd /d agent-project-console\backend
python run.py
```

Verify: `curl http://127.0.0.1:8765/api/health` should return `{"status": "ok", ...}`.

The first call also creates the SQLite tables. To reinitialize manually:

```bash
cd agent-project-console/backend
set FLASK_APP=app    # cmd
$env:FLASK_APP="app" # PowerShell
export FLASK_APP=app # bash
flask init-db
```

## Start the frontend

Default address: `http://127.0.0.1:5173`. The dev server proxies `/api/*` to the backend.

### Linux / macOS

```bash
cd agent-project-console/frontend
npm run dev
```

### Windows

```powershell
cd agent-project-console\frontend
npm run dev
```

Open `http://127.0.0.1:5173` in a browser.

## Start both at once

### Windows

```powershell
cd agent-project-console
powershell -ExecutionPolicy Bypass -File scripts\dev.ps1
```

### Linux / macOS

```bash
cd agent-project-console
bash scripts/dev.sh
```

## Run the MCP STDIO server manually

You normally do not run this yourself; an MCP client (Cline, Claude Code, Codex CLI) launches it. To test it manually:

```bash
cd agent-project-console/backend
export APC_BASE_URL=http://127.0.0.1:8765
export APC_MCP_TOKEN=<paste-token>
python -m app.mcp.server
```

It reads JSON-RPC 2.0 lines from stdin and writes responses to stdout. The protocol expected by Cline / Claude Code / Codex is implemented (`initialize`, `tools/list`, `tools/call`, `ping`).

## Tests

### Backend

```bash
cd agent-project-console/backend
python -m pytest tests -v
```

### Frontend type check + build

```bash
cd agent-project-console/frontend
npm run build
```

## Configuration

Backend reads these env vars (all optional):

* `APC_HOST` (default `127.0.0.1`)
* `APC_PORT` (default `8765`)
* `APC_DATABASE_URI` (default `sqlite:///<backend>/instance/apc.sqlite3`)
* `APC_SECRET_KEY` (default `dev-secret-change-me`)

MCP server reads:

* `APC_BASE_URL` (default `http://127.0.0.1:8765`)
* `APC_MCP_TOKEN` (required for write operations)
* `APC_AGENT_NAME` (optional, used as actor in activity log; defaults to `mcp-agent`)
