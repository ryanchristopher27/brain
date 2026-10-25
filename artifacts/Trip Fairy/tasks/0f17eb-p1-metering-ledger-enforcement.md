---
id: 0f17eb
source: plan:trip-planner:P1
title: P1 — Metering ledger + enforcement
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-20T03:38:32Z
updated: 2026-09-24T04:11:46Z
---

## Brief
Supabase balance + usage log + atomic consume RPC; JWT-gate api/ai/plan.js; client sends token; 401/402 flows. Makes the public server key safe. Keystone.

## Acceptance

## Runs

## Updates
- 2026-09-20T03:38:32Z · created
- 2026-09-20T03:44:41Z · status: backlog → doing (Building metering ledger: migration + server/billing.mjs + enforce in api/ai/plan.js + client token/kind.)
- 2026-09-20T03:49:32Z · status: doing → review (Built + verified: migration 0001_billing.sql (tables/RLS/RPCs w/ service-role-only grants), server/billing.mjs, metering in api/ai/plan.js (open until env set; 401/402/refund/log), client token+kind in aiClient.js. All branches tested via stubbed fetch. Waiting on you: apply migration in Supabase, set SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in Vercel, seed credits.)
- 2026-09-24T04:11:46Z · status: review → done (Cleanup: shipped — monetization P1–P4 live (metered /ai/plan, model split + cache, Lemon Squeezy webhook, free tier + rate limits).)
