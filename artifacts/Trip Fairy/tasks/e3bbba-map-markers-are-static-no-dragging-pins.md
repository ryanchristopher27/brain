---
id: e3bbba
source: user:trip-planner:static-map-markers
title: "Map markers are static: no dragging pins"
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-13T04:18:55Z
updated: 2026-10-17T21:11:14Z
---

## Brief
User request 2026-10-12: nothing on the maps should be draggable. MapCanvas.jsx ~line 542 makes markers draggable when an onMove handler is passed (OdMap.jsx documents a draggable marker that moves a stop/home on drop). Remove marker dragging everywhere (and the tf-mk--draggable styling); if moving a pin was the only way to fix a wrong location, keep a non-drag alternative (e.g. edit the place name / 'Wrong spot? Search again' on the city page).

## Acceptance

## Runs

## Updates
- 2026-10-13T04:18:55Z · created
- 2026-10-14T01:35:26Z · status: backlog → doing
- 2026-10-14T02:24:14Z · status: doing → review (Merged 2026-10-13 (mobile polish): 477 unit, 139 smoke, signout/market/oauth green.)
- 2026-10-17T21:11:14Z · status: review → done (User review pass 2026-10-17: PASS)
