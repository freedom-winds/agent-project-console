"""Node REST API."""
from flask import Blueprint, jsonify, request

from ..services import node_service, evidence_service
from ._utils import actor_from_request, auth_required, handle_validation, json_error

bp = Blueprint("nodes", __name__, url_prefix="/api/nodes")


@bp.route("", methods=["POST"])
@auth_required()
@handle_validation
def create_node():
    data = request.get_json(silent=True) or {}
    node = node_service.create_node(
        project_id=data.get("project_id", ""),
        parent_id=data.get("parent_id"),
        node_type=data.get("node_type", ""),
        title=data.get("title", ""),
        description=data.get("description", ""),
        acceptance_criteria=data.get("acceptance_criteria", ""),
        priority=data.get("priority", "medium"),
        tags=data.get("tags"),
        owner=data.get("owner", ""),
        actor=actor_from_request(),
        reason=data.get("reason", ""),
    )
    return jsonify(node.to_dict()), 201


@bp.route("/<node_id>", methods=["GET"])
@auth_required()
@handle_validation
def get_node(node_id):
    from ..models.node import Node
    node = Node.query.get(node_id)
    if not node or node.deleted_at is not None:
        return json_error("node not found", 404)
    out = node.to_dict()
    out["evidences"] = evidence_service.list_evidence(node_id)
    out["artifacts"] = evidence_service.list_artifacts(node_id)
    return jsonify(out)


@bp.route("/<node_id>", methods=["PATCH"])
@auth_required()
@handle_validation
def patch_node(node_id):
    data = request.get_json(silent=True) or {}
    reason = data.pop("reason", "")
    node = node_service.update_node(node_id, actor=actor_from_request(), reason=reason, **data)
    return jsonify(node.to_dict())


@bp.route("/<node_id>", methods=["DELETE"])
@auth_required()
@handle_validation
def delete_node(node_id):
    reason = (request.args.get("reason") or "").strip()
    if not reason:
        body = request.get_json(silent=True) or {}
        reason = body.get("reason", "")
    node_service.delete_node(node_id, actor=actor_from_request(), reason=reason)
    return jsonify({"ok": True})


@bp.route("/<node_id>/status", methods=["POST"])
@auth_required()
@handle_validation
def update_status(node_id):
    data = request.get_json(silent=True) or {}
    node = node_service.update_status(
        node_id=node_id,
        status=data.get("status", ""),
        progress=data.get("progress"),
        evidence_summary=data.get("evidence_summary", ""),
        blocker_reason=data.get("blocker_reason", ""),
        impact=data.get("impact", ""),
        next_action=data.get("next_action", ""),
        needs_human=data.get("needs_human"),
        rollback_reason=data.get("rollback_reason", ""),
        override_reason=data.get("override_reason", ""),
        actor=actor_from_request(),
        reason=data.get("reason", ""),
    )
    return jsonify(node.to_dict())


@bp.route("/<node_id>/evidence", methods=["POST"])
@auth_required()
@handle_validation
def add_evidence(node_id):
    data = request.get_json(silent=True) or {}
    ev = evidence_service.add_evidence(
        node_id=node_id,
        evidence_type=data.get("evidence_type", "note"),
        title=data.get("title", ""),
        content=data.get("content", ""),
        summary=data.get("summary", ""),
        confidence=data.get("confidence", "medium"),
        actor=actor_from_request(),
    )
    return jsonify(ev.to_dict()), 201


@bp.route("/<node_id>/evidence", methods=["GET"])
@auth_required()
@handle_validation
def list_evidence(node_id):
    return jsonify({"evidences": evidence_service.list_evidence(node_id)})


@bp.route("/<node_id>/artifacts", methods=["POST"])
@auth_required()
@handle_validation
def add_artifact(node_id):
    data = request.get_json(silent=True) or {}
    art = evidence_service.add_artifact(
        node_id=node_id,
        artifact_type=data.get("artifact_type", "document"),
        title=data.get("title", ""),
        path_or_url=data.get("path_or_url", ""),
        summary=data.get("summary", ""),
        actor=actor_from_request(),
    )
    return jsonify(art.to_dict()), 201


@bp.route("/<node_id>/artifacts", methods=["GET"])
@auth_required()
@handle_validation
def list_artifacts(node_id):
    return jsonify({"artifacts": evidence_service.list_artifacts(node_id)})


@bp.route("/<node_id>/move", methods=["POST"])
@auth_required()
@handle_validation
def move(node_id):
    data = request.get_json(silent=True) or {}
    node = node_service.move_node(
        node_id=node_id,
        new_parent_id=data.get("new_parent_id"),
        new_sort_order=data.get("new_sort_order"),
        actor=actor_from_request(),
        reason=data.get("reason", ""),
    )
    return jsonify(node.to_dict())


@bp.route("/<node_id>/blocker", methods=["POST"])
@auth_required()
@handle_validation
def report_blocker(node_id):
    data = request.get_json(silent=True) or {}
    node = node_service.report_blocker(
        node_id=node_id,
        blocker_reason=data.get("blocker_reason", ""),
        impact=data.get("impact", ""),
        next_action=data.get("next_action", ""),
        needs_human=bool(data.get("needs_human", False)),
        actor=actor_from_request(),
    )
    return jsonify(node.to_dict())


@bp.route("/<node_id>/blocker/resolve", methods=["POST"])
@auth_required()
@handle_validation
def resolve_blocker(node_id):
    data = request.get_json(silent=True) or {}
    node = node_service.resolve_blocker(
        node_id=node_id,
        resolution=data.get("resolution", ""),
        evidence_summary=data.get("evidence_summary", ""),
        actor=actor_from_request(),
    )
    return jsonify(node.to_dict())
