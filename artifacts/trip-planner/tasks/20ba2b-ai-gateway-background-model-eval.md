---
id: 20ba2b
source: reflect:trip-planner:ai-gateway-eval
title: AI gateway + background-model eval
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-27T00:57:57Z
updated: 2026-09-27T20:48:12Z
---

## Brief
Route managed AI through Vercel AI Gateway (ANTHROPIC_BASE_URL first), add provider-neutral server/llm.mjs + a 'chat' call kind, run the 10-prompt-per-kind eval, then consider moving background calls to a cheaper model; add prompt caching to reasoning calls. See docs/research/ai-providers.md.

## Acceptance

## Runs

## Updates
- 2026-09-27T00:57:57Z · created
- 2026-09-27T19:15:41Z · status: backlog → doing (Starting gateway + eval)
- 2026-09-27T19:22:24Z · comment: 2026-09-27: shipped server/llm.mjs (gateway-ready, per-kind models + fallbacks, chat kind, prompt caching) and eval/ harness (fixtures from real prompt builders, run + score, scorer validated on synthetic outputs). Live AI verified on mytripfairy.com (gateway off). Next: user creates AI_GATEWAY_API_KEY (Vercel env + eval/.env), approves ~$1 eval spend; then run background/reasoning/chat evals and decide models.
- 2026-09-27T20:15:12Z · comment: 2026-09-27: eval run (gpt-oss-120b/20b via gateway free tier; Haiku 4.5 + Sonnet 5 direct). Results: docs/research/model-eval-2026-09-27.md. Recommend background → openai/gpt-oss-120b with claude-haiku-4-5 fallback; keep Sonnet 5 for edits/chat. Fixed live bug (stays/food dropped on ~30% of Haiku briefings), hybrid routing, gateway slug + base URL bugs. Pending: user sets Vercel env AI_GATEWAY_API_KEY + MODEL_BACKGROUND + MODEL_BACKGROUND_FALLBACKS.
- 2026-09-27T20:48:12Z · comment: 2026-09-27: live on mytripfairy.com — gateway on; background calls served by openai/gpt-oss-120b (usage_events), chat/edits on claude-sonnet-5 direct (1 credit). Fixed along the way: background size cap (city briefings with Wikivoyage text were failing with 400 since getting-around shipped).
- 2026-09-27T20:48:12Z · status: doing → review (Gateway + eval done; background on gpt-oss-120b in production)
- 2026-09-27T20:48:12Z · status: review → done (Gateway + eval done; background on gpt-oss-120b in production)
