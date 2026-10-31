---
id: 477d21
source: review:ryans-boomin-beats:player-poll-429
title: Spotify /me/player 429s from player polling (1,157 in 38 min)
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-10-26T02:36:31Z
updated: 2026-10-26T22:58:31Z
---

## Brief
High · /player/state/ poll · 2026-10-25 20:35–21:13 CDT on prod, every ~2s, while the sim (prod) and web tabs (local) polled the same Spotify app. Likely the 30s rolling limit across pollers. Options: honour Retry-After with backoff, poll slower away from track end, only the driving device/tab polls fast, participants slower

## Acceptance

## Runs

## Updates
- 2026-10-26T02:36:31Z · created
- 2026-10-26T02:42:09Z · status: backlog → doing (fixing)
- 2026-10-26T02:42:09Z · status: doing → review (fixed + tested; deploy pending)
- 2026-10-26T02:50:45Z · comment: Live in prod (a9c360a): polls ~5.5-6s, no errors; ba361a1 stops request URLs (user ids, search terms) being logged
- 2026-10-26T22:58:31Z · status: review → done (verified (housekeeping 2026-10-26))
