---
id: f928a0
source: plan:trip-planner:N3
title: N3 — Kind-gated proposal editor
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T20:10:49Z
updated: 2026-09-06T20:33:09Z
---

## Brief
ProposalView + hide committed-only sections in TripEditor when kind=proposal; reuse Timeline/chat

## Acceptance

## Runs

## Updates
- 2026-09-06T20:10:49Z · created
- 2026-09-06T20:29:14Z · status: backlog → doing (building)
- 2026-09-06T20:33:09Z · status: doing → review (built + verified)
- 2026-09-06T20:33:09Z · comment: TripEditor kind-gated: proposals hide Start/End date, Status, Flights section, segment arrive/depart/lodging, and activity day/time/cost; labels soften (Rough length, Ideas of things to do). ProposalView real: reuses three-pane Workspace (self-gates via kind) under a 'Proposal · Plans' bar (quick-links to plans; Create-plan reserved for N4). App routes proposal→ProposalView, plan→Workspace(+breadcrumb). Verified in-app: proposal editor has no date/flight/lodging/status inputs; a plan still shows Start/End date + Flights + Status (kind-specific).
