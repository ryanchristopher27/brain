# Command: /status

## Overview
A utility command that scans the current project and reports workflow state at a glance. Tells you which phases have run, what's outstanding, and what to do next — then offers to jump to the suggested next phase.

Not a workflow phase — no handoff, no output doc. Chat-only, read-only.

## Trigger
User invokes `/status` manually. No automatic firing.

## Behavior
- Scans project entirely from existing files — asks nothing
- Works in any project, with or without brain workflow docs
- Always ends with a suggested next phase and an offer to start it

## Detection Logic
| Phase | Signal |
|-------|--------|
| Brainstorm | `docs/brainstorm.md` exists |
| Plan | `docs/plan.md` exists |
| Scaffold | Recognizable project structure (entry points, dependency manifest) |
| Build | Source files with meaningful content beyond boilerplate |
| Review | `docs/review.md` exists |
| Iterate | `docs/review.md` has "Resolved This Session" entries |
| Reflect | `docs/reflect.md` exists |

## Output
Chat only — no files written.

## Relationship to Workflow
`/status` is the orientation layer for the whole workflow. Useful when:
- Returning to a project after a break
- Mid-session context switch
- Unsure which phase to run next
- Handing a project to someone else
