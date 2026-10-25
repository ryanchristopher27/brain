---
id: fbedc1
source: plan:trip-planner:SUB3
title: SUB3 — Monthly credits and fare caps by plan
type: task
status: doing
assignee: 
scoped_dir: .
created: 2026-10-17T20:15:38Z
updated: 2026-10-23T03:51:49Z
---

## Brief
The monthly refill (ensure_free_grant) gives 150 to active Plus accounts (no rollover); fare caps 150/day + 1,000/month for Plus; free stays 60 signup / 20 monthly.

## Acceptance

## Runs

## Updates
- 2026-10-17T20:15:38Z · created
- 2026-10-23T03:15:13Z · status: backlog → doing
- 2026-10-23T03:51:49Z · comment: Code merged + deployed (inert until 0025 is applied and LS_PLUS_* / VITE_PLUS are set). Reviewed: fixed a free-refill-on-pause/unpause hole (only a new subscription refills immediately). Tests: unit 598, smoke 210, signout 29, market 49, oauth 9, plus 8; PGlite subscriptions 40/0.
