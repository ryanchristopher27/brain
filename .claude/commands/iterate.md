# /iterate

You are entering **Iterate Mode** — a refinement phase for improving, fixing, and extending what already exists. Distinct from `/build` (milestone-driven new implementation) by intent: `/iterate` is quality- and feedback-driven.

## First: Read Context

1. `docs/review.md` — deferred findings ("Carried to /iterate" section)
2. `docs/plan.md` — intent, architecture, scope (to catch when changes warrant a plan update)
3. `CLAUDE.md` — project conventions
4. Current code — understand the current state before changing anything

## Build the Working List

Combine all inputs into one list before starting:
- Review findings carried from `/review` (cross-reference against current code first — some may already be resolved)
- User feedback from the conversation

If both are present, merge them. Don't work through them separately.

## Working Order

**Default — auto-prioritized:**
1. Critical findings (if any remain)
2. User-directed feedback (what the user specifically raised this session)
3. Warnings from review
4. Suggestions from review

**User can override at any time** — "start with X", "skip Y", "do suggestions first". Follow their lead without pushback.

## Scope Check: Iterate vs. Plan

Before starting any item, assess whether it belongs in `/iterate` or `/plan` + `/build`:

**Handle in `/iterate`:**
- Bug fixes, refactors, quality improvements
- Small bounded additions (one module, no new architecture, clear implementation path)
- User feedback on existing implementation

**Kick to `/plan` + `/build`:**
- New functionality requiring new architecture, data models, or significant new modules
- Changes spanning multiple plan milestones
- Anything that materially changes the scope of the project
- If it needs more than a brief discussion to scope — it belongs in `/plan`

When something lands at the boundary: explain the distinction, give a recommendation, let the user decide.

## Plan Update Rules

| Change | Plan Update |
|--------|------------|
| Bug fix, minor refactor, quality improvement | None |
| New functionality added | Update relevant milestone/task |
| Architectural change | Update architecture section + decisions log |
| Scope change | Update scope section + decisions log |
| Tech stack change | Update tech stack section + decisions log |

When updating: append or update the specific section only. Don't rewrite the plan. Always note what changed and why in the decisions log.

## Working Through the List

For each item:
1. State what's being addressed and why (which finding or feedback it maps to)
2. Implement the change
3. Confirm it resolves the issue
4. Note it as resolved
5. Move to the next item

Keep the project runnable between tasks — don't introduce broken states.

## Stopping Points

Stop iterating when:
- All items are resolved
- User says they're done
- A natural break point is reached

At each stopping point:
- Summarize what was changed
- List anything deliberately deferred
- Suggest running `/review` again to validate
- If clean or user is satisfied, suggest `/ship`

## Behavior Rules

- **Merge inputs first** — one working list, not two parallel tracks
- **Cross-reference before acting** — some review findings may already be fixed; check first
- **Auto-prioritize by default** — follow the order unless overridden
- **Surface the line** — when a request is too large for iterate, say so and offer the right path
- **Plan updates are proportional** — minor fixes don't touch the plan; meaningful changes do
- **Always leave runnable** — no broken states between tasks
- **End with the loop** — iteration feeds back into review; always suggest `/review` when done
