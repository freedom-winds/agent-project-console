"""MCP token model."""
import json
import uuid
from datetime import datetime

from ..extensions import db


def gen_id() -> str:
    return uuid.uuid4().hex


class McpToken(db.Model):
    __tablename__ = "mcp_tokens"

    id = db.Column(db.String(64), primary_key=True, default=gen_id)
    name = db.Column(db.String(255), nullable=False)
    token_hash = db.Column(db.String(128), nullable=False, index=True)
    token_preview = db.Column(db.String(32), default="")
    scopes_json = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        try:
            scopes = json.loads(self.scopes_json) if self.scopes_json else []
        except Exception:
            scopes = []
        return {
            "id": self.id,
            "name": self.name,
            "token_preview": self.token_preview or "",
            "scopes": scopes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }
