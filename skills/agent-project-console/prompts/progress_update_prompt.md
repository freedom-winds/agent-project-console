# Progress update prompt fragment

For each Step you work on, follow this loop:

1. **Before**: `set_current_focus`, then `update_status` → `in_progress`, with a one-sentence `reason`.
2. **During**: do the work. Do NOT spawn extra Steps for sub-edits.
3. **After**: `add_evidence` (file path, commit, command output, test result, …). If a deliverable was produced, `add_artifact`.
4. **Close**: `update_status` → `done` with `evidence_summary`. If you cannot personally verify completion, use `review`.

If at any point you discover a blocker, stop the loop and call `report_blocker` with `blocker_reason`, `impact`, `next_action`.

If you discover the plan was wrong, adjust nodes via `create_node` / `move_node` / `update_node` with explicit `reason`. Then resume the loop.
