---
id: 88b6ec
source: plan:trip-planner:LIB1
title: LIB1 — Bookmarks store for saved places
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-17T21:56:50Z
updated: 2026-10-19T03:01:02Z
---

## Brief
Trip library (#812ee5, decided 2026-10-17). Synced per-account list of saved places (name, kind, city/country, coords, blurb, source trip) like trips/chats; own-only. May need a Supabase table (migration only with the user's OK) or ride inside an existing synced store.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:56:50Z · created
- 2026-10-17T22:09:05Z · status: backlog → doing
- 2026-10-17T23:30:20Z · status: doing → review (Merged 2026-10-17: 518 unit, 200 smoke, signout 29, market 31, oauth 9. Migration 0022 NOT applied (saved places stay on the device until it is).)
- 2026-10-17T23:37:34Z · comment: 0022_saved_places applied to production 2026-10-17 with the user's OK. Verified: RLS on, 4 owner-only policies, LWW guard + limits triggers, anon has no access, FK on delete cascade, run_cleanup now 14 steps and a dry run reports no errors.
- 2026-10-19T03:01:02Z · status: review → done (Review pass 2: PASS (user, 2026-10-18))
