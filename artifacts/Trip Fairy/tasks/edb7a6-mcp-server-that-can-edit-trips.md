---
id: edb7a6
source: user:trip-planner:mcp-trip-editor
title: MCP server that can edit trips
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-02T04:25:15Z
updated: 2026-10-09T02:00:11Z
---

## Brief
An MCP server so an AI client (Claude Desktop/Code, etc.) can read and edit Trip Fairy trips: list/read trips and versions, apply the same patch ops the in-app assistant uses (stops, activities, legs, dates, anchors, bases), create versions. Decide auth (per-user token scoped to their trips), where it runs (local helper vs hosted), and guardrails (undo, rate limits).

## Acceptance

## Runs

## Updates
- 2026-10-02T04:25:15Z · created
- 2026-10-05T02:29:17Z · comment: Built on feat/trip-mcp (246dde5): hosted api/mcp.js (hand-rolled JSON-RPC, no SDK), PATs in Settings, 7 tools incl. undo. Needs migration 0012 applied. 261 tests, build ok, smoke 80/80. No OAuth yet.
- 2026-10-05T02:29:25Z · status: backlog → doing (Built)
- 2026-10-05T02:29:25Z · status: doing → review (Ready for review; apply 0012_mcp_tokens.sql before use.)
- 2026-10-05T02:37:39Z · comment: Migrations 0012+0013 applied; endpoint live (401 without token). End-to-end test with a real Claude client tabled by user 2026-10-04 — still to do: create token, claude mcp add, list + edit a trip, verify setup snippets.
- 2026-10-09T02:00:11Z · status: review → done (Verified end to end through the claude.ai connector (2026-10-08))
