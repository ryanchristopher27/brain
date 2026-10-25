---
id: 767a7b
source: user:trip-planner:mobile-pinch-zoom
title: Smooth two-finger (pinch) zoom on mobile maps
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-13T04:18:55Z
updated: 2026-10-17T21:11:14Z
---

## Brief
User request 2026-10-12: pinch-zoom on phones should feel smooth. Check src/components/MapCanvas.jsx map options (~line 276: scrollZoom, cooperativeGestures in 'cooperative' mode, touchZoomRotate with rotation disabled) and anything that fights the gesture: the page/scroll container intercepting touch (touch-action CSS), cooperative-gesture overlay requiring two fingers to pan, per-frame re-framing (cameraForBounds/jumpTo on scroll — MyTripsPage notes a stutter from this), heavy layers or markers re-rendered on zoom. Test on a real phone/Simulator at 375px.

## Acceptance

## Runs

## Updates
- 2026-10-13T04:18:55Z · created
- 2026-10-14T01:35:26Z · status: backlog → doing
- 2026-10-14T02:24:14Z · status: doing → review (Merged 2026-10-13 (mobile polish): 477 unit, 139 smoke, signout/market/oauth green.)
- 2026-10-17T21:11:14Z · status: review → done (User review pass 2026-10-17: PASS)
