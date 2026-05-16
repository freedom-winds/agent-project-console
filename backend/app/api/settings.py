"""Settings & MCP token REST API."""
from flask import Blueprint, jsonify, request

from ..services import token_service
from ._utils import actor_from_request, auth_required, handle_validation, json_error

bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@bp.route("/tokens", methods=["GET"])
@auth_required()
@handle_validation
def list_tokens():
    return jsonify({"tokens": token_service.list_tokens()})


@bp.route("/tokens", methods=["POST"])
@auth_required()
@handle_validation
def create_token():
    data = request.get_json(silent=True) or {}
    try:
        record = token_service.create_token(
            name=data.get("name", ""),
            scopes=data.get("scopes"),
            actor=actor_from_request(),
        )
    except ValueError as e:
        return json_error(str(e), 400)
    return jsonify(record), 201


@bp.route("/tokens/<token_id>", methods=["DELETE"])
@auth_required()
@handle_validation
def revoke_token(token_id):
    token_service.revoke_token(token_id, actor=actor_from_request())
    return jsonify({"ok": True})
