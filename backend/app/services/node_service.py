"""Node service: hierarchy validation, CRUD, status updates."""
from datetime import datetime
from typing import Optional, List

from ..extensions import db
from ..models.node import (
    Node,
    VALID_NODE_TYPES,
    VALID_NODE_STATUS,
    VALID_PRIORITY,
    VALID_RISK,
)
from ..models.project import Project
from . import activity_service, progress_service


class ValidationError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status
        self.message = message


def _ensure_project(project_id: str) -> Project:
    project = Project.query.get(project_id)
    if not project:
        raise ValidationError("project not found", 404)
    return project


def _validate_hierarchy(project_id: str, parent_id: Optional[str], node_type: str) -> None:
    if node_type not in VALID_NODE_TYPES:
        raise ValidationError(
            f"invalid node_type '{node_type}'. must be one of {sorted(VALID_NODE_TYPES)}"
        )
    if node_type == "part":
        if parent_id:
            raise ValidationError("part nodes must have parent_id=null (root under project)")
        return
    if not parent_id:
        raise ValidationError(f"{node_type} requires parent_id")
    parent = Node.query.get(parent_id)
    if not parent or parent.deleted_at is not None:
        raise ValidationError("parent node not found")
    if parent.project_id != project_id:
        raise ValidationError("parent node belongs to a different project")
    if node_type == "phase" and parent.node_type != "part":
        raise ValidationError("phase parent must be a part")
    if node_type == "step" and parent.node_type != "phase":
        raise ValidationError("step parent must be a phase")


def _next_sort_order(project_id: str, parent_id: Optional[str]) -> int:
    q = Node.query.filter_by(project_id=project_id, deleted_at=None)
    if parent_id is None:
        q = q.filter(Node.parent_id.is_(None))
    else:
        q = q.filter(Node.parent_id == parent_id)
    existing = q.all()
    if not existing:
        return 0
    return max(int(n.sort_order or 0) for n in existing) + 1


def _join_tags(tags) -> str:
    if not tags:
        return ""
    if isinstance(tags, str):
        return tags
    return ",".join([str(t).strip() for t in tags if str(t).strip()])


def create_node(
    project_id: str,
    parent_id: Optional[str],
    node_type: str,
    title: str,
    description: str = "",
    acceptance_criteria: str = "",
    priority: str = "medium",
    tags=None,
    owner: str = "",
    actor: str = "human",
    reason: str = "",
) -> Node:
    project = _ensure_project(project_id)
    _validate_hierarchy(project_id, parent_id, node_type)
    if priority not in VALID_PRIORITY:
        priority = "medium"
    if not title or not title.strip():
        raise ValidationError("title is required")

    node = Node(
        project_id=project_id,
        parent_id=parent_id,
        node_type=node_type,
        title=title.strip(),
        description=description or "",
        acceptance_criteria=acceptance_criteria or "",
        priority=priority,
        owner=owner or "",
        tags=_join_tags(tags),
        sort_order=_next_sort_order(project_id, parent_id),
        created_by=actor or "human",
        updated_by=actor or "human",
        status="planned",
        progress=0.0,
    )
    db.session.add(node)
    db.session.flush()

    activity_service.record(
        project_id=project_id,
        node_id=node.id,
        actor=actor or "human",
        action_type="node_created",
        before=None,
        after=node.to_dict(),
        reason=reason,
    )
    progress_service.recalc_for_node(node)
    db.session.commit()
    return node


def update_node(
    node_id: str,
    actor: str = "human",
    reason: str = "",
    **fields,
) -> Node:
    node = Node.query.get(node_id)
    if not node or node.deleted_at is not None:
        raise ValidationError("node not found", 404)
    before = node.to_dict()

    if "title" in fields and fields["title"] is not None:
        title = str(fields["title"]).strip()
        if not title:
            raise ValidationError("title cannot be empty")
        node.title = title
    if "description" in fields and fields["description"] is not None:
        node.description = str(fields["description"])
    if "acceptance_criteria" in fields and fields["acceptance_criteria"] is not None:
        node.acceptance_criteria = str(fields["acceptance_criteria"])
    if "priority" in fields and fields["priority"]:
        if fields["priority"] not in VALID_PRIORITY:
            raise ValidationError("invalid priority")
        node.priority = fields["priority"]
    if "tags" in fields and fields["tags"] is not None:
        node.tags = _join_tags(fields["tags"])
    if "owner" in fields and fields["owner"] is not None:
        node.owner = str(fields["owner"])
    if "risk_level" in fields and fields["risk_level"]:
        if fields["risk_level"] not in VALID_RISK:
            raise ValidationError("invalid risk_level")
        node.risk_level = fields["risk_level"]
    if "latest_note" in fields and fields["latest_note"] is not None:
        node.latest_note = str(fields["latest_note"])

    node.updated_by = actor or "human"
    db.session.flush()

    activity_service.record(
        project_id=node.project_id,
        node_id=node.id,
        actor=actor or "human",
        action_type="node_updated",
        before=before,
        after=node.to_dict(),
        reason=reason,
    )
    db.session.commit()
    return node


def delete_node(node_id: str, actor: str = "human", reason: str = "") -> None:
    node = Node.query.get(node_id)
    if not node or node.deleted_at is not None:
        raise ValidationError("node not found", 404)
    if not reason or not reason.strip():
        raise ValidationError("delete requires reason")

    before = node.to_dict()
    # Soft delete recursively
    def _soft_delete(n: Node):
        n.deleted_at = datetime.utcnow()
        for child in Node.query.filter_by(parent_id=n.id, deleted_at=None).all():
            _soft_delete(child)

    _soft_delete(node)

    activity_service.record(
        project_id=node.project_id,
        node_id=node.id,
        actor=actor or "human",
        action_type="node_deleted",
        before=before,
        after=None,
        reason=reason,
    )
    progress_service.recalc_for_node(node)
    db.session.commit()


def update_status(
    node_id: str,
    status: str,
    progress: Optional[float] = None,
    evidence_summary: str = "",
    blocker_reason: str = "",
    impact: str = "",
    next_action: str = "",
    needs_human: Optional[bool] = None,
    rollback_reason: str = "",
    override_reason: str = "",
    actor: str = "human",
    reason: str = "",
) -> Node:
    node = Node.query.get(node_id)
    if not node or node.deleted_at is not None:
        raise ValidationError("node not found", 404)
    if status not in VALID_NODE_STATUS:
        raise ValidationError("invalid status")

    before = node.to_dict()
    prev_status = node.status

    # Required fields per status
    if status == "done":
        if not (evidence_summary and evidence_summary.strip()) and not (
            node.evidence_summary and node.evidence_summary.strip()
        ):
            raise ValidationError("done status requires evidence_summary")
    if status == "blocked":
        if not (blocker_reason and blocker_reason.strip()):
            raise ValidationError("blocked status requires blocker_reason")
        if not (next_action and next_action.strip()):
            raise ValidationError("blocked status requires next_action")
    if prev_status == "done" and status != "done":
        if not (rollback_reason and rollback_reason.strip()) and not (reason and reason.strip()):
            raise ValidationError("rolling back from done requires rollback_reason")

    # Override reason for non-step status
    if node.node_type != "step":
        if not override_reason and not reason:
            # Allow if status is being set to a calculated value, but we still require reason
            raise ValidationError(
                f"updating status of {node.node_type} requires override_reason"
            )
        node.override_reason = override_reason or reason

    node.status = status
    if evidence_summary:
        node.evidence_summary = evidence_summary
    if status == "blocked":
        node.blocker_reason = blocker_reason
        node.blocker_impact = impact
        node.next_action = next_action
        if needs_human is not None:
            node.needs_human = bool(needs_human)
    if status != "blocked":
        # Clear blocker fields when no longer blocked
        if prev_status == "blocked":
            node.blocker_reason = ""
            node.blocker_impact = ""
            node.next_action = ""
            node.needs_human = False

    if progress is not None:
        try:
            p = float(progress)
            if p < 0 or p > 100:
                raise ValueError
            node.progress = p
        except Exception:
            raise ValidationError("progress must be a number 0..100")

    if status == "in_progress" and not node.started_at:
        node.started_at = datetime.utcnow()
    if status == "done":
        node.completed_at = datetime.utcnow()
        if node.progress is None or node.progress < 100:
            node.progress = 100.0
    if status == "review" and (node.progress is None or node.progress < 90):
        node.progress = 90.0

    node.updated_by = actor or "human"
    db.session.flush()

    activity_service.record(
        project_id=node.project_id,
        node_id=node.id,
        actor=actor or "human",
        action_type="status_changed",
        before=before,
        after=node.to_dict(),
        reason=reason or override_reason or rollback_reason,
    )
    progress_service.recalc_for_node(node)
    db.session.commit()
    return node


def report_blocker(
    node_id: str,
    blocker_reason: str,
    impact: str = "",
    next_action: str = "",
    needs_human: bool = False,
    actor: str = "agent",
) -> Node:
    return update_status(
        node_id=node_id,
        status="blocked",
        blocker_reason=blocker_reason,
        impact=impact,
        next_action=next_action,
        needs_human=needs_human,
        actor=actor,
        reason="blocker reported",
    )


def resolve_blocker(
    node_id: str,
    resolution: str,
    evidence_summary: str = "",
    actor: str = "agent",
) -> Node:
    node = Node.query.get(node_id)
    if not node or node.deleted_at is not None:
        raise ValidationError("node not found", 404)
    if node.status != "blocked":
        raise ValidationError("node is not blocked")
    return update_status(
        node_id=node_id,
        status="in_progress",
        evidence_summary=evidence_summary or node.evidence_summary,
        actor=actor,
        reason=f"blocker resolved: {resolution}",
    )


def move_node(
    node_id: str,
    new_parent_id: Optional[str],
    new_sort_order: Optional[int] = None,
    actor: str = "human",
    reason: str = "",
) -> Node:
    node = Node.query.get(node_id)
    if not node or node.deleted_at is not None:
        raise ValidationError("node not found", 404)
    if not reason:
        raise ValidationError("move requires reason")
    before = node.to_dict()

    _validate_hierarchy(node.project_id, new_parent_id, node.node_type)

    # Prevent moving into own descendant
    if new_parent_id:
        ancestor = Node.query.get(new_parent_id)
        seen = set()
        while ancestor:
            if ancestor.id == node.id:
                raise ValidationError("cannot move node into its own descendant")
            if ancestor.id in seen:
                break
            seen.add(ancestor.id)
            ancestor = Node.query.get(ancestor.parent_id) if ancestor.parent_id else None

    node.parent_id = new_parent_id
    if new_sort_order is not None:
        node.sort_order = int(new_sort_order)
    else:
        node.sort_order = _next_sort_order(node.project_id, new_parent_id)
    node.updated_by = actor or "human"
    db.session.flush()

    activity_service.record(
        project_id=node.project_id,
        node_id=node.id,
        actor=actor or "human",
        action_type="node_moved",
        before=before,
        after=node.to_dict(),
        reason=reason,
    )
    progress_service.recalc_for_node(node)
    db.session.commit()
    return node


def get_project_tree(project_id: str, include_done: bool = True) -> dict:
    project = _ensure_project(project_id)
    nodes: List[Node] = (
        Node.query.filter_by(project_id=project_id, deleted_at=None)
        .order_by(Node.sort_order.asc(), Node.created_at.asc())
        .all()
    )
    by_parent = {}
    for n in nodes:
        by_parent.setdefault(n.parent_id, []).append(n)

    def build(parent_id):
        children = by_parent.get(parent_id, [])
        out = []
        for child in children:
            if not include_done and child.status == "done":
                continue
            data = child.to_dict()
            data["children"] = build(child.id)
            out.append(data)
        return out

    progress_service.recalc_project(project)
    db.session.commit()

    return {
        "project": project.to_dict(),
        "stats": progress_service.project_stats(project_id),
        "tree": build(None),
    }


def search_nodes(
    project_id: str,
    query: str = "",
    statuses: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
) -> list:
    q = Node.query.filter_by(project_id=project_id, deleted_at=None)
    if query:
        like = f"%{query}%"
        q = q.filter(
            (Node.title.ilike(like))
            | (Node.description.ilike(like))
            | (Node.evidence_summary.ilike(like))
            | (Node.latest_note.ilike(like))
        )
    if statuses:
        q = q.filter(Node.status.in_(list(statuses)))
    nodes = q.order_by(Node.created_at.desc()).limit(200).all()
    if tags:
        tagset = set(tags)
        nodes = [
            n for n in nodes if tagset.intersection(set((n.tags or "").split(",")))
        ]
    return [n.to_dict() for n in nodes]
