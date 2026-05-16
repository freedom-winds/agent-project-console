# Agent Project Console — Tray Launcher (Windows .exe)

This directory contains a single-file Windows launcher that bundles the
Flask backend and the built React frontend into one executable. Double-click
the resulting `AgentProjectConsole.exe`:

1. A small "服务已启动" popup confirms startup (auto-closes in ~2.5s).
2. The Flask + waitress backend starts on `http://127.0.0.1:8765`.
   The same port also serves the React UI (single-port deploy).
3. A tray icon appears (Windows: usually under "Hidden icons / 隐藏的图标").
   Right-click the icon for:
     - **打开网页端** — open the web UI in the default browser
     - **重启服务** — stop and restart the backend
     - **关闭服务** — stop the backend and quit the launcher

The SQLite database lives at:

```
%LOCALAPPDATA%\AgentProjectConsole\apc.sqlite3
```

A start-up diagnostics file is written to:

```
%LOCALAPPDATA%\AgentProjectConsole\launcher_debug.log
```

## Build the .exe

Prerequisites: Python 3.11+, Node 18+, npm.

```powershell
# 1. Install backend + launcher dependencies (use the project's venv if you have one)
cd agent-project-console
python -m venv backend\venv
backend\venv\Scripts\activate
pip install -r backend\requirements.txt
pip install -r launcher\requirements.txt

# 2. Build the React frontend (output: frontend\dist)
cd frontend
npm install
npm run build
cd ..

# 3. Build the single-file exe (output: dist\AgentProjectConsole.exe)
python -m PyInstaller --noconfirm --clean launcher\tray_app.spec
```

If you ran the backend earlier from source, delete any stale `__pycache__`
directories before rebuilding so PyInstaller picks up the latest bytecode:

```powershell
Get-ChildItem agent-project-console\backend\app -Recurse -Filter '__pycache__' -Directory `
    | Remove-Item -Recurse -Force
```

The output `dist\AgentProjectConsole.exe` is fully self-contained — copy it
anywhere and double-click. No Python/Node installation required on the
target machine.

## Run from source (for development of the launcher itself)

```powershell
cd agent-project-console
backend\venv\Scripts\activate
pip install -r launcher\requirements.txt
# Build frontend first (or set APC_FRONTEND_DIST manually):
cd frontend && npm run build && cd ..
python launcher\tray_app.py
```

## Environment overrides

| Variable             | Purpose                                                                |
| -------------------- | ---------------------------------------------------------------------- |
| `APC_HOST`           | Bind address (default `127.0.0.1`)                                     |
| `APC_PORT`           | Bind port (default `8765`)                                             |
| `APC_DATABASE_URI`   | SQLAlchemy URL (default: `sqlite:///%LOCALAPPDATA%/.../apc.sqlite3`)   |
| `APC_FRONTEND_DIST`  | Path to a built `frontend/dist` (auto-detected by the launcher)        |

## Diagnostics endpoint

The bundled backend exposes `GET /__apc_debug__` returning JSON with the
resolved frontend dist directory and PyInstaller bundle info. Useful when
the SPA fallback isn't serving the UI as expected.
