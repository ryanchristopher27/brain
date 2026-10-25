---
id: 7498c8
source: plan:trip-planner:P2
title: P2 — Supply-side cost stack
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-20T03:38:32Z
updated: 2026-09-24T04:11:46Z
---

## Brief
Gateway (Vercel AI Gateway/OpenRouter) + cheap/smart model split + shared cross-user cache + hard spend cap.

## Acceptance

## Runs

## Updates
- 2026-09-20T03:38:32Z · created
- 2026-09-20T05:25:26Z · status: backlog → doing (Building cheap/smart model split (server-controlled by kind) + shared cross-user cache for background facts; gateway-ready base URL; spend cap = workspace limit.)
- 2026-09-20T05:28:44Z · status: doing → review (Built+verified: server model split (haiku bg / sonnet reasoning, client model ignored), shared cross-user cache (0002_ai_cache.sql, cache-first for background, hits skip model), gateway-ready ANTHROPIC_BASE_URL. Deployed. Waiting on you: apply supabase/migrations/0002_ai_cache.sql to enable the cache + cached column.)
- 2026-09-24T04:11:46Z · status: review → done (Cleanup: shipped — monetization P1–P4 live (metered /ai/plan, model split + cache, Lemon Squeezy webhook, free tier + rate limits).)
