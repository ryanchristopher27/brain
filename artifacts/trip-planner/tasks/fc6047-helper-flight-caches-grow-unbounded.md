---
id: fc6047
source: review:trip-planner:helper-cache-unbounded
title: Helper flight caches grow unbounded
type: issue
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T23:30:35Z
updated: 2026-09-06T23:38:01Z
---

## Brief
Suggestion · server/index.mjs · searchCache/airportCache only evict on access after TTL; cap (LRU) or sweep

## Acceptance

## Runs

## Updates
- 2026-09-06T23:30:35Z · created
- 2026-09-06T23:38:01Z · status: backlog → doing (iterate)
- 2026-09-06T23:38:01Z · status: doing → review (fixed + verified)
