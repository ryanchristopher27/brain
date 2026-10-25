---
id: 78d712
source: adhoc:trip-planner:friends
title: "Friends: view each other's trips"
type: feature
status: review
assignee: 
scoped_dir: .
created: 2026-09-28T01:47:43Z
updated: 2026-10-17T21:11:14Z
---

## Brief
Let users friend each other (request/accept) and view friends' trips (read-only). Needs a friendships table + RLS so only accepted friends can read. Depends on profile info (username/avatar).

## Acceptance

## Runs

## Updates
- 2026-09-28T01:47:43Z · created
- 2026-10-05T03:12:19Z · comment: Built on feat/friends: migration 0014_friends.sql (friendships + RLS + friend_trips RPC; NOT applied), lib/friends.js, FriendsPage, FriendTripView, hide-from-friends toggle, sync scoped to own rows. 278 tests, build, smoke 82/82 pass; mocked-Supabase screenshots in /tmp/tf-friends-shots.
- 2026-10-05T03:12:29Z · status: backlog → doing (Built)
- 2026-10-05T03:12:29Z · status: doing → review (Friends implemented on feat/friends; needs migration 0014 applied and a real two-account check.)
- 2026-10-05T03:19:03Z · comment: 0014 applied 2026-10-04; sanity checks pass (no rows without auth, booking fields stripped). Awaiting a real two-account test by the user.
- 2026-10-17T21:11:14Z · comment: User review pass 2026-10-17: FAIL — see follow-up.
