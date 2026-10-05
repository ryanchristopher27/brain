---
id: 8033e3
source: user:brain:project-dev-dashboard
title: Per-project developer dashboard (resources, hosting, traffic)
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-02T04:34:33Z
updated: 2026-10-02T18:13:41Z
---

## Brief
A developer dashboard view per major project in brain's dashboard — one place to route most checks through. (1) External resources: every service the project uses or is hosted on (e.g. for Trip Fairy: Vercel, Supabase, GitHub, npm, Ignav, Open-Meteo, Nominatim, Wikipedia/Openverse, Lemon Squeezy, Cloudflare Turnstile; later Foursquare/Viator/Stay22) with a link, what it's for, plan/cost and limits, and which env vars it needs (names only, never values). Declared in a per-project file (e.g. .brain/resources.yaml), seeded from package.json / .env.example / vercel.json. (2) App status: production URL and latest deploy (commit, state), visitors (Vercel Analytics), recent errors (runtime logs), database health/usage (Supabase), open tracker tasks and what's in review. Read-only tokens stored locally; first project: trip-planner.

## Acceptance

## Runs

## Updates
- 2026-10-02T04:34:33Z · created
- 2026-10-02T18:13:13Z · status: backlog → doing
- 2026-10-02T18:13:41Z · status: doing → review (Dev dashboard built end-to-end for Trip Fairy: resources schema+seed, status collectors (git/tracker/Vercel/Supabase/uptime), API, standalone UI, 19 passing tests. No tokens exist yet for Vercel/Supabase — not-configured states explain how to add them.)
