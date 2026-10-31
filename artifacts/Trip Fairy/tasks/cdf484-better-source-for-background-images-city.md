---
id: cdf484
source: user:trip-fairy:better-bg-images
title: Better source for background images (city heroes, trip cards, ideas)
type: task
status: backlog
assignee: 
scoped_dir: .
created: 2026-10-28T04:18:34Z
updated: 2026-10-28T04:18:34Z
---

## Brief
Background/hero images today come from lib/images.js: Wikipedia lead image for cities, Openverse CC search for things-to-do, Unsplash only if a server key is set, cached on the record. Results are inconsistent (odd crops, maps/flags/diagrams, low-res, missing → broken image on the city page). Find a better source: evaluate Unsplash (configure the key / API terms + attribution), Pexels, Google Places photos, Wikimedia Commons quality filters; consider curated per-city picks, minimum resolution/aspect checks, and a designed fallback instead of a broken <img>. Check licensing/attribution and cost. Ties into the mobile UI cleanup's city hero and trip cards.

## Acceptance

## Runs

## Updates
- 2026-10-28T04:18:34Z · created
