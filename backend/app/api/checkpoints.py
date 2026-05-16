"""Checkpoint REST API."""
from flask import Blueprint, jsonify, request

from ..services import checkpoint_service
from ._utils import actor_from_request, auth_required, handle_validation

bp = Blueprint("checkpoints", __name__, url_prefix="/api/projects")


@bp.route("/<project_id>/checkpoints", methods=["GET"])
@auth_required()
@handle_validation
def list_checkpoints(project_id):
    limit = int(request.args.get("limit", "100"))
    return jsonify({"checkpoints": checkpoint_service.list_checkpoints(project_id, limit)})


@bp.route("/<project_id>/checkpoints", methods=["POST"])
@auth_required()
@handle_validation
def create_checkpoint(project_id):
    data = request.get_json(silent=True) or {}
    cp = checkpoint_service.create_checkpoint(
        project_id=project_id,
        agent_name=data.get("agent_name", ""),
        current_focus_node_id=data.get("current_focus_node_id", ""),
        completed=data.get("completed", []),
        in_progress=data.get("in_progress", []),
        next_items=data.get("next", []),
        blockers=data.get("blockers", []),
        risks=data.get("risks", []),
        related_node_ids=data.get("related_node_ids", []),
        summary=data.get("summary", ""),
        actor=actor_from_request(),
    )
    return jsonify(cp.to_dict()), 201
