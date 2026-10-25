---
id: 8e0756
source: adhoc:trip-planner:city-page-layout
title: Rethink city page layout — map always visible across tabs
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-29T04:37:51Z
updated: 2026-10-05T02:17:26Z
---

## Brief
Keep the map in view while browsing Things to do / Places to stay / Food (e.g. a split view on desktop with a sticky map; on phones a collapsible map). Picking/hovering a place should highlight it on the map.

## Acceptance

## Runs

## Updates
- 2026-09-29T04:37:51Z · created
- 2026-10-05T02:10:49Z · comment: Built on feat/city-layout: one shared map per city page. Desktop (page area >=880px) = list left + sticky full-height map right; phone = sticky tabs + collapsible 150px map strip. Card hover/focus lights its marker; card click or 'Show on map' centers + pulses it; marker click selects/scrolls its card. 239 tests, build ok, smoke 80/80.
- 2026-10-05T02:10:53Z · status: backlog → ready
- 2026-10-05T02:10:53Z · status: ready → doing
- 2026-10-05T02:10:53Z · status: doing → review (Implemented; see docs/plan.md 2026-10-04 section)
- 2026-10-05T02:17:26Z · status: review → done (Closed by user)
