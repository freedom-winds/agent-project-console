# REST API

Base URL: `http://127.0.0.1:8765`

All endpoints accept and return JSON. CORS is allowed for `http://127.0.0.1:5173` and `http://localhost:5173` only.

Authentication is optional for the dev backend; if you pass `Authorization: Bearer <token>` it must be a valid (non-revoked) MCP token. The MCP server always passes one. The Web UI does not need one (it runs on the same machine).

The actor name (recorded in activity log) is taken from the `X-APC-Actor` header, otherwise `"human"`.

## Health

`GET /api/health` → `{ "status": "ok", "service": "agent-project-console", "version": "0.1.0" }`

## Projects

`GET /api/projects` → `{ projects: [Project & {stats}] }`

`POST /api/projects`

```json
{
  "name": "...",
  "description": "...",
  "local_path": "...",
  "repo_url": "...",
  "default_branch": "main",
  "status": "planning",
  "active_agent": ""
}
```

→ 201, the new Project.

`GET /api/projects/{project_id}` → Project

`PATCH /api/projects/{project_id}` — partial update. Allowed fields: `name`, `description`, `local_path`, `repo_url`, `default_branch`, `active_agent`, `current_focus_node_id`, `status`. Plus `reason`.

`GET /api/projects/{project_id}/tree[?include_done=true|false]`

→ `{ project, stats, tree: [Node{children}] }`

`POST /api/projects/{project_id}/focus` — `{ node_id, reason }` — set the current focus node.

`GET /api/projects/{project_id}/search?q=&status=&tags=` — full-text search nodes.

## Nodes

`POST /api/nodes`

```json
{
  "project_id": "...",
  "parent_id": null | "<id>",
  "node_type": "part" | "phase" | "step",
  "title": "...",
  "description": "...",
  "acceptance_criteria": "...",
  "priority": "low|medium|high|critical",
  "tags": ["..."],
  "owner": "...",
  "reason": "..."
}
```

Hierarchy validation:

- `part` → `parent_id` must be `null`.
- `phase` → `parent_id` must be a `part`.
- `step`  → `parent_id` must be a `phase`.

`GET /api/nodes/{node_id}` → Node + `evidences`, `artifacts`.

`PATCH /api/nodes/{node_id}` — partial update. Allowed fields: `title`, `description`, `acceptance_criteria`, `priority`, `tags`, `owner`, `risk_level`, `latest_note`. Plus `reason` (required for activity log).

`DELETE /api/nodes/{node_id}?reason=...` — soft delete (records `deleted_at`). `reason` is required.

`POST /api/nodes/{node_id}/status`

```json
{
  "status": "in_progress",
  "progress": 50,
  "evidence_summary": "...",
  "blocker_reason": "...",
  "impact": "...",
  "next_action": "...",
  "needs_human": false,
  "rollback_reason": "...",
  "override_reason": "...",
  "reason": "..."
}
```

Constraints:

- `status="done"` requires `evidence_summary` (or an existing one on the node).
- `status="blocked"` requires `blocker_reason` and `next_action`.
- Rolling back from `done` to anything else requires `rollback_reason` (or `reason`).
- Setting status on a `part`/`phase` requires `override_reason` (or `reason`).

`POST /api/nodes/{node_id}/evidence`

```json
{
  "evidence_type": "file_path|commit_hash|command_output|test_result|screenshot_path|url|note",
  "title": "...",
  "content": "...",
  "summary": "...",
  "confidence": "low|medium|high"
}
```

`GET /api/nodes/{node_id}/evidence` → `{ evidences: [...] }`

`POST /api/nodes/{node_id}/artifacts`

```json
{
  "artifact_type": "document|source|build|design|report|package",
  "title": "...",
  "path_or_url": "...",
  "summary": "..."
}
```

`GET /api/nodes/{node_id}/artifacts`

`POST /api/nodes/{node_id}/move`

```json
{
  "new_parent_id": "<id>" | null,
  "new_sort_order": 3,
  "reason": "..."
}
```

`POST /api/nodes/{node_id}/blocker`

```json
{ "blocker_reason": "...", "impact": "...", "next_action": "...", "needs_human": false }
```

`POST /api/nodes/{node_id}/blocker/resolve`

```json
{ "resolution": "...", "evidence_summary": "..." }
```

## Activity

`GET /api/projects/{project_id}/activity[?limit=200]` → `{ activities: [{actor, action_type, before, after, reason, created_at, ...}] }`

`GET /api/activity[?limit=200]` → all activities (admin/debug).

## Checkpoints

`GET /api/projects/{project_id}/checkpoints[?limit=100]`

`POST /api/projects/{project_id}/checkpoints`

```json
{
  "agent_name": "...",
  "current_focus_node_id": "<id>",
  "completed": ["..."],
  "in_progress": ["..."],
  "next": ["..."],
  "blockers": ["..."],
  "risks": ["..."],
  "related_node_ids": ["..."],
  "summary": "..."
}
```

## Settings — MCP tokens

`GET /api/settings/tokens` → list (no token values, only previews).

`POST /api/settings/tokens`

```json
{ "name": "cline", "scopes": ["read_project", "write_plan", "update_status", "write_evidence", "write_checkpoint"] }
```

→ 201, `{ id, name, token, token_preview, scopes, created_at, ... }`. **`token` is shown only once.**

`DELETE /api/settings/tokens/{token_id}` — revoke a token (sets `revoked_at`).

## Error format

```json
{ "error": "validation_error", "message": "blocked status requires blocker_reason" }
```

Status codes: 200, 201, 400, 401, 404, 500.
