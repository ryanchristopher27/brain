---
id: 6c718b
source: review:trip-planner:base-geocode
title: Base (bed) pins geocode to the wrong place — Page, AZ base shows near Yorktown, Iowa
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-10-17T21:11:14Z
updated: 2026-10-19T03:01:02Z
---

## Brief
From the user's review pass 2026-10-17. Stop pins are right (region-aware since #f136f4) but bed/base pins aren't: geocodeBases sends only [base, country] and the AI's base names carry no region. Fix: geocode a base with the stop's region (and reject results far from the stop it serves, e.g. > 300 km), plus a trip-realism check that flags a base or stop far off the route.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:11:14Z · created
- 2026-10-17T21:11:24Z · status: backlog → doing
- 2026-10-17T21:35:54Z · status: doing → review (Merged 2026-10-17: 491 unit, 143 smoke, market 31, signout 25.)
- 2026-10-19T03:01:02Z · status: review → done (Review pass 2: PASS (user, 2026-10-18))
