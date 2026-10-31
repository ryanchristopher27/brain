---
id: a4e4ce
source: user:trip-fairy:home-leg-mode
title: "Home leg mode: choose fly / drive / train to and from the first stop up front"
type: feature
status: backlog
assignee: 
scoped_dir: .
created: 2026-10-28T02:08:49Z
updated: 2026-10-28T02:08:49Z
---

## Brief
Today the home→first-stop (and last-stop→home) mode can only be changed after the hop exists: the trip page's hop options or the editor's per-leg mode dropdown; the Flights page assumes the home leg is a flight. Add an up-front choice (trip settings and/or account default, e.g. alongside start location) for how you get to the first stop and back — flight, drive, train, other — that the AI planner, leg derivation, cost estimates, budget and Flights page all respect (e.g. no flight search or flight cost for a driven home leg). Code: lib/trip.js travelHops ('origin'/'return'), lib/legOptions.js, pages/TripPage.jsx hop rows, components/TripEditor.jsx Travel, pages/FlightsPage.jsx homeLeg, lib/fareOptimizer.js home hops.

## Acceptance

## Runs

## Updates
- 2026-10-28T02:08:49Z · created
