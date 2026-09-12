---
id: d1e739
source: plan:trip-planner:D3
title: D3 — Sync engine + first-login merge
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-11T14:06:17Z
updated: 2026-09-11T15:09:52Z
---

## Brief
pull-merge on login, debounced push, tombstones, record-level LWW; merge local↔cloud

## Acceptance

## Runs

## Updates
- 2026-09-11T14:06:17Z · created
- 2026-09-11T15:06:05Z · status: backlog → doing (building)
- 2026-09-11T15:09:52Z · status: doing → review (built; merge unit-tested + logged-out clean; live round-trip pending user check)
- 2026-09-11T15:09:52Z · comment: Sync engine. sync.js: pushChanges (upsert live trips + tombstone rows), mergeSets (pure record-level LWW, tombstone-aware; exported for tests), pullMerge (fetch+merge+converge-push), firstLoginMerge=pullMerge. storage.js: loadTombstones/saveTombstones. App: tombstones state + persist; deleteTrip records tombstones for record+cascaded plans; pull-merge on sign-in (userId change); debounced (1.5s) push on trips/tombstones change while signed in. supabase.js guarded for Node (import.meta.env). Verified: 9/9 mergeSets assertions (LWW both directions, local-only/remote-only, local-tombstone beats older remote, remote tombstone stays deleted); logged-out path clean (fresh tab, no console errors, no sync calls). LIVE cloud round-trip pending user (pane isn't signed in; user is, in their own browser).
