---
id: 834ccc
source: adhoc:trip-planner:turnstile
title: Bot check (Turnstile) for guest sessions + email sign-in
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-27T23:46:31Z
updated: 2026-09-29T02:52:45Z
---

## Brief
Supabase Auth CAPTCHA via Turnstile; code ships dormant until VITE_TURNSTILE_SITE_KEY is set, then enable in Supabase

## Acceptance

## Runs

## Updates
- 2026-09-27T23:46:31Z · created
- 2026-09-28T03:12:21Z · comment: Code shipped 2026-09-27 (commit 42ef07d): src/lib/captcha.js adds a Turnstile token to guest sign-in, email sign-up/log-in, magic link, reset. Dormant until set up. Remaining (user): 1) Cloudflare → Turnstile widget (mytripfairy.com, www, localhost; Managed); 2) Vercel env VITE_TURNSTILE_SITE_KEY + redeploy; 3) THEN Supabase → Auth → Attack Protection → CAPTCHA (Turnstile, secret key). Replace the local .env test key when enabling.
- 2026-09-28T03:12:21Z · status: backlog → doing
- 2026-09-28T03:12:21Z · status: doing → review
- 2026-09-29T02:52:45Z · status: review → done (closed at Ryan's request in chat 2026-09-28)
