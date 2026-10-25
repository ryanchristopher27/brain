---
id: 64df91
source: scale:trip-planner:monitoring
title: Usage and cost monitoring
type: task
status: doing
assignee: 
scoped_dir: .
created: 2026-10-17T22:14:53Z
updated: 2026-10-24T00:51:53Z
---

## Brief
From docs/research/scaling-plan.md (2026-10-17). AI spend weekly + AI Gateway budget cap; Ignav searches/day; Supabase DB/egress/realtime/sign-ups at 70% of limits; Resend daily sends; client geocode/route failure rate; cleanup_runs errors; purchases per MAU.

## Acceptance

## Runs

## Updates
- 2026-10-17T22:14:53Z · created
- 2026-10-23T03:15:13Z · status: backlog → doing
- 2026-10-23T03:19:58Z · comment: Code deployed (d4a3cd5 merge): migration 0026_ops_summary (written + PGlite-checked 14/0, NOT applied — needs owner OK), npm run ops report, daily Vercel cron /ops/check (15:00 UTC) emailing via Resend only when a limit is crossed. Owner env: CRON_SECRET, RESEND_API_KEY, OPS_ALERT_EMAIL (+ optional OPS_* limits, OPS_FARE_MONTH = Ignav plan size).
- 2026-10-24T00:51:53Z · comment: 0026_ops_summary applied to production 2026-10-23. Verified: service_role only; runs (30d AI $1.75, 17 active, 16 MB DB, cleanup 0 errors); run_cleanup dry run clean. Remaining: owner sets CRON_SECRET, RESEND_API_KEY, OPS_ALERT_EMAIL in Vercel.
