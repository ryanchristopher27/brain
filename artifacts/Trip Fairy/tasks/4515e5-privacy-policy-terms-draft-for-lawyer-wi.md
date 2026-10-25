---
id: 4515e5
source: adhoc:trip-planner:legal-docs
title: Privacy Policy + Terms (draft for lawyer) with in-app pages, sign-up agreement and age line
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-10T18:21:09Z
updated: 2026-10-17T21:11:14Z
---

## Brief
Draft a Trip Fairy Privacy Policy and Terms of Service from the audit's outline (sub-processors listed, Missouri law/venue, 13+), add /privacy and /terms pages + links, a sign-up agreement line and age confirmation

## Acceptance

## Runs

## Updates
- 2026-10-10T18:21:09Z · created
- 2026-10-10T18:21:09Z · status: backlog → doing (subagent started)
- 2026-10-10T18:25:05Z · comment: Started on feat/legal-docs (worktree tp-legal): drafting docs/legal/privacy-policy.md + terms.md from the privacy audit, then ?page=privacy/terms with a tiny safe markdown renderer, footer/menu links, and the sign-up agreement checkbox.
- 2026-10-10T18:41:01Z · comment: Done in 3383f1f: docs/legal/{privacy-policy,terms,README}.md (drafts, not legal advice; reflects the privacy agent's facts: gateway provider allowlist, no ZDR claim, guest IP 7d, deletion/export in Settings > Account > Your data, friend view, 1km pins). ?page=privacy|terms (lazy LegalPage + safe md parser, 7 unit tests), footer on Home/Explore/published, account menu, OAuth consent; sign-up checkbox gates Create account. npm test 396/396, build ok, smoke 112/112, signout 19/19, oauth 9/9, market 25/25.
- 2026-10-10T18:41:01Z · status: doing → review (Legal drafts + in-app pages + sign-up agreement ready for review; owner must fill placeholders and get lawyer review (see docs/legal/README.md).)
- 2026-10-17T21:11:14Z · comment: User review pass 2026-10-17: FAIL — see follow-up.
