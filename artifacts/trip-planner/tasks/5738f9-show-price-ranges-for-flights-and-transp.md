---
id: 5738f9
source: adhoc:trip-planner:price-ranges
title: Show price ranges for flights and transport
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-29T04:37:51Z
updated: 2026-10-05T02:18:36Z
---

## Brief
Show an expected range (e.g. $480–$620) instead of a single value for flights and other transport, especially when prices are high or vary a lot; collapse to a single value when the variance is low. Sources: fare sweep cells / date grid spread, multiple itineraries, LLM low–high estimates for ground modes. Must go through the shared Price formatter (per traveler / trip total).

## Acceptance

## Runs

## Updates
- 2026-09-29T04:37:51Z · created
- 2026-10-04T21:49:16Z · status: backlog → doing
- 2026-10-04T21:49:16Z · status: doing → review (Estimated legs/options carry costLow/costHigh (cost = midpoint, budget unchanged); shown as ranges in Getting around + chips + chat context; live/booked fares stay single. 223 tests, smoke 70/70.)
- 2026-10-05T02:18:36Z · status: review → done (Closed by user)
