---
id: 50103d
source: user:trip-planner:helper-login-expired-message
title: "Helper: clear message when Claude Code's login expired"
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-04T20:25:07Z
updated: 2026-10-05T02:18:35Z
---

## Brief
When the 'Your Claude Code' engine's claude -p fails with 'Failed to authenticate: OAuth session expired…' (or 'not logged in'), the helper should return a typed error the app shows as: 'Your Claude Code needs you to sign in again — run claude, then /login', with a link to switch to Trip Fairy's AI meanwhile. Seen 2026-10-04.

## Acceptance

## Runs

## Updates
- 2026-10-04T20:25:07Z · created
- 2026-10-04T20:47:47Z · status: backlog → doing
- 2026-10-04T20:47:47Z · status: doing → review (Helper returns claude_login; app shows sign-in steps + 'Use Trip Fairy's AI instead'; helper 0.1.2 ready to publish)
- 2026-10-05T02:18:35Z · status: review → done (Closed by user)
