# /fleet

Orchestrate a multi-persona attack on a task: decompose it, dispatch brain personas in
parallel via the Task tool, and merge their results into one synthesized answer.

`/fleet <task>` — the task to orchestrate. If no task is given, ask what to orchestrate.

## When to use

Explicit, on-demand orchestration for tasks big enough to split — broad research, multi-area
audits, or a build that divides across independent file scopes. For small or strictly
sequential work, skip the ceremony and just do it directly.

## Process

1. **Decompose** — break the task into independent slices. If it doesn't split (steps are
   sequential/dependent), say so and handle it directly instead of forcing a fan-out.
2. **Assign personas** — map each slice to the right persona by posture:
   - **Scout** — read-only research/exploration (parallelize freely)
   - **Reviewer** — critique/review of existing code (read-only)
   - **Builder** — implementation, only across **non-overlapping** file scopes
   - *(Operator is background-only — not used for interactive fan-out)*
3. **Brief** — give each agent a self-contained prompt: its slice, the context it needs, and
   an explicit report-back contract (what to return, in what shape).
4. **Dispatch in parallel** — spawn all agents concurrently (multiple Task calls in one turn).
   Keep writers off shared files.
5. **Merge** — synthesize the reports: reconcile conflicts, surface disagreements, dedupe,
   and attribute findings where it matters. Don't just concatenate.
6. **Report** — one unified result, plus a short note on which persona produced what and any
   unresolved conflicts.

## Guardrails

- Never run multiple Builders over the same files — partition scopes or sequence them.
- Read-only fan-out (Scout/Reviewer) is always safe. Autonomous fan-out (Builder) requires
  non-overlapping scopes **and** a post-merge verify.
- If the decomposition is unclear, ask before dispatching — a bad split wastes parallel work.

## Tool behavior

- **Claude Code:** spawns the installed personas (`~/.claude/agents/`) via the Task tool.
- **Cursor:** no Task-tool fan-out — fall back to sequential persona-style passes.

See the "Multi-Agent Orchestration" rule in `universal/rules.md` for the ambient version of
this behavior.
