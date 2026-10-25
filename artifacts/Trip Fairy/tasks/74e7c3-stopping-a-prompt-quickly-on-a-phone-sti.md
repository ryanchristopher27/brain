---
id: 74e7c3
source: review:trip-planner:stop-still-charged
title: Stopping a prompt quickly on a phone still used a credit
type: bug
status: review
assignee: 
scoped_dir: .
created: 2026-10-17T21:11:15Z
updated: 2026-10-19T03:09:55Z
---

## Brief
From the user's review pass 2026-10-17. The answer didn't land but a credit was spent. Likely the server never learns of the disconnect (res 'close' not propagated on Vercel for a non-streamed call), so the model finishes and charges. Fix server-side cancellation detection or charge only after delivery.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:11:15Z · created
- 2026-10-17T21:11:25Z · status: backlog → doing
- 2026-10-17T21:18:08Z · status: doing → review (Merged 2026-10-17: supportsCancellation for api/ai/plan.js + refund under waitUntil. Needs a real-phone check on production (Vercel-only behaviour).)
- 2026-10-19T03:01:03Z · comment: Review pass 2: FAIL — Stop still charges a credit on production. Reinvestigating.
- 2026-10-19T03:09:55Z · comment: Fix d27fc14 (pushed): on Vercel's Node handler the cancel arrives as req 'error' (we only listened to req.signal/'aborted'/res 'close'), and the refund was registered with waitUntil only after the cancel — too late, the platform ends the function immediately. Now listens for 'error' and registers waitUntil before the model call. Client also re-reads the balance 3s after a turn (the refund lands after the request ends), and the companion chat refreshes on Stop too. New regression test fails on the old code. Retest: tap Stop before any text appears; balance should return within ~3s. A Stop after text started streaming keeps the charge by design.
- 2026-10-19T03:09:55Z · status: review → review
