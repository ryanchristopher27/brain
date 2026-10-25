---
id: 6d815b
source: sub:delete-cancels
title: Account deletion cancels the Plus subscription at Lemon Squeezy
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-10-23T03:51:49Z
updated: 2026-10-24T00:45:27Z
---

## Brief
Deleting an account removes our subscriptions row (cascade) but Lemon Squeezy keeps billing. Before Plus goes live: cancel via the LS API (LS_API_KEY) in the delete flow, or at minimum warn in the delete dialog to cancel first.

## Acceptance

## Runs

## Updates
- 2026-10-23T03:51:49Z · created
- 2026-10-24T00:34:30Z · status: backlog → doing
- 2026-10-24T00:45:27Z · status: doing → review (Deployed (inert until 0025 + LS_API_KEY). Delete flow cancels a renewing Plus sub at LS first (runs to period end, no refund) and records it; delete_my_account (in 0025) refuses while a sub can bill; without LS_API_KEY the user is told to cancel in the portal first. Unit 603, PGlite subs 44/0, smoke 210, signout 29, plus 8.)
