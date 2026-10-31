---
id: 207807
source: review:ryans-boomin-beats:refresh-failure-signs-out
title: Transient token-refresh failure signs the user out
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-10-24T20:56:21Z
updated: 2026-10-26T22:58:43Z
---

## Brief
Fixed 2026-10-24 · SpotifySession.refresh · only 400/401 logs out now

## Acceptance

## Runs

## Updates
- 2026-10-24T20:56:21Z · created
- 2026-10-26T22:58:43Z · status: backlog → doing (already built (housekeeping))
- 2026-10-26T22:58:43Z · status: doing → review (verified against code)
- 2026-10-26T22:58:43Z · status: review → done (fixed: iOS TokenError.rejected/unavailable (DJ6); web single-flight refresh, sign out only on invalid_grant)
