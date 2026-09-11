---
id: 91a6fe
source: plan:trip-planner:F1
title: F1 — Shared server capability (Ignav)
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T22:45:22Z
updated: 2026-09-06T23:20:56Z
---

## Brief
/flights/health,search,airports in helper; Ignav API-key client from .env; identical-search cache; verify Ignav API

## Acceptance

## Runs

## Updates
- 2026-09-06T22:45:22Z · created
- 2026-09-06T23:15:05Z · status: backlog → doing (building)
- 2026-09-06T23:20:56Z · status: doing → review (built + verified live)
- 2026-09-06T23:20:56Z · comment: server/index.mjs: built-in .env loader (env vars win over server/.env), Ignav config (IGNAV_API_KEY/BASE_URL), ignav() client w/ X-Api-Key, short-term identical-search + airport caches. Endpoints: GET /flights/health {configured}, POST /flights/search (routes one-way vs /fares/round-trip by return_date, validates origin/dest/departure_date), GET /flights/airports?q=&limit=. vite proxies /flights. Verified LIVE against real Ignav: airports q=paris→CDG/ORY/BVA; one-way JFK→LHR→22 itineraries ( verified, ignav_id, segment detail); round-trip→131 w/ outbound+inbound (); validation + not-configured 503 paths clean. Ignav contract confirmed via openapi.json.
