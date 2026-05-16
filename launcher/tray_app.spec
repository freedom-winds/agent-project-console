# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Agent Project Console.

Builds a single-file Windows .exe with:
  - tray launcher (no console window: --windowed)
  - the Flask backend `app/` package
  - the pre-built React frontend (frontend/dist) under bundle path `frontend_dist/`

Run from agent-project-console/ root:
    pyinstaller launcher/tray_app.spec
"""
from __future__ import annotations
import os
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Resolve key paths relative to the spec file location.
HERE = os.path.abspath(os.path.dirname(SPEC))               # agent-project-console/launcher
ROOT = os.path.abspath(os.path.join(HERE, ".."))            # agent-project-console/
BACKEND = os.path.join(ROOT, "backend")
APP_PKG = os.path.join(BACKEND, "app")
FRONTEND_DIST = os.path.join(ROOT, "frontend", "dist")

if not os.path.isdir(APP_PKG):
    raise SystemExit(f"backend app package not found at {APP_PKG}")

if not os.path.isdir(FRONTEND_DIST) or not os.path.isfile(os.path.join(FRONTEND_DIST, "index.html")):
    raise SystemExit(
        f"frontend dist not found at {FRONTEND_DIST}.\n"
        f"Run:  cd frontend && npm install && npm run build  (then re-run pyinstaller)"
    )

# Bundle every backend python file under bundle path "app/...". This guarantees
# Flask blueprints can be found via normal import even when frozen.
datas = []
for dirpath, _dirnames, filenames in os.walk(APP_PKG):
    rel_dir = os.path.relpath(dirpath, BACKEND)
    for f in filenames:
        if f.endswith((".py", ".json", ".md")):
            datas.append((os.path.join(dirpath, f), rel_dir))

# Bundle the frontend build under bundle-root "frontend_dist".
for dirpath, _dirnames, filenames in os.walk(FRONTEND_DIST):
    rel = os.path.relpath(dirpath, FRONTEND_DIST)
    target = "frontend_dist" if rel == "." else os.path.join("frontend_dist", rel)
    for f in filenames:
        datas.append((os.path.join(dirpath, f), target))

# Only collect submodules for *our* backend package and the small set of
# packages whose Flask blueprints need string imports. Flask / SQLAlchemy /
# Pillow / pystray / waitress all have proper PyInstaller hooks already.
hiddenimports = []
for pkg in ("app", "app.api", "app.models", "app.services", "app.mcp"):
    try:
        hiddenimports.extend(collect_submodules(pkg))
    except Exception:
        pass

# Aggressively exclude packages that happen to be installed in this dev env
# but are NOT used by the runtime: Qt bindings, matplotlib, IPython, pygame,
# pytest, jupyter / nbformat, numpy, jedi, parso, etc. These get pulled in by
# transitive imports in things like flask test utilities and bloat / break
# the build (Qt bindings collide).
excludes = [
    "PyQt5", "PyQt6", "PySide2", "PySide6", "shiboken2", "shiboken6",
    "matplotlib", "scipy", "pandas", "numpy",
    "IPython", "ipykernel", "ipywidgets", "jupyter", "jupyter_client",
    "jupyter_core", "notebook", "nbformat", "nbconvert",
    "pytest", "_pytest", "py", "hypothesis", "coverage",
    "pygame",
    "jedi", "parso",
    "tornado",
    "lark",
    "regex",
    "cryptography.hazmat",
    "tkinter.test", "test",
]

a = Analysis(
    [os.path.join(HERE, "tray_app.py")],
    pathex=[HERE, BACKEND],
    binaries=[],
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AgentProjectConsole",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,            # no console window: pure tray app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(HERE, "icon.ico") if os.path.exists(os.path.join(HERE, "icon.ico")) else None,
)
