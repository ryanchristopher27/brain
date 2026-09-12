---
id: 8da4f4
source: plan:trip-planner:D4
title: D4 — AI capability-tier gating
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-11T14:06:17Z
updated: 2026-09-11T14:37:03Z
---

## Brief
aiAvailable (local agent or key) gates AI affordances + hint; manual always on; agent-registry shape

## Acceptance

## Runs

## Updates
- 2026-09-11T14:06:17Z · created
- 2026-09-11T14:10:22Z · status: backlog → doing (building)
- 2026-09-11T14:37:03Z · status: doing → review (built + verified)
- 2026-09-11T14:37:03Z · comment: AI capability-tier gating (AI-only gate). App computes aiAvailable = localAvailable || anthropicKey, threaded to Brainstorm and (via Workspace/ProposalView) PlanChat. When false: Brainstorm composer+starters replaced by a hint; PlanChat composer replaced by a hint ('run npm run ai or add a key; you can still edit by hand'). Manual create/edit never gated. Verified live: killed the AI helper (no key) → Brainstorm + Proposal chat both showed the hint (no composer), while + New proposal still created and opened the full manual editor. Restarted app; AI available again. Note: agent-registry multi-CLI shape deferred (helper-side, later).
