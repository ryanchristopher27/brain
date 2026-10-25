---
id: bfacb6
source: adhoc:trip-planner:friends-family-credits
title: Free credits for family & friends testers (promo codes)
type: feature
status: review
assignee: 
scoped_dir: .
created: 2026-10-09T04:12:41Z
updated: 2026-10-25T00:16:42Z
---

## Brief
Let invited testers use the managed AI without buying credits: e.g. a redeemable promo code that grants N credits once per account (capped, revocable), or manual grants

## Acceptance

## Runs

## Updates
- 2026-10-09T04:12:41Z · created
- 2026-10-24T22:58:12Z · status: backlog → doing
- 2026-10-24T23:13:21Z · comment: Built on feat/promo-codes (c44f2a2), not merged: 0028_promo_codes (server-only codes, one use per account, max uses/expiry/revoke, 5 codes per account, guests excluded), POST /credits/redeem (free grant first), Settings → Credits → Have a code?, npm run promo create|list|revoke, export + terms/privacy lines. Unit 624, PGlite promo 17/0, smoke 226, plus 10, signout 29, market 49. Waiting on owner OK for 0028.
- 2026-10-25T00:16:42Z · status: doing → review (0028 applied + verified (RLS, codes server-only, own-redemptions read only, redeem service-only). Merged + deployed; /credits/redeem live (401 without sign-in). Owner: npm run promo -- create --credits N --uses N [--days N] [--note …] with SUPABASE_URL + SUPABASE_SECRET_KEY.)
