---
id: 7e0b9a
source: plan:trip-planner:SUB4
title: "SUB4 — Settings → Credits: Plus card, subscribe and manage"
type: task
status: doing
assignee: 
scoped_dir: .
created: 2026-10-17T20:15:38Z
updated: 2026-10-23T03:51:49Z
---

## Brief
A Plus card in the Credits tab: what's included, .99/mo or /yr, subscribe via Lemon Squeezy checkout, manage/cancel via the customer portal, renewal date and status. Covers the tiers info page (#dca3f2).

## Acceptance

## Runs

## Updates
- 2026-10-17T20:15:38Z · created
- 2026-10-23T03:15:13Z · status: backlog → doing
- 2026-10-23T03:51:49Z · comment: Code merged + deployed (inert until 0025 is applied and LS_PLUS_* / VITE_PLUS are set). Reviewed: fixed a free-refill-on-pause/unpause hole (only a new subscription refills immediately). Tests: unit 598, smoke 210, signout 29, market 49, oauth 9, plus 8; PGlite subscriptions 40/0.
