# Skill Setup

The `skills/agent-project-console/` directory is a self-contained skill package that teaches an AI agent **when** and **how** to use the MCP tools.

It contains:

```
skills/agent-project-console/
  SKILL.md                          ← entry point with YAML frontmatter
  examples/
    initial_planning.md
    before_work.md
    after_step_done.md
    blocker.md
    checkpoint.md
  schemas/
    create_node.schema.json
    update_status.schema.json
    checkpoint.schema.json
  prompts/
    planning_prompt.md
    progress_update_prompt.md
    review_prompt.md
```

The `SKILL.md` frontmatter:

```yaml
---
name: agent-project-console
description: Use this skill when working on a software project connected to Agent Project Console. ...
---
```

## Cline

Cline supports custom rules and instructions per workspace.

1. Copy or symlink the skill folder into your project workspace, or place it where Cline reads instructions:
   - **Recommended**: copy `skills/agent-project-console/SKILL.md` into your project's `.cline/rules/agent-project-console.md`.
2. Or, paste the contents of `SKILL.md` into Cline's **Custom Instructions** box.
3. Reload Cline. When the user asks Cline to work on a project, it will read these rules and follow them.

## Claude Code

Claude Code reads skills from a configurable directory. Two options:

### Option 1: per-project (recommended)

Inside your project repo, create:

```
.claude/skills/agent-project-console/
```

and copy the contents of `agent-project-console/skills/agent-project-console/` into it.

When Claude Code starts in that workspace it will pick up the skill.

### Option 2: global

Copy the skill to the user-level skills directory:

* Linux/macOS: `~/.claude/skills/agent-project-console/`
* Windows:     `%APPDATA%\Claude\skills\agent-project-console\`

## Codex CLI

Codex CLI reads skills/instructions from a configurable list of directories:

### Option 1: project-level

Place the skill at the root of your project as `AGENTS.md` or under `.codex/skills/agent-project-console/`. Reference the SKILL.md in your project's `AGENTS.md`:

```markdown
## Skills

- See `.codex/skills/agent-project-console/SKILL.md`. Use when working on this project.
```

### Option 2: user-level

```
~/.codex/skills/agent-project-console/
```

## Smoke test

Once the skill is installed and the MCP server is configured:

1. Ask the agent: *"What is in the current project?"*
2. The agent should call `get_projects` then `get_project_tree`.
3. Then ask: *"Plan an initial breakdown for this project."*
4. The agent should call `create_node` repeatedly with explicit `reason`s, then `create_checkpoint`.

If the agent does not follow the rules (e.g. it tries to mark `done` with no evidence), the backend will reject the call and the agent will see the validation error and learn to comply.
