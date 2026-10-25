---
id: 346b10
source: web:trip-planner:trip-audit
title: "Trip audit: keep every part of the trip in sync"
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-26T00:16:45Z
updated: 2026-09-26T02:05:10Z
---

## Brief
Parts of a trip go stale when others change: weather, map coordinates, travel legs between stops, budget, city briefings and places, day ranges, flights vs dates. Add an audit that checks everything against the latest trip and flags or refreshes what's out of date. Start cheap and deterministic (change keys like the places prefsKey on each derived cache; flag mismatches), then add an AI pass for semantic checks. Decide the cadence from cost: always for the cheap checks, every few assistant edits or on demand for the AI pass. Show a small 'Trip is up to date / 3 things to refresh' indicator.

## Acceptance

## Runs

## Updates
- 2026-09-26T00:16:45Z · created
- 2026-09-26T00:57:35Z · status: backlog → doing (Started: inventory of derived data + deterministic audit layer.)
- 2026-09-26T01:04:46Z · status: doing → review (Layer 1 shipped locally: fingerprints + autoRepairs + auditTrip + trip-bar indicator. Verified: rename Kyoto→Nara self-heals pin/photo/legs in ~10s; Nara briefing refresh via indicator; dates fix + undo/redo. Layer 2 (AI pass) filed separately.)
- 2026-09-26T02:05:10Z · status: review → done (Shipped 2026-09-25 (pushed + verified live).)
