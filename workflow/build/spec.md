# Phase: Build

## Overview
An active implementation generator that reads the plan and builds the project task by task. Collaborative by default — pauses for feedback between tasks — but supports a "build all" mode that runs autonomously through the plan. Always flags deviations from the plan. Infers build state from the plan and existing code; no separate tracking file needed.

---

## Trigger
User invokes `/build` manually. No automatic firing.

---

## Input

**Primary:** `docs/plan.md`

Reads from the plan:
- Milestones and task breakdown
- Tech stack and architecture decisions
- Decisions log (for implementation guidance)
- Open questions (flags any that are still unresolved before starting)

**State inference (no tracking file):**
- Reads existing code to determine what's already implemented vs. what's missing
- Cross-references against plan milestones and task breakdown
- Constructs a mental picture of current build state before the first task

**Other context read if present:**
- `docs/brainstorm.md` — intent and direction
- `CLAUDE.md` — project-specific rules and conventions
- Test files — to understand what's already validated

**If no plan exists:**
- Warn the user strongly — build without a plan risks scope drift and rework
- Offer to run `/plan` first
- If user insists on proceeding, ask for the minimum: what to build, tech stack, and where to start

---

## Operating Modes

### Collaborative Mode (Default)
- Present the inferred build state and the next task before starting
- Implement one logical task at a time
- After each task: summarize what was built, check it against the plan, invite feedback before moving to the next
- Wait for explicit continuation ("next", "continue", "looks good") before proceeding

### Build All Mode
- Triggered by user saying "build all", "go", "run through everything", or equivalent
- Implements tasks sequentially without pausing for feedback between each
- **Still pauses for:** deviations from the plan, unresolved blockers, ambiguous implementation decisions
- Summarizes everything built at the end with a full diff against the plan

---

## Pre-Task Behavior

Before implementing each task:
1. Re-read the relevant plan section for that task
2. Check whether any of the plan's open questions affect this task — flag if so
3. State clearly what is about to be built and why (which milestone/task it maps to)
4. If anything is ambiguous, surface options + recommendation before writing code

---

## Post-Task Behavior

After implementing each task:
1. Summarize what was built
2. Verify it matches the plan — note any gaps or differences
3. If in collaborative mode: invite feedback before continuing
4. If a milestone is now complete: flag it and suggest running `/review` before continuing to the next milestone

---

## Deviation Handling

Any time implementation deviates from the plan — whether initiated by the AI or the user:

1. **Flag it explicitly** — name what's changing and how it differs from the plan
2. **State the reason** — why the deviation is happening (technical constraint, better approach, user direction)
3. **Proceed only after confirmation** — user must acknowledge before the deviation is implemented
4. **Note it** — add a comment in the code and/or note it for the plan's decisions log

Deviations are allowed. They are never silently introduced.

---

## Blocker Handling (Dynamic)

When something in the plan is unclear, ambiguous, contradictory, or technically infeasible:

1. **Stop** (unless in "build all" mode where the blocker is minor — then note and continue)
2. **Present the problem clearly** — what specifically is unclear or problematic
3. **Offer options** — at minimum two approaches with tradeoffs explained
4. **Give a recommendation** — which option is suggested and why
5. **Ask the user** — unless they've said "use your judgment" or equivalent

---

## Scope Rules

- Only implement what is in the plan or explicitly requested mid-session
- Do not add error handling, abstractions, or features beyond what was asked
- Do not refactor surrounding code unless the task specifically requires it
- If something adjacent would clearly improve the implementation, mention it — but do not build it without confirmation

---

## Handoff to `/review`

Suggest `/review` when:
- A full milestone is complete
- A significant logical chunk of work is done
- The user has been building for a while without reviewing
- Something was built that deviates from the plan (review that section specifically)

Never force the handoff — always a suggestion.

---

## Behavior Notes

- **Infer state, don't ask** — read the plan and code to figure out where things stand before asking the user what's been done
- **Collaborative by default** — don't assume "build all" unless the user says so
- **Always flag deviations** — no silent scope changes, ever
- **Blockers get options** — never just stop with a problem; always bring a recommendation
- **Plan is the source of truth** — if code and plan conflict, flag the conflict; don't silently pick one
- **Milestone-complete = review prompt** — suggest `/review` at natural completion points
