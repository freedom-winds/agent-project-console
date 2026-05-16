"""Project model."""
import uuid
from datetime import datetime

from ..extensions import db


def gen_id() -> str:
    return uuid.uuid4().hex


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.String(64), primary_key=True, default=gen_id)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, default="")
    local_path = db.Column(db.String(1024), default="")
    repo_url = db.Column(db.String(1024), default="")
    default_branch = db.Column(db.String(255), default="main")
    status = db.Column(db.String(32), default="planning")
    progress = db.Column(db.Float, default=0.0)
    active_agent = db.Column(db.String(255), default="")
    current_focus_node_id = db.Column(db.String(64), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "local_path": self.local_path or "",
            "repo_url": self.repo_url or "",
            "default_branch": self.default_branch or "main",
            "status": self.status,
            "progress": float(self.progress or 0),
            "active_agent": self.active_agent or "",
            "current_focus_node_id": self.current_focus_node_id or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
