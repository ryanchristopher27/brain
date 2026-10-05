---
id: 8517f3
source: web:trip-planner:flight-optimized-planning
title: Flight-optimized trip planning (UI + LLM + date-finding)
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-20T00:02:23Z
updated: 2026-09-27T00:16:34Z
---

## Brief
Add flight UI + LLM planning context that optimizes a trip around real flights: cheapest/best flight TO the first city and FROM the last city, and auto-suggest trip DATES that make the whole thing work. Surface tradeoffs to the user.

## Acceptance

## Runs

## Updates
- 2026-09-20T00:02:23Z · created
- 2026-09-24T04:12:02Z · comment: Unblocked: the departure airport is now on trip.startLocation.iata (settings.home default). Date finder + Flights page already prefill from it.
- 2026-09-26T21:59:45Z · status: backlog → doing (Brainstorm started)
- 2026-09-26T23:02:41Z · status: doing → review (FO1–FO5 built and deployed; awaiting user check on the live site)
- 2026-09-27T00:16:34Z · status: review → done (User confirmed working on the live site)
