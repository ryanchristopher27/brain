---
id: ccb807
source: plan:trip-planner:F4
title: F4 — AI chat flight search
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T22:45:22Z
updated: 2026-09-07T01:04:40Z
---

## Brief
Client-orchestrated search loop in PlanChat + confirm-before-apply for flight adds (was deferred F5)

## Acceptance

## Runs

## Updates
- 2026-09-06T22:45:22Z · created
- 2026-09-07T00:54:25Z · status: backlog → doing (building)
- 2026-09-07T01:04:40Z · status: doing → review (built + verified live)
- 2026-09-07T01:04:40Z · comment: aiClient: plan editPlan prompt gains a client-run FLIGHT_SEARCH capability — model returns {search:{origin,destination,departure_date,...}} (plan-only), never fabricates flights/ops; editPlan returns search. PlanChat: on search intent → searchFlights → renders offer cards inline (ChatOffer: price/cabin/out+ret summary), Add button = confirm-to-add → offerToLegs → add/flight ops (undoable). Verified LIVE: 'find nonstop JFK→London Nov 15' → model emitted search → Ignav returned BA/AA nonstops as cards → Add wrote BA182 leg (, confirmation empty) → Undo enabled. DEVIATION (logged): model proposes a SEARCH + user Add-click confirms, instead of model proposing add-ops + confirm-card — prevents model fabricating flight data. Also hardened prompt test (plan has search rule, proposal doesn't). Note: tripToContext assumes legacy trip.stops exists (real records always do via newTrip/migrate); a hand-seeded record without it throws — not a live path.
