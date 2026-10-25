---
id: 387eee
source: review:trip-planner:slow-stop-on-map
title: Adding a stop takes a long time to appear on the map
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-17T21:11:15Z
updated: 2026-10-19T03:01:02Z
---

## Brief
From the user's review pass 2026-10-17. An assistant-added stop took a long time to show on the trip map. Profile: Nominatim throttle (1/s queue), AI-geocode fallback, re-render. Show the pin immediately when the AI gives coordinates, or a placeholder while geocoding.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:11:15Z · created
- 2026-10-17T21:45:00Z · status: backlog → doing
- 2026-10-17T22:47:49Z · status: doing → review (Merged 2026-10-17: 497 unit, 178 smoke, signout/market/oauth green.)
- 2026-10-19T03:01:02Z · status: review → done (Review pass 2: PASS (user, 2026-10-18))
