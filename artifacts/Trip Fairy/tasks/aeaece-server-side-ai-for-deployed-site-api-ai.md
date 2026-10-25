---
id: aeaece
source: web:trip-planner:prod-ai-serverless
title: Server-side AI for deployed site (api/ai/plan.js)
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-19T23:47:42Z
updated: 2026-09-24T04:11:47Z
---

## Brief
Deployed site has no local helper; /ai 404s so auto->byok and AI/model silently need a key. Add api/ai/plan.js serverless calling Anthropic with ANTHROPIC_API_KEY (mirror flights proxy) so model picker works in prod for all visitors.

## Acceptance

## Runs

## Updates
- 2026-09-19T23:47:42Z · created
- 2026-09-20T00:30:57Z · status: backlog → doing (Implementing server-side AI serverless.)
- 2026-09-20T00:30:57Z · status: doing → review (Built: server/anthropic.mjs + api/ai/plan.js + api/ai/health.js + vercel.json /ai rewrite. Guards + build verified. Waiting on you: set ANTHROPIC_API_KEY in Vercel env, then deploy to verify live.)
- 2026-09-24T04:11:47Z · status: review → done (Cleanup: shipped — api/ai/plan.js live (metered).)
