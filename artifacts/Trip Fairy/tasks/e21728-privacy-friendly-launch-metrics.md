---
id: e21728
source: growth:trip-planner:first-party-metrics
title: Privacy-friendly launch metrics
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-17T21:53:23Z
updated: 2026-10-19T03:01:02Z
---

## Brief
From docs/research/marketing.md (2026-10-17). Count signup source, trip created, share clicked, copy clicked, invite accepted — first-party counts in Supabase, no third-party trackers (the privacy policy says none). Needed to judge launch channels.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:53:23Z · created
- 2026-10-19T02:15:15Z · status: backlog → doing
- 2026-10-19T02:48:20Z · status: doing → review (Merged 2026-10-18: functions 12 → 8 (live endpoints checked), metrics client inert until 0024 is applied.)
- 2026-10-19T03:01:02Z · comment: 0024_app_events applied to production 2026-10-18. Verified: RLS on, 0 policies, anon/auth no table privileges, log_event executable by anon, metrics_summary not executable by anon/auth, run_cleanup 31 steps, dry run errors {}.
