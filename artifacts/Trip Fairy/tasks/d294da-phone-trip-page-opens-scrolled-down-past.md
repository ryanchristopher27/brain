---
id: d294da
source: adhoc:trip-planner:phone-first-load-scroll
title: "Phone: trip page opens scrolled down past the map"
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-10-14T02:24:14Z
updated: 2026-10-19T03:01:02Z
---

## Brief
Found during #767a7b: on a fresh 375px load of a trip with no home city set, <main> is already scrolled ~647px, hiding the map. Suspect the autoFocus on the 'Where are you flying from?' city input pulling it into view. Fix: no autofocus on load (or preventScroll), keep the page at the top.

## Acceptance

## Runs

## Updates
- 2026-10-14T02:24:14Z · created
- 2026-10-17T20:40:42Z · status: backlog → doing
- 2026-10-17T20:40:42Z · status: doing → review (Merged 2026-10-17: 478 unit, 140 smoke, signout/market/oauth green.)
- 2026-10-17T21:11:14Z · comment: User review pass 2026-10-17: FAIL — see follow-up.
- 2026-10-19T03:01:02Z · status: review → done (Review pass 2: PASS (user, 2026-10-18))
