"""Progress calculation service."""
from typing import List, Tuple

from ..extensions import db
from ..models.node import Node
from ..models.project import Project


STATUS_DEFAULT_PROGRESS = {
    "done": 100.0,
    "review": 90.0,
    "in_progress": 50.0,
    "blocked": None,  # keep current
    "ready": 0.0,
    "planned": 0.0,
}

# These are not counted in totals
EXCLUDED_STATUSES = {"skipped", "cancelled"}


def _step_effective_progress(node: Node) -> float:
    if node.status in EXCLUDED_STATUSES:
        return 0.0
    if node.status == "blocked":
        return float(node.progress or 0)
    default = STATUS_DEFAULT_PROGRESS.get(node.status)
    if default is None:
        return float(node.progress or 0)
    # If user/agent manually set progress, use it; otherwise use default
    if node.progress and node.progress > 0:
        return float(node.progress)
    return float(default)


def recalc_phase(phase: Node) -> None:
    steps: List[Node] = (
        Node.query.filter_by(parent_id=phase.id, deleted_at=None).all()
    )
    counted = [s for s in steps if s.status not in EXCLUDED_STATUSES]
    if not counted:
        phase.progress = 0.0
        return
    total = sum(_step_effective_progress(s) for s in counted)
    phase.progress = round(total / len(counted), 2)


def recalc_part(part: Node) -> None:
    phases: List[Node] = Node.query.filter_by(parent_id=part.id, deleted_at=None).all()
    if not phases:
        part.progress = 0.0
        return
    # Recalculate each phase first
    for phase in phases:
        recalc_phase(phase)
    total = sum(float(p.progress or 0) for p in phases)
    part.progress = round(total / len(phases), 2)


def recalc_project(project: Project) -> None:
    parts: List[Node] = Node.query.filter_by(
        project_id=project.id, node_type="part", deleted_at=None
    ).all()
    if not parts:
        project.progress = 0.0
        return
    for part in parts:
        recalc_part(part)
    total = sum(float(p.progress or 0) for p in parts)
    project.progress = round(total / len(parts), 2)


def recalc_for_node(node: Node) -> None:
    """Recalculate progress upstream from any node."""
    project = Project.query.get(node.project_id)
    if not project:
        return
    recalc_project(project)


def project_stats(project_id: str) -> dict:
    nodes: List[Node] = Node.query.filter_by(project_id=project_id, deleted_at=None).all()
    parts = [n for n in nodes if n.node_type == "part"]
    phases = [n for n in nodes if n.node_type == "phase"]
    steps = [n for n in nodes if n.node_type == "step"]
    done_steps = [n for n in steps if n.status == "done"]
    blocked_steps = [n for n in steps if n.status == "blocked"]
    in_progress_steps = [n for n in steps if n.status == "in_progress"]
    review_steps = [n for n in steps if n.status == "review"]
    return {
        "parts": len(parts),
        "phases": len(phases),
        "steps": len(steps),
        "done_steps": len(done_steps),
        "blocked_steps": len(blocked_steps),
        "in_progress_steps": len(in_progress_steps),
        "review_steps": len(review_steps),
    }
