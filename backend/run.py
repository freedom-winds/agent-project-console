"""Run the Flask server."""
import os

from app import create_app
from app.config import Config


def main():
    app = create_app(Config)
    host = app.config.get("HOST", "127.0.0.1")
    port = app.config.get("PORT", 8765)
    print(f"[apc] Starting Agent Project Console on http://{host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
