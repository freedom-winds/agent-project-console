# Example: before starting actual work on a Step

You are about to start the Step "Implement /auth/login endpoint".

## 1. Refresh the tree

```jsonc
// tool: get_project_tree
{ "project_id": "<project_id>" }
```

This guards against the human or another agent having moved/closed the Step.

## 2. Mark current focus

```jsonc
// tool: set_current_focus
{
  "project_id": "<project_id>",
  "node_id": "<step_id>",
  "reason": "starting implementation of login endpoint"
}
```

## 3. Move the Step to in_progress

```jsonc
// tool: update_status
{
  "node_id": "<step_id>",
  "status": "in_progress",
  "reason": "writing route + service + tests"
}
```

Now do the actual work. Do not create a Step for every file edit.
