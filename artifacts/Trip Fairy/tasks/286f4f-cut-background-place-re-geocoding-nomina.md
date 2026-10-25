---
id: 286f4f
source: scale:trip-planner:poi-audit
title: Cut background place re-geocoding (Nominatim load)
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-17T22:14:53Z
updated: 2026-10-18T23:07:54Z
---

## Brief
From docs/research/scaling-plan.md (2026-10-17). auditPoiGeo re-checks ~15 places per city view (~80% of Nominatim traffic). Run it only on demand ('Wrong spot?') or for places the AI flagged; keep stop geocoding.

## Acceptance

## Runs

## Updates
- 2026-10-17T22:14:53Z · created
- 2026-10-18T22:29:33Z · status: backlog → doing
- 2026-10-18T23:07:54Z · status: doing → review (Merged 2026-10-18: 525 unit, 200 smoke, market 47, signout 29, oauth 9. 0023 not applied yet (link section hidden until it is).)
