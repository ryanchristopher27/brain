---
id: 7d8973
source: scale:trip-planner:shared-geo-cache
title: Shared geocode and road-route caches
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-17T22:14:53Z
updated: 2026-10-24T22:37:57Z
---

## Brief
From docs/research/scaling-plan.md (2026-10-17). Look each place/route up once for everyone: server-side cache tables for geocodes and OSRM routes (keyed like roadKey), then a self-hosted or paid geocoder behind a proxy so the browser stops calling Nominatim/OSRM directly.

## Acceptance

## Runs

## Updates
- 2026-10-17T22:14:53Z · created
- 2026-10-24T22:02:31Z · status: backlog → doing
- 2026-10-24T22:37:57Z · status: doing → review (0027 applied + verified (RLS, no client access, service-only limiter, run_cleanup 35 steps, dry run clean). Deployed; live check: /geo/search (Sedona) and /geo/route answer, CDN HIT on repeat, 1 geo + 1 road row cached. Browser falls back to direct when our server can't answer. Privacy policy updated. Upgrade path: a keyed geocoder behind server/geo.mjs.)
