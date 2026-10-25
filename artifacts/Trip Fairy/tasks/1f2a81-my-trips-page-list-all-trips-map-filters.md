---
id: 1f2a81
source: adhoc:trip-planner:my-trips-page
title: "My trips page: list + all-trips map + filters"
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-28T01:47:44Z
updated: 2026-10-02T02:40:43Z
---

## Brief
A page for the current user's trips: a list view like the home page, plus a map showing every trip's stops in a different colour per trip. Filter trips by fields (status, dates, country, length, kind, etc.).

## Acceptance

## Runs

## Updates
- 2026-09-28T01:47:44Z · created
- 2026-09-29T02:54:08Z · status: backlog → doing
- 2026-09-29T03:01:14Z · comment: Shipped: lib/myTrips.js + MyTripsPage (header tab, Home link), per-trip colours on list + map (coloured legs, trip dots), filters (search, status, when, country, length), summary counts. Verified desktop/375, light/dark; smoke 35/35; 153 unit tests.
- 2026-09-29T03:01:14Z · status: doing → review
- 2026-09-29T03:09:49Z · comment: Reworked to the trip-overview layout: full-bleed sticky globe, title + filters over its bottom edge, list scrolls up over it with dimming + re-framing. Verified desktop + 375; smoke 35/35.
- 2026-09-29T03:16:26Z · comment: Scroll-zoom out on My trips now goes straight out from the current spot (zoomOut='straight'); trip pages still glide back to the trip. Smoke checks both (37/37).
- 2026-09-29T03:35:44Z · comment: Fixed scroll lag: stopped per-frame globe re-framing during page scroll (49 camera jumps per sweep → 0). Smoke 38/38 incl. a stillness check.
- 2026-09-29T03:52:23Z · comment: Map returns to its landing scale before content scrolls (My trips: landing zoom, centre kept; trip page: full landing framing). Gate covers scrolls over content too; catch-all for scrollbar/keys; drag-inertia moveend bug fixed. Smoke 41/41, mutation-checked.
- 2026-09-29T04:14:10Z · comment: Fixed: after zooming in far from the landing latitude, My trips came back too zoomed in (1.87x at 65N) because globe zoom numbers vary with latitude. Gate now uses latitude-adjusted landing zoom; smoke 42/42 incl. apparent-size check (fails on old code).
- 2026-10-02T02:40:43Z · status: review → done (Approved by user 2026-10-01)
