---
id: 2c0bbd
source: growth:trip-planner:marketplace-seo
title: "Marketplace: indexable public trip pages (SEO)"
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-17T21:53:23Z
updated: 2026-10-24T23:30:24Z
---

## Brief
From docs/research/marketing.md (2026-10-17). Public published-trip pages that search engines can index: server-rendered or prerendered HTML with title/description, OG image, sitemap.xml, canonical URLs, 'Copy to my trips' + 'planned with Trip Fairy'. Watch the Vercel function cap (no new api/*.js). Seed 20 quality trips.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:53:23Z · created
- 2026-10-24T22:58:12Z · status: backlog → doing
- 2026-10-24T23:30:24Z · status: doing → review (Deployed + verified live: /sitemap.xml (home, Explore, legal, published trips), robots.txt, /trips/<slug>-<id> serves the trip's title/canonical/JSON-LD + app, stale slug 301s, unknown 404s. CDN cache 5 min (+5 min stale). Owner steps: Google Search Console + submit sitemap; run scripts/seed/publish-seed.mjs --apply with a dedicated account to publish the 20 seed trips.)
