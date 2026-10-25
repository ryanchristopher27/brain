---
id: 7bf27b
source: web:trip-planner:departure-city
title: User-specified departure city (w/ current location)
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-20T00:02:23Z
updated: 2026-09-24T04:11:46Z
---

## Brief
Let the user set the city they're flying from. Use current-location (geolocation) as a smart default but PROMPT to confirm/provide rather than assuming. Feeds startLocation + flight-optimized planning.

## Acceptance

## Runs

## Updates
- 2026-09-20T00:02:23Z · created
- 2026-09-23T03:03:07Z · status: backlog → doing
- 2026-09-23T03:03:07Z · status: doing → review (Home city default + per-trip Flying from, opt-in geolocation suggestion (confirm before save), airport auto-pick, flight forms prefill. Verified typed, one-click, geolocation (mocked position, real OSM), denied, skip paths.)
- 2026-09-24T04:11:46Z · status: review → done (Cleanup: shipped 2026-09-22 — home city + per-trip Flying from, opt-in geolocation.)
