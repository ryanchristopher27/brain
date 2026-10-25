---
id: 6ccb2e
source: adhoc:trip-planner:collab-owner-checked-save
title: "Shared trips: owner edits through the checked save"
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-07T02:31:13Z
updated: 2026-10-17T21:11:14Z
---

## Brief
Route the owner's edits on shared trips through conflict-checked saves (no LWW vs collaborators); remove device-clock dependence

## Acceptance

## Runs

## Updates
- 2026-10-07T02:31:13Z · created
- 2026-10-07T02:31:13Z · status: backlog → doing (subagent started)
- 2026-10-07T02:39:50Z · comment: Implemented on feat/owner-checked-save: owner store (second createSharedStore) + migration 0016 (not applied). 314 tests, build ok, smoke 82/82. See docs/plan.md 2026-10-06.
- 2026-10-07T02:39:50Z · status: doing → review (Ready for review; 0016 must be applied before the client change is useful)
- 2026-10-07T02:46:06Z · comment: 0016 applied 2026-10-06; sanity: no rows/saves without auth. Needs a real Ava/Ben test (re-seed first: no accepted members exist yet).
- 2026-10-17T21:11:14Z · status: review → done (User review pass 2026-10-17: PASS)
