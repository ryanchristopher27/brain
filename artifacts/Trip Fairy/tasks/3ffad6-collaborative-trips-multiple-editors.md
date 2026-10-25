---
id: 3ffad6
source: adhoc:trip-planner:collaborative-trips
title: Collaborative trips (multiple editors)
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-28T01:47:44Z
updated: 2026-10-17T21:11:14Z
---

## Brief
Add multiple users to a trip; any collaborator can edit. Needs trip membership + RLS in Supabase, and conflict handling on concurrent edits (builds on D7 realtime sync). Invite by username/email.

## Acceptance

## Runs

## Updates
- 2026-09-28T01:47:44Z · created
- 2026-10-06T02:55:59Z · comment: Built on feat/collab-trips (0a0140d): migration 0015_trip_members.sql (NOT applied), RPC-based shared edits with optimistic concurrency + three-way merge, Share UI, Shared with me, invites on Friends. 302 tests, build, smoke 82 pass; mocked-Supabase screenshots in /tmp/tf-collab-shots.
- 2026-10-06T02:56:10Z · status: backlog → doing (Implementation done)
- 2026-10-06T02:56:10Z · status: doing → review (Ready for review; apply 0015 before manual testing.)
- 2026-10-07T02:18:55Z · comment: 0015 applied 2026-10-06; sanity: no shared rows/saves without auth (forbidden), 3 triggers present, advisors show only the intended RPCs. Follow-up: route owner edits on shared trips through the checked save (stale-copy/clock-skew gap). Awaiting user test with re-seeded Ava/Ben/Cleo.
- 2026-10-17T21:11:14Z · status: review → done (User review pass 2026-10-17: PASS)
