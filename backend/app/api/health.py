"""Health endpoint."""
from flask import Blueprint, jsonify

bp = Blueprint("health", __name__)


@bp.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "agent-project-console", "version": "0.1.0"})
