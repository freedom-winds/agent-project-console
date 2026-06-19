"""Agent Project Console backend application package."""
import os
import sys
from flask import Flask, jsonify, send_from_directory, abort
from flask_cors import CORS

from .extensions import db
from .config import Config


def _resolve_frontend_dist() -> str | None:
    """Locate the built frontend (frontend/dist).

    Search order:
      1. APC_FRONTEND_DIST env var
      2. <repo>/frontend/dist when running from source
      3. <pyinstaller bundle>/frontend_dist (used by the tray exe)
    """
    env_dir = os.environ.get("APC_FRONTEND_DIST")
    if env_dir and os.path.isdir(env_dir):
        return env_dir

    here = os.path.abspath(os.path.dirname(__file__))
    candidates = [
        os.path.join(here, "..", "..", "frontend", "dist"),
        os.path.join(here, "..", "frontend_dist"),
    ]
    # PyInstaller one-file bundle: data is unpacked into sys._MEIPASS.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.insert(0, os.path.join(meipass, "frontend_dist"))

    for c in candidates:
        c_abs = os.path.abspath(c)
        if os.path.isdir(c_abs) and os.path.exists(os.path.join(c_abs, "index.html")):
            return c_abs
    return None


def create_app(config_object: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.json.ensure_ascii = False

    # Ensure instance directory exists for SQLite
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("sqlite:///"):
        db_path = db_uri.replace("sqlite:///", "", 1)
        if db_path and not os.path.isabs(db_path):
            db_path = os.path.join(app.root_path, "..", db_path)
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    from .database_recovery import ensure_sqlite_database
    recovery_report = ensure_sqlite_database(
        db_uri,
        relative_to=os.path.join(app.root_path, ".."),
    )
    app.config["APC_DATABASE_RECOVERY"] = (
        recovery_report.to_dict() if recovery_report else None
    )

    db.init_app(app)

    # CORS for local dev only
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["http://127.0.0.1:5173", "http://localhost:5173"])}},
        supports_credentials=False,
    )

    # Register blueprints
    from .api.projects import bp as projects_bp
    from .api.nodes import bp as nodes_bp
    from .api.activity import bp as activity_bp
    from .api.checkpoints import bp as checkpoints_bp
    from .api.settings import bp as settings_bp
    from .api.health import bp as health_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(nodes_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(checkpoints_bp)
    app.register_blueprint(settings_bp)

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "bad_request", "message": str(e.description) if hasattr(e, "description") else str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not_found", "message": "resource not found"}), 404

    @app.errorhandler(500)
    def server_err(e):
        return jsonify({"error": "internal_error", "message": "internal server error"}), 500

    @app.cli.command("init-db")
    def init_db_cmd():
        """Initialize the database (create tables)."""
        with app.app_context():
            from . import models  # noqa: F401
            db.create_all()
            print("Database initialized.")

    # Auto-create tables on startup for MVP convenience
    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()

    # Serve the built frontend (single-port deploy / packaged exe).
    # We register the SPA fallback *unconditionally* so packaging order can't
    # accidentally drop the routes. The handler resolves the dist dir on each
    # request, which is cheap and lets the launcher set APC_FRONTEND_DIST late.
    initial_dist = _resolve_frontend_dist()
    app.config["APC_FRONTEND_DIST"] = initial_dist or ""

    @app.route("/__apc_debug__")
    def _apc_debug():
        return jsonify({
            "frontend_dist": _resolve_frontend_dist(),
            "env_APC_FRONTEND_DIST": os.environ.get("APC_FRONTEND_DIST"),
            "_MEIPASS": getattr(sys, "_MEIPASS", None),
            "frozen": getattr(sys, "frozen", False),
        })

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def _serve_frontend(path: str):
        if path.startswith("api/"):
            abort(404)
        dist_dir = _resolve_frontend_dist()
        if not dist_dir:
            return jsonify({
                "error": "frontend_not_built",
                "message": "Run `npm run build` in frontend/ or set APC_FRONTEND_DIST.",
            }), 503
        full = os.path.join(dist_dir, path)
        if path and os.path.isfile(full):
            return send_from_directory(dist_dir, path)
        return send_from_directory(dist_dir, "index.html")

    return app
