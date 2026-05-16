"""Project REST API."""
from flask import Blueprint, jsonify, request

from ..services import project_service, node_service
from ._utils import actor_from_request, auth_required, handle_validation, json_error

bp = Blueprint("projects", __name__, url_prefix="/api/projects")


@bp.route("", methods=["GET"])
@auth_required()
@handle_validation
def list_projects():
    return jsonify({"projects": project_service.list_projects()})


@bp.route("", methods=["POST"])
@auth_required()
@handle_validation
def create_project():
    data = request.get_json(silent=True) or {}
    project = project_service.create_project(
        name=data.get("name", ""),
        description=data.get("description", ""),
        local_path=data.get("local_path", ""),
        repo_url=data.get("repo_url", ""),
        default_branch=data.get("default_branch", "main"),
        status=data.get("status", "planning"),
        active_agent=data.get("active_agent", ""),
        actor=actor_from_request(),
    )
    return jsonify(project.to_dict()), 201


@bp.route("/<project_id>", methods=["GET"])
@auth_required()
@handle_validation
def get_project(project_id):
    project = project_service.get_project(project_id)
    return jsonify(project.to_dict())


@bp.route("/<project_id>", methods=["PATCH"])
@auth_required()
@handle_validation
def patch_project(project_id):
    data = request.get_json(silent=True) or {}
    reason = data.pop("reason", "")
    project = project_service.update_project(project_id, actor=actor_from_request(), reason=reason, **data)
    return jsonify(project.to_dict())


@bp.route("/<project_id>/tree", methods=["GET"])
@auth_required()
@handle_validation
def get_tree(project_id):
    include_done = request.args.get("include_done", "true").lower() != "false"
    return jsonify(node_service.get_project_tree(project_id, include_done=include_done))


@bp.route("/<project_id>/focus", methods=["POST"])
@auth_required()
@handle_validation
def set_focus(project_id):
    data = request.get_json(silent=True) or {}
    project = project_service.set_current_focus(
        project_id=project_id,
        node_id=data.get("node_id", ""),
        actor=actor_from_request(),
        reason=data.get("reason", ""),
    )
    return jsonify(project.to_dict())


@bp.route("/<project_id>/search", methods=["GET"])
@auth_required()
@handle_validation
def search(project_id):
    q = request.args.get("q", "")
    statuses = [s for s in request.args.get("status", "").split(",") if s]
    tags = [t for t in request.args.get("tags", "").split(",") if t]
    return jsonify({"results": node_service.search_nodes(project_id, q, statuses or None, tags or None)})
