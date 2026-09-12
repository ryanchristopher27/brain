---
id: a7826a
source: plan:trip-planner:D1
title: D1 — Supabase project + schema + client
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-11T14:06:17Z
updated: 2026-09-11T14:59:40Z
---

## Brief
Provision Supabase; trips jsonb table + RLS (user_id=auth.uid()); supabase.js client from env

## Acceptance

## Runs

## Updates
- 2026-09-11T14:06:17Z · created
- 2026-09-11T14:56:48Z · status: backlog → doing (building)
- 2026-09-11T14:59:40Z · status: doing → review (built + verified live)
- 2026-09-11T14:59:40Z · comment: Supabase project provisioned; trips table (id text PK, user_id uuid default auth.uid(), kind, data jsonb, updated_at, deleted) + RLS (4 owner-scoped policies) created; index on (user_id, updated_at desc). supabase.js client reads VITE_SUPABASE_URL/ANON_KEY (new publishable key sb_publishable_*, browser-safe; secret key kept out of client), null when unconfigured. Verified live via REST: unauth select→200 [] (table exists, key valid, RLS blocks rows); unauth insert→401 RLS violation (writes require authed owner). .env gitignored.
