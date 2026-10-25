---
id: 9a319d
source: web:trip-planner:prod-auth-config
title: Prod auth config (Supabase + Google) for real domain
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-19T23:47:42Z
updated: 2026-09-27T19:15:41Z
---

## Brief
Add the production/custom-domain URL to Supabase Auth Redirect URLs and Google OAuth Authorized JS origins + redirect, so login/reset/magic-link work on the live domain. Dashboard config is user-run.

## Acceptance

## Runs

## Updates
- 2026-09-19T23:47:42Z · created
- 2026-09-27T01:03:16Z · comment: Domain is mytripfairy.com. Needs (user, dashboards): Supabase Site URL + Redirect URLs https://mytripfairy.com/**; Google OAuth JS origin https://mytripfairy.com; Lemon Squeezy return URL if it points at vercel.app. Helper 0.1.1 ready — user publishes with npm publish --otp.
- 2026-09-27T19:15:41Z · status: backlog → doing (User fixed Supabase URL config + Google origin; Google sign-in returns to mytripfairy.com)
- 2026-09-27T19:15:41Z · status: doing → review (User fixed Supabase URL config + Google origin; Google sign-in returns to mytripfairy.com)
- 2026-09-27T19:15:41Z · status: review → done (User fixed Supabase URL config + Google origin; Google sign-in returns to mytripfairy.com)
