---
id: 2dd5cb
source: plan:trip-planner:D7
title: D7 — Realtime live-sync
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-11T14:06:17Z
updated: 2026-09-12T02:17:13Z
---

## Brief
Later: Supabase subscriptions for live multi-device updates

## Acceptance

## Runs

## Updates
- 2026-09-11T14:06:17Z · created
- 2026-09-12T02:15:54Z · status: backlog → doing (building)
- 2026-09-12T02:17:13Z · status: doing → review (built; live test + realtime publication pending user)
- 2026-09-12T02:17:13Z · comment: Realtime live-sync. App: supabase.channel('trips-sync').on(postgres_changes, {table:trips, filter:user_id=eq.<uid>}) while signed in; per-row LWW apply (soft-delete = deleted=true rows). Echo-safe: own push echoes with same updatedAt → guard skips → no loop. removeChannel on cleanup; logged-out = no subscription. Verified: build clean, logged-out fresh-tab console clean (no realtime when signed out). Pushed (75f6917). PENDING user: (1) enable realtime on the table — SQL: alter publication supabase_realtime add table public.trips; (2) two signed-in sessions (two windows / laptop+phone) to see live propagation. RLS scopes events per-user.
