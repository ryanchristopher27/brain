---
id: eaa922
source: plan:brain:H0
title: H0 — SDK spike
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-31T20:05:45Z
updated: 2026-10-31T20:15:59Z
---

## Brief
Probe claude-agent-sdk: long-lived client, persona+model, subscription auth (no API key), in-process tool, can_use_tool scope block, budget, resume, mid-session model switch, router-mod skip; go/no-go

## Acceptance

## Runs

## Updates
- 2026-10-31T20:05:45Z · created
- 2026-10-31T20:15:57Z · comment: H0 GO: 9/9 probes pass (dashboard/harness/probe_sdk.py). Router mod must be disabled in harness sessions; gate via PreToolUse hook. See docs/plan.md H0 results.
- 2026-10-31T20:15:59Z · status: backlog → doing
- 2026-10-31T20:15:59Z · status: doing → review
