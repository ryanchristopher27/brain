---
id: a44747
source: web:trip-planner:chat-history
title: Saved chat history per trip, viewable in a tab
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-25T23:59:01Z
updated: 2026-09-27T00:48:08Z
---

## Brief
Save every assistant conversation and tie it to its trip: brainstorming that led to a trip, the proposal chat, and each plan's chat. Add a Chat/History tab in the trip bar to browse past conversations (with timestamps and what changed). Today chats live only in this browser's localStorage (trippin.chat.<tripId>; brainstorm is one global thread) and aren't synced, so decide storage (Supabase alongside trips) and privacy/retention.

## Acceptance

## Runs

## Updates
- 2026-09-25T23:59:01Z · created
- 2026-09-27T00:16:35Z · status: backlog → doing (Starting chat history)
- 2026-09-27T00:24:35Z · status: doing → review (Built + verified locally; sync needs migration 0007)
- 2026-09-27T00:48:08Z · status: review → done (User confirmed on the live site; 0007 applied, sync verified)
