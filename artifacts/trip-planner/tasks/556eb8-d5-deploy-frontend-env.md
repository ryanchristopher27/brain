---
id: 556eb8
source: plan:trip-planner:D5
title: D5 — Deploy frontend + env
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-11T14:06:17Z
updated: 2026-09-11T15:37:34Z
---

## Brief
Vite build to Vercel; Supabase public env; hosted AI=BYOK; flights degrade to local-only

## Acceptance

## Runs

## Updates
- 2026-09-11T14:06:17Z · created
- 2026-09-11T15:19:48Z · status: backlog → doing (building)
- 2026-09-11T15:37:34Z · status: doing → review (deployed + verified live)
- 2026-09-11T15:37:34Z · comment: Deployed to Vercel: https://trip-planner-sooty-nine.vercel.app (Vite auto-detected; VITE_SUPABASE_* env set in Vercel; Supabase Auth redirect URLs updated to include the vercel domain + localhost). Prod build clean (96 modules, ~126KB gz). Verified live: app loads + full layout renders correctly at 1280x720 (earlier 'cramped' was just a 400x225 pane viewport — h-screen confirmed = viewport); Supabase configured (sign-in UI present); AI correctly gated on prod (no local agent + no key → 'Brainstorming needs an AI engine' hint; manual + sync still work); flights degrade to not-configured; only expected 404 is the /ai/health probe. Cross-device sign-in round-trip on the deployed URL pending user (needs their magic-link).
