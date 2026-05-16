"""MCP tool input schemas (JSON Schema dicts)."""

TOOL_SCHEMAS = [
    {
        "name": "get_projects",
        "description": "List all projects accessible to this agent.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "get_project_tree",
        "description": "Read the full Part / Phase / Step tree for a project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "include_done": {"type": "boolean", "default": True},
                "include_history": {"type": "boolean", "default": False},
            },
            "required": ["project_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "create_node",
        "description": "Create a Part, Phase or Step node. Part has parent_id=null. Phase parent must be a Part. Step parent must be a Phase.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "parent_id": {"type": ["string", "null"]},
                "node_type": {"type": "string", "enum": ["part", "phase", "step"]},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "acceptance_criteria": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "tags": {"type": "array", "items": {"type": "string"}},
                "owner": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["project_id", "node_type", "title"],
            "additionalProperties": True,
        },
    },
    {
        "name": "update_node",
        "description": "Modify a node's basic information (title, description, priority, tags, acceptance_criteria).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "acceptance_criteria": {"type": "string"},
                "priority": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "owner": {"type": "string"},
                "risk_level": {"type": "string"},
                "latest_note": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["node_id", "reason"],
            "additionalProperties": True,
        },
    },
    {
        "name": "update_status",
        "description": (
            "Update node status and progress. status='done' requires evidence_summary. "
            "status='blocked' requires blocker_reason and next_action. "
            "Rolling back from done requires rollback_reason."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["planned", "ready", "in_progress", "blocked", "review", "done", "skipped", "cancelled"],
                },
                "progress": {"type": "number", "minimum": 0, "maximum": 100},
                "evidence_summary": {"type": "string"},
                "blocker_reason": {"type": "string"},
                "impact": {"type": "string"},
                "next_action": {"type": "string"},
                "needs_human": {"type": "boolean"},
                "rollback_reason": {"type": "string"},
                "override_reason": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["node_id", "status"],
            "additionalProperties": True,
        },
    },
    {
        "name": "add_evidence",
        "description": "Attach evidence (file_path, commit_hash, command_output, test_result, screenshot_path, url, note) to a node.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "evidence_type": {
                    "type": "string",
                    "enum": ["file_path", "commit_hash", "command_output", "test_result", "screenshot_path", "url", "note"],
                },
                "title": {"type": "string"},
                "content": {"type": "string"},
                "summary": {"type": "string"},
                "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
            },
            "required": ["node_id", "evidence_type", "title"],
            "additionalProperties": True,
        },
    },
    {
        "name": "add_artifact",
        "description": "Attach an artifact (document, source, build, design, report, package) to a node.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "artifact_type": {"type": "string"},
                "title": {"type": "string"},
                "path_or_url": {"type": "string"},
                "summary": {"type": "string"},
            },
            "required": ["node_id", "title"],
            "additionalProperties": True,
        },
    },
    {
        "name": "report_blocker",
        "description": "Mark a node as blocked with blocker_reason, impact, next_action and whether human intervention is needed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "blocker_reason": {"type": "string"},
                "impact": {"type": "string"},
                "next_action": {"type": "string"},
                "needs_human": {"type": "boolean"},
            },
            "required": ["node_id", "blocker_reason", "next_action"],
            "additionalProperties": True,
        },
    },
    {
        "name": "resolve_blocker",
        "description": "Resolve a blocked node by transitioning it back to in_progress with a resolution note.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "resolution": {"type": "string"},
                "evidence_summary": {"type": "string"},
            },
            "required": ["node_id", "resolution"],
            "additionalProperties": True,
        },
    },
    {
        "name": "create_checkpoint",
        "description": "Create a structured progress snapshot: completed, in_progress, next, blockers, risks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "agent_name": {"type": "string"},
                "current_focus_node_id": {"type": "string"},
                "completed": {"type": "array", "items": {"type": "string"}},
                "in_progress": {"type": "array", "items": {"type": "string"}},
                "next": {"type": "array", "items": {"type": "string"}},
                "blockers": {"type": "array", "items": {"type": "string"}},
                "risks": {"type": "array", "items": {"type": "string"}},
                "related_node_ids": {"type": "array", "items": {"type": "string"}},
                "summary": {"type": "string"},
            },
            "required": ["project_id"],
            "additionalProperties": True,
        },
    },
    {
        "name": "move_node",
        "description": "Move a node under a new parent. Hierarchy must remain Part->Phase->Step.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "new_parent_id": {"type": ["string", "null"]},
                "new_sort_order": {"type": "integer"},
                "reason": {"type": "string"},
            },
            "required": ["node_id", "reason"],
            "additionalProperties": True,
        },
    },
    {
        "name": "search_nodes",
        "description": "Search nodes by query, status list and tags within a project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "query": {"type": "string"},
                "status": {"type": "array", "items": {"type": "string"}},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["project_id"],
            "additionalProperties": True,
        },
    },
    {
        "name": "set_current_focus",
        "description": "Mark which Step the agent is currently working on.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "node_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["project_id", "node_id"],
            "additionalProperties": True,
        },
    },
]
