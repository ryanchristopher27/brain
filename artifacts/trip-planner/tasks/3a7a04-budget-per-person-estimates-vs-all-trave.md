---
id: 3a7a04
source: adhoc:trip-planner:budget-per-person
title: "Budget: per-person estimates vs all-traveler fares"
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-09-28T01:15:40Z
updated: 2026-09-29T02:47:28Z
---

## Brief
computeBudget sums leg costs as-is: LLM/ live-check estimates are per person, chosen Ignav fares cover all travelers. Scale estimates by travelers (or label) so transport totals are consistent.

## Acceptance

## Runs

## Updates
- 2026-09-28T01:15:40Z · created
- 2026-09-28T02:06:04Z · status: backlog → doing
- 2026-09-28T02:08:02Z · comment: Fixed: budget is a group total — per-person legs (derived / costBasis pp / live check) × travelers, chosen Ignav fares as-is, food × travelers, 'pp' activities × travelers, lodging × rooms (2/room). Labels: 'for N travelers', '$X pp' on legs/options. 145 tests.
- 2026-09-28T02:08:02Z · status: doing → review
- 2026-09-28T02:28:33Z · comment: Superseded by the per-traveler / trip-total pricing rework (commit after deaefac): money normalized per traveler, display toggle, rooms field. See docs/plan.md 'Pricing display'.
- 2026-09-28T03:12:21Z · comment: Replaced by #9bce76 (per-traveler normalization + Show prices setting). Nothing left to do here — close as superseded.
- 2026-09-29T02:47:28Z · status: review → done (superseded by #9bce76, which Ryan approved 2026-09-28)
