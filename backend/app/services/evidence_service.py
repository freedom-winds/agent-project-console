"""Evidence and artifact services."""
from ..extensions import db
from ..models.node import Node
from ..models.evidence import Evidence, VALID_EVIDENCE_TYPES
from ..models.artifact import Artifact
from . import activity_service


class ValidationError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status
        self.message = message


def add_evidence(
    node_id: str,
    evidence_type: str,
    title: str,
    content: str = "",
    summary: str = "",
    confidence: str = "medium",
    actor: str = "agent",
) -> Evidence:
    node = Node.query.get(node_id)
    if not node or node.deleted_at is not None:
        raise ValidationError("node not found", 404)
    if evidence_type not in VALID_EVIDENCE_TYPES:
        raise ValidationError(
            f"invalid evidence_type. allowed: {sorted(VALID_EVIDENCE_TYPES)}"
        )
    if not title or not title.strip():
        raise ValidationError("title is required")
    ev = Evidence(
        node_id=node_id,
        evidence_type=evidence_type,
        title=title.strip(),
        content=content or "",
        summary=summary or "",
        confidence=confidence or "medium",
        created_by=actor or "agent",
    )
    db.session.add(ev)
    # Also update node.evidence_summary as a quick synopsis if empty
    if summary and not (node.evidence_summary or "").strip():
        node.evidence_summary = summary
    db.session.flush()
    activity_service.record(
        project_id=node.project_id,
        node_id=node.id,
        actor=actor or "agent",
        action_type="evidence_added",
        before=None,
        after=ev.to_dict(),
        reason=summary or title,
    )
    db.session.commit()
    return ev


def list_evidence(node_id: str) -> list:
    items = (
        Evidence.query.filter_by(node_id=node_id)
        .order_by(Evidence.created_at.desc())
        .all()
    )
    return [e.to_dict() for e in items]


def add_artifact(
    node_id: str,
    artifact_type: str,
    title: str,
    path_or_url: str = "",
    summary: str = "",
    actor: str = "agent",
) -> Artifact:
    node = Node.query.get(node_id)
    if not node or node.deleted_at is not None:
        raise ValidationError("node not found", 404)
    if not title or not title.strip():
        raise ValidationError("title is required")
    art = Artifact(
        node_id=node_id,
        artifact_type=artifact_type or "document",
        title=title.strip(),
        path_or_url=path_or_url or "",
        summary=summary or "",
        created_by=actor or "agent",
    )
    db.session.add(art)
    db.session.flush()
    activity_service.record(
        project_id=node.project_id,
        node_id=node.id,
        actor=actor or "agent",
        action_type="artifact_added",
        before=None,
        after=art.to_dict(),
        reason=summary or title,
    )
    db.session.commit()
    return art


def list_artifacts(node_id: str) -> list:
    items = (
        Artifact.query.filter_by(node_id=node_id)
        .order_by(Artifact.created_at.desc())
        .all()
    )
    return [a.to_dict() for a in items]
