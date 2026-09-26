---
id: 75fde8
source: web:trip-planner:taller-trip-map
title: Taller map on the trip page (full height by default)
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-26T00:16:45Z
updated: 2026-09-26T00:54:20Z
---

## Brief
The trip hero map is 280px tall (src/pages/TripPage.jsx). Make it much taller by default, e.g. filling the viewport under the top bars, so the map leads and the day-by-day cards and everything below sit under the fold. Keep the title overlay; check the map padding for the stops, and the phone layout.

## Acceptance

## Runs

## Updates
- 2026-09-26T00:16:45Z · created
- 2026-09-26T00:20:51Z · status: backlog → doing (Subagent building in its own worktree (polish batch).)
- 2026-09-26T00:25:30Z · status: doing → review (Built by subagent, merged + verified in browser (desktop + phone); not yet deployed.)
- 2026-09-26T00:34:56Z · comment: Reworked per user: full-page sticky map backdrop; sheet (title first) scrolls over it with scroll-driven dimming; cooperative gestures on embedded maps.
- 2026-09-26T00:54:20Z · status: review → done (Shipped 2026-09-25 (user reviewed + approved push).)
