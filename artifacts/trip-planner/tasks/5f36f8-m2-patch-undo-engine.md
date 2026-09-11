---
id: 5f36f8
source: plan:trip-planner:M2
title: M2 — Patch + undo engine
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-05T23:06:21Z
updated: 2026-09-05T23:27:21Z
---

## Brief
Patch-op protocol, applyOps() reducer, bounded snapshot undo stack, tolerant parser

## Acceptance

## Runs

## Updates
- 2026-09-05T23:06:21Z · created
- 2026-09-05T23:26:01Z · status: backlog → doing (building)
- 2026-09-05T23:27:21Z · status: doing → review (built + verified)
- 2026-09-05T23:27:21Z · comment: patch.js: applyOps() pure reducer (add/update/remove/move/reorder over activity|segment|flight|field), FIELD_WHITELIST guard, remove-segment orphans activities, all-or-nothing throws; parsePatch() reuses parseJsonObject. history.js: bounded snapshot stack (createHistory/record/undo/redo/canUndo, default depth 20). 25/25 engine assertions pass. Not yet UI-wired — App integration lands in M4.
