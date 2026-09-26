---
id: f7b577
source: plan:trip-planner:P3
title: P3 — Credit packs + MoR checkout
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-20T03:38:32Z
updated: 2026-09-24T04:11:46Z
---

## Brief
Pack SKUs, Merchant-of-Record (Paddle/Lemon Squeezy) checkout, purchase webhook -> balance top-up.

## Acceptance

## Runs

## Updates
- 2026-09-20T03:38:32Z · created
- 2026-09-21T00:05:53Z · status: backlog → doing (Implementing P3.)
- 2026-09-21T00:05:53Z · status: doing → review (Built+verified: 0003_purchases.sql (idempotent grant_purchase), api/webhooks/lemonsqueezy.js (raw-body HMAC, server-authoritative LS_PACKS), buy UI. Webhook tested. Waiting on you: apply 0003, create LS store/variants/webhook, set LS env vars.)
- 2026-09-24T04:11:46Z · status: review → done (Cleanup: shipped — monetization P1–P4 live (metered /ai/plan, model split + cache, Lemon Squeezy webhook, free tier + rate limits).)
