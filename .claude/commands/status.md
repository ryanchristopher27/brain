# /status

Scan the current project and report workflow state — what's been done, what's outstanding, and what to do next.

## Scan the Project

Check for each of the following in order. Do not ask the user anything — infer everything from what exists.

### Phase Detection

| Phase | How to detect |
|-------|--------------|
| Brainstorm | `docs/brainstorm.md` exists |
| Plan | `docs/plan.md` exists |
| Scaffold | Recognizable project structure exists (entry points, dependency manifest, etc.) |
| Build | Source files exist with meaningful content beyond boilerplate |
| Review | `docs/review.md` exists |
| Iterate | `docs/review.md` has entries in "Resolved This Session" |
| Reflect | `docs/reflect.md` exists |

### Content Extraction (if docs exist)

**From `docs/plan.md`:**
- Current active milestone (the first milestone not yet complete)
- Total milestone count
- Count of unresolved open questions
- Any decisions marked as unresolved

**From `docs/review.md`:**
- Count of findings in "Carried to /iterate" (unresolved)
- Date of last review

**From `docs/reflect.md`:**
- Date of last reflection
- Suggested next phase from the last reflect entry (if present)

**From `docs/brainstorm.md`:**
- Date of last brainstorm entry

## Output Format

Present the report in chat. Never write to a file.

```
Project Status — [project name or current directory]
Scanned: YYYY-MM-DD

── Phases ──────────────────────────────────────
  ✓  Brainstorm    [date of last entry]
  ✓  Plan          [date created]
  ✓  Scaffold      detected
  ◑  Build         Milestone 2 of 4 — [milestone name]
  ✗  Review        not yet run
  ─  Iterate       n/a
  ✗  Reflect       not yet run

── Outstanding ─────────────────────────────────
  • [N] open questions in plan
  • [N] deferred findings from last review
  • [N] unresolved decisions

── Last Activity ────────────────────────────────
  Brainstorm:  YYYY-MM-DD
  Plan:        YYYY-MM-DD
  Review:      YYYY-MM-DD
  Reflect:     YYYY-MM-DD

── Suggested Next ───────────────────────────────
  /review — Milestone 2 is complete and hasn't been reviewed yet.

→ Want me to start /review now?
```

### Phase Status Icons
- `✓` — completed (doc exists or structure detected)
- `◑` — in progress (started but not complete)
- `✗` — not yet run
- `─` — not applicable given current state

### If No Workflow Docs Exist

Still run the scan. Report what IS there (directory structure, existing files, any docs). Then:

```
Project Status — [directory]
Scanned: YYYY-MM-DD

No brain workflow docs found in this project.

── Project Contains ─────────────────────────────
  [list what was found — files, dirs, existing docs]

── Suggested Start ──────────────────────────────
  This project has [no code / some code / a full codebase].

  → /brainstorm — if you're exploring a new idea
  → /plan       — if the direction is already clear
  → /review     — if you want to audit existing code

→ Which would you like to start with?
```

## After the Report

Always end with a suggested next phase and offer to jump there:
- If the suggestion is clear (e.g., milestone complete, no review yet) — name it directly and ask
- If multiple phases are valid — list the top 2 options with one-line reasoning each and ask which to start
- If the project is fully clean (all phases done, nothing outstanding) — say so and ask if they're starting something new

## Behavior Rules

- **Scan first, ask nothing** — infer everything from what exists
- **Always report something** — even an empty project gets a useful response
- **Offer to jump** — don't just report; always close with a suggested next phase and a prompt to start it
- **Keep it scannable** — the report is a quick reference, not a wall of text
- **Date everything** — last activity dates help orient after a break
