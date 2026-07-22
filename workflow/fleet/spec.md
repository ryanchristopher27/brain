# Command: /fleet

## Overview
On-demand multi-agent orchestration verb. Takes a task, decomposes it into independent slices,
dispatches brain personas (Scout / Reviewer / Builder) in parallel via the Task tool, and
merges their reports into one synthesized answer. It is the operative, user-invoked counterpart
to the ambient "Multi-Agent Orchestration" rule in `universal/rules.md`.

Not a workflow phase — no output doc, no handoff. A utility verb that can be invoked from any
phase.

## Trigger
User invokes `/fleet <task>` manually. No automatic firing.

## Input
A task description. Optionally the current project/plan context (`docs/plan.md`, active domain).

## Process
1. Decompose the task into independent subtasks. If it won't split (sequential/dependent),
   handle it directly and say so — don't force a fan-out.
2. Assign each slice to a persona by posture (read-only vs scoped-write).
3. Brief each agent with a self-contained prompt + an explicit report-back contract.
4. Dispatch concurrently (multiple Task calls in one turn).
5. Merge/synthesize: reconcile conflicts, surface disagreements, attribute findings.
6. Report one unified result with a persona-attribution note.

## Output
Chat-only: a synthesized answer plus attribution. No output doc — though dispatched Builders
may have edited files as a side effect.

## Handoff
None. Pairs naturally with `/review` (audit what was produced) or `/build` (carry a chosen
approach forward).

## Safety
- Read-only personas (Scout/Reviewer) fan out freely.
- Builder fan-out requires non-overlapping file scopes plus a post-merge verify.
- Never parallel-write shared files.

## Tool behavior
- **Claude Code:** spawns installed personas from `~/.claude/agents/` via the Task tool.
- **Cursor:** no parallel Task-tool dispatch — degrades to sequential persona-style passes as
  described in the orchestration rule.

## Design intent (the why)
Orchestration lives in two places on purpose: an ambient rule (so fan-out is considered
automatically on large tasks) and this explicit verb (so the user can force it). The personas
carry the safety contract in their frontmatter tool allowlists; `/fleet` only decides *who*
runs and *how results merge* — it never widens a persona's permissions.
