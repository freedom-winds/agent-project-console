"""Project service."""
from typing import Optional

from ..extensions import db
from ..models.project import Project
from . import activity_service, progress_service


VALID_PROJECT_STATUS = {
    "planning",
    "active",
    "paused",
    "blocked",
    "review",
    "completed",
    "archived",
}


class ValidationError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status
        self.message = message


def list_projects() -> list:
    projects = Project.query.order_by(Project.created_at.desc()).all()
    out = []
    for p in projects:
        progress_service.recalc_project(p)
        data = p.to_dict()
        data["stats"] = progress_service.project_stats(p.id)
        out.append(data)
    db.session.commit()
    return out


def get_project(project_id: str) -> Project:
    p = Project.query.get(project_id)
    if not p:
        raise ValidationError("project not found", 404)
    return p


def create_project(
    name: str,
    description: str = "",
    local_path: str = "",
    repo_url: str = "",
    default_branch: str = "main",
    status: str = "planning",
    active_agent: str = "",
    actor: str = "human",
) -> Project:
    if not name or not name.strip():
        raise ValidationError("project name is required")
    if status not in VALID_PROJECT_STATUS:
        status = "planning"

    project = Project(
        name=name.strip(),
        description=description or "",
        local_path=local_path or "",
        repo_url=repo_url or "",
        default_branch=default_branch or "main",
        status=status,
        active_agent=active_agent or "",
    )
    db.session.add(project)
    db.session.flush()
    activity_service.record(
        project_id=project.id,
        node_id=None,
        actor=actor or "human",
        action_type="project_created",
        before=None,
        after=project.to_dict(),
        reason="project created",
    )
    db.session.commit()
    return project


def update_project(
    project_id: str,
    actor: str = "human",
    reason: str = "",
    **fields,
) -> Project:
    project = get_project(project_id)
    before = project.to_dict()
    for key in [
        "name",
        "description",
        "local_path",
        "repo_url",
        "default_branch",
        "active_agent",
        "current_focus_node_id",
    ]:
        if key in fields and fields[key] is not None:
            setattr(project, key, str(fields[key]))
    if "status" in fields and fields["status"]:
        if fields["status"] not in VALID_PROJECT_STATUS:
            raise ValidationError("invalid project status")
        project.status = fields["status"]
    db.session.flush()
    activity_service.record(
        project_id=project.id,
        node_id=None,
        actor=actor or "human",
        action_type="project_updated",
        before=before,
        after=project.to_dict(),
        reason=reason,
    )
    db.session.commit()
    return project


def set_current_focus(project_id: str, node_id: str, actor: str = "agent", reason: str = "") -> Project:
    project = get_project(project_id)
    before = project.to_dict()
    project.current_focus_node_id = node_id or ""
    if actor:
        project.active_agent = actor
    db.session.flush()
    activity_service.record(
        project_id=project.id,
        node_id=node_id,
        actor=actor or "agent",
        action_type="focus_set",
        before=before,
        after=project.to_dict(),
        reason=reason or "current focus updated",
    )
    db.session.commit()
    return project
