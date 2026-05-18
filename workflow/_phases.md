# Workflow Phases — Connective Tissue

This document maps how the workflow phases connect, when to move between them, what each phase needs from the previous one, and how the full loop works. The workflow is not strictly linear — it's a directed graph with a primary path, built-in cycles, and multiple entry points.

---

## The Primary Path (New Project)

```
/brainstorm → /plan → /scaffold → /build → /review → /iterate → /reflect
                                               ↑______________|
                                           (review/iterate loop)
```

This is the default flow for a new project from scratch. Not every project follows every step — see Skip Conditions below.

---

## The Core Refinement Loop

```
/build → /review → /iterate → /review → /iterate → ... → /reflect
```

After the first build milestone, the work lives in this loop until the project is ready to ship or the session ends. `/review` and `/iterate` alternate until findings are resolved, then `/reflect` closes the cycle.

---

## Phase Map

### /brainstorm
| | |
|---|---|
| **Needs from prior phase** | Nothing — entry point |
| **Produces** | `docs/brainstorm.md` |
| **Hands off to** | `/plan` (primary), or back to `/brainstorm` for sub-features |
| **Can be skipped if** | Problem is fully clear — `/plan` runs a mini-brainstorm internally |
| **Can loop back from** | `/reflect` when direction changes significantly |

### /plan
| | |
|---|---|
| **Needs from prior phase** | `docs/brainstorm.md` (preferred) or runs inline mini-brainstorm |
| **Produces** | `docs/plan.md` |
| **Hands off to** | `/scaffold` (if greenfield) or `/build` (if structure exists) |
| **Can be skipped if** | Never fully skipped — `/build` requires a plan or demands one |
| **Can loop back from** | `/iterate` (when changes are too large to handle inline), `/reflect` (when plan needs updating after retrospective) |

### /scaffold
| | |
|---|---|
| **Needs from prior phase** | `docs/plan.md` with tech stack and structure defined |
| **Produces** | Project file structure, boilerplate, config files, optionally `CLAUDE.md` |
| **Hands off to** | `/build` |
| **Can be skipped if** | Project structure already exists — `/build` starts directly |
| **Runs once** | Not meant to be re-run; detects and skips existing files if re-invoked |

### /build
| | |
|---|---|
| **Needs from prior phase** | `docs/plan.md` + scaffolded project (or existing codebase) |
| **Produces** | Implemented code per plan milestones |
| **Hands off to** | `/review` at milestone completion (suggested), or `/reflect` at session end |
| **Can be skipped if** | Never — this is where work happens |
| **Suggests** | `/review` after each milestone; `/reflect` at natural session end |

### /review
| | |
|---|---|
| **Needs from prior phase** | Code in scope + `docs/plan.md` |
| **Produces** | Findings in chat (small) or `docs/review.md` (larger) |
| **Hands off to** | `/iterate` (for deferred findings), `/reflect` (if clean), `/ship` (if ready — deferred) |
| **Can be skipped if** | User consciously decides not to review — not recommended before ship |
| **Soft gates** | Warns on unresolved criticals before `/ship` |

### /iterate
| | |
|---|---|
| **Needs from prior phase** | `docs/review.md` findings and/or user feedback |
| **Produces** | Refined code, optionally updated `docs/plan.md` |
| **Hands off to** | `/review` (to validate changes — always suggested), or `/reflect` if done |
| **Can be skipped if** | No findings to address and no feedback to incorporate |
| **Kicks back to** | `/plan` + `/build` when a requested change is too large to handle inline |

### /reflect
| | |
|---|---|
| **Needs from prior phase** | Session history + any docs produced (plan, review, prior reflections) |
| **Produces** | `docs/reflect.md` entry; optionally memory updates, CLAUDE.md additions, plan flags |
| **Hands off to** | `/build` (continuing), `/brainstorm` or `/plan` (new direction), `/ship` (wrapping up — deferred) |
| **Can be skipped if** | User chooses not to — but suggested at every session end and milestone |
| **Depth scales with scope** | Session-end = lighter; project close = more thorough |

---

## Entry Points

The workflow doesn't always start at `/brainstorm`. Common mid-project entry points:

| Situation | Start here |
|-----------|-----------|
| New project, problem unclear | `/brainstorm` |
| New project, problem clear | `/plan` |
| Existing codebase, continuing work | `/build` |
| Existing codebase, something feels off | `/review` |
| Returning after a break | `/reflect` (brief) → then `/build` or `/plan` |
| New feature on existing project | `/brainstorm` or `/plan` (scoped) |
| Stuck or lost direction | `/brainstorm` or `/reflect` |
| Quality pass on finished work | `/review` → `/iterate` |

---

## Skip Conditions

| Phase | Safe to skip when |
|-------|------------------|
| `/brainstorm` | Problem is fully defined — `/plan` covers it with mini-brainstorm |
| `/scaffold` | Project structure already exists |
| `/review` | Conscious decision — not recommended before shipping |
| `/iterate` | No findings and no feedback to address |
| `/reflect` | User chooses not to — always suggested, never forced |
| `/ship` | Deferred — build when formally needed |

**Never safe to skip:** `/plan`, `/build`

---

## Feedback Loops

### Review → Iterate → Review
The primary quality loop. Runs as many times as needed until findings are resolved or user is satisfied.

### Iterate → Plan → Build
Triggered when a change requested during iteration is too large to handle inline. `/iterate` surfaces this, kicks to `/plan` to scope it properly, then `/build` implements it.

### Reflect → Brainstorm / Plan
Triggered when a retrospective reveals a significant direction change, unresolved strategic question, or plan that no longer reflects reality. `/reflect` flags it; user decides whether to re-enter at `/brainstorm` or go straight to `/plan`.

### Build → Reflect → Build
At session end during a long build phase. `/reflect` captures progress and sets up the next session, then `/build` continues where it left off.

---

## Phase Transition Signals

How to know it's time to move to the next phase:

| From | To | Signal |
|------|----|--------|
| `/brainstorm` | `/plan` | A recommended direction exists and key constraints are known |
| `/plan` | `/scaffold` | Tech stack decided, structure defined, entry points clear |
| `/plan` | `/build` | Structure already exists — skip scaffold |
| `/scaffold` | `/build` | Project is runnable, structure is in place |
| `/build` | `/review` | A milestone is complete or a logical chunk of work is done |
| `/review` | `/iterate` | Findings exist that need addressing |
| `/review` | `/reflect` | No significant findings — work is clean |
| `/iterate` | `/review` | All items in the working list are resolved |
| `/iterate` | `/plan` | A requested change is too large for inline iteration |
| Any phase | `/reflect` | Session is ending, milestone is complete, or user steps back to assess |
| `/reflect` | `/build` | Continuing — next steps are clear |
| `/reflect` | `/brainstorm` | Direction has meaningfully changed |
| `/reflect` | `/plan` | Plan needs updating based on what was learned |

---

## The Full Loop (Reference)

```
New project:
  /brainstorm → /plan → /scaffold → /build
                                       ↓
                              [milestone complete]
                                       ↓
                                   /review
                                  ↙       ↘
                           findings      clean
                              ↓             ↓
                          /iterate       /reflect
                              ↓             ↓
                          /review      [next session]
                              ↓             ↓
                           clean         /build
                              ↓
                           /reflect
                              ↓
                    [ship when ready — /ship deferred]
```

Mid-project (returning or new feature):
```
  /reflect (brief) → /plan (scoped) → /build → /review → /iterate → /reflect
```

Quality pass only:
```
  /review → /iterate → /review → /reflect
```
