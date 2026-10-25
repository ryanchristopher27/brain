---
id: cd994b
source: scale:trip-planner:fold-functions
title: Fold Vercel function endpoints (12 → ~7)
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-17T22:14:53Z
updated: 2026-10-19T02:48:20Z
---

## Brief
From docs/research/scaling-plan.md (2026-10-17). Merge api/ai/health + api/flights/health, and flights airports/booking-links/search into one handler with ?op= rewrites (pattern: api/oauth.js). Keep sweep.js (maxDuration) and ai/plan.js (supportsCancellation) separate.

## Acceptance

## Runs

## Updates
- 2026-10-17T22:14:53Z · created
- 2026-10-19T02:15:15Z · status: backlog → doing
- 2026-10-19T02:48:20Z · status: doing → review (Merged 2026-10-18: functions 12 → 8 (live endpoints checked), metrics client inert until 0024 is applied.)
