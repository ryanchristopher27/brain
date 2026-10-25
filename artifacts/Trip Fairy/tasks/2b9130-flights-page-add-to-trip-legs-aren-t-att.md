---
id: 2b9130
source: review:trip-planner:flights-page-unlinked-legs
title: Flights page 'Add to trip' legs aren't attached to the route
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-09-26T22:53:18Z
updated: 2026-09-26T23:20:05Z
---

## Brief
FlightsPage/AssistantRail add legs via offerToLegs: one leg per flight segment, from/to = airport codes, no fromSegmentId/toSegmentId. The trip audit then flags them as off-route and they don't show on the trip's hops. Attach them like fareOptimizer.applyOption does (one leg per hop, hop names, airports in fields).

## Acceptance

## Runs

## Updates
- 2026-09-26T22:53:18Z · created
- 2026-09-26T23:20:05Z · status: backlog → doing (Fixed: lib/tripFlights.js; verified live)
- 2026-09-26T23:20:05Z · status: doing → review (Fixed: lib/tripFlights.js; verified live)
- 2026-09-26T23:20:05Z · status: review → done (Fixed: lib/tripFlights.js; verified live)
