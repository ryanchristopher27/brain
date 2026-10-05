---
id: 70bfba
source: adhoc:trip-planner:rename-github-repo
title: Rename GitHub repo to trip-fairy
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-09-29T04:37:51Z
updated: 2026-10-05T02:17:26Z
---

## Brief
Rename ryanchristopher27/trip-planner → trip-fairy on GitHub (Settings → Repository name; old URLs redirect, Vercel's Git link follows). Then: update the local git remote, packages/helper/package.json repository URL, the 'In the trip-planner repo' line in Settings.jsx; optionally rename the local folder and brain's project registry entry. Helper package.json change ships with the next helper release.

## Acceptance

## Runs

## Updates
- 2026-09-29T04:37:51Z · created
- 2026-10-05T01:55:22Z · status: backlog → doing (subagent started)
- 2026-10-05T01:56:38Z · comment: Blocked: GitHub API rename returned 'Resource not accessible by personal access token' (token lacks Administration: write). Waiting on user to rename in GitHub settings.
- 2026-10-05T02:13:39Z · status: doing → review (Renamed on GitHub by user; remote, helper package.json, Settings copy updated. Vercel follows (deploy from ryanchristopher27/trip-fairy confirmed).)
- 2026-10-05T02:17:26Z · status: review → done (Closed by user)
