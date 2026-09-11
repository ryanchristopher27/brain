---
id: 77ced4
source: plan:trip-planner:F2
title: F2 — Snapshot schema + normalize
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T22:45:22Z
updated: 2026-09-06T23:27:42Z
---

## Brief
Extend flight leg (snapshot fields) + v3→v4 migration; normalizeOffer/offerToLegs + client searchFlights/searchAirports

## Acceptance

## Runs

## Updates
- 2026-09-06T22:45:22Z · created
- 2026-09-06T23:23:24Z · status: backlog → doing (building)
- 2026-09-06T23:27:42Z · status: doing → review (built + verified)
- 2026-09-06T23:27:42Z · comment: trip.js: newFlight extended with v4 snapshot fields (flightNumber/departAt/arriveAt/durationMinutes/stops/cabin/priceAtSelection/currency/bookingUrl); SCHEMA_VERSION=4. migrate.js: v3→v4 defaults flight fields; FIXED split guard to gate on kind-absence (was schemaVersion>=4 → would have re-split/duplicated committed plans on v3→v4). flights.js: pure normalizeOffer/offerToLegs (flatten outbound+inbound segments→legs, total price on first leg, new ids, confirmation empty) + client searchFlights/searchAirports/flightsConfigured. Verified: 24 assertions incl. against REAL saved Ignav one-way(2 legs)/round-trip(4 legs) responses; v2→v3 + patch regressions green; in-app v3→v4 load keeps 2 records (no duplication), flight legs gain v4 fields.
