---
id: 8235db
source: web:trip-planner:domain-dns-vercel
title: Point domain at Vercel + DNS
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-19T23:47:42Z
updated: 2026-09-27T01:03:16Z
---

## Brief
After purchase: add custom domain to the Vercel project, configure DNS/records, verify HTTPS.

## Acceptance

## Runs

## Updates
- 2026-09-19T23:47:42Z · created
- 2026-09-24T04:12:02Z · comment: Also after the domain is live: add it to the helper's allowed sites (packages/helper/lib/core.mjs DEFAULT_ORIGINS) and publish trip-fairy-helper 0.1.1; the repo helper reads HELPER_ALLOWED_ORIGINS.
- 2026-09-27T01:03:16Z · status: backlog → doing (mytripfairy.com bought and pointed at Vercel by the user)
- 2026-09-27T01:03:16Z · status: doing → review (Live: 200, www→apex 307, /ai /flights /advisories answer)
- 2026-09-27T01:03:16Z · status: review → done (Verified 2026-09-26)
