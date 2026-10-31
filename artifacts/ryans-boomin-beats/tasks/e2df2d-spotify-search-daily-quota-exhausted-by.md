---
id: e2df2d
source: review:ryans-boomin-beats:spotify-search-daily-quota
title: Spotify search daily quota exhausted by DJ prefetch
type: bug
status: review
assignee: 
scoped_dir: .
created: 2026-10-25T19:09:28Z
updated: 2026-10-26T02:27:29Z
---

## Brief
High. /dj/suggest/ validation. 2026-10-25: search 429 QUOTA_EXCEEDED, resets around 21:20 local, same as 10-24, after a morning of Co-pilot prefetch (10-20 searches per track change). A 4h party of about 60 tracks could exhaust it. Options: validate lazily (only shown picks), fewer overasks, prefetch only on open or in Autofill/Driver, a cross-instance cache in Supabase, and measure the real quota.

## Acceptance

## Runs

## Updates
- 2026-10-25T19:09:28Z · created
- 2026-10-25T22:36:32Z · comment: Partial mitigation: per-process search lockout honours Retry-After, so a locked-out instance makes zero search calls (live: 2nd+ searches refused in 0 ms). Root cause (searches per suggestion, prefetch frequency) still open.
- 2026-10-26T00:33:13Z · comment: 2026-10-25 W4: web prefetch now gated to an open DJ page or Autofill/Driver (was every tab, every song). iOS still prefetches per track in Co-pilot.
- 2026-10-26T00:59:05Z · comment: 2026-10-25: root-cause fix shipped on dev: Supabase track_lookup shared cache (migration 20261026005535 applied), early-stop validation, 4-in-flight cap, iOS prefetch gated to Now Playing/autopilot, typeahead 3 chars/350ms. Live to Vercel on next main merge. Measure tomorrow.
- 2026-10-26T02:27:29Z · status: backlog → doing (fixing)
- 2026-10-26T02:27:29Z · status: doing → review (Q0–Q4: showing songs costs 0 Spotify searches, queueing 1)
