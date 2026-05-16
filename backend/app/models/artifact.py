"""Artifact model."""
import uuid
from datetime import datetime

from ..extensions import db


def gen_id() -> str:
    return uuid.uuid4().hex


class Artifact(db.Model):
    __tablename__ = "artifacts"

    id = db.Column(db.String(64), primary_key=True, default=gen_id)
    node_id = db.Column(db.String(64), db.ForeignKey("nodes.id"), nullable=False, index=True)
    artifact_type = db.Column(db.String(32), default="document")
    title = db.Column(db.String(512), default="")
    path_or_url = db.Column(db.String(2048), default="")
    summary = db.Column(db.Text, default="")
    created_by = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "artifact_type": self.artifact_type,
            "title": self.title or "",
            "path_or_url": self.path_or_url or "",
            "summary": self.summary or "",
            "created_by": self.created_by or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
