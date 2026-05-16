# Planning prompt fragment

When you receive a new project task, before writing any code:

1. Call `get_projects` and pick or confirm the target project.
2. Call `get_project_tree` to see what exists.
3. If the tree is empty or stale, draft a plan as Part / Phase / Step nodes:
   - One **Part** per major component (backend, web, mobile, deployment, docs).
   - One **Phase** per significant stage within a Part.
   - One **Step** per single, verifiable outcome (≈ 1–4 hours of work).
4. Create the nodes via `create_node`. Pass a `reason` for each (e.g. "initial breakdown", "split for parallel work").
5. Record an initial checkpoint via `create_checkpoint`.

Do not start coding before steps 1–5 are done. The human dashboard expects the plan to exist before progress.
