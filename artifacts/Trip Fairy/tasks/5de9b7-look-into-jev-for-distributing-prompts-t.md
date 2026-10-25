---
id: 5de9b7
source: idea:trip-planner:jev-routing
title: Look into Jev for routing prompts to the right model
type: task
status: backlog
assignee: 
scoped_dir: .
created: 2026-10-10T21:46:02Z
updated: 2026-10-10T21:47:35Z
---

## Brief
Jev is TypeSafe AI's classify/route/score model, available on Vercel AI Gateway (which Trip Fairy already uses; TypeSafe AI is on Vercel's no-prompt-training list). Idea: a cheap Jev call picks the model tier per request (e.g. gpt-oss-120b vs Sonnet) instead of the user's model picker / fixed background model. Evaluate: cost per routing call vs savings (per-turn costs in docs/research/free-tier.md §9), latency, quality on the eval set, and fit with server/llm.mjs gateway options (provider pin + disallowPromptTraining). Refs: vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway ; vercel.com/kb/guide/typesafe-jev-and-ai-sdk

## Acceptance

## Runs

## Updates
- 2026-10-10T21:46:02Z · created
