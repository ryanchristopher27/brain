---
id: 61f3a5
source: plan:trip-planner:F3
title: F3 — Inline flight search UI
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T22:45:22Z
updated: 2026-09-06T23:47:20Z
---

## Brief
FlightSearch panel (standalone + contextual/pre-filled), results, add-as-legs via patch op; richer leg display

## Acceptance

## Runs

## Updates
- 2026-09-06T22:45:22Z · created
- 2026-09-06T23:41:50Z · status: backlog → doing (building)
- 2026-09-06T23:47:20Z · status: doing → review (built + verified live)
- 2026-09-06T23:47:20Z · comment: FlightSearch.jsx: collapsible panel in the plan Flights section (plan-only via onApplyOps gate) — origin/dest with debounced airport autocomplete, dates (prefilled from trip), travelers/cabin/max-stops, results list (carrier/times/stops/duration/price via normalizeOffer), result cap 15, not-configured/empty/error states. Add-to-trip → offerToLegs → batch add/flight ops through onApplyOps (one undo step). TripEditor: accepts onApplyOps, mounts FlightSearch, richer leg display (flightNumber·times·duration·cabin). Workspace threads onApplyOps to TripEditor. Verified LIVE: JFK→LHR nonstop search returned real BA/AA offers; added BA182 leg (durable snapshot: departAt/duration 410m/295 USD/priceAtSelection, confirmation empty); Undo removed it, Redo enabled.
