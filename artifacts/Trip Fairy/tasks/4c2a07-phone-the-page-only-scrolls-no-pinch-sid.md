---
id: 4c2a07
source: user:trip-planner:no-page-zoom
title: "Phone: the page only scrolls (no pinch/sideways zoom)"
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-17T20:40:42Z
updated: 2026-10-19T03:01:02Z
---

## Brief
User request 2026-10-17: on phones the page shouldn't zoom or drift sideways, only scroll. Done: viewport maximum-scale=1, body touch-action: pan-x pan-y (no pinch/double-tap zoom; horizontal rows still swipe), html/body overflow-x hidden; maps keep their own pinch. iOS Safari may still allow pinch-zoom for accessibility; check on an iPhone.

## Acceptance

## Runs

## Updates
- 2026-10-17T20:40:42Z · created
- 2026-10-17T20:40:42Z · status: backlog → doing
- 2026-10-17T20:40:42Z · status: doing → review (Merged with #d294da.)
- 2026-10-17T21:11:14Z · comment: User review pass 2026-10-17: FAIL — see follow-up.
- 2026-10-19T03:01:02Z · status: review → done (Review pass 2: PASS (user, 2026-10-18))
