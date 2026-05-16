# Example: after finishing a Step

You finished implementing `/auth/login`. Tests pass. You committed.

## 1. Add evidence

```jsonc
// tool: add_evidence
{
  "node_id": "<step_id>",
  "evidence_type": "file_path",
  "title": "JWT login implementation",
  "content": "backend/app/auth/routes.py",
  "summary": "implemented login + refresh token; pytest passing",
  "confidence": "high"
}
```

You may add multiple evidences (file_path, commit_hash, test_result).

## 2. Optional: add an artifact

```jsonc
// tool: add_artifact
{
  "node_id": "<step_id>",
  "artifact_type": "document",
  "title": "Auth API spec",
  "path_or_url": "docs/auth_api.md",
  "summary": "request/response shape and error codes"
}
```

## 3. Mark done with evidence_summary

```jsonc
// tool: update_status
{
  "node_id": "<step_id>",
  "status": "done",
  "evidence_summary": "POST /auth/login returns JWT; 6 unit tests pass; committed in abcd123",
  "reason": "completed and verified locally"
}
```

If you cannot verify the result yourself, use `status: "review"` instead and let a human approve.

## Wrong examples (do NOT do this)

```jsonc
// WRONG: marking done with no evidence
{ "node_id": "...", "status": "done" }
```

```jsonc
// WRONG: marking done because you "intend" to verify later
{ "node_id": "...", "status": "done", "evidence_summary": "I'll test it later" }
```

```jsonc
// WRONG: silently rolling done -> in_progress with no rollback_reason
{ "node_id": "...", "status": "in_progress" }
```
