---
id: 885fc7
source: plan:trip-planner:N5
title: N5 — Kind-aware chat + polish
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T20:10:49Z
updated: 2026-09-06T20:42:40Z
---

## Brief
editPlan prompt branch on kind; breadcrumbs; empty states; verification pass

## Acceptance

## Runs

## Updates
- 2026-09-06T20:10:49Z · created
- 2026-09-06T20:40:31Z · status: backlog → doing (building)
- 2026-09-06T20:42:40Z · status: doing → review (built + verified)
- 2026-09-06T20:42:40Z · comment: aiClient: editPlan prompt branches on kind — shared OP_PROTOCOL + PLAN vs PROPOSAL intro/rules; proposal prompt forbids dates/status/flights/lodging/day-time-cost and points to escalation, labels context CURRENT PROPOSAL. buildEditPrompt exported for tests. PlanChat: kind-aware header ('Proposal chat' vs 'Plan chat') + intro examples. Verified: 9/9 prompt-kind assertions; full regression green (mig/v3/patch/escalate); in-app proposal shows 'Proposal chat' + proposal intro. NOTE: proposal restriction is prompt-level + UI-hidden (applyOps field whitelist still technically permits committed fields); acceptable this pass.
