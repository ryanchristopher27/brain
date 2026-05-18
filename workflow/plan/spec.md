# Phase: Plan

## Overview
Transforms a problem space into a structured, actionable plan. Reads existing brainstorm context if available; if not, runs a lightweight brainstorm internally before planning to ensure the plan is grounded. Starts high-level and grows in depth based on how much detail the user wants to go into.

Can be invoked at any point: initial project planning, planning a sub-feature, or re-planning after a pivot.

---

## Trigger
User invokes `/plan` manually. No automatic firing.

---

## Input

**Preferred:** A brainstorm doc (`docs/brainstorm.md`) from a prior `/brainstorm` session.

**If no brainstorm doc exists:**
- Run a condensed internal brainstorm before planning
- Cover: problem/opportunity, goal, audience, constraints, rough direction
- Keep it short — enough to ground the plan, not a full brainstorm session
- Do not produce a separate brainstorm doc; fold the context into the plan

**Other context it will read if present:**
- Existing plan docs (for mid-project or sub-feature invocations)
- `CLAUDE.md` project context
- Prior session memory
- Directory structure (to understand what already exists)

---

## Interaction Style (Adaptive Depth)

### Default: High-Level
Start by producing a high-level plan covering milestones, tech stack, architecture overview, and scope. Do not dive into granular task breakdowns unless asked.

### Signals to Go Deeper
Watch for:
- User asking follow-up questions about specific sections
- User providing more technical detail or constraints
- User explicitly asking to break down a milestone or task
- User approving a section and asking "what's next" at a granular level

When these signals appear, drill into that section without replanning everything.

### Depth Levels
| Level | What's Covered |
|-------|---------------|
| High | Milestones, tech stack, architecture, scope, success criteria |
| Mid | Above + file/folder structure, task breakdown per milestone, dependencies |
| Deep | Above + implementation steps, API shapes, data models, acceptance criteria, edge cases |

The plan document grows as depth increases — new sections are added, existing sections are expanded. The structure never resets.

---

## Decision Approach

For significant decisions (tech stack, architecture patterns, data model choices, major scope calls):
- Present a recommendation with clear reasoning
- Explain tradeoffs vs. alternatives
- Flag where user input is required before proceeding
- Allow the user to provide context inline or confirm post-hoc after reading the full plan

For minor decisions:
- Make the call with a brief note explaining why
- User can override when reviewing

---

## Process

1. **Context check** — Look for brainstorm doc, existing plan, CLAUDE.md, and project state
2. **Mini-brainstorm (if needed)** — If no brainstorm doc, ask 2-4 grounding questions before planning
3. **Draft high-level plan** — Produce the default template sections
4. **Present and checkpoint** — Share the high-level plan, invite feedback and questions
5. **Drill deeper (if signaled)** — Expand specific sections based on user engagement
6. **Finalize** — Confirm open questions, flag what `/scaffold` needs, mark plan as ready

---

## Output

A markdown file saved to the project: `docs/plan.md`

If one already exists (mid-project or sub-feature), append a new versioned section rather than overwriting.

### Default Document Structure

```
# Plan — [Project / Feature Name]
Date: YYYY-MM-DD
Status: Draft | Active | Archived
Brainstorm: [link to brainstorm doc if exists, or "inline" if mini-brainstorm was run]

## Overview
What is being built and why. One paragraph.

## Goals & Success Criteria
What "done" looks like. Measurable where possible.

## Scope
### In Scope
### Out of Scope

## Tech Stack & Architecture
Key decisions with reasoning. Alternatives considered noted briefly.

## Milestones
High-level phases of work with rough sequencing.
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|

## Task Breakdown
(Populated as depth increases — starts empty or high-level)

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|

## Dependencies
External systems, APIs, services, or people required.

## Open Questions
Unresolved decisions that may affect planning. Assigned to plan or build phase.

## Decisions Log
Record of significant choices made and why.
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
```

---

## Handoff to `/scaffold`

Before closing, `/plan` should confirm:
- Tech stack is decided
- Top-level project structure is clear
- Entry points and primary modules are identified

These are the minimum inputs `/scaffold` needs to generate the file structure. If any are unresolved, flag them explicitly.

---

## Behavior Notes

- If invoked without a brainstorm doc, do not skip grounding — run the mini-brainstorm first
- Never fully commit to deep granularity unprompted — follow the user's lead
- When recommending a tech decision, always note what was considered and ruled out
- For mid-project invocations: read the existing plan, scope the new plan section tightly, and note how it relates to existing decisions
- If the user contradicts a prior decision from brainstorm or an earlier plan version, surface the conflict and ask them to confirm the change
- The plan doc is a living artifact — it should be updatable, not a one-shot output
