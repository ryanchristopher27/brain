---
id: a369af
source: web:trip-planner:credit-estimates
title: Per-action credit estimates (P5 remainder)
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-24T04:12:01Z
updated: 2026-09-26T02:05:10Z
---

## Brief
Send real action kinds to /ai/plan (new_proposal=3, new_plan=5; today every reasoning call is billed as 'prompt'=1) and show the cost before the action ('Create plan · 5 credits'). Costs live in server/billing.mjs ACTION_COST.

## Acceptance

## Runs

## Updates
- 2026-09-24T04:12:01Z · created
- 2026-09-26T01:08:34Z · status: backlog → doing (Subagent building in its own worktree.)
- 2026-09-26T01:23:31Z · comment: Merged: kinds + cost display + background abuse guard (21/21 harness). OPEN DECISION: per-record-emptiness pricing overcharges repeated turns on empty plans/proposals; recommended server-side outcome-based charging before shipping.
- 2026-09-26T01:30:42Z · status: doing → review (Outcome-based pricing built (server/outcome.mjs) + cost display + background guard. 19/19 outcome harness.)
- 2026-09-26T02:05:10Z · status: review → done (Shipped 2026-09-25 (pushed + verified live).)
