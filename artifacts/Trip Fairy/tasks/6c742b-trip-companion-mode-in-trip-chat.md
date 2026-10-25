---
id: 6c742b
source: adhoc:trip-planner:trip-companion
title: Trip companion mode (in-trip chat)
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-28T01:47:44Z
updated: 2026-10-09T02:48:43Z
---

## Brief
A specialized harness / LLM context layer for use DURING a trip: a chat for questions on the ground (what's nearby, opening hours, how to get somewhere, translations), not for planning edits. Its own prompt, context (today's stop, schedule, picks, location) and no plan-editing ops.

## Acceptance

## Runs

## Updates
- 2026-09-28T01:47:44Z · created
- 2026-10-07T03:09:28Z · status: backlog → doing (subagent started)
- 2026-10-07T03:24:22Z · comment: Built on feat/trip-companion: Today view (before/during/after/undated) as first On the trip entry + landing while in progress; companion chat with own prompt/context, separate mode:'companion' chat thread (synced, no migration), priced as a 1-credit chat turn (no new server kind, outcome pricing untouched), opt-in one-shot rough location never stored. Tests 332, smoke 101, build ok. Docs appended to docs/plan.md.
- 2026-10-07T03:24:22Z · status: doing → review (Ready for review on feat/trip-companion; not pushed/merged.)
- 2026-10-09T02:48:43Z · status: review → done (User verified the Today page works (2026-10-08))
