---
id: 2f1b1f
source: plan:trip-planner:N1
title: N1 — v3 model + migration
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-06T20:10:49Z
updated: 2026-09-06T20:19:31Z
---

## Brief
kind/proposalId/variantName, newProposal/newPlan, field partition, v2→v3 shim (proposal + conditional plan), storage v3

## Acceptance

## Runs

## Updates
- 2026-09-06T20:10:49Z · created
- 2026-09-06T20:16:56Z · status: backlog → doing (building)
- 2026-09-06T20:19:31Z · status: doing → review (built + verified)
- 2026-09-06T20:19:31Z · comment: trip.js: SCHEMA_VERSION=3, KINDS, kind/proposalId/variantName on records, newProposal/newPlan, field-partition consts (SHARED/PLAN_ONLY/SEGMENT_PLAN), newId + remapRecordIds (shared id-remap infra). migrate.js: v2→v3 — every legacy trip → proposal; committed ones (dates/flights/segment arrive-depart-lodging) also spawn a plan snapshot w/ regenerated ids + proposalId, proposal generalized. storage.js: v3 key + v3→v2→v1 load chain, older keys as backstops. 23/23 v3 assertions (split, orphan-free remap, idempotency, no-signal). Verified in-app: existing v2 trip migrated to 1 v3 proposal, no console errors. NOTE: id-remap kept in trip.js (not escalate.js) as shared infra; escalate.js stays N4 stub.
