---
id: 3db26f
source: user:trip-planner:chat-inflight
title: Closing the chat mid-reply loses the loading state
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-10-19T02:48:20Z
updated: 2026-10-19T03:35:18Z
---

## Brief
User report 2026-10-18: on a phone, sending a prompt then closing and reopening the chat drawer showed no loader although the reply was still coming. Fix: turns in flight live in lib/inflight.js per conversation key; the reopened drawer shows the loader + Stop, a second send is blocked, errors that happened while closed show on reopen.

## Acceptance

## Runs

## Updates
- 2026-10-19T02:48:20Z · created
- 2026-10-19T02:48:20Z · status: backlog → doing
- 2026-10-19T03:30:13Z · status: doing → review (Merged + deployed. Closing the phone chat drawer mid-reply and reopening keeps the loader and Stop.)
- 2026-10-19T03:35:18Z · status: review → done (User tested: pass (2026-10-18))
