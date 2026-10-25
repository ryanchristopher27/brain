---
id: aa49dc
source: growth:trip-planner:share-no-signup
title: Shared trips viewable without signing up, with an invite link
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-17T21:53:23Z
updated: 2026-10-19T03:01:03Z
---

## Brief
From docs/research/marketing.md (2026-10-17). Recipients of a shared trip see the whole trip (read-only) without an account and sign up only to edit; one-tap 'Invite to plan this trip' link with a rich preview (OG image/title). The Polarsteps/Wanderlog growth loop.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:53:23Z · created
- 2026-10-18T22:29:33Z · status: backlog → doing
- 2026-10-18T23:07:54Z · status: doing → review (Merged 2026-10-18: 525 unit, 200 smoke, market 47, signout 29, oauth 9. 0023 not applied yet (link section hidden until it is).)
- 2026-10-19T01:19:52Z · comment: 2026-10-18: 0023 applied to production with the user's OK (verified: RLS, 2 owner policies, anon has no table access and can't read snapshot column via authenticated grant, anon can only call view_trip, cascade on user delete, unknown token returns no row). Decisions (user took the recommendations): snapshot-in-link (refreshed when Share opens); hidden trips can't have/pause links; no AI geoUncertain flag for now; site-wide 1200x630 og-image.png added, per-trip previews after Vercel Pro.
- 2026-10-19T03:01:03Z · status: review → done (Review pass 2: PASS (user, 2026-10-18))
