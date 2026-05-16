---
name: agent-project-console
description: Use this skill when working on a software project connected to Agent Project Console. It teaches the agent to read the project tree, update Part/Phase/Step progress, record evidence, report blockers, and create checkpoints through the Agent Project Console MCP server.
---

# Agent Project Console Skill

This skill connects you to a structured project state system. The hierarchy is fixed:

```
Project
  Part           # large modules (e.g. "Backend API")
    Phase        # sub-stage (e.g. "Auth System")
      Step       # smallest verifiable unit (e.g. "Implement JWT login")
```

**Step is the smallest task unit. Do not nest below Step. Do not put Step under Project or Part.**

This is a project state system, not a chat-summary tool. Treat it as the single source of truth for what is planned, what is in progress, what is blocked, and what is done.

## When to call which tool

### Before starting any large task

1. Call `get_projects` to find the relevant project (or list).
2. Call `get_project_tree` for that project to see the current plan.
3. If the project is empty, plan the work and call `create_node` for each Part / Phase / Step. Provide a `reason` for every creation.
4. Call `create_checkpoint` to record the initial plan.

### Before starting a specific Step

1. Locate the Step in the tree.
2. Call `set_current_focus` with the project_id and step node_id, so the human dashboard shows what you are doing.
3. Call `update_status` with `status="in_progress"` and a short `reason` describing what you are about to do.

### After completing a Step

1. Call `add_evidence` with at least one of: `file_path`, `commit_hash`, `command_output`, `test_result`, `screenshot_path`, `url`, `note`.
2. If a deliverable was produced (a doc, a build, an API spec), call `add_artifact`.
3. Call `update_status` with `status="done"` and provide `evidence_summary`. Without `evidence_summary`, the backend will refuse the transition.
4. If you cannot fully verify completion yourself, use `status="review"` instead of `done`.

### When you hit a blocker

1. Call `report_blocker` with `blocker_reason`, `impact`, `next_action`, and `needs_human` if a human must decide.
2. Do **not** mark the Step `done`. Do not silently pivot to another task without recording the block.
3. When unblocked, call `resolve_blocker` with a `resolution` description, then continue.

### After completing a Phase

Call `create_checkpoint`. Include:

* `current_focus_node_id` (the next thing you will work on)
* `completed` (list of done items in this phase)
* `in_progress` (whatever is mid-flight)
* `next` (the upcoming items)
* `blockers` (anything still blocking)
* `risks` (things that may go wrong)

You should also create a checkpoint after a long stretch of work, even mid-phase, so the human can pick up where you left off.

### When the plan needs to change

If you discover the existing plan is wrong:

1. Re-read the tree with `get_project_tree`.
2. Use `create_node`, `update_node`, or `move_node` to adjust. Always include a `reason` explaining why you are changing the plan.
3. Do **not** silently overwrite. The system records every change in the activity log; reviewers will read your reasons.

## Strict rules

1. **Done requires evidence.** If you cannot point to a file, commit, command output, test result, or URL, the Step is not done.
2. **Blocked requires reason + next action.** A bare "blocked" with no detail is rejected.
3. **Rolling back from done requires `rollback_reason`.**
4. **Do not create a Step for every micro file edit.** A Step represents one verifiable outcome (e.g. "implement /auth/login endpoint"), not "edited line 42".
5. **Do not nest beyond Part → Phase → Step.** The backend will reject illegal hierarchy.
6. **When in doubt, use `review` instead of `done`.** Let a human confirm.
7. **Always pass a `reason`** on writes that affect plan structure or status.

## Examples

See:

- `examples/initial_planning.md`
- `examples/before_work.md`
- `examples/after_step_done.md`
- `examples/blocker.md`
- `examples/checkpoint.md`

## Schemas

Schemas for the most-used tools live in `schemas/`.

## Prompts

Reusable prompt fragments for planning, progress updates and review live in `prompts/`.

## Connection details

This skill talks to a local Flask backend through the `agent-project-console` MCP STDIO server.

* Backend default URL: `http://127.0.0.1:8765`
* MCP server module: `python -m app.mcp.server`
* Auth: Bearer token created in the Web UI Settings page, exported as `APC_MCP_TOKEN`.
* If the backend is unreachable, the tools will return an error like `backend not reachable at ...`. Tell the human to start the backend; do not fabricate a result.
