# /plan

You are entering **Plan Mode** — a structured planning phase that transforms a problem space into an actionable, living plan document.

## First: Check Context

Before doing anything else, look for:
1. `docs/brainstorm.md` — prior brainstorm output
2. `docs/plan.md` — existing plan (mid-project or sub-feature invocation)
3. `CLAUDE.md` — project-level context
4. Project directory structure — what already exists

## If No Brainstorm Doc Exists

Run a short grounding session before planning. Ask 2-4 focused questions:
- What are we building and what problem does it solve?
- What does success look like?
- Who is it for?
- Are there known constraints (tech, time, scope)?

Keep it tight — enough to ground the plan, not a full brainstorm. Do not produce a separate brainstorm doc. Fold this context directly into the plan.

## Default Behavior: Start High-Level

Produce the plan starting at a high level:
- Overview
- Goals & Success Criteria
- Scope (in / out)
- Tech Stack & Architecture (with reasoning)
- Milestones

**Do not dive into granular task breakdowns unless the user signals they want more depth.**

## Signals to Go Deeper

Watch for these and drill into that section when you see them:
- User asking follow-up questions about a specific section
- User providing additional technical detail
- User asking to break something down further
- User approving a section and asking "what's next" at a granular level

When drilling deeper, expand the relevant section — do not restart or reformat the whole plan.

## Depth Levels

| Level | Covers |
|-------|--------|
| High | Milestones, tech stack, architecture, scope, success criteria |
| Mid | Above + task breakdown per milestone, file/folder structure, dependencies |
| Deep | Above + implementation steps, API shapes, data models, acceptance criteria |

## Decision Approach

**For significant decisions** (tech stack, architecture, major scope):
- Give a recommendation with clear reasoning
- Note what alternatives were considered and ruled out
- Flag explicitly where you need the user's input before continuing

**For minor decisions:**
- Make the call, note it briefly in the Decisions Log
- User can override on review

## Output

Save to `docs/plan.md`. Create the `docs/` directory if it doesn't exist.

If `docs/plan.md` already exists, append a new versioned section — do not overwrite.

### Document Structure

```
# Plan — [Project / Feature Name]
Date: YYYY-MM-DD
Status: Draft | Active | Archived
Brainstorm: [path to brainstorm doc, or "inline" if mini-brainstorm was run]

## Overview

## Goals & Success Criteria

## Scope
### In Scope
### Out of Scope

## Tech Stack & Architecture

## Milestones
| # | Milestone | Description | Dependencies |

## Task Breakdown
(grows as depth increases)

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |

## Dependencies

## Open Questions

## Decisions Log
| Decision | Choice | Reasoning | Date |
```

## Before Closing

Confirm these are resolved (needed by `/scaffold`):
- Tech stack decided
- Top-level project structure is clear
- Entry points and primary modules identified

If any are unresolved, flag them before handing off.

## Behavior Rules

- Always ground the plan — run the mini-brainstorm if no brainstorm doc exists
- Follow the user's depth signals — don't go deep unprompted
- Always reason through significant decisions; never just pick one
- If the user contradicts a prior decision from brainstorm or an earlier plan version, surface the conflict explicitly and ask them to confirm
- The plan is a living document — frame it as something to update, not a one-shot output
- For mid-project invocations: read the existing plan first, scope the new section tightly, and note how it connects to existing decisions
