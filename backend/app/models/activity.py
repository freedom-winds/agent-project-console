"""Activity log model."""
import json
import uuid
from datetime import datetime

from ..extensions import db


def gen_id() -> str:
    return uuid.uuid4().hex


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.String(64), primary_key=True, default=gen_id)
    project_id = db.Column(db.String(64), db.ForeignKey("projects.id"), nullable=True, index=True)
    node_id = db.Column(db.String(64), nullable=True, index=True)
    actor = db.Column(db.String(255), default="")
    action_type = db.Column(db.String(64), default="")
    before_json = db.Column(db.Text, default="")
    after_json = db.Column(db.Text, default="")
    reason = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self) -> dict:
        before = None
        after = None
        try:
            before = json.loads(self.before_json) if self.before_json else None
        except Exception:
            before = self.before_json
        try:
            after = json.loads(self.after_json) if self.after_json else None
        except Exception:
            after = self.after_json
        return {
            "id": self.id,
            "project_id": self.project_id,
            "node_id": self.node_id,
            "actor": self.actor or "",
            "action_type": self.action_type or "",
            "before": before,
            "after": after,
            "reason": self.reason or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
