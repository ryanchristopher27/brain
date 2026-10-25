---
id: 0c307f
source: plan:trip-planner:BI1
title: BI1 — Season explorer
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-28T00:44:06Z
updated: 2026-09-29T02:47:28Z
---

## Brief
Climate normals (Open-Meteo, shared cache) → 12-month when-to-go per stop + route verdict; replaces LLM weather

## Acceptance

## Runs

## Updates
- 2026-09-28T00:44:06Z · created
- 2026-09-28T00:54:02Z · status: backlog → doing
- 2026-09-28T01:03:30Z · comment: Shipped: /climate (Open-Meteo archive, 0.1° cells, memory→Supabase climate_normals→upstream), WhenToGo grid + route verdict, assistant context, LLM fallback. 0008 applied; verified prod write. Pending: OPEN_METEO_API_KEY (commercial) before promotion.
- 2026-09-28T01:03:30Z · status: doing → review
- 2026-09-29T02:47:28Z · status: review → done (approved by Ryan in chat 2026-09-28: ideation is a good start — follow-ups go in new tasks)
