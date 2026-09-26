---
id: da94b7
source: web:trip-planner:trip-audit-ai
title: "Trip audit layer 2: AI consistency pass"
type: feature
status: backlog
assignee: 
scoped_dir: .
created: 2026-09-26T01:04:46Z
updated: 2026-09-26T01:04:46Z
---

## Brief
Add an AI check on top of the deterministic audit (src/lib/audit.js) for things fingerprints can't see: e.g. an activity that no longer fits the city, a pace/budget that contradicts the plan, day plans that ignore travel time, seasonal closures on the dates. Run on demand from the trip-bar check, and optionally every few assistant edits; background model, results as issues in the same TripAudit popover with suggested fixes.

## Acceptance

## Runs

## Updates
- 2026-09-26T01:04:46Z · created
