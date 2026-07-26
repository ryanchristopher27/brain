# Brainstorm — Agent Dashboard enhancements
Date: 2026-07-24
Feeds: `docs/plan.md` → "Agent Dashboard (Pillar C v2)" + its "Enhancements & Revisions (v2)"

## Problem / Opportunity
The dashboard plan (v1) covered a control server, the orb-as-active-session panel, roster,
jobs, schedule, control actions, and a run registry. This session pressure-tested it for what
would make it genuinely better before scaffolding — and surfaced a second product axis the
original framing missed.

## The reframe (biggest outcome)
The dashboard has **two axes**, and they unify:
1. **Agents & Runs** — who's working, how, at what cost.
2. **Work Pipeline** — ideas progressing brainstorm → plan → scaffold → build → review →
   reflect (a Kanban board; phase detected via `/status` doc-logic).
Agents are what *move a pipeline card forward*. This turns the dashboard into mission control
for both the fleet and the flow of work.

## Ideas & Directions (all adopted)
- **Live activity + cost** — per-run tool-call feed + spend panel, from `stream-json`
  `tool_use` + `total_cost_usd`/tokens we already parse. Near-free, high signal.
- **Approvals inbox** — `claude -p --permission-prompt-tool` routes tool-approval requests to
  the dashboard (approve/deny). Unlocks safe autonomous writes and pays off the "headless can't
  prompt" debt open since B4. *Must probe the flag against 2.1.167 first.*
- **MCP + daemon health** — connection status for github/notion/playwright (surfaces the A2
  tokens-not-set gap), daemon liveness, model/permission-mode.
- **Task queue / dispatcher** — enqueue tasks, assign to personas, watch them drain (later phase).
- **Work-pipeline board** — the user's addition; the second axis above.
- **Extras** — macOS notifications on job finish/fail/spend; quick-action templates; `/fleet`
  run visualization (parallel personas as concurrent runs).

## Correction folded in (not optional)
**localhost is not private** — any web page you visit can POST to `127.0.0.1:<port>` (CSRF). The
plan's "local bind, no auth" is unsafe. Mandatory: token + `Origin`/`Host` check + an action
audit log on the control API.

## Recommendations / Suggested Decisions (confirmed)
- Registry storage: **SQLite** (enables cost/stats/history).
- Adopt all enhancements + extras; phase strictly so Phase 1 still ships a real read-only
  dashboard (D1–D3, D7) before any control.
- Approvals via `--permission-prompt-tool`, verified before D8.
- Security hardening mandatory in D4.

## Open Questions for /plan (recorded there)
- Pipeline: current repo only (v1) vs configured project roots; phase-detection tiebreak.
- Approvals: probe `--permission-prompt-tool` on claude 2.1.167 before D8.
- Backend home (`dashboard/` recommended), local auth token, default spawn persona (Scout).

## Next Steps
Decisions are folded into `docs/plan.md`. Phase 1 (D1 control server → D2 shell+orb → D3
panels → D7 pipeline board) is the first shippable slice → ready for `/scaffold` once the
Phase-1 open questions have their (safe) defaults confirmed.
