"""Activity REST API."""
from flask import Blueprint, jsonify, request

from ..models.activity import Activity
from ._utils import auth_required, handle_validation

bp = Blueprint("activity", __name__, url_prefix="/api")


@bp.route("/projects/<project_id>/activity", methods=["GET"])
@auth_required()
@handle_validation
def list_activity(project_id):
    limit = int(request.args.get("limit", "200"))
    items = (
        Activity.query.filter_by(project_id=project_id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify({"activities": [a.to_dict() for a in items]})


@bp.route("/activity", methods=["GET"])
@auth_required()
@handle_validation
def list_activity_global():
    limit = int(request.args.get("limit", "200"))
    items = Activity.query.order_by(Activity.created_at.desc()).limit(limit).all()
    return jsonify({"activities": [a.to_dict() for a in items]})
