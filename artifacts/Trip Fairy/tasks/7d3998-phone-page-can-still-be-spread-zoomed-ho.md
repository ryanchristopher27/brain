---
id: 7d3998
source: review:trip-planner:page-zoom-ios
title: Phone page can still be spread-zoomed horizontally
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-10-17T21:11:15Z
updated: 2026-10-19T03:01:02Z
---

## Brief
From the user's review pass 2026-10-17. After #4c2a07 the page still pinch-zooms (better than before). iOS Safari ignores user-scalable/maximum-scale for accessibility; check for content wider than the viewport and gesture handlers; decide what's achievable.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:11:15Z · created
- 2026-10-17T21:45:01Z · status: backlog → doing
- 2026-10-17T22:47:49Z · status: doing → review (Merged 2026-10-17: 497 unit, 178 smoke, signout/market/oauth green.)
- 2026-10-19T03:01:02Z · status: review → done (Review pass 2: PASS (user, 2026-10-18))
