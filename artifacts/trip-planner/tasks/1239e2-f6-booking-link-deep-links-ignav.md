---
id: 1239e2
source: plan:trip-planner:F6
title: F6 — Booking-link deep-links (Ignav)
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-07T01:15:25Z
updated: 2026-09-07T01:35:12Z
---

## Brief
Add /flights/booking-links endpoint (POST ignav_id) + populate leg.bookingUrl; 'Book' link-out on saved plan flights + result cards. Deep-link hand-off only, no in-app booking.

## Acceptance

## Runs

## Updates
- 2026-09-07T01:15:25Z · created
- 2026-09-07T01:24:31Z · status: backlog → doing (building)
- 2026-09-07T01:35:12Z · status: doing → review (built + verified live)
- 2026-09-07T01:35:12Z · comment: Booking deep-links. Helper: POST /flights/booking-links {ignav_id} → Ignav /fares/booking-links (path verified live; /booking-links 404s) + booking cache. flights.js: getBookingLink (flatten booking_options[].links, prefer airline) + openBooking (new tab, noopener). trip.js: newFlight gains ignavId; offerToLegs stores offer.ignav_id on first leg. Book ↗ buttons on FlightSearch results, PlanChat offer cards, and saved plan flight rows (TripEditor caches resolved bookingUrl, best-effort). Verified live: booking-links returns real deep-links (airline/3rd-party); Book click fires POST; full client path search→id→link→url ok. LIMITATION: fares expire → booking-links 424 for stale/old offers (inherent); saved-flight Book is best-effort. Deep-link hand-off only, no in-app booking. +2 offerToLegs ignavId assertions.
