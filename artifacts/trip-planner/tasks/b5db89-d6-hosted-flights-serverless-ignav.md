---
id: b5db89
source: plan:trip-planner:D6
title: D6 — Hosted flights (serverless Ignav)
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-11T14:06:17Z
updated: 2026-09-12T02:11:18Z
---

## Brief
Later: deploy /flights/* proxy as serverless fn (key in host env) for cross-device flights

## Acceptance

## Runs

## Updates
- 2026-09-11T14:06:17Z · created
- 2026-09-11T15:39:29Z · status: backlog → doing (building)
- 2026-09-11T16:01:52Z · status: doing → review (built + dev-verified; prod pending IGNAV_API_KEY in Vercel)
- 2026-09-11T16:01:52Z · comment: Serverless Ignav proxy. server/ignav.mjs shared core (ignavCall/flightSearch/airportSearch/bookingLinks/friendlyError, key from process.env) used by BOTH the dev helper and api/flights/{health,search,airports,booking-links}.js Vercel functions. vercel.json rewrites /flights/* → /api/flights/* so client path is unchanged (dev uses vite proxy → localhost helper; prod uses functions). server/index.mjs refactored onto the shared core. Verified DEV via shared module: health configured, airports CDG/ORY, search 18 itineraries. Pushed (8ef3486) → Vercel auto-deploys functions. PROD pending: user adds IGNAV_API_KEY (no VITE_ prefix) to Vercel env + redeploy, then verify deployed /flights/health + search. /ai/* intentionally NOT hosted (local agent only; prod AI = BYOK).
- 2026-09-12T02:11:18Z · comment: PROD verified on https://trip-planner-sooty-nine.vercel.app after fixing Vercel git-author email (empty commit 91094a4) + IGNAV_API_KEY set in Vercel env: /flights/health→{configured:true}, /flights/airports→CDG/ORY, /flights/search JFK→LHR→18 itineraries. All via the vercel.json rewrite → api/flights/* serverless functions. booking-links function deployed + reaching Ignav (returns Ignav 424 for volatile offers — provider fare-expiry behavior, not a deploy defect; client surfaces the S9 friendly message, never the raw error). Flights now work on the deployed app + phone. Minor cosmetic (non-user-facing): ignavCall stringifies a nested Ignav error object as '[object Object]' in the raw error text — candidate polish.
