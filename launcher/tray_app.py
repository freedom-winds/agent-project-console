"""Agent Project Console - Windows tray launcher.

Double-clicking the produced .exe will:
  1. Show a brief startup popup ("Agent Project Console is starting...").
  2. Start the Flask backend (which also serves the built React frontend) on
     http://127.0.0.1:8765 in a background thread.
  3. Show a tray icon (Windows: appears under "Hidden icons" by default) with
     a right-click menu:
       - 打开网页端 (Open Web UI)
       - 重启服务 (Restart Services)
       - 关闭服务 (Stop & Exit)

The whole thing runs silently in the tray after the popup closes.

Usage when developing:
    python launcher/tray_app.py

Build the exe (Windows):
    cd agent-project-console
    pip install -r launcher/requirements.txt
    cd frontend && npm install && npm run build && cd ..
    pyinstaller launcher/tray_app.spec
    # output: dist/AgentProjectConsole.exe
"""
from __future__ import annotations

import os
import sys
import time
import threading
import webbrowser
from typing import Optional

# ---------------------------------------------------------------------------
# Make the bundled "backend/app" package importable, both when running from
# source and when running from a PyInstaller --onefile bundle.
# ---------------------------------------------------------------------------
HERE = os.path.abspath(os.path.dirname(__file__))


def _resource_root() -> str:
    """Return the directory holding the embedded `app/` package + frontend_dist/."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return meipass
    # Running from source: launcher/ is a sibling of backend/ and frontend/.
    return os.path.abspath(os.path.join(HERE, ".."))


def _ensure_paths() -> None:
    root = _resource_root()
    diag_lines = [
        f"resource_root={root}",
        f"sys._MEIPASS={getattr(sys, '_MEIPASS', None)}",
        f"sys.frozen={getattr(sys, 'frozen', None)}",
        f"sys.executable={sys.executable}",
        f"__file__={__file__}",
        f"HERE={HERE}",
    ]
    # Source layout: <root>/backend/app
    backend = os.path.join(root, "backend")
    if os.path.isdir(os.path.join(backend, "app")) and backend not in sys.path:
        sys.path.insert(0, backend)
        diag_lines.append(f"sys.path += {backend}")
    # Bundle layout: <root>/app
    if os.path.isdir(os.path.join(root, "app")) and root not in sys.path:
        sys.path.insert(0, root)
        diag_lines.append(f"sys.path += {root}")

    # Tell the Flask app where the frontend/dist lives.
    if "APC_FRONTEND_DIST" not in os.environ:
        for cand in (
            os.path.join(root, "frontend_dist"),
            os.path.join(root, "frontend", "dist"),
        ):
            diag_lines.append(f"frontend cand: {cand} exists={os.path.isdir(cand)}")
            if os.path.isdir(cand) and os.path.exists(os.path.join(cand, "index.html")):
                os.environ["APC_FRONTEND_DIST"] = cand
                diag_lines.append(f"set APC_FRONTEND_DIST={cand}")
                break

    # Write a diagnostics file so we can inspect what the exe saw.
    try:
        log_dir = os.path.join(
            os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"),
            "AgentProjectConsole",
        )
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "launcher_debug.log"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(diag_lines) + "\n")
    except Exception:
        pass

    # Use a writable location for the SQLite DB. PyInstaller bundle dirs are
    # read-only on some setups, so default to %LOCALAPPDATA%\AgentProjectConsole.
    if "APC_DATABASE_URI" not in os.environ:
        if sys.platform.startswith("win"):
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        else:
            base = os.path.expanduser("~/.local/share")
        data_dir = os.path.join(base, "AgentProjectConsole")
        os.makedirs(data_dir, exist_ok=True)
        os.environ["APC_DATABASE_URI"] = "sqlite:///" + os.path.join(data_dir, "apc.sqlite3")


_ensure_paths()

# Imports that depend on sys.path being set:
from PIL import Image, ImageDraw  # noqa: E402
import pystray  # noqa: E402

HOST = os.environ.get("APC_HOST", "127.0.0.1")
PORT = int(os.environ.get("APC_PORT", "8765"))
URL = f"http://{HOST}:{PORT}"


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------
class ServerController:
    """Start / stop the Flask app inside a background thread, using waitress."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._thread: Optional[threading.Thread] = None
        self._server = None  # waitress.create_server() result
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._run, daemon=True, name="apc-backend")
            self._thread.start()
        # Best-effort wait until the port responds.
        self._wait_ready(timeout=12.0)

    def stop(self) -> None:
        with self._lock:
            srv = self._server
            self._server = None
        if srv is not None:
            try:
                srv.close()
            except Exception:
                pass
        # Give the thread a moment to exit; do not block UI.
        if self._thread:
            self._thread.join(timeout=3.0)

    def restart(self) -> None:
        self.stop()
        # Allow the OS to free the port.
        time.sleep(0.3)
        self.start()

    # internals -------------------------------------------------------------
    def _run(self) -> None:
        try:
            from app import create_app  # type: ignore[import-not-found]
            from app.config import Config  # type: ignore[import-not-found]
            from waitress import create_server
        except Exception as e:  # pragma: no cover - shown to the user
            _show_error(f"Failed to import backend:\n{e}")
            return

        try:
            flask_app = create_app(Config)
            recovery = flask_app.config.get("APC_DATABASE_RECOVERY")
            if recovery:
                recovered_rows = sum(recovery["recovered_rows"].values())
                restored_rows = sum(recovery["restored_from_activity"].values())
                skipped_rows = sum(recovery["skipped_rows"].values())
                _show_warning(
                    "The SQLite database was damaged and has been recovered.\n\n"
                    f"Recovered rows: {recovered_rows}\n"
                    f"Restored from activity history: {restored_rows}\n"
                    f"Unreadable rows skipped: {skipped_rows}\n"
                    f"Backup: {recovery['backup_path']}"
                )
            server = create_server(flask_app, host=self.host, port=self.port, threads=8)
            self._server = server
            print(f"[apc] backend listening on http://{self.host}:{self.port}", flush=True)
            server.run()
        except Exception as e:  # pragma: no cover
            _show_error(f"Backend crashed:\n{e}")

    def _wait_ready(self, timeout: float) -> None:
        import socket

        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with socket.create_connection((self.host, self.port), timeout=0.5):
                    return
            except OSError:
                time.sleep(0.2)


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def _build_icon_image() -> Image.Image:
    """Create a simple cockpit-style icon if no .ico is bundled.

    The icon: dark navy background with a white tree-like shape.
    """
    bundled = os.path.join(_resource_root(), "icon.png")
    if os.path.exists(bundled):
        try:
            return Image.open(bundled).convert("RGBA")
        except Exception:
            pass

    size = 64
    img = Image.new("RGBA", (size, size), (11, 16, 32, 255))  # #0B1020
    d = ImageDraw.Draw(img)
    # Trunk
    d.rectangle([28, 36, 36, 56], fill=(96, 165, 250, 255))  # blue 400
    # Three layers (wide → narrow)
    d.polygon([(12, 38), (52, 38), (32, 22)], fill=(34, 197, 94, 255))   # green
    d.polygon([(16, 28), (48, 28), (32, 14)], fill=(96, 165, 250, 255))  # blue
    d.polygon([(20, 18), (44, 18), (32, 6)], fill=(167, 139, 250, 255))  # purple
    return img


def _show_startup_popup(url: str) -> None:
    """Show a small auto-closing popup announcing startup. Does not block."""

    def _show():
        try:
            import tkinter as tk
        except Exception:
            return  # Tk not available; silently skip.
        root = tk.Tk()
        root.title("Agent Project Console")
        root.configure(bg="#0B1020")
        root.attributes("-topmost", True)
        root.resizable(False, False)
        # Center the small dialog
        w, h = 380, 130
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 3
        root.geometry(f"{w}x{h}+{x}+{y}")
        try:
            root.iconbitmap(default="")
        except Exception:
            pass

        title = tk.Label(
            root,
            text="Agent Project Console",
            fg="#E5E7EB",
            bg="#0B1020",
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(pady=(16, 4))
        msg = tk.Label(
            root,
            text=f"服务已启动\n{url}\n\n本窗口将自动关闭，应用图标位于任务栏的“隐藏的图标”内",
            fg="#9CA3AF",
            bg="#0B1020",
            font=("Segoe UI", 9),
            justify="center",
        )
        msg.pack(pady=(0, 12))
        root.after(2500, root.destroy)
        root.mainloop()

    threading.Thread(target=_show, daemon=True).start()


def _show_error(text: str) -> None:
    def _go():
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk()
            r.withdraw()
            messagebox.showerror("Agent Project Console", text)
            r.destroy()
        except Exception:
            print(text, file=sys.stderr)
    threading.Thread(target=_go, daemon=True).start()


def _show_warning(text: str) -> None:
    def _go():
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk()
            r.withdraw()
            messagebox.showwarning("Agent Project Console", text)
            r.destroy()
        except Exception:
            print(text, file=sys.stderr)
    threading.Thread(target=_go, daemon=True).start()


# ---------------------------------------------------------------------------
# Tray icon
# ---------------------------------------------------------------------------
def _build_tray(controller: ServerController) -> "pystray.Icon":
    def on_open(_icon, _item):
        webbrowser.open(URL, new=2)

    def on_restart(icon, _item):
        icon.notify("正在重启服务...", "Agent Project Console")
        try:
            controller.restart()
            icon.notify("服务已重启", "Agent Project Console")
        except Exception as e:
            _show_error(f"Restart failed:\n{e}")

    def on_quit(icon, _item):
        icon.notify("正在关闭服务...", "Agent Project Console")
        try:
            controller.stop()
        finally:
            icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("打开网页端", on_open, default=True),
        pystray.MenuItem("重启服务", on_restart),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("关闭服务", on_quit),
    )
    icon = pystray.Icon(
        "agent-project-console",
        _build_icon_image(),
        "Agent Project Console",
        menu,
    )
    return icon


# ---------------------------------------------------------------------------
# Single-instance guard (Windows-friendly): bind a local TCP port.
# ---------------------------------------------------------------------------
def _acquire_single_instance() -> Optional[object]:
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", 58765))
        s.listen(1)
        return s
    except OSError:
        return None


def main() -> int:
    guard = _acquire_single_instance()
    if guard is None:
        _show_error("Agent Project Console 已经在运行。\n请在任务栏“隐藏的图标”里查看。")
        # Try to open the web page so the user sees the existing instance.
        try:
            webbrowser.open(URL, new=2)
        except Exception:
            pass
        return 0

    controller = ServerController(HOST, PORT)
    _show_startup_popup(URL)

    try:
        controller.start()
    except Exception as e:
        _show_error(f"Failed to start backend:\n{e}")
        return 2

    icon = _build_tray(controller)
    # icon.run() blocks on the main thread until icon.stop() is called.
    try:
        icon.run()
    finally:
        controller.stop()
        try:
            guard.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
