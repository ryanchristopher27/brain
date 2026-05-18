# Phase: Brainstorm

## Overview
The entry point for any new project, feature, or problem. Explores the problem space divergently, then converges toward a set of options, recommendations, and suggested decisions — without fully committing. Output serves as the primary input to `/plan`.

Can be invoked at any point in a project: initial kickoff, a new sub-feature, a pivot, or a stuck point.

---

## Trigger
User invokes `/brainstorm` manually. No automatic firing.

---

## Input
Whatever the user brings — from a single sentence to a full brain dump. The command adapts its behavior based on input richness (see Interaction Style below).

Optional context it can use if present:
- Existing brainstorm or plan docs in the project
- `CLAUDE.md` project context
- Prior session memory

---

## Interaction Style (Dynamic)

Assess the user's opening message before responding.

**If the user provides rich input** (detailed description, multiple ideas, clear context):
- Acknowledge what was shared
- Ask at most 1-2 high-signal clarifying questions
- Move quickly into synthesis and divergent exploration

**If the user provides sparse input** (vague idea, single sentence, open-ended):
- Enter guided questionnaire mode
- Ask questions progressively — don't front-load everything at once
- Cover: problem/opportunity, goal, audience, constraints, existing ideas
- Build toward synthesis as answers accumulate

**In both cases:**
- Stay curious, not prescriptive
- Surface assumptions the user may not have stated
- Push thinking into areas not yet considered
- Explicitly flag when enough has been covered to move toward output

---

## Process

1. **Intake** — Assess input richness, choose interaction style
2. **Explore (Diverge)** — Surface multiple directions, angles, and framings. Don't prune yet.
3. **Probe** — Identify constraints, unknowns, and assumptions. Ask about what hasn't been said.
4. **Synthesize (Converge)** — Cluster ideas into coherent directions. Evaluate tradeoffs.
5. **Recommend** — Identify the most promising direction(s) and why. Flag decisions that should be locked before planning.
6. **Document** — Produce the brainstorm output doc.

---

## Output

A markdown file saved to the project: `docs/brainstorm.md` (or appended to an existing one if mid-project).

### Document Structure

```
# Brainstorm — [Project / Feature Name]
Date: YYYY-MM-DD
Phase: Initial | Mid-project | Sub-feature | Pivot

## Problem / Opportunity
What are we actually solving or building toward?

## Goals
What does success look like? What are we optimizing for?

## Audience
Who is this for? What do they need?

## Constraints
Technical, time, resource, scope, or other limits.

## Ideas & Directions
Divergent section — all ideas captured, no pruning yet.

### Direction A — [Name]
Description, tradeoffs, fit with goals/constraints.

### Direction B — [Name]
...

### Direction N — [Name]
...

## Recommendations
Which directions look most promising and why.
Ranked or prioritized if applicable.

## Suggested Decisions
Specific choices to lock in before moving to /plan.
These are not mandates — they are informed starting points.

## Open Questions
Unknowns, risks, or things to resolve during /plan.

## Next Steps
What /plan needs to begin. Any prep work flagged here.
```

---

## Handoff to `/plan`

The brainstorm doc is the primary artifact `/plan` reads. At minimum, `/plan` needs:
- A clear problem statement
- At least one viable direction chosen or recommended
- Known constraints
- Open questions to resolve during planning

If the brainstorm doc doesn't cover these, `/brainstorm` should flag that before closing.

---

## Behavior Notes

- Do not make final decisions — surface and recommend, let the user confirm
- If the user hasn't considered something important (security, scalability, cost, audience edge cases), raise it even if not asked
- Keep the tone collaborative, not interrogative
- Mid-project invocations should reference prior brainstorm/plan docs and frame new ideas in relation to existing decisions
- If invoked on a sub-feature, scope the output accordingly — don't re-litigate the whole project
