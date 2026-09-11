---
id: 394b11
source: plan:trip-planner:M1
title: M1 — Segment model + migration
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-05T23:06:21Z
updated: 2026-09-05T23:18:55Z
---

## Brief
v2 schema (segments[], activity.segmentId), helpers, v1→v2 shim; TripEditor edits segments

## Acceptance

## Runs

## Updates
- 2026-09-05T23:06:21Z · created
- 2026-09-05T23:15:22Z · status: backlog → doing (building)
- 2026-09-05T23:18:55Z · status: doing → review (built + verified)
- 2026-09-05T23:18:55Z · comment: v2 schema: segments[]+activity.segmentId+SCHEMA_VERSION in trip.js; day-range helpers (orderedSegments/segmentDayRanges/segmentForDay); real v1→v2 migrate.js (14/14 assertions pass); storage.js loads v2 w/ migrate-on-read + v1 backstop; TripEditor Segments section + activity city selector; Sidebar label prefers segment cities. Verified in-app: Rome 3n→D1-3, Florence 2n→D4-5.
