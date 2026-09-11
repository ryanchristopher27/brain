---
id: b8d39b
source: plan:trip-planner:M5
title: M5 — Timeline drag-and-drop
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-05T23:06:21Z
updated: 2026-09-06T06:11:29Z
---

## Brief
Drag activity cards between days/segments → emits patch ops

## Acceptance

## Runs

## Updates
- 2026-09-05T23:06:21Z · created
- 2026-09-06T06:09:03Z · status: backlog → doing (building)
- 2026-09-06T06:11:29Z · status: doing → review (built + verified)
- 2026-09-06T06:11:29Z · comment: Timeline.jsx: native HTML5 DnD (no deps). Cards draggable; day columns, per-segment Unscheduled, and Unassigned band are drop targets; drop emits a single move op via onApplyOps (same apply+undo path as chat). Read-only when onApplyOps absent; no-op drops skipped; ring highlight on active target. Verified in-app: dragged Colosseum Day2→Day1 (move applied, Undo enabled), Undo reverted to Day2.
