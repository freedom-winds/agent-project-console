# Requirements & Design

This document captures the product and visual design constraints that the MVP implements. The full original specification lives in `req.md` at the repository root; this file is the implementation-focused summary.

## Product

A local Web app that acts as a **project cockpit** for AI agents. Humans see what the agent has planned, what is in progress, what is blocked, and what was finished with what evidence. Agents do their planning and progress reporting through the MCP server.

### Hierarchy (fixed)

```
Project
  Part      (e.g. Backend API, Web Frontend, Deployment, Docs)
    Phase   (e.g. Auth System, Upload API, CI Pipeline)
      Step  (the smallest verifiable task)
```

Steps cannot be nested. Phases cannot be created directly under a Project. The backend rejects illegal hierarchy.

### Node statuses

`planned`, `ready`, `in_progress`, `blocked`, `review`, `done`, `skipped`, `cancelled`.

Mandatory invariants:

| Status   | Required field |
|----------|----------------|
| `done`   | `evidence_summary` |
| `blocked`| `blocker_reason`, `next_action` |
| rollback `done -> *` | `rollback_reason` |
| `part/phase` status set by hand | `override_reason` |
| node delete | `reason` |
| `move_node` | `reason` |

### Progress

* Step: 100 (done) / 90 (review) / 50 (in_progress, default) / 0 (planned/ready). `blocked` keeps last known progress. `skipped` and `cancelled` are excluded from totals.
* Phase: average over its non-excluded children.
* Part: average over its phases.
* Project: average over its parts.

### Activity log

Every write goes through `activity_service.record(...)` and produces a row in `activities`. Includes actor, action_type, before/after JSON, reason, timestamp. Soft-deletes only — history is never lost.

## Visual design (project cockpit)

### Layout

```
┌──────────────┬─────────────────────────────────────────────────┐
│ Sidebar      │ Project header (status badge, progress bar,     │
│ (Projects /  │ active agent, current focus, % progress)        │
│  Settings)   ├─────────────────────────────────────────────────┤
│              │ Tabs: Overview / Tree / Checkpoints / Activity  │
│              ├─────────────────────────────────────────────────┤
│              │ Page content                                    │
│              │                                                 │
│              │ (Tree page may show right Step Drawer 420px)    │
└──────────────┴─────────────────────────────────────────────────┘
```

Sidebar width: 240px. Step Drawer width: 420px.

### Color tokens (Tailwind config)

| Role | Hex |
|------|-----|
| bg / DEFAULT | `#0B1020` |
| bg / subtle  | `#111827` |
| bg / card    | `#161E2E` |
| border       | `#263247` |
| fg / DEFAULT | `#E5E7EB` |
| fg / muted   | `#9CA3AF` |
| fg / dim     | `#6B7280` |
| status.planned     | `#6B7280` |
| status.ready       | `#38BDF8` |
| status.in_progress | `#60A5FA` |
| status.blocked     | `#F97316` |
| status.review      | `#A78BFA` |
| status.done        | `#22C55E` |
| status.skipped     | `#64748B` |
| status.cancelled   | `#EF4444` |
| priority.low / medium / high / critical | `#64748B` / `#38BDF8` / `#F59E0B` / `#EF4444` |

### Typography

* Page title: 24/32 600
* Block title: 18/28 600
* Card numeric: 28/36 700 (font-mono)
* Body: 14/22 400
* Aux: 12/18 400
* Code & paths: JetBrains Mono / ui-monospace

### Status badge

Bilingual — English enum + Chinese. Example:

```
in_progress · 进行中
blocked     · 阻塞
review      · 待审核
done        · 完成
```

### Step Detail Drawer

Right-side drawer (420 px) with 5 tabs:

1. **Overview** — title, status, priority, progress, description, acceptance criteria, evidence summary, blocker block (if blocked), inline status updater.
2. **Evidence** — list + add form.
3. **Artifacts** — list + add form.
4. **Notes** — `latest_note`.
5. **History** — change records pulled from the activity log (filtered by node_id).

### Realtime updates (MVP)

Polling every 3 s for: project list, project detail/tree, activity, checkpoints. Future: SSE or WebSocket.

## Security

* The backend listens on `127.0.0.1:8765` only. CORS allows `http://127.0.0.1:5173` and `http://localhost:5173` only.
* MCP tokens are stored as SHA-256 hashes; the raw token is shown once at creation and used as `Authorization: Bearer ...` from the MCP server.
* The MCP server **calls the REST API** — it does not touch the database directly.

## What is intentionally not in the MVP

* Multi-user auth & roles
* Cloud sync
* Git diff parsing
* Mobile app
* Full RBAC

These are listed in `req.md` §12.
