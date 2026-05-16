"""Activity logging service."""
import json
from typing import Optional, Any

from ..extensions import db
from ..models.activity import Activity


def _to_json(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    try:
        return json.dumps(val, ensure_ascii=False, default=str)
    except Exception:
        return str(val)


def record(
    project_id: Optional[str],
    node_id: Optional[str],
    actor: str,
    action_type: str,
    before: Any = None,
    after: Any = None,
    reason: str = "",
) -> Activity:
    activity = Activity(
        project_id=project_id,
        node_id=node_id,
        actor=actor or "system",
        action_type=action_type,
        before_json=_to_json(before),
        after_json=_to_json(after),
        reason=reason or "",
    )
    db.session.add(activity)
    return activity
