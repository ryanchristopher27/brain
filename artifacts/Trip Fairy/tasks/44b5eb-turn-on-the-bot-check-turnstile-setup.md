---
id: 44b5eb
source: adhoc:trip-planner:turnstile-setup
title: Turn on the bot check (Turnstile setup)
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-29T02:52:45Z
updated: 2026-10-05T02:57:04Z
---

## Brief
Code is live but dormant (#834ccc). Steps, in order: 1) Cloudflare → Turnstile widget (mytripfairy.com, www, localhost; Managed); 2) Vercel env VITE_TURNSTILE_SITE_KEY + redeploy; 3) only then Supabase → Auth → Attack Protection → CAPTCHA (Turnstile + secret key). Swap the local .env test key for the real site key.

## Acceptance

## Runs

## Updates
- 2026-09-29T02:52:45Z · created
- 2026-10-05T02:57:04Z · status: backlog → doing (Setup done by user; verified live)
- 2026-10-05T02:57:04Z · status: doing → review (Setup done by user; verified live)
- 2026-10-05T02:57:04Z · status: review → done (Turnstile live: real site key deployed, Supabase CAPTCHA on, user verified sign-in + guest session 2026-10-04)
