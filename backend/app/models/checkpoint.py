"""Checkpoint model."""
import json
import uuid
from datetime import datetime

from ..extensions import db


def gen_id() -> str:
    return uuid.uuid4().hex


class Checkpoint(db.Model):
    __tablename__ = "checkpoints"

    id = db.Column(db.String(64), primary_key=True, default=gen_id)
    project_id = db.Column(db.String(64), db.ForeignKey("projects.id"), nullable=False, index=True)
    agent_name = db.Column(db.String(255), default="")
    current_focus_node_id = db.Column(db.String(64), default="")
    completed_json = db.Column(db.Text, default="[]")
    in_progress_json = db.Column(db.Text, default="[]")
    next_json = db.Column(db.Text, default="[]")
    blockers_json = db.Column(db.Text, default="[]")
    risks_json = db.Column(db.Text, default="[]")
    related_node_ids_json = db.Column(db.Text, default="[]")
    summary = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    @staticmethod
    def _load(s: str):
        try:
            return json.loads(s) if s else []
        except Exception:
            return []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "agent_name": self.agent_name or "",
            "current_focus_node_id": self.current_focus_node_id or "",
            "completed": self._load(self.completed_json),
            "in_progress": self._load(self.in_progress_json),
            "next": self._load(self.next_json),
            "blockers": self._load(self.blockers_json),
            "risks": self._load(self.risks_json),
            "related_node_ids": self._load(self.related_node_ids_json),
            "summary": self.summary or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
