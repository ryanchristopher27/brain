# Background Agents

Unattended agents that run without a human in the loop — on a schedule or on demand.

## How it runs
- **Persona:** `operator.md` — the tightest-scope autonomous agent. Every run is logged.
- **Runner:** `runner.sh` — wraps a single headless `claude -p` invocation, pinning the
  Operator persona and an explicit tool allowlist, and tees output to a timestamped log.
- **Scheduling (primary):** Claude Code's own `/schedule` (fleet-aware, minimal plumbing).
- **Scheduling (escape hatch):** a `launchd` user-agent invoking `runner.sh`, reserved for
  jobs that must fire even when Claude Code isn't open. Not built until a job needs it.

## Safety
Background agents are the highest-risk surface (no human to approve a prompt). Rules:
- Start read-only; grant writes only per-job, scoped as narrowly as possible.
- Full logging, always. Dry-run new jobs before enabling.
- Never `--dangerously-skip-permissions`.

## Status
`operator.md` frontmatter + `runner.sh` skeleton are scaffolded. Wiring a real scheduled
task is **milestone A4**.
