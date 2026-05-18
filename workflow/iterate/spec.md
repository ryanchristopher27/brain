# Phase: Iterate

## Overview
A refinement phase driven by review findings, user feedback, or both. Distinct from `/build` in intent — `/build` implements new things from the plan milestone by milestone; `/iterate` improves, fixes, and refines what already exists. Can add new functionality if the change is small enough to handle inline; anything large enough to need its own planning kicks back to `/plan` + `/build`.

Can be invoked at any point — after a `/review`, mid-build when something feels off, or any time the user wants to refine rather than build forward.

---

## Trigger
User invokes `/iterate` manually. `/review` suggests it for deferred findings. Never fires automatically.

---

## Input

**Either or both, depending on context:**

### Review Findings
- Reads `docs/review.md` for deferred findings (Warnings and Suggestions carried from review)
- Checks the "Carried to /iterate" section specifically
- Cross-references findings against current code — some may already be resolved

### User Feedback
- Direct feedback in the conversation ("this feels wrong", "can we rework X", "I want to add Y")
- New requirements or direction changes that don't warrant a full planning session
- Performance or UX concerns observed during use

**If both are present:** merge them into a single working list before starting.

**Also reads:**
- `docs/plan.md` — to understand intent and catch when a change warrants a plan update
- `CLAUDE.md` — project conventions
- Current code — to understand current state before changing anything

---

## Scope of Work

### What `/iterate` handles
- Fixing review findings (warnings, suggestions)
- Refactoring for clarity, structure, or performance
- Minor quality improvements
- Small new functionality — additions that are clearly bounded and don't require architectural decisions
- Addressing user feedback on existing implementation

### What kicks back to `/plan` + `/build`
- New functionality that introduces new architecture, data models, or significant new modules
- Changes that affect multiple milestones in the plan
- Anything that would meaningfully change the scope section of the plan
- When in doubt: if it needs more than a brief discussion to scope, it belongs in `/plan`

Surface the distinction explicitly when a request lands at the boundary — explain why and offer to kick it to `/plan`.

---

## Working Order

### Default: Auto-Prioritized
Work through findings and feedback in this order:
1. Critical findings (if any remain from review)
2. User-directed feedback (what the user specifically raised)
3. Warnings from review
4. Suggestions from review

### User Override
User can direct the order at any time — "start with X", "skip Y for now", "do suggestions first". Follow their lead.

---

## Plan Update Rules

Update `docs/plan.md` when `/iterate` makes:

| Change Type | Plan Update |
|-------------|------------|
| Bug fix, minor refactor, small quality improvement | None |
| New functionality added | Update relevant milestone/task section |
| Architectural change | Update architecture section + decisions log |
| Scope change (adding or removing something material) | Update scope section + decisions log |
| Tech stack change | Update tech stack section + decisions log |

Always note what changed and why in the decisions log when updating. Do not rewrite the plan — append or update the specific section only.

---

## New Functionality Handling

When a user requests new functionality during `/iterate`:

1. **Assess size** — is this a small, bounded addition or something larger?
2. **Small** (contained to one module, no new architecture, clear implementation path): proceed inline, flag it as an addition, update plan if needed
3. **Large** (new modules, architectural decisions, significant scope change): stop, explain why it warrants its own planning, offer to open `/plan`
4. **Boundary cases**: surface the distinction, give a recommendation, let the user decide

---

## Iteration Cycle

Iterate until one of:
- All review findings and feedback items are resolved
- User indicates they're done ("that's enough", "looks good", "ship it")
- A natural stopping point is reached

At any stopping point:
- Summarize what was changed
- List anything deliberately deferred
- Suggest running `/review` again to validate the changes
- If review passes clean (or user is satisfied), suggest `/ship`

---

## Behavior Notes

- **Merge inputs** — combine review findings and user feedback into one working list before starting
- **Cross-reference first** — some review findings may already be resolved; check before acting on them
- **Auto-prioritize by default** — criticals first, then user feedback, then warnings, then suggestions
- **Respect user override** — if they want to work in a different order, follow them
- **Plan updates are proportional** — don't update the plan for minor fixes; do update it for anything that changes what was built or how
- **Surface the line** — when a request is too large for iterate, say so clearly and offer the right path
- **Always leave the project runnable** — don't introduce broken states between iteration tasks
- **End with a loop suggestion** — iteration naturally feeds back into review; suggest the cycle
