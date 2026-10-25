---
id: 57a1a2
source: review:trip-planner:weather-replaces-when
title: Weather for your dates replaces 'When to go'
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-17T21:11:15Z
updated: 2026-10-22T02:17:58Z
---

## Brief
From the user's review pass 2026-10-17. When the trip has dates (or a travel month), the date-aware weather card should take the place of the When to go section and its weather strip, not sit beside it.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:11:15Z · created
- 2026-10-17T21:45:00Z · status: backlog → doing
- 2026-10-17T22:47:49Z · status: doing → review (Merged 2026-10-17: 497 unit, 178 smoke, signout/market/oauth green.)
- 2026-10-19T03:01:03Z · comment: Review pass 2: FAIL — 'no data available yet' for the selected dates; format unlike When to go. Wants: visual like When to go, AI fallback for typical weather when no forecast exists, more zoomed in than When to go.
- 2026-10-19T11:05:12Z · status: review → doing
- 2026-10-22T01:49:33Z · status: doing → review (Merged + deployed at user's request (2026-10-21) without a final smoke run on the merged code (machine overloaded; the subagent's earlier run of the branch passed 206/0). Unit 571/0, build OK.)
- 2026-10-22T02:17:58Z · comment: User: dated card far bigger than When to go. Rebuilt as When to go's compact table (day axis × stop rows, detail line per stop; per-day forecast numbers in cell tooltips). Smoke 206/0, unit 571/0. Pushed.
