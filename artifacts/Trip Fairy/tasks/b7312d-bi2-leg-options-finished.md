---
id: b7312d
source: plan:trip-planner:BI2
title: BI2 — Leg options, finished
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-28T00:44:06Z
updated: 2026-09-29T02:47:28Z
---

## Brief
Unify options[]+pickedId on legs; live fare as flight option; options on proposals; audit/budget read the pick

## Acceptance

## Runs

## Updates
- 2026-09-28T00:44:06Z · created
- 2026-09-28T01:09:23Z · status: backlog → doing
- 2026-09-28T01:15:40Z · comment: Shipped legOptions.js (pick w/ flight snapshot stash+restore, chosen flight as option, inherit on flight picks, merge keeps live/stashed, live one-way price on dated plans, assistant mode change via pick, stable order). 120 tests, mutation-checked; verified live LIS→OPO $64 TAP nonstop.
- 2026-09-28T01:15:40Z · status: doing → review
- 2026-09-29T02:47:28Z · status: review → done (approved by Ryan in chat 2026-09-28: ideation is a good start — follow-ups go in new tasks)
