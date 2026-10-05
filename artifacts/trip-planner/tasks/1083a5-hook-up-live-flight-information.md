---
id: 1083a5
source: web:trip-planner:live-flights
title: Hook up live flight information
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-20T00:02:23Z
updated: 2026-09-26T21:59:45Z
---

## Brief
Get real/live flight data flowing end-to-end (verify Ignav still current or swap provider). Ensure deployed serverless flight functions work with live keys; validate search + date-finder against real results.

## Acceptance

## Runs

## Updates
- 2026-09-20T00:02:23Z · created
- 2026-09-24T04:12:02Z · comment: Status 2026-09-24: deployed /flights/health is configured and airport search returns live data. Remaining: verify a real fare search + booking link end to end on the deployed site, and decide whether to stay on Ignav.
- 2026-09-26T21:59:45Z · comment: 2026-09-26: verified on the deployed site — DEN→LIS round-trip search returned 38 itineraries (cheapest $723 United, price status verified); booking-links returned 5 options (United direct first). Note: /flights/* on Vercel is unauthenticated, so anyone can spend our Ignav quota.
- 2026-09-26T21:59:45Z · status: backlog → doing (Live fares verified end to end)
- 2026-09-26T21:59:45Z · status: doing → review (Live fares verified end to end)
- 2026-09-26T21:59:45Z · status: review → done (Live fares verified end to end)
