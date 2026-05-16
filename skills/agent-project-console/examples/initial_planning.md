# Example: initial planning

A user says: "Build me a small file uploader: backend (Python), web client (React), and a deployment script."

The agent should NOT just start coding. The agent should plan first.

## 1. Read existing state

```jsonc
// tool: get_projects
{}
```

Pick or create a project (creating projects is currently done in the Web UI; ask the user if there is no relevant project).

```jsonc
// tool: get_project_tree
{ "project_id": "<project_id>" }
```

If the response shows `tree: []`, the project is empty.

## 2. Create the high-level Parts

Create one Part per major component, with a `reason`.

```jsonc
// tool: create_node
{
  "project_id": "<project_id>",
  "parent_id": null,
  "node_type": "part",
  "title": "Backend API",
  "description": "Python service that accepts uploads and stores them.",
  "priority": "high",
  "reason": "initial planning: backend is the largest area"
}
```

Repeat for "Web Client" and "Deployment".

## 3. Create Phases under each Part

```jsonc
// tool: create_node
{
  "project_id": "<project_id>",
  "parent_id": "<part_id_for_backend>",
  "node_type": "phase",
  "title": "Auth System",
  "priority": "high",
  "reason": "uploads need an authenticated user"
}
```

```jsonc
// tool: create_node
{
  "project_id": "<project_id>",
  "parent_id": "<part_id_for_backend>",
  "node_type": "phase",
  "title": "Upload API",
  "reason": "core endpoint for the project"
}
```

## 4. Create Steps under each Phase

Each Step should be a single verifiable outcome.

```jsonc
{
  "project_id": "<project_id>",
  "parent_id": "<phase_id_for_auth>",
  "node_type": "step",
  "title": "Implement /auth/login endpoint",
  "acceptance_criteria": "POST /auth/login returns JWT for valid creds; 401 otherwise; covered by a test.",
  "priority": "high",
  "reason": "initial breakdown"
}
```

## 5. Record an initial checkpoint

```jsonc
// tool: create_checkpoint
{
  "project_id": "<project_id>",
  "agent_name": "cline",
  "summary": "initial plan committed",
  "completed": [],
  "in_progress": [],
  "next": ["Implement /auth/login endpoint"],
  "blockers": [],
  "risks": ["JWT secret rotation strategy still TBD"]
}
```

Now, and only now, you may begin to actually work on the first Step.
