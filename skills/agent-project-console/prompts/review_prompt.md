# Review prompt fragment

When the human asks you to review a project's status:

1. Call `get_project_tree` for the project.
2. List all Steps with status `review` — these are the ones waiting for human approval.
3. List all Steps with status `blocked` — these are unresolved issues.
4. Summarize the result like:
   - "X parts, Y phases, Z steps. <D> done, <I> in progress, <B> blocked, <R> in review."
   - For each blocked step: title, blocker_reason, impact, next_action.
   - For each review step: title, evidence_summary.
5. If you find a step in status `done` whose evidence is weak (no `evidence_summary`, no concrete evidence rows), call this out — but do NOT silently demote it. Suggest the human reviews and either approves or rolls it back with a `rollback_reason`.

Never invent the state of nodes you have not read.
