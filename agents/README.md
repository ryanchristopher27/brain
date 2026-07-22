# Agents

Curated **Claude Code subagents** — brain's fleet. Each agent is one Markdown file with
YAML frontmatter (the structural contract) followed by a system prompt (the behavior).
`install.sh` symlinks every `*.md` here into `~/.claude/agents/`, making them available in
any Claude Code session via the Task tool and `/agents`.

---

## Structure

```
agents/
├── _template/agent.md   # Copy this to create a new agent
├── personas/            # Interactive personas (summoned per task)
│   ├── scout.md         # Collaborative · READ-ONLY  (voice default)
│   ├── reviewer.md      # Collaborative · read + comment
│   └── builder.md       # Autonomous · scoped read/write/bash
└── background/          # Unattended / scheduled agents
    ├── operator.md      # Autonomous · tightest scope + full logging
    └── runner.sh        # Headless `claude -p` wrapper for scheduled runs
```

---

## The safety model — posture is structural, not trust-based

An agent can only use the tools listed in its `tools:` frontmatter. That is the enforcement
boundary. "Read-only" personas literally have no write/exec tools available; autonomous
personas do, and are summoned deliberately.

| Persona | Posture | Tools (allowlist) | Use |
|---------|---------|-------------------|-----|
| **Scout** | Collaborative, read-only | Read, Grep, Glob, WebFetch, WebSearch | Research, explain, propose — default for voice |
| **Reviewer** | Collaborative, read + comment | Read, Grep, Glob, Bash(git *) | Critique / review diffs |
| **Builder** | Autonomous, scoped | Read, Write, Edit, Grep, Glob, Bash | Multi-step build tasks, logs everything |
| **Operator** | Autonomous, background | (tightest per-job) | Unattended / scheduled jobs |

---

## Adding an agent

1. `cp _template/agent.md personas/<name>.md` (or `background/<name>.md`)
2. Fill in the frontmatter — **the `tools:` list is load-bearing; keep it minimal.**
3. Write the system prompt body.
4. Re-run `install/install.sh` to sync it into `~/.claude/agents/`.

---

## Status

Frontmatter contracts are authored; system-prompt bodies are seeded and get their full
treatment in **milestone A1**. `install.sh` agent-sync lands in **A1** as well.
