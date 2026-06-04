# Brain — Project Brainstorm

Living document capturing decisions, open questions, and direction for the Brain LLM resource suite.

---

## What Is Brain?

A modular, hierarchical vault of LLM resources — rules, skills, hooks, MCPs, prompts, and commands — that enhance workflow and productivity. Resources can be used together or independently. Designed for personal use but built to be shareable.

---

## Decisions Made

### Purpose & Audience
- **Primary user:** Personal use
- **Secondary:** Resources should be written so anyone could pick them up and use them
- **Portability:** Resources must work in both Claude Code and Cursor

### Hierarchy (Scope Levels)
| Level | Scope | Description |
|-------|-------|-------------|
| L1 | Universal | Always active, cross-project. Tone, safety, memory conventions, core MCPs |
| L2 | Domain | Active for a category of work (ML, frontend, research, systems) |
| L3 | Project | Per-repo CLAUDE.md, project hooks, project-specific commands |
| L4 | Session | Ephemeral, conversation-scoped context |

### Invocation Tiers
| Tier | How it fires | Examples |
|------|-------------|---------|
| Ambient | Always on | Global rules, tone, memory conventions, safety hooks |
| Contextual | Auto-fires by directory/file type | ML rules in ML repo, frontend rules in Next.js project |
| On-demand | User explicitly calls it | `/brainstorm`, `/plan`, `/review` |
| Gated | Fires at a specific event | Pre-commit hook, session-end reflection |

### Automation Philosophy
- **Automated:** All structural wiring — loading rules, registering MCPs, syncing skills to tool directories, wiring hooks. Handled by `install.sh`, run once or after brain updates.
- **Manual:** All invocation — the user explicitly calls on-demand commands. Nothing workflow-related fires without intent.

### Cross-Tool Strategy
- **Rules** → written once, installed to Claude Code (`CLAUDE.md`) and Cursor (`.cursor/rules/`)
- **Skills** → written once in `brain/shared/skills/`, registered to `~/.claude/commands/` for CC and adapted for Cursor
- **MCPs** → configured once in `brain/mcps/`, injected into both tool configs
- **Prompts** → stored in `brain/shared/prompts/`, referenced by both tools
- **Install** → `install.sh` detects which tools are present, backs up existing configs, wires everything idempotently

---

## Directory Structure (Planned)

```
brain/
├── BRAINSTORM.md               # This file
├── README.md
├── CLAUDE.md                   # Brain's own project rules (for when brain/ is open)
│
├── .claude/                    # Claude Code native — auto-picked up when brain/ is open
│   ├── commands/               # Operative skill files (the actual slash commands)
│   │   ├── brainstorm.md
│   │   ├── plan.md
│   │   ├── scaffold.md
│   │   ├── build.md
│   │   ├── review.md
│   │   ├── iterate.md
│   │   └── reflect.md
│   └── settings.json           # Brain-level hooks and MCPs
│
├── .cursor/                    # Cursor native — auto-picked up when brain/ is open
│   └── rules/
│       ├── universal.mdc       # Always-on rules
│       └── domains/            # Domain-specific rules (future)
│
├── universal/                  # L1 — Source content for ambient rules
│   ├── rules.md                # Core behavior, tone, response style
│   ├── memory.md               # Memory usage conventions
│   └── hooks/                  # Global pre/post tool hooks
│
├── domains/                    # L2 — Contextual, activated by project type
│   ├── ml/
│   ├── frontend/
│   ├── research/
│   └── systems/
│
├── workflow/                   # Specs only — operative files live in .claude/commands/
│   ├── _phases.md              # How phases connect, when to transition
│   ├── brainstorm/spec.md
│   ├── plan/spec.md
│   ├── scaffold/spec.md
│   ├── build/spec.md
│   ├── review/spec.md
│   ├── iterate/spec.md
│   └── reflect/spec.md
│
├── mcps/                       # MCP server configs (shared across tools)
│
└── install/
    └── install.sh              # One-time global wiring for cross-project availability
```

---

## Workflow Phases (To Define)

The primary focus. Each phase is an on-demand command the user invokes. Below is the phase map — details TBD per phase.

| Phase | Command | Status |
|-------|---------|--------|
| Brainstorm | `/brainstorm` | Defined |
| Plan | `/plan` | Defined |
| Scaffold | `/scaffold` | Defined |
| Build | `/build` | Defined |
| Review | `/review` | Defined |
| Iterate | `/iterate` | Defined |
| Reflect | `/reflect` | Defined |
| Status | `/status` | Defined |
| Ship | `/ship` | Deferred — build when needed |

### Phase Definition Template
Each phase needs:
- **Trigger:** How/when to invoke it
- **Input:** What it expects (prior phase output, user context, etc.)
- **Process:** What it actually does — the prompt logic, steps, structure
- **Output:** What it produces (a doc, a plan, code, a checklist, etc.)
- **Handoff:** What the next phase needs from this one
- **Tool behavior:** How it should act differently in Claude Code vs Cursor

---

## Open Questions

- [ ] Should phases be strictly linear or can they be invoked out of order?
- [x] Should there be a `/status` command that shows which phase a project is in? — Yes, built.
- [~] How does the workflow interact with git? — Deferred until `/ship` is built.
- [ ] Should domain resources auto-detect context (e.g., detect `package.json` → frontend mode) or require a manual domain declaration?
- [x] File watcher to auto-run `install.sh` on brain changes — Implemented as a PostToolUse hook (`post-edit-install-sync.sh`) that fires on Write|Edit within the brain directory.
- [x] ~~Should `brain/shared/` resources be publishable as a standalone repo?~~ — Dropped. Normal resources are already shareable as-is.
