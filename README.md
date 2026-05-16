# Agent Project Console

A local-only project progress console for AI agents working on large projects.

The fixed hierarchy is:

```
Project
  Part           (e.g. "Backend API")
    Phase        (e.g. "Auth System")
      Step       (smallest verifiable unit)
```

Step is the smallest task unit. The system enforces this hierarchy.

The console gives you:

* A dark **project cockpit** Web UI on `http://127.0.0.1:5173`.
* A Flask REST API on `http://127.0.0.1:8765`.
* A SQLite database (default).
* An **MCP STDIO server** (`python -m app.mcp.server`) so an AI agent can read the tree, update progress, add evidence, report blockers and create checkpoints.
* A **Skill package** (`skills/agent-project-console/`) that teaches an agent when and how to call those tools.

It is **not** a chat archive. Every write is recorded in an immutable activity log. `done` requires evidence. `blocked` requires reason and next action. The plan is the source of truth.

## What's inside

```
agent-project-console/
  backend/        Flask + SQLAlchemy backend, REST API, MCP STDIO server
  frontend/       Vite + React + TypeScript + TailwindCSS dark UI
  skills/agent-project-console/
                  SKILL.md, examples/, schemas/, prompts/
  docs/           REQUIREMENTS, RUNNING, MCP_SETUP, SKILLS_SETUP, API
  scripts/        dev.ps1, dev.sh, create_mcp_token.py
```

## Quick start

### 1. Install backend dependencies

```bash
cd agent-project-console/backend
python -m pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd agent-project-console/frontend
npm install
```

### 3. Start everything

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev.ps1
```

Linux / macOS:

```bash
bash scripts/dev.sh
```

Or run them separately (see `docs/RUNNING.md`).

* Web UI:  http://127.0.0.1:5173
* API:     http://127.0.0.1:8765/api/health

### 4. Create a project

Open http://127.0.0.1:5173, click **New Project**.

### 5. Create an MCP token

Open the **Settings** page in the UI, click **Create Token**. Copy it (it is shown only once).

Or from the command line:

```bash
python agent-project-console/scripts/create_mcp_token.py cline
```

### 6. Configure your MCP client

See `docs/MCP_SETUP.md`. Cline / Claude Code / Codex examples are included.

### 7. Install the skill

See `docs/SKILLS_SETUP.md`. The skill teaches the agent when to call which MCP tool.

## Testing

```bash
cd agent-project-console/backend
python -m pytest tests
```

```bash
cd agent-project-console/frontend
npm run build
```

## Windows: one-click `.exe` (optional)

The `launcher/` directory packages everything (Flask backend + built React UI)
into a single tray application. Double-click the resulting `.exe` and:

1. A small popup confirms startup, then auto-closes.
2. The backend listens on `http://127.0.0.1:8765` (API + UI on the same port).
3. A tray icon appears under "Hidden icons" with right-click options:
   **打开网页端 / 重启服务 / 关闭服务**.

Build it with:

```powershell
cd agent-project-console
python -m venv backend\venv ; backend\venv\Scripts\activate
pip install -r backend\requirements.txt
pip install -r launcher\requirements.txt
cd frontend ; npm install ; npm run build ; cd ..
python -m PyInstaller --noconfirm --clean launcher\tray_app.spec
# -> dist\AgentProjectConsole.exe
```

See `launcher/README.md` for full details.

## License

Local tool. No license imposed.
