---
id: d69149
source: feedback:trip-planner:eric-route-detour-check
title: Stop AI suggestions from adding far-out-of-the-way stops
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-10T22:41:24Z
updated: 2026-10-22T02:46:22Z
---

## Brief
Eric's test (Sedona/Grand Canyon/Zion), 2026-10-10. A suggestion added a stop well off the route in the middle of the trip. Add a detour check (extra driving vs direct route) when the AI builds or edits a route, and either drop the stop, move it, or flag it with the added time.

## Acceptance

## Runs

## Updates
- 2026-10-10T22:41:24Z · created
- 2026-10-22T02:23:41Z · status: backlog → doing
- 2026-10-22T02:46:22Z · status: doing → review (Deployed. Trip page: a stop that adds a big detour between its neighbors shows 'Out of the way · +Nh' (hover explains) and 'Move it' when it fits better elsewhere (ends stay put; fixed-date and out-and-back stops ignored). Edit + finder prompts now tell the AI to keep routes sensible and say how much extra travel an off-route request adds. Unit 576/0, smoke 207/0.)
