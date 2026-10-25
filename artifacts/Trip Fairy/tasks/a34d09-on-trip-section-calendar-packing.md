---
id: a34d09
source: user:trip-planner:on-trip-section
title: "On-trip section: calendar + packing"
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-02T04:31:08Z
updated: 2026-10-04T21:40:20Z
---

## Brief
A new section of the app for while you're on the trip (goes with trip companion mode, #6c742b): a calendar view of the whole trip, a stretch of it, or a single day (stops, travel legs, activities with times, anchors); and a packing list — essentials plus gear for what you're doing (hiking → hiking backpack, boots, layers; beach → …), driven by the trip's activities, places, weather and length, with checkboxes.

## Acceptance

## Runs

## Updates
- 2026-10-02T04:31:08Z · created
- 2026-10-02T18:14:10Z · status: backlog → doing
- 2026-10-02T18:14:17Z · status: doing → review (Built calendar (whole trip / range / day-by-day) + packing list (deterministic generator: essentials, clothing scaled to length/travelers, gear from place types/activities/interests, climate-normals weather pass), saved as record.packing. New lib/onTrip.js + lib/packing.js (pure, 11 mutation-checked tests), pages/CalendarPage.jsx + PackingPage.jsx, trip-bar "On the trip" menu. Tests 207/207, build clean, smoke 62/62 (added Calendar/Packing layout + 3 feature steps), screenshots checked dark+light at 1280/375. Branch feat/on-trip-calendar-packing in worktree ../trip-planner-ontrip.)
- 2026-10-04T21:40:20Z · status: review → done (Approved by user 2026-10-04 after use + polish)
