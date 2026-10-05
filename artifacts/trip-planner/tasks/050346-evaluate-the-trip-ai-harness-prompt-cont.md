---
id: 050346
source: user:trip-planner:ai-harness-audit
title: Evaluate the trip AI harness (prompt context)
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-30T03:44:26Z
updated: 2026-10-05T02:18:35Z
---

## Brief
Audit what information is sent to the LLM with each prompt (tripToContext, chat history, op protocol, finder qualities, etc.): size, relevance, gaps, redundancy; recommend changes.

## Acceptance

## Runs

## Updates
- 2026-09-30T03:44:26Z · created
- 2026-10-02T02:40:43Z · status: backlog → doing
- 2026-10-02T02:42:17Z · comment: Review written: docs/plan.md 'Review — Trip AI harness'. 10 findings: 5 correctness (no travel-leg ids, no op-outcome feedback, no date, hidden stop/activity/leg detail, unchecked numeric fields), 4 efficiency (double listing, misleading destinations line, unbounded transcript, protocol vs proposal rules), 1 dead code.
- 2026-10-02T02:49:09Z · status: doing → review (All 10 findings fixed in one change; tests/harness.test.mjs)
- 2026-10-05T02:18:35Z · status: review → done (Closed by user)
