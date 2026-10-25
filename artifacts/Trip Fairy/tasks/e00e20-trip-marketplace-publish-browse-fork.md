---
id: e00e20
source: adhoc:trip-planner:marketplace
title: Trip marketplace (publish, browse, fork)
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-09-28T01:47:44Z
updated: 2026-10-09T04:03:16Z
---

## Brief
Users publish established trip proposals; subscribers browse the marketplace and fork a trip into their own version (snapshot copy, like escalation). Note: billing today is credit packs, not subscriptions — needs a subscription tier decided first (see tiers info page). Moderation/reporting needed for public content.

## Acceptance

## Runs

## Updates
- 2026-09-28T01:47:44Z · created
- 2026-10-09T03:04:46Z · status: backlog → doing (Decisions: public link pages (browse/copy need account); publishing = snapshot without dates/budget/notes/booking/home)
- 2026-10-09T03:22:19Z · comment: Built on feat/marketplace: migration 0018 (verified in PGlite, not applied), publish dialog, public page, Explore, copy, report. 380 tests, smoke 105 + market 24 + signout 16 pass; build ok.
- 2026-10-09T03:22:19Z · status: doing → review (Ready for review; migration 0018 needs applying.)
- 2026-10-09T03:31:08Z · comment: 0018 applied 2026-10-08; sanity: browse/facets return nothing without auth, public_trip unknown id → 0 rows, snapshot validator accepts a clean snapshot and rejects one with a notes field. Pushed.
- 2026-10-09T04:03:16Z · status: review → done (User verified publish / public page / Explore / copy (2026-10-08); duplicate-copy prompt and seed duplicates fixed (0020 server-side LWW))
