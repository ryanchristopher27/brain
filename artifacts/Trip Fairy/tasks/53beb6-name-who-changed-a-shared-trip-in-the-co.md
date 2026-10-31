---
id: 53beb6
source: user:trip-planner:conflict-names
title: Name who changed a shared trip in the conflict message
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-17T23:30:20Z
updated: 2026-10-26T02:41:19Z
---

## Brief
User said yes 2026-10-17. Record the editor on each save of a shared trip (an updated_by column on trips + the shared-save RPCs, one migration — show it to the user before applying) so the conflict banner can say 'Ben changed the nights in Lisbon'. Use the collaborator's display name/username from profiles.

## Acceptance

## Runs

## Updates
- 2026-10-17T23:30:20Z · created
- 2026-10-26T02:40:21Z · status: backlog → doing
- 2026-10-26T02:40:21Z · comment: Built + deployed (inert until 0030): trips.updated_by stamped by trigger on every save; trip_last_editor() returns the other person's username to the owner / accepted collaborators only; banner: 'You and @ava both changed … @ava's version is showing'. PGlite 9/0, unit 679, smoke 226, signout 29, market 54. Waiting on owner OK for 0030.
- 2026-10-26T02:41:19Z · status: doing → review (0030 applied + verified: updated_by column + trigger live, trip_last_editor callable by signed-in users only (anon refused, no caller → null), cleanup dry run clean. Test with two accounts editing the same stop at once.)
