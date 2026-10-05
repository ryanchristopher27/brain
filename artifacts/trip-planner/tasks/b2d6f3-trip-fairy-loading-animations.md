---
id: b2d6f3
source: user:trip-planner:fairy-loading-animations
title: Trip Fairy loading animations
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-02T04:27:16Z
updated: 2026-10-05T02:18:36Z
---

## Brief
Add loading animations built around the Trip Fairy logo — especially while waiting for an agent response (trip chat, Home finder, drafts/route options, city briefings), and for other loading states (fares, photos, maps). Respect prefers-reduced-motion; keep it light (SVG/CSS).

## Acceptance

## Runs

## Updates
- 2026-10-02T04:27:16Z · created
- 2026-10-02T18:10:21Z · status: backlog → doing
- 2026-10-02T18:10:26Z · status: doing → review (FairyLoader (inline/block/typing) built from TripFairyMark with orbiting sparkles + bob, CSS keyframes + reduced-motion fallback. Wired into assistant Thinking, Home finder (history row, phone line, empty panel, send button), Versions draft/routes buttons, City briefing, Trip Audit + GoodToKnow AI-check buttons. Tests 198/198 (+2 new for pickStatusLine), build passes, smoke 56/56 (+1 new loader-visibility step). Visually checked dark/light + desktop/mobile + reduced-motion via playwright-cli.)
- 2026-10-05T02:18:36Z · status: review → done (Closed by user)
