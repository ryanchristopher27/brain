---
id: e863fb
source: adhoc:trip-planner:db-cleanup-job
title: Daily database cleanup job (pg_cron)
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-09T03:08:48Z
updated: 2026-10-17T21:11:14Z
---

## Brief
Scheduled cleanup inside Supabase (pg_cron, no Vercel function): expired OAuth codes/unused clients/dead grants, old MCP undo history, stale fare/AI cache, old tombstones, stale pending invites, long-inactive guest accounts — with retention rules documented

## Acceptance

## Runs

## Updates
- 2026-10-09T03:08:48Z · created
- 2026-10-09T03:08:48Z · status: backlog → doing (subagent started)
- 2026-10-09T03:11:44Z · status: doing → review (Merged 4a19421; migration 0019 awaiting user OK)
- 2026-10-09T03:13:40Z · comment: 0019 applied 2026-10-08; job scheduled 09:15 UTC; preview: fare_cache 7, everything else 0, no errors; dry run rolled back (rows still present). Check cleanup_runs after first run.
- 2026-10-10T19:00:26Z · comment: Scheduled runs logged (latest 2026-10-10 09:15 UTC), no errors.
- 2026-10-17T21:11:14Z · status: review → done (User review pass 2026-10-17: PASS)
