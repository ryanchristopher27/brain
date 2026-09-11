---
id: e4a6aa
source: review:trip-planner:proposal-delete-orphans-plans
title: Deleting a proposal orphans its plans
type: bug
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T20:47:37Z
updated: 2026-09-06T20:47:38Z
---

## Brief
Warning · App.deleteTrip · child plans left unreachable in storage; FIXED via cascade delete

## Acceptance

## Runs

## Updates
- 2026-09-06T20:47:37Z · created
- 2026-09-06T20:47:37Z · status: backlog → doing (fixing)
- 2026-09-06T20:47:38Z · status: doing → review (fixed: cascade-delete plans + reset selection; verified 3→0 records)
