---
id: 042819
source: adhoc:trip-planner:signout-clears-data
title: Sign out leaves the account's trips and data on the device
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-10-07T03:11:32Z
updated: 2026-10-17T21:11:14Z
---

## Brief
After signing out, trips/chats/etc. from the signed-in account stay visible. Clear account data on sign-out (after flushing unsynced changes) and never merge one account's local data into another account on sign-in.

## Acceptance

## Runs

## Updates
- 2026-10-07T03:11:32Z · created
- 2026-10-07T03:11:32Z · status: backlog → doing (subagent started)
- 2026-10-08T03:54:35Z · comment: Added Sync now to the unsynced-changes dialog (user request)
- 2026-10-10T22:41:30Z · comment: Eric's test 2026-10-10: 'Sync now' during sign-out didn't work. Tracked as bug #497d1d.
- 2026-10-17T21:11:13Z · status: doing → review (Tested by user 2026-10-17)
- 2026-10-17T21:11:14Z · status: review → done (User review pass 2026-10-17: PASS)
