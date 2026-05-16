# Example: handling a blocker

You started implementing the upload endpoint and discovered the test database keeps failing migration.

## DO: report the blocker explicitly

```jsonc
// tool: report_blocker
{
  "node_id": "<step_id>",
  "blocker_reason": "alembic revision conflict: 4f2a vs 9c1d both reference base",
  "impact": "cannot run pytest, cannot verify upload endpoint",
  "next_action": "ask user to resolve revision conflict, or run alembic merge",
  "needs_human": true
}
```

After this call, the Step status is automatically set to `blocked`. The Web UI will surface it in the Blockers panel.

## DO NOT silently mark done or skip

```jsonc
// WRONG
{ "node_id": "<step_id>", "status": "done" }
```

```jsonc
// WRONG
{ "node_id": "<step_id>", "status": "skipped" }
```

## When unblocked

```jsonc
// tool: resolve_blocker
{
  "node_id": "<step_id>",
  "resolution": "merged conflicting revisions and re-ran upgrade",
  "evidence_summary": "alembic upgrade head succeeds; tests now run"
}
```

This transitions the Step back to `in_progress`. Continue work, then `add_evidence` and `update_status` as usual.
