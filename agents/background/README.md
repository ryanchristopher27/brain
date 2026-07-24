# Background Agents

Unattended agents that run without a human in the loop — on a schedule or on demand.

## How it runs
- **Persona:** `operator.md` — read-only (Read/Grep/Glob), tightest scope, every run logged.
- **Runner:** `runner.sh` — wraps one headless `claude -p --agent operator` call, pins a
  read-only tool allowlist, and saves both a log and a report to `~/.claude/brain-bg-logs/`
  (outside the repo, so no git churn).

```sh
agents/background/runner.sh "<task prompt>" [label]
# e.g.
agents/background/runner.sh "Read updates/queue.md and summarize the most recent entry." queue-digest
```

## The safety model — the runner writes, not the agent
A headless `claude -p` agent can't interactively approve its own writes, so granting an
unattended agent write access is the footgun. Instead: **Operator stays read-only and emits
text; `runner.sh` persists that text.** The agent never needs write permission. `runner.sh`
never passes `--dangerously-skip-permissions`. To widen tools for a specific job, set
`BRAIN_BG_TOOLS` — an explicit, per-invocation opt-in.

## Scheduling
Pick the trigger by *where the work lives*:

- **Local job (reads your repo/files) → launchd.** Use `com.brain.queue-digest.plist.example`
  as a template (see the comments in it to install/enable/disable). This is the right choice
  for anything that touches local files — it runs on *this* machine.
- **Remote/cloud-appropriate job → Claude Code `/schedule`.** `/schedule` creates remote
  routines; use it when the task doesn't depend on your local working tree.

> Note: the plan originally named `/schedule` as primary, but the seed job here reads local
> files, so launchd is the correct trigger for it. `/schedule` remains right for remote work.

## Safety checklist for any new background job
- Start read-only; grant writes only per-job via `BRAIN_BG_TOOLS`, as narrowly as possible.
- Dry-run the task with `runner.sh` before scheduling it.
- Keep the logs — every run writes one.
- Never `--dangerously-skip-permissions`.

## Status
`operator.md` + `runner.sh` are live and verified (the queue-digest job runs read-only and
writes a report). The launchd template is provided but **not installed** — enabling a
recurring job is your call (milestone A4).
