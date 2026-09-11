---
id: 55067e
source: plan:trip-planner:N4
title: N4 — Escalation (snapshot)
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T20:10:49Z
updated: 2026-09-06T20:37:11Z
---

## Brief
escalateToPlan() with id remap; Create plan flow (name + optional start date); open plan workspace

## Acceptance

## Runs

## Updates
- 2026-09-06T20:10:49Z · created
- 2026-09-06T20:34:19Z · status: backlog → doing (building)
- 2026-09-06T20:37:11Z · status: doing → review (built + verified)
- 2026-09-06T20:37:11Z · comment: escalate.js: escalateToPlan(proposal,{variantName,startDate}) — copies SHARED_FIELDS (arrays cloned) + remapRecordIds for fresh segment/activity ids, returns newPlan w/ proposalId. ProposalView: inline Create-plan form (name prefilled 'Plan N' + optional start date, snapshot hint). App: createPlan escalates + selects the new plan. 12/12 escalate unit assertions (independence, id remap, no dangling). Verified in-app: created 'September trip' from proposal → opened in plan Workspace w/ committed fields, nested under proposal (1 plan), disjoint segment ids from proposal (true snapshot). Test plan removed after.
