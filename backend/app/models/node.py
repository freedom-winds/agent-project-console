"""Node model representing Part / Phase / Step."""
import uuid
from datetime import datetime

from ..extensions import db


def gen_id() -> str:
    return uuid.uuid4().hex


VALID_NODE_TYPES = {"part", "phase", "step"}
VALID_NODE_STATUS = {
    "planned",
    "ready",
    "in_progress",
    "blocked",
    "review",
    "done",
    "skipped",
    "cancelled",
}
VALID_PRIORITY = {"low", "medium", "high", "critical"}
VALID_RISK = {"none", "low", "medium", "high", "critical"}


class Node(db.Model):
    __tablename__ = "nodes"

    id = db.Column(db.String(64), primary_key=True, default=gen_id)
    project_id = db.Column(db.String(64), db.ForeignKey("projects.id"), nullable=False, index=True)
    parent_id = db.Column(db.String(64), db.ForeignKey("nodes.id"), nullable=True, index=True)
    node_type = db.Column(db.String(16), nullable=False)
    title = db.Column(db.String(512), nullable=False, default="")
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(32), default="planned")
    priority = db.Column(db.String(16), default="medium")
    progress = db.Column(db.Float, default=0.0)
    owner = db.Column(db.String(255), default="")
    sort_order = db.Column(db.Integer, default=0)
    risk_level = db.Column(db.String(16), default="none")
    acceptance_criteria = db.Column(db.Text, default="")
    evidence_summary = db.Column(db.Text, default="")
    latest_note = db.Column(db.Text, default="")
    override_reason = db.Column(db.Text, default="")
    blocker_reason = db.Column(db.Text, default="")
    blocker_impact = db.Column(db.Text, default="")
    next_action = db.Column(db.Text, default="")
    needs_human = db.Column(db.Boolean, default=False)
    tags = db.Column(db.Text, default="")  # comma separated
    created_by = db.Column(db.String(255), default="")
    updated_by = db.Column(db.String(255), default="")
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    due_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "parent_id": self.parent_id,
            "node_type": self.node_type,
            "title": self.title or "",
            "description": self.description or "",
            "status": self.status,
            "priority": self.priority,
            "progress": float(self.progress or 0),
            "owner": self.owner or "",
            "sort_order": self.sort_order or 0,
            "risk_level": self.risk_level or "none",
            "acceptance_criteria": self.acceptance_criteria or "",
            "evidence_summary": self.evidence_summary or "",
            "latest_note": self.latest_note or "",
            "override_reason": self.override_reason or "",
            "blocker_reason": self.blocker_reason or "",
            "blocker_impact": self.blocker_impact or "",
            "next_action": self.next_action or "",
            "needs_human": bool(self.needs_human),
            "tags": [t for t in (self.tags or "").split(",") if t],
            "created_by": self.created_by or "",
            "updated_by": self.updated_by or "",
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
