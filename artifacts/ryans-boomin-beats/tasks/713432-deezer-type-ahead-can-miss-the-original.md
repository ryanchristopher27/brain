---
id: 713432
source: review:ryans-boomin-beats:deezer-typeahead-misses-originals
title: "Deezer type-ahead can miss the original (Money Trees: covers/sped-up fill top 10)"
type: issue
status: done
assignee: 
scoped_dir: .
created: 2026-10-26T02:36:31Z
updated: 2026-10-26T22:58:32Z
---

## Brief
Medium · /search/ · filter re-upload/cover variants from results, and offer 'Search Spotify' (1 search) when the wanted song isn't listed

## Acceptance

## Runs

## Updates
- 2026-10-26T02:36:31Z · created
- 2026-10-26T02:53:43Z · status: backlog → doing (fixing)
- 2026-10-26T02:53:43Z · status: doing → review (fixed + live-checked; deploy pending)
- 2026-10-26T02:57:23Z · comment: Live in prod (26dad29): 'money trees' -> Kendrick Lamar first. Follow-ups: mid-word queries weak; '(Speed)' labels not filtered
- 2026-10-26T03:03:53Z · comment: Mid-word + (Speed) fixed: popularity-led ordering, relevance check, label-based re-upload filter; live checked
- 2026-10-26T03:06:36Z · comment: Live in prod (11a951d): mid-word 'septem' -> Earth, Wind & Fire first
- 2026-10-26T03:13:16Z · comment: Artist-named uploads dropped ('Artist - Song', titles naming the searched artist, Official Audio/Lyrics labels); live checked
- 2026-10-26T22:58:32Z · status: review → done (verified (housekeeping 2026-10-26))
