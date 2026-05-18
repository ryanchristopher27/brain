# /scaffold

You are entering **Scaffold Mode** — generating the project structure, boilerplate, and config files needed to produce a runnable starting point.

## First: Read Context

In order:
1. `docs/plan.md` — primary source of truth
2. `docs/brainstorm.md` — supplementary context on intent
3. Current project directory — detect what already exists

**If no plan exists:**
Warn the user that a plan is strongly recommended. Offer to run `/plan` first. If they want to proceed anyway, ask:
- What is the project and what tech stack is being used?
- What is the top-level structure?
- What are the entry points?

## Extract From the Plan

Pull these before doing anything else:
- Tech stack and framework
- Architecture overview and module breakdown
- File/folder structure (if explicitly defined)
- AI resources section (CLAUDE.md, brain domains, project-specific rules)
- Dependencies and entry points
- Any CI/deployment mentions

## Determine Structure

**Priority order:**
1. Explicitly defined in plan → use it directly
2. Tech stack recognized → apply domain default (see below)
3. Neither → ask the user before proceeding

**Domain defaults:**
| Stack | Default Structure |
|-------|-----------------|
| Next.js / React | `app/`, `components/`, `lib/`, `public/`, `styles/` |
| FastAPI / Flask | `app/`, `routers/`, `models/`, `services/`, `tests/` |
| Node / Express | `src/`, `routes/`, `middleware/`, `models/`, `tests/` |
| Python CLI | `src/`, `cli.py`, `utils/`, `tests/` |
| Monorepo | `apps/`, `packages/`, `shared/` |
| Generic | `src/`, `tests/`, `docs/` |

## Detect Existing Files

Scan the project directory. Any file or folder that already exists:
- Will NOT be overwritten
- Will be listed in the preview under "Will skip"

## Build the Preview

Always generate and present a preview before writing anything.

```
Scaffold Preview — [Project Name]

Will create:
  [tree of files with one-line description of each]

Will skip (already exists):
  [list of existing paths]

Unspecified — need input:
  [list of gaps found in the plan, with a yes/no or choice question for each]

AI Resources:
  [what will be generated based on plan's AI resources section, or "Not specified in plan — skipping"]
```

## Confirmation Behavior

**If everything is fully specified in the plan:**
After preview, ask once: "Ready to scaffold?" — write everything on confirmation.

**If there are gaps:**
Ask about each unspecified item before writing. Once all gaps are resolved, write in stages:
1. Directory structure
2. Entry points and boilerplate files
3. Config files (`.gitignore`, dependency manifest, `README.md`)
4. AI resources (`CLAUDE.md`, brain wiring) if specified

## What to Generate

**Always (if not already present):**
- Directories per structure
- Entry point files with correct imports and minimal runnable boilerplate
- Dependency manifest (`package.json`, `requirements.txt`, `go.mod`, etc.) with dependencies listed
- `.gitignore` for the tech stack
- `README.md` pre-populated from plan overview and setup instructions

**Only if specified in the plan:**
- `CLAUDE.md` — pre-populated with project context, tech stack, conventions, linked brain resources
- Domain config files (`.eslintrc`, `tsconfig.json`, `pyproject.toml`, `Dockerfile`, etc.)
- Test directory with a starter test file
- CI config if deployment or CI was in the plan

**Never:**
- Business logic or feature implementation
- Overwriting existing files

## AI Resources Rule

Generate `CLAUDE.md` and brain resource wiring **only if the plan specifies it**. The brainstorm and plan phases are responsible for this decision. If the plan is silent on AI resources, skip this entirely and note it in the preview.

## After Scaffolding

Produce a brief build-ready summary:
- What was created
- What was skipped and why
- Entry point(s) to start from
- First suggested task drawn from plan milestones

## Behavior Rules

- **Runnable is the target** — the project should execute after scaffold, even if it does nothing
- **Never overwrite** — detect, skip, report
- **Never assume** on significant gaps — ask
- **Preview always** — no files written before the user sees the full picture
- **AI resources are plan-driven** — do not generate without plan specification
