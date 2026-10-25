---
id: 67184a
source: design:trip-planner:sv-ai-rule
title: "SV2 — AI: parks/events near your base become day visits"
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-13T02:06:16Z
updated: 2026-10-17T21:11:13Z
---

## Brief
Stays vs visits (#279087). Finder + assistant prompts: a park, viewpoint or event within ~2 h of where you already sleep is a 0-night day visit from that base, not a new overnight stop; give a base only when you actually stay near the place. Update prompt rules (aiClient.js, tripFinder.js) and an eval/fixture (Sedona/Grand Canyon/Zion).

## Acceptance

## Runs

## Updates
- 2026-10-13T02:06:16Z · created
- 2026-10-13T02:06:51Z · status: backlog → doing
- 2026-10-13T02:32:41Z · status: doing → review (Merged 2026-10-12: 467 unit, 127 smoke.)
- 2026-10-17T21:11:13Z · status: review → done (User review pass 2026-10-17: PASS)
