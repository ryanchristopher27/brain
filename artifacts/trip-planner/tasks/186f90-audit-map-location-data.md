---
id: 186f90
source: web:trip-planner:location-audit
title: Audit map location data
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-25T23:59:01Z
updated: 2026-09-26T02:05:10Z
---

## Brief
Check that places land where they should on the map. Coordinates for stops, departure city, and city places (things to do/stays/food) are guessed by the model (lib/geo.js, lib/derive.js), cached on the record, and never re-checked. Audit a sample of trips for wrong or off pins, then decide on fixes: validate against a geocoder (e.g. OpenStreetMap Nominatim), let users drag or correct a pin, and re-geocode when a name changes.

## Acceptance

## Runs

## Updates
- 2026-09-25T23:59:01Z · created
- 2026-09-26T01:08:34Z · status: backlog → doing (Subagent building in its own worktree.)
- 2026-09-26T01:23:31Z · status: doing → review (Built by subagent, merged + verified in browser 2026-09-25; not yet deployed.)
- 2026-09-26T02:05:10Z · status: review → done (Shipped 2026-09-25 (pushed + verified live).)
