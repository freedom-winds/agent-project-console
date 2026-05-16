"""MCP token service."""
import hashlib
import json
import secrets
from datetime import datetime
from typing import List, Optional

from ..extensions import db
from ..models.token import McpToken
from . import activity_service


VALID_SCOPES = {
    "read_project",
    "write_plan",
    "update_status",
    "write_evidence",
    "write_checkpoint",
    "admin",
}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def list_tokens() -> list:
    tokens = McpToken.query.order_by(McpToken.created_at.desc()).all()
    return [t.to_dict() for t in tokens]


def create_token(name: str, scopes: Optional[List[str]] = None, actor: str = "human") -> dict:
    name = (name or "").strip() or "default"
    scopes = list(scopes or ["read_project", "write_plan", "update_status", "write_evidence", "write_checkpoint"])
    invalid = [s for s in scopes if s not in VALID_SCOPES]
    if invalid:
        raise ValueError(f"invalid scopes: {invalid}")
    raw = "apc_" + secrets.token_urlsafe(36)
    token_hash = _hash_token(raw)
    preview = raw[:8] + "..." + raw[-4:]
    rec = McpToken(
        name=name,
        token_hash=token_hash,
        token_preview=preview,
        scopes_json=json.dumps(scopes),
    )
    db.session.add(rec)
    db.session.flush()
    activity_service.record(
        project_id=None,
        node_id=None,
        actor=actor or "human",
        action_type="token_created",
        before=None,
        after=rec.to_dict(),
        reason=f"token created: {name}",
    )
    db.session.commit()
    out = rec.to_dict()
    out["token"] = raw  # only returned at creation time
    return out


def revoke_token(token_id: str, actor: str = "human") -> None:
    rec = McpToken.query.get(token_id)
    if not rec:
        return
    rec.revoked_at = datetime.utcnow()
    activity_service.record(
        project_id=None,
        node_id=None,
        actor=actor or "human",
        action_type="token_revoked",
        before=None,
        after=rec.to_dict(),
        reason=f"token revoked: {rec.name}",
    )
    db.session.commit()


def verify_token(token: str) -> Optional[McpToken]:
    if not token:
        return None
    h = _hash_token(token)
    rec = McpToken.query.filter_by(token_hash=h).first()
    if not rec or rec.revoked_at is not None:
        return None
    rec.last_used_at = datetime.utcnow()
    db.session.commit()
    return rec
