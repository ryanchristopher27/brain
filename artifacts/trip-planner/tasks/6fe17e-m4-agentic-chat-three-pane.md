---
id: 6fe17e
source: plan:trip-planner:M4
title: M4 — Agentic chat + three-pane
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-05T23:06:21Z
updated: 2026-09-05T23:50:39Z
---

## Brief
Per-trip persistent chat, editPlan() prompt path, three-pane layout (tabs on narrow)

## Acceptance

## Runs

## Updates
- 2026-09-05T23:06:21Z · created
- 2026-09-05T23:42:31Z · status: backlog → doing (building)
- 2026-09-05T23:50:39Z · status: doing → review (built + verified)
- 2026-09-05T23:50:39Z · comment: editPlan() in aiClient (id-annotated plan context + scout patch prompt); per-trip chat storage (loadChat/saveChat); PlanChat.jsx (persistent thread, auto-apply, applied-count badge, error rollback); Workspace.jsx three-pane (plan|timeline|chat, tabs <xl, undo/redo bar); App owns undo history (createHistory/record/replace/undo/redo). Removed AiPanel. Verified in-app: real claude round-trip added 'Gelato stop Florence D4 $8' via 1 op, badge shown, timeline updated, Undo reverted cleanly + Redo enabled.
