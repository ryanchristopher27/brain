# Domains

Domain resources scope the brain suite to a specific discipline — ML, frontend, research, systems, etc. A domain can add rules, commands, Cursor rules, or any combination. Each domain is self-contained and optional.

---

## How Domains Work

### Auto-Detection
At the start of any session, Claude checks for domain signals in the current project (see each domain's `detect.md`). If a domain is detected, its `rules.md` is read and applied for the session.

Multiple domains can be active simultaneously — a FastAPI + React project would activate both ml and frontend domains.

Detection signals are defined per domain and typically include:
- File presence (`package.json`, `requirements.txt`, `pyproject.toml`, etc.)
- Directory patterns (`models/`, `components/`, `notebooks/`, etc.)
- Config files (`.eslintrc`, `tsconfig.json`, `Dockerfile`, etc.)
- Import patterns in source files

### Cursor Activation
Domain rules for Cursor use glob patterns in `.mdc` frontmatter to activate automatically on relevant file types. No detection logic needed — Cursor handles it natively.

### Manual Override
Any project can declare a domain explicitly in its `CLAUDE.md`:
```
domains: ml, frontend
```
This supplements auto-detection — useful when signals are ambiguous or missing.

---

## Domain Structure

```
domains/<name>/
├── README.md        # What this domain covers, when it activates
├── detect.md        # Auto-detection signals (file patterns, dirs, configs)
├── rules.md         # Domain-specific behavior rules
└── commands/        # Domain-specific slash commands (optional)
    └── *.md         # Each file = one slash command
```

And in `.cursor/rules/`:
```
.cursor/rules/<name>.mdc    # Cursor rule file for this domain
```

---

## Creating a New Domain

1. Copy `domains/_template/` to `domains/<name>/`
2. Fill in `README.md`, `detect.md`, and `rules.md`
3. Add domain commands to `commands/` if needed
4. Create `.cursor/rules/<name>.mdc` for Cursor support
5. Re-run `install/install.sh` to register any new commands globally

---

## Existing Domains

| Domain | Status | Activates when |
|--------|--------|---------------|
| *(none yet)* | — | — |

---

## Detection in Universal Rules

Universal rules instruct Claude to check for domain signals at session start. The check is lightweight — Claude looks at the top-level directory, key config files, and any explicit `domains:` declaration in `CLAUDE.md`. It then reads and applies matching domain `rules.md` files before proceeding.
