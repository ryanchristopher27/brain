---
id: f3adf0
source: plan:trip-planner:SUB2
title: SUB2 — Subscription webhooks and plan record
type: task
status: doing
assignee: 
scoped_dir: .
created: 2026-10-17T20:15:38Z
updated: 2026-10-24T00:51:53Z
---

## Brief
Extend api/webhooks/lemonsqueezy.js for subscription_created/updated/cancelled/expired/payment_failed/resumed; store each account's plan + period end (one Supabase migration — apply only with the user's OK). Verify signatures; idempotent.

## Acceptance

## Runs

## Updates
- 2026-10-17T20:15:38Z · created
- 2026-10-23T03:15:12Z · status: backlog → doing
- 2026-10-23T03:51:49Z · comment: Code merged + deployed (inert until 0025 is applied and LS_PLUS_* / VITE_PLUS are set). Reviewed: fixed a free-refill-on-pause/unpause hole (only a new subscription refills immediately). Tests: unit 598, smoke 210, signout 29, market 49, oauth 9, plus 8; PGlite subscriptions 40/0.
- 2026-10-24T00:51:53Z · comment: 0025_subscriptions applied to production 2026-10-23. Verified: RLS on, 1 policy (select own), anon/auth no table write, auth can read status but not LS ids, RPCs service_role only, delete_my_account has the plus_active guard, FK cascade, 0 rows.
