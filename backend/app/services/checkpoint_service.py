"""Checkpoint service."""
import json
from typing import Optional, List

from ..extensions import db
from ..models.checkpoint import Checkpoint
from ..models.project import Project
from . import activity_service


class ValidationError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status
        self.message = message


def _dump(val) -> str:
    if val is None:
        return "[]"
    if isinstance(val, str):
        return val
    return json.dumps(val, ensure_ascii=False, default=str)


def create_checkpoint(
    project_id: str,
    agent_name: str = "",
    current_focus_node_id: str = "",
    completed: Optional[list] = None,
    in_progress: Optional[list] = None,
    next_items: Optional[list] = None,
    blockers: Optional[list] = None,
    risks: Optional[list] = None,
    related_node_ids: Optional[list] = None,
    summary: str = "",
    actor: str = "agent",
) -> Checkpoint:
    project = Project.query.get(project_id)
    if not project:
        raise ValidationError("project not found", 404)
    cp = Checkpoint(
        project_id=project_id,
        agent_name=agent_name or actor or "agent",
        current_focus_node_id=current_focus_node_id or "",
        completed_json=_dump(completed),
        in_progress_json=_dump(in_progress),
        next_json=_dump(next_items),
        blockers_json=_dump(blockers),
        risks_json=_dump(risks),
        related_node_ids_json=_dump(related_node_ids),
        summary=summary or "",
    )
    db.session.add(cp)
    db.session.flush()
    activity_service.record(
        project_id=project_id,
        node_id=current_focus_node_id or None,
        actor=actor or "agent",
        action_type="checkpoint_created",
        before=None,
        after=cp.to_dict(),
        reason=summary or "checkpoint created",
    )
    db.session.commit()
    return cp


def list_checkpoints(project_id: str, limit: int = 100) -> list:
    cps = (
        Checkpoint.query.filter_by(project_id=project_id)
        .order_by(Checkpoint.created_at.desc())
        .limit(limit)
        .all()
    )
    return [c.to_dict() for c in cps]
