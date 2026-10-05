---
id: 3e0c68
source: plan:trip-planner:FO1
title: FO1 — Fare gating, cache & sweep
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-26T22:12:08Z
updated: 2026-09-26T22:31:24Z
---

## Brief
Sign-in for live fares on Vercel, per-user daily cap (150), shared fare_cache table, POST /flights/sweep with bounded concurrency; client sends auth + handles 401/429

## Acceptance

## Runs

## Updates
- 2026-09-26T22:12:08Z · created
- 2026-09-26T22:13:27Z · status: backlog → doing (Building FO1)
- 2026-09-26T22:21:46Z · status: doing → review (Built + verified locally (41-check harness, live open-jaw + 7-day sweep). Deploy after migration 0005 is applied.)
- 2026-09-26T22:27:23Z · comment: 2026-09-26: deployed. Applied migrations 0002–0005 to the live Supabase project via MCP (only 0001 had ever been applied — usage logging with 'cached', AI cache, purchase grants, free-tier grants and the AI rate limit were silently off). Live: signed-out /flights/search, /flights/sweep, /flights/booking-links → 401; airports open. Remaining: one signed-in sweep on the live site.
- 2026-09-26T22:31:24Z · status: review → done (Signed-in sweep verified live by user)
