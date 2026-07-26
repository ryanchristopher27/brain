# /build

You are entering **Build Mode** — an active implementation generator that reads the plan and builds the project task by task.

## First: Read Context

1. `docs/plan.md` — primary source of truth for what to build
2. Existing code in the project — determine what's already implemented vs. missing
3. `CLAUDE.md` — project conventions and rules
4. `docs/brainstorm.md` — intent context if needed

**If no plan exists:**
Warn the user strongly. Offer to run `/plan` first. If they insist, ask: what to build, the tech stack, and where to start.

## Infer Build State

Before starting, cross-reference the plan's milestones and tasks against the existing codebase. Determine:
- What is already implemented
- What is partially done
- What hasn't been started

Present this state summary before the first task. Do not ask the user what's been done — figure it out from the code.

**Flag any unresolved open questions from the plan before proceeding.**

## Determine Operating Mode

**Default: Collaborative**
Implement one task at a time. After each task, summarize what was built, check against the plan, and wait for feedback or continuation before moving on.

**Build All Mode**
Triggered when the user says "build all", "go", "run through it", or equivalent. Implement tasks sequentially without pausing between them.

Still pause in build all mode for:
- Deviations from the plan
- Unresolved blockers
- Ambiguous implementation decisions

Summarize everything at the end with a full comparison against the plan.

## Pre-Task (Every Task)

Before writing any code:
1. Re-read the relevant plan section
2. Check if any open questions affect this task — flag if so
3. State what you're about to build and which plan milestone/task it maps to
4. If anything is ambiguous, present options + recommendation and ask before starting

## Post-Task (Every Task)

After completing a task:
1. Summarize what was built
2. Verify it matches the plan — note any gaps or differences
3. In collaborative mode: invite feedback before continuing
4. If a milestone is now complete: flag it and suggest `/review` before the next milestone

## Task Sync (tracker)

Keep the tracker task for the milestone you're building current (auto — then report). Milestones
seeded by `/plan` have a task with source `plan:<project>:<milestone-id>`. Docs stay the record;
the tracker reflects progress.

Resolve paths once:
```bash
BRAIN="$(python3 -c "import os;p=os.path.realpath(os.path.expanduser('~/.claude/commands/build.md'));print(os.path.dirname(os.path.dirname(os.path.dirname(p))))")"
PROJ="$(basename "$PWD")"; ID="<milestone-id>"   # e.g. the milestone named in the /build argument
```
- **On starting** the milestone → mark it in progress:
  ```bash
  python3 "$BRAIN/dashboard/tracker_cli.py" --root "$PWD" status --source "plan:$PROJ:$ID" --to doing --note "building"
  ```
- **On completing** it (built + verified) → move to review + log a one-line result:
  ```bash
  python3 "$BRAIN/dashboard/tracker_cli.py" --root "$PWD" status  --source "plan:$PROJ:$ID" --to review --note "built + verified"
  python3 "$BRAIN/dashboard/tracker_cli.py" --root "$PWD" comment --source "plan:$PROJ:$ID" --detail "<what was built>"
  ```
  If a **fleet run** produced the work, also link it:
  ```bash
  python3 "$BRAIN/dashboard/tracker_cli.py" --root "$PWD" link --source "plan:$PROJ:$ID" --run <run_id> --result "<summary>"
  ```

Guardrails: the CLI **skips cleanly** if the milestone has no tracked task (not every build targets
one). Move a task to `review`, not `done` — a human or `/review`/`/reflect` closes it. Never fail
the build over task sync.

## Deviation Rule

Any time implementation deviates from the plan — for any reason:
1. Stop and flag it explicitly — name what's changing and why
2. Get user confirmation before proceeding
3. Note the deviation (code comment + flag for decisions log)

Deviations are allowed. They are never introduced silently.

## Blocker Handling

When something is unclear, ambiguous, contradictory, or infeasible:
1. Stop (or note-and-continue in build all mode for minor issues)
2. Describe the problem clearly
3. Present at least two options with tradeoffs
4. Give a recommendation with reasoning
5. Ask the user — unless they've said "use your judgment"

## Scope Rules

Only build what is in the plan or explicitly requested:
- No extra error handling beyond what's needed
- No abstractions for hypothetical future use
- No refactoring of surrounding code unless the task requires it
- If something adjacent would clearly improve the implementation — mention it, don't build it without confirmation

## Suggest /review When

- A full milestone is complete
- A significant chunk of work is done
- Something was built that deviated from the plan
- The user has been building for a while without reviewing

Always a suggestion, never forced.

## Behavior Rules

- **Infer state from code and plan** — don't ask the user what's been done
- **Collaborative by default** — assume task-by-task unless told otherwise
- **Flag every deviation** — no silent scope changes
- **Blockers get options** — never just stop; always bring a recommendation
- **Plan is source of truth** — if code and plan conflict, surface it
- **Runnable after every task** — leave the project in a working state between tasks where possible
