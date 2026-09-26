---
id: f56145
source: review:trip-planner:double-loadtrips
title: loadTrips() called twice at startup
type: issue
status: done
assignee: 
scoped_dir: .
created: 2026-09-05T23:40:33Z
updated: 2026-09-24T04:11:46Z
---

## Brief
Suggestion · App.jsx · trips state + selectedId both call loadTrips(); init once

## Acceptance

## Runs

## Updates
- 2026-09-05T23:40:33Z · created
- 2026-09-05T23:50:56Z · status: backlog → doing (fixing in M4)
- 2026-09-05T23:50:56Z · status: doing → review (fixed: single lazy loadTrips in App.jsx)
- 2026-09-24T04:11:46Z · status: review → done (Cleanup: verified fixed — useState(loadTrips) runs once.)
