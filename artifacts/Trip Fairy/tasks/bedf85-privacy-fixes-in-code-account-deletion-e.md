---
id: bedf85
source: adhoc:trip-planner:privacy-code-fixes
title: Privacy fixes in code (account deletion/export, headers, friend defaults, AI routing, retention)
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-10T18:21:09Z
updated: 2026-10-17T21:11:14Z
---

## Brief
From docs/research/privacy-legal-audit.md: self-serve account deletion + data export, security headers (CSP/frame-ancestors), friends see less by default, pin gpt-oss routing, shorter guest IP-hash retention, coarser marketplace coordinates, commit trips schema/RLS migration

## Acceptance

## Runs

## Updates
- 2026-10-10T18:21:09Z · created
- 2026-10-10T18:21:09Z · status: backlog → doing (subagent started)
- 2026-10-10T18:36:39Z · comment: All 9 fixes in fb3e135 on feat/privacy-fixes: delete account + export (Settings > Account > Your data), migration 0021_privacy.sql (trips schema, delete_my_account RPC, purchases set-null, friend_safe_trip stricter, run_cleanup ip_hash 7d) NOT applied, security headers, gateway provider pin (ZDR opt-in, needs Pro), salted OAuth IP hash, 2-dp marketplace coords, fail-closed /ai/plan. Tests 406, PGlite 19/19, smoke 105/19/25/9, build OK.
- 2026-10-10T18:36:39Z · status: doing → review (Ready for review; user must apply 0021 and decide on GATEWAY_ZDR (Pro).)
- 2026-10-10T19:00:26Z · comment: 0021 applied 2026-10-10 (incl. recent-sign-in check in delete_my_account); trips still 4 policies; credit_purchases FK set null; cleanup preview no errors. Fares fail closed in prod.
- 2026-10-17T21:11:14Z · status: review → done (User review pass 2026-10-17: PASS)
