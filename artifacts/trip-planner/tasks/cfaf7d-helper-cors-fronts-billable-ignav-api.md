---
id: cfaf7d
source: review:trip-planner:helper-cors-wildcard
title: Helper CORS '*' fronts billable Ignav API
type: bug
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T23:30:35Z
updated: 2026-09-06T23:38:01Z
---

## Brief
Warning · server/index.mjs sendJson · Allow-Origin:* lets any visited site hit localhost:8787 (spend Ignav quota/invoke AI) while helper runs; app uses Vite proxy so header is unneeded — reflect localhost origins or drop

## Acceptance

## Runs

## Updates
- 2026-09-06T23:30:35Z · created
- 2026-09-06T23:38:01Z · status: backlog → doing (iterate)
- 2026-09-06T23:38:01Z · status: doing → review (fixed + verified)
