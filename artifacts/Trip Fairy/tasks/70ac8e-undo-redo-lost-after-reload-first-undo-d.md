---
id: 70ac8e
source: review3:undo-sync
title: Undo/redo lost after reload; first undo dropped background updates (fixed)
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-10-26T01:43:35Z
updated: 2026-10-26T03:16:08Z
---

## Brief
Live review 2026-10-26: (1) the undo history's present was the snapshot from when the trip opened, so the first undo dropped background updates (deleted estimated home flights after Add to trip → Undo); (2) undo/redo restored an old updatedAt, so sync (last-write-wins) kept the server copy and the undo came back after a reload. Fixed in 0376083 + e92a961; verified live (undo survives reload, server copy matches).

## Acceptance

## Runs

## Updates
- 2026-10-26T01:43:35Z · created
- 2026-10-26T03:16:08Z · status: backlog → doing
- 2026-10-26T03:16:08Z · status: doing → review
- 2026-10-26T03:16:08Z · status: review → done (Closed with the user's OK (2026-10-26).)
