# Phase: Scaffold

## Overview
Generates the project structure, boilerplate, and config files from the plan. The goal is a runnable starting point — not just empty folders, but enough real content that you can immediately execute the project even if it does nothing yet.

Detects what already exists and only creates missing pieces. Always previews before writing. Asks about anything the plan left unspecified.

---

## Trigger
User invokes `/scaffold` manually. No automatic firing.

---

## Input

**Primary:** `docs/plan.md`

Reads from the plan:
- Tech stack and architecture decisions
- Milestones and module breakdown
- File/folder structure (if specified)
- AI resources section (determines whether to generate `CLAUDE.md` and wire brain resources)
- Dependencies and entry points

**If no plan exists:**
- Warn the user that a plan is strongly recommended
- Offer to run `/plan` first, or proceed with a guided setup (ask for tech stack, structure, and purpose before scaffolding)

**Other context read if present:**
- `docs/brainstorm.md` — for additional context on intent
- Existing project directory — to detect what's already there

---

## What It Generates

### Always (if not already present)
- Directory structure matching the plan
- Entry point files with correct imports and minimal working boilerplate
- Dependency manifest (`package.json`, `requirements.txt`, `go.mod`, etc.) with listed dependencies
- `.gitignore` appropriate for the tech stack
- `README.md` pre-populated from plan overview and setup steps

### If Specified in the Plan
- `CLAUDE.md` — pre-populated with project context, tech stack, conventions, and linked brain resources
- Domain config files (`.eslintrc`, `tsconfig.json`, `pyproject.toml`, `Dockerfile`, etc.)
- Test directory with a starter test file
- CI config (`.github/workflows/`) if deployment or CI was mentioned in the plan

### Never
- Business logic or feature implementation — scaffold creates the shell, build fills it
- Files that already exist (detects and skips, reports what was skipped)

---

## Structure Source (Priority Order)

1. **Explicitly defined in plan** — use it directly
2. **Domain-aware default** — inferred from tech stack (Next.js, FastAPI, CLI, etc.)
3. **Ask the user** — if tech stack is ambiguous or no recognizable pattern applies

### Domain Defaults
| Stack | Default Structure |
|-------|-----------------|
| Next.js / React | `app/`, `components/`, `lib/`, `public/`, `styles/` |
| FastAPI / Flask | `app/`, `routers/`, `models/`, `services/`, `tests/` |
| Node / Express | `src/`, `routes/`, `middleware/`, `models/`, `tests/` |
| Python CLI | `src/`, `cli.py`, `utils/`, `tests/` |
| Monorepo | `apps/`, `packages/`, `shared/`, per-app structure within |
| Generic | `src/`, `tests/`, `docs/` |

---

## AI Resources Section

Whether to generate `CLAUDE.md` and which brain resources to wire in is determined entirely by what the plan specifies. The brainstorm and plan phases should have addressed:
- Does this project use Claude Code or Cursor (or both)?
- Which brain domains apply (ml, frontend, research, systems)?
- Are there project-specific rules, hooks, or MCPs needed?

If this section is present in the plan, scaffold generates and wires accordingly.
If absent, scaffold does not generate any AI resource files and notes this in the preview.

---

## Confirmation Behavior (Dynamic)

### Always
- Generate a full preview before writing any files
- Show: tree of files to create, brief description of each file's content, files detected as already existing (will be skipped)

### If Everything Is Specified in the Plan
- After preview, ask once: "Ready to scaffold?" and write everything on confirmation

### If Anything Is Unspecified
- Surface the gaps explicitly in the preview
- Ask about each gap before writing
- Once gaps are resolved, write in stages — structure first, then boilerplate, then config

### Preview Format
```
Scaffold Preview — [Project Name]

Will create:
  src/
    main.py          # Entry point, FastAPI app init
    routers/
      users.py       # Placeholder router
    models/
      user.py        # SQLAlchemy User model shell
  tests/
    test_main.py     # Starter pytest test
  requirements.txt   # fastapi, uvicorn, sqlalchemy, pytest
  .gitignore         # Python gitignore
  README.md          # Pre-populated from plan

Will skip (already exists):
  docs/              # Exists

Unspecified (need input):
  Auth strategy not defined in plan — include auth scaffold? [yes/no]
  CI/CD not mentioned — generate GitHub Actions workflow? [yes/no]

AI Resources:
  CLAUDE.md          # Will generate (specified in plan)
  brain domains: frontend, ml (will link in CLAUDE.md)
```

---

## Handoff to `/build`

After scaffolding, produce a brief build-ready summary:
- What was created
- What was skipped and why
- Entry point(s) to start from
- First suggested build task (drawn from plan milestones)

---

## Behavior Notes

- **Runnable is the target** — after scaffold, the project should execute even if it does nothing
- **Never overwrite** existing files — detect, skip, and report
- **Never assume** when the plan is silent on something significant — ask
- **Domain awareness** — apply the right defaults for the tech stack without being asked
- **AI resources are plan-driven** — do not generate CLAUDE.md or brain wiring unless the plan specifies it; brainstorm and plan are responsible for that decision
- The scaffold is a one-time operation per project (or per new sub-section) — it is not meant to be re-run repeatedly
