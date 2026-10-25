---
id: f136f4
source: feedback:trip-planner:eric-page-az-geocode
title: AI-added stop geocoded to the wrong place (Page, AZ → "Page, USA")
type: bug
status: review
assignee: 
scoped_dir: .
created: 2026-10-10T22:41:24Z
updated: 2026-10-17T21:11:14Z
---

## Brief
Eric's test (Sedona/Grand Canyon/Zion), 2026-10-10. The assistant said it would add Page, Arizona but the stop landed as "Page, USA" in a different spot. Keep state/region from the AI's place text when geocoding and reject results outside the stated state; show the resolved place before applying.

## Acceptance

## Runs

## Updates
- 2026-10-10T22:41:24Z · created
- 2026-10-11T16:58:12Z · status: backlog → doing
- 2026-10-11T17:19:43Z · status: doing → review (Merged to main 2026-10-11; 428 unit + all smoke suites green. Needs your test on production.)
- 2026-10-17T21:11:14Z · comment: User review pass 2026-10-17: FAIL — see follow-up.
