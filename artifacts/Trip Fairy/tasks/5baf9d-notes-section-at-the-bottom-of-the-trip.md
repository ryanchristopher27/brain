---
id: 5baf9d
source: user:trip-planner:notes-sections
title: Notes section at the bottom of the trip page and each city/event page
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-13T04:17:10Z
updated: 2026-10-17T21:11:14Z
---

## Brief
User request 2026-10-12: a free-form notes area at the bottom of the trip overview and of every stop page (city, park, event). Existing fields: trip.notes (also used by the finder for e.g. 'Travel month: X' — keep that working or move it) and segment.notes (assistant ops can set it). Autosave as you type (debounced, one undo step per edit session), works for shared trips (collaborators' edits merge), included in the assistant's trip context, export, and Friends/marketplace views only if appropriate (treat notes as private by default: exclude from friend views and published snapshots unless the owner opts in). Readable on phones.

## Acceptance

## Runs

## Updates
- 2026-10-13T04:17:10Z · created
- 2026-10-14T01:35:26Z · status: backlog → doing
- 2026-10-14T02:24:14Z · status: doing → review (Merged 2026-10-13 (mobile polish): 477 unit, 139 smoke, signout/market/oauth green.)
- 2026-10-17T21:11:14Z · status: review → done (User review pass 2026-10-17: PASS)
