---
id: 8235db
source: web:trip-planner:domain-dns-vercel
title: Point domain at Vercel + DNS
type: task
status: backlog
assignee: 
scoped_dir: .
created: 2026-09-19T23:47:42Z
updated: 2026-09-24T04:12:02Z
---

## Brief
After purchase: add custom domain to the Vercel project, configure DNS/records, verify HTTPS.

## Acceptance

## Runs

## Updates
- 2026-09-19T23:47:42Z · created
- 2026-09-24T04:12:02Z · comment: Also after the domain is live: add it to the helper's allowed sites (packages/helper/lib/core.mjs DEFAULT_ORIGINS) and publish trip-fairy-helper 0.1.1; the repo helper reads HELPER_ALLOWED_ORIGINS.
