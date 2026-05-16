# Example: creating a checkpoint after a Phase

You finished the entire "Auth System" Phase. Each Step inside is marked `done` (with evidence) or explicitly `cancelled` / `skipped`.

## Create a checkpoint

```jsonc
// tool: create_checkpoint
{
  "project_id": "<project_id>",
  "agent_name": "cline",
  "current_focus_node_id": "<id_of_first_step_in_next_phase>",
  "summary": "Auth System phase complete; moving to Upload API",
  "completed": [
    "Implement /auth/login endpoint",
    "Implement /auth/refresh endpoint",
    "Add permission guard middleware"
  ],
  "in_progress": [],
  "next": [
    "POST /uploads init endpoint",
    "PUT /uploads/<id> chunk endpoint",
    "GET /uploads/<id>/status"
  ],
  "blockers": [],
  "risks": [
    "Token refresh under heavy load not yet load-tested"
  ],
  "related_node_ids": ["<phase_id_for_auth>"]
}
```

## Also: create a checkpoint after a long stretch of work

Even if a Phase is not done, if you've done a lot of work since the last checkpoint, write one. The human dashboard relies on these snapshots.
