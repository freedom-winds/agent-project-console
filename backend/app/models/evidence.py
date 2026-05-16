"""Evidence model."""
import uuid
from datetime import datetime

from ..extensions import db


def gen_id() -> str:
    return uuid.uuid4().hex


VALID_EVIDENCE_TYPES = {
    "file_path",
    "commit_hash",
    "command_output",
    "test_result",
    "screenshot_path",
    "url",
    "note",
}


class Evidence(db.Model):
    __tablename__ = "evidences"

    id = db.Column(db.String(64), primary_key=True, default=gen_id)
    node_id = db.Column(db.String(64), db.ForeignKey("nodes.id"), nullable=False, index=True)
    evidence_type = db.Column(db.String(32), default="note")
    title = db.Column(db.String(512), default="")
    content = db.Column(db.Text, default="")
    summary = db.Column(db.Text, default="")
    confidence = db.Column(db.String(16), default="medium")
    created_by = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "evidence_type": self.evidence_type,
            "title": self.title or "",
            "content": self.content or "",
            "summary": self.summary or "",
            "confidence": self.confidence or "medium",
            "created_by": self.created_by or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
