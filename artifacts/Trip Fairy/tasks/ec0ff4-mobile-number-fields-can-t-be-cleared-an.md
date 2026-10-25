---
id: ec0ff4
source: user:trip-planner:mobile-number-inputs
title: "Mobile: number fields can't be cleared and have no +/- (travelers stuck at 1)"
type: bug
status: done
assignee: 
scoped_dir: .
created: 2026-10-13T04:16:39Z
updated: 2026-10-17T21:11:14Z
---

## Brief
User report 2026-10-12: on mobile, manual number inputs (e.g. travelers) won't let you delete the 1 and have no +/- controls, so the number of travelers can't be changed. Root cause candidates: onChange coerces '' to 1 (e.g. TripEditor.jsx:131 'Number(e.target.value) || 1'; check TripPage.jsx travelers/rooms/length inputs ~462/568/584, FlightsPage adults, CityPage/TripEditor nights, DatesPopover days, home QualityEditor). Fix: allow an empty draft while typing and validate on blur/commit; add a shared stepper (− value +) for small integers (travelers, rooms, nights, days) with inputMode=numeric. Verify on a 375px viewport.

## Acceptance

## Runs

## Updates
- 2026-10-13T04:16:39Z · created
- 2026-10-14T01:35:26Z · status: backlog → doing
- 2026-10-14T02:24:14Z · status: doing → review (Merged 2026-10-13 (mobile polish): 477 unit, 139 smoke, signout/market/oauth green.)
- 2026-10-17T21:11:14Z · status: review → done (User review pass 2026-10-17: PASS)
