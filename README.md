# Brain

A modular LLM resource suite for Claude Code and Cursor. Brain provides a structured workflow, always-on rules, domain-specific behavior, hooks, and MCP configurations — all in one place, wired into your tools with a single install command.

---

## What's Included

### Workflow Commands
A complete project lifecycle as slash commands — invoke any phase manually, in any order.

| Command | Phase | Purpose |
|---------|-------|---------|
| `/brainstorm` | Ideation | Explore a problem space, diverge and converge on direction |
| `/plan` | Planning | Transform ideas into a structured, living plan |
| `/scaffold` | Setup | Generate project structure and runnable boilerplate |
| `/build` | Implementation | Build from the plan, task by task |
| `/review` | Audit | Plan adherence, code quality, and security review |
| `/iterate` | Refinement | Address findings and feedback on existing work |
| `/reflect` | Retrospective | Capture lessons, update memory, close with next steps |
| `/status` | Orientation | Scan project state and suggest what to do next |

### Universal Rules
Always-on behavior layer covering tone, response style, scope discipline, and security baseline. Applied in every session across all projects.

### Domains
Domain-specific rules and commands that activate automatically when a matching project type is detected (ML, frontend, research, systems, etc.). Infrastructure is ready — add domains as you need them.

### Hooks
Shell scripts that fire on Claude Code events (pre/post tool use, session end). Infrastructure and examples included — activate when you have specific automations in mind.

### MCPs
MCP server configuration templates, organized into `personal/` (auth-required) and `shared/` (open). Merged into Claude Code and Cursor configs at install time. No secrets stored.

---

## Quick Start

### Requirements
- [Claude Code](https://claude.ai/code) and/or [Cursor](https://cursor.sh)
- `jq` — for config merging during install (`brew install jq` / `apt install jq` / [Windows](https://jqlang.github.io/jq/download/))
- Bash (Git Bash on Windows)

### Install
```sh
git clone https://github.com/your-username/brain.git
cd brain
bash install/install.sh
```

This wires all workflow commands, rules, and MCP configs into Claude Code and Cursor globally. Re-run after any changes to brain.

### Uninstall
```sh
bash install/install.sh uninstall
```

---

## Usage

### Using workflow commands
Open any project in Claude Code or Cursor and invoke commands directly:
```
/brainstorm  ← start here for new projects
/status      ← check where you are at any point
```

### When brain/ is your open project
All commands and rules are available automatically — no install needed for working on brain itself.

### Workflow phases connect
See [`workflow/_phases.md`](workflow/_phases.md) for the full phase map — how phases hand off, when to transition, and which entry point fits your situation.

---

## Extending Brain

### Add a domain
```sh
cp -r domains/_template domains/my-domain
# Fill in detect.md, rules.md, cursor-rule.mdc
bash install/install.sh
```

### Add a hook
1. Write a script in `universal/hooks/scripts/`
2. Wire it into `.claude/settings.json`
3. Run `bash install/install.sh`

See [`universal/hooks/README.md`](universal/hooks/README.md) for hook types and examples.

### Add an MCP
```sh
cp mcps/_template/personal.json mcps/personal/my-service.json
# Fill in config using ${ENV_VAR} references for secrets
bash install/install.sh
```

See [`mcps/README.md`](mcps/README.md) for full instructions.

---

## Structure

```
brain/
├── .claude/commands/     Workflow skill files (slash commands)
├── .cursor/rules/        Cursor rule files
├── workflow/             Phase specs and the phase map
├── universal/            Always-on rules and hook infrastructure
├── domains/              Domain-specific rules and commands
├── mcps/                 MCP config templates
└── install/              Global wiring script
```

---

## Design Decisions

See [`BRAINSTORM.md`](BRAINSTORM.md) for the full design history — decisions made, open questions, and the reasoning behind the structure.
