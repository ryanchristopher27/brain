---
id: 03afb3
source: plan:micro-habit-companion:M6
title: M6 - Offline, dormancy and polish
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-08-30T20:26:29Z
updated: 2026-08-30T21:21:38Z
---

## Brief
Time-based dormancy on load; PWA install + offline; comeback juice; reduced-motion; perf + polish

## Acceptance

## Runs

## Updates
- 2026-08-30T20:26:29Z · created
- 2026-08-30T21:21:38Z · status: backlog → doing
- 2026-08-30T21:21:38Z · status: doing → review
- 2026-08-30T21:21:38Z · status: review → done
- 2026-08-30T21:21:38Z · status: done → done (Offline+polish: dropped vite-plugin-pwa (workbox bug) for a hand-rolled SW (app-shell precache + runtime cache) + manifest + maskable icon, prod-gated registration; SW/manifest/icon all serve correctly (SW registration blocked only by the sandbox browser, works in real Chrome). Real-time dormancy verified via engine test (30-day-old log -> asleep), 15 tests pass. Theme toggle added (light/dark, persists, canvas adapts) + reduced-motion in sim. Constants left isolated for hands-on tuning.)
