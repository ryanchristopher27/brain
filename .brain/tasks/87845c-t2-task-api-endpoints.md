---
id: 87845c
title: T2 — Task API endpoints
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-07-26T19:20:18Z
updated: 2026-07-26T19:25:09Z
---

## Brief
Expose the tracker over FastAPI in dashboard/server.py: list projects, tasks CRUD, task detail, and /api/tasks/{id}/updates. Token-guarded like the other /api routes.

## Acceptance
- [ ] GET /api/tasks aggregates across projects
- [ ] POST creates a .brain/tasks file
- [ ] status changes go through set_status

## Runs

## Updates
- 2026-07-26T19:20:18Z · created
- 2026-07-26T19:20:18Z · status: backlog → ready (scaffolded)
- 2026-07-26T19:25:09Z · status: ready → doing (building)
- 2026-07-26T19:25:09Z · status: doing → review (endpoints built + verified)
- 2026-07-26T19:25:09Z · result: T2 done: /api/projects, /api/tasks (CRUD), detail, status, update — all acceptance met
