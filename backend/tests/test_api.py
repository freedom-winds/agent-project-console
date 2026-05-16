"""End-to-end tests for the REST API."""
import json
import os
import sys

import pytest

# Make backend importable
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))

from app import create_app
from app.config import TestConfig
from app.extensions import db


@pytest.fixture()
def app():
    a = create_app(TestConfig)
    with a.app_context():
        db.drop_all()
        db.create_all()
    yield a


@pytest.fixture()
def client(app):
    return app.test_client()


def test_health(client):
    rv = client.get("/api/health")
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "ok"


def test_full_workflow(client):
    # Create project
    rv = client.post(
        "/api/projects",
        json={"name": "Demo Project", "description": "for tests"},
    )
    assert rv.status_code == 201, rv.get_json()
    project = rv.get_json()
    pid = project["id"]

    # Create part
    rv = client.post(
        "/api/nodes",
        json={
            "project_id": pid,
            "parent_id": None,
            "node_type": "part",
            "title": "Backend API",
            "reason": "initial planning",
        },
    )
    assert rv.status_code == 201, rv.get_json()
    part = rv.get_json()

    # Create phase under part
    rv = client.post(
        "/api/nodes",
        json={
            "project_id": pid,
            "parent_id": part["id"],
            "node_type": "phase",
            "title": "Auth System",
            "reason": "plan",
        },
    )
    assert rv.status_code == 201
    phase = rv.get_json()

    # Reject creating step under part directly
    rv = client.post(
        "/api/nodes",
        json={
            "project_id": pid,
            "parent_id": part["id"],
            "node_type": "step",
            "title": "bad step",
            "reason": "should fail",
        },
    )
    assert rv.status_code == 400

    # Create step under phase
    rv = client.post(
        "/api/nodes",
        json={
            "project_id": pid,
            "parent_id": phase["id"],
            "node_type": "step",
            "title": "Implement JWT login",
            "reason": "plan",
        },
    )
    assert rv.status_code == 201
    step = rv.get_json()
    sid = step["id"]

    # Status -> in_progress
    rv = client.post(
        f"/api/nodes/{sid}/status",
        json={"status": "in_progress", "reason": "starting"},
    )
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "in_progress"

    # Cannot mark done without evidence_summary
    rv = client.post(
        f"/api/nodes/{sid}/status",
        json={"status": "done", "reason": "missing evidence"},
    )
    assert rv.status_code == 400

    # Add evidence
    rv = client.post(
        f"/api/nodes/{sid}/evidence",
        json={
            "evidence_type": "file_path",
            "title": "JWT implementation",
            "content": "backend/app/auth/routes.py",
            "summary": "implemented login + refresh",
        },
    )
    assert rv.status_code == 201

    # Now mark done with evidence_summary
    rv = client.post(
        f"/api/nodes/{sid}/status",
        json={"status": "done", "evidence_summary": "all tests pass", "reason": "complete"},
    )
    assert rv.status_code == 200
    assert rv.get_json()["status"] == "done"

    # Block another step
    rv = client.post(
        "/api/nodes",
        json={
            "project_id": pid,
            "parent_id": phase["id"],
            "node_type": "step",
            "title": "Refresh token",
            "reason": "plan",
        },
    )
    sid2 = rv.get_json()["id"]
    rv = client.post(
        f"/api/nodes/{sid2}/status",
        json={
            "status": "blocked",
            "blocker_reason": "library bug",
            "next_action": "open issue",
            "reason": "blocked",
        },
    )
    assert rv.status_code == 200

    # Activity log
    rv = client.get(f"/api/projects/{pid}/activity")
    assert rv.status_code == 200
    actions = [a["action_type"] for a in rv.get_json()["activities"]]
    assert "project_created" in actions
    assert "node_created" in actions
    assert "status_changed" in actions
    assert "evidence_added" in actions

    # Tree
    rv = client.get(f"/api/projects/{pid}/tree")
    tree = rv.get_json()
    assert tree["project"]["id"] == pid
    assert len(tree["tree"]) == 1
    assert tree["tree"][0]["children"][0]["children"][0]["id"] in (sid, sid2)

    # Checkpoint
    rv = client.post(
        f"/api/projects/{pid}/checkpoints",
        json={
            "agent_name": "test-agent",
            "current_focus_node_id": sid,
            "completed": ["JWT login"],
            "in_progress": ["Refresh token"],
            "next": ["Permission guard"],
            "blockers": ["lib bug"],
            "summary": "phase 1 progress",
        },
    )
    assert rv.status_code == 201

    rv = client.get(f"/api/projects/{pid}/checkpoints")
    assert len(rv.get_json()["checkpoints"]) == 1


def test_token_lifecycle(client):
    rv = client.post("/api/settings/tokens", json={"name": "test"})
    assert rv.status_code == 201
    body = rv.get_json()
    assert body["token"].startswith("apc_")
    tid = body["id"]

    rv = client.get("/api/settings/tokens")
    assert rv.status_code == 200
    assert any(t["id"] == tid for t in rv.get_json()["tokens"])

    rv = client.delete(f"/api/settings/tokens/{tid}")
    assert rv.status_code == 200
