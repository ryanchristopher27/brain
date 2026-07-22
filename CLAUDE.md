# Brain — Claude Code Project Rules

Brain is a modular LLM resource suite — a vault of workflow skills, rules, hooks, and MCP configs that enhance productivity across projects. It works natively in Claude Code and Cursor.

---

## What Lives Where

| Location | Purpose |
|----------|---------|
| `.claude/commands/` | Operative skill files — the actual slash commands |
| `agents/` | Curated Claude Code subagents (personas + background); synced to `~/.claude/agents/` |
| `mcps/` | MCP server configs (`shared/` no-auth, `personal/` env-var'd); merged into tool settings |
| `voice/` | Runtime module — local voice core driving headless `claude -p` (self-contained deps) |
| `web/` | Runtime module — live visualizer of the voice agent (subscribes to `voice/`'s event stream) |
| `.cursor/rules/` | Cursor rule files, auto-loaded when brain/ is open |
| `workflow/*/spec.md` | Design docs for each workflow phase — not operative |
| `workflow/_phases.md` | How phases connect and when to transition |
| `universal/rules.md` | Source content for always-on behavior rules |
| `universal/hooks/` | Hook infrastructure — examples and active scripts |
| `domains/` | Domain-specific rules (ml, frontend, research, systems) |
| `install/install.sh` | Wires brain globally into Claude Code and Cursor |
| `BRAINSTORM.md` | Living design doc — decisions, structure, open questions |

---

## Working in Brain

### Editing a skill
The operative file is in `.claude/commands/<name>.md`. The corresponding spec is in `workflow/<name>/spec.md`.
- Edit `.claude/commands/<name>.md` to change how the command behaves
- Update `workflow/<name>/spec.md` if the design intent changes
- Keep them in sync — the spec is the why, the command is the what

### Adding a new skill
1. Create `.claude/commands/<name>.md` with the full prompt
2. Create `workflow/<name>/spec.md` with the phase definition
3. Re-run `install/install.sh` to register it globally

### Adding a hook
1. Write the script in `universal/hooks/scripts/`
2. Add the hook config to `.claude/settings.json`
3. Re-run `install/install.sh` to sync globally

### Adding a domain
1. Create `domains/<name>/rules.md` with domain-specific behavior
2. Create `.cursor/rules/<name>.mdc` for Cursor pickup
3. Re-run `install/install.sh`

### Adding an agent (subagent)
1. `cp agents/_template/agent.md agents/personas/<name>.md` (or `agents/background/<name>.md`)
2. Fill in the frontmatter — the `tools:` allowlist **is** the safety boundary; keep it minimal
3. Write the system-prompt body
4. Re-run `install/install.sh` — it symlinks every agent `*.md` (with a `name:` field) into
   `~/.claude/agents/`, flattened by basename, so **agent filenames must be globally unique**
5. Verify with `/agents` in a fresh session

Personas encode posture structurally: Scout (read-only, voice default) · Reviewer (read +
git-inspect) · Builder (autonomous, scoped) · Operator (background, tightest scope). See
`agents/README.md`.

### After any structural change
Re-run `install/install.sh` to keep global Claude Code and Cursor configs in sync.

---

## Conventions

- Specs (`workflow/*/spec.md`) document intent — they explain why a phase works the way it does
- Commands (`.claude/commands/*.md`) are operative — they are the actual prompt the AI runs
- Never overwrite prior entries in `docs/` files — always append
- `BRAINSTORM.md` is the source of truth for design decisions — update it when significant changes are made
