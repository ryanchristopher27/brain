---
id: 531a85
source: web:trip-planner:anon-sessions
title: Anonymous sessions + signed-out taste
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-26T22:12:09Z
updated: 2026-09-26T23:32:29Z
---

## Brief
Supabase anonymous sign-ins so signed-out visitors get a small allowance (e.g. 3 fare searches / 2 AI turns) that upgrades with their trips on sign-in; needs IP rate limits or CAPTCHA.

## Acceptance

## Runs

## Updates
- 2026-09-26T22:12:09Z · created
- 2026-09-26T23:24:39Z · status: backlog → doing (Code shipped; needs migration 0006 + enabling anonymous sign-ins)
- 2026-09-26T23:24:39Z · status: doing → review (Code shipped; needs migration 0006 + enabling anonymous sign-ins)
- 2026-09-26T23:27:26Z · comment: 2026-09-26: migration 0006 applied to the live project via MCP (guest columns, ip_hash index, ensure_free_grant_v2 service-role only). Waiting on the user enabling anonymous sign-ins.
- 2026-09-26T23:32:29Z · status: review → done (Live: anonymous sign-ins on; signed-out search → guest session (Guest · Sign up), guest usage row with ip_hash; guest chat → 3 credits granted, 1 spent. Fixed new-user balance bug found here.)
