---
id: fef1c5
source: adhoc:trip-planner:signout-rejected-shared
title: "Sign-out: a shared trip the server rejected blocks Sync now"
type: bug
status: review
assignee: 
scoped_dir: .
created: 2026-10-11T17:58:22Z
updated: 2026-10-19T03:01:03Z
---

## Brief
If a shared trip's save is rejected by the server (over the saved-trip limit, too large), the sign-out dialog's Sync now fails every time (flushAll stops on 'rejected' rows; src/lib/collab.js flushAll, src/lib/accountData.js flushPending), so the only way out is 'Sign out and lose them' — which drops all unsynced edits, not just the rejected trip. Fix ideas: name the rejected trip and why in the dialog; let Sync now save everything else and offer to keep a local copy (export/stash for this account) of just the rejected trip; or a 'Sign out, keep a copy' option. Found while fixing #497d1d.

## Acceptance

## Runs

## Updates
- 2026-10-11T17:58:22Z · created
- 2026-10-17T20:40:42Z · status: backlog → doing
- 2026-10-17T20:40:42Z · status: doing → review (Merged 2026-10-17: 478 unit, 140 smoke, signout/market/oauth green.)
- 2026-10-19T03:01:03Z · comment: Review pass 2: not tested yet (left open).
