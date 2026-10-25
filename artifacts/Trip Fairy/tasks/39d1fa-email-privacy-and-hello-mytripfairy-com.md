---
id: 39d1fa
source: owner:trip-planner:email-forwarding
title: "Email: privacy@ and hello@mytripfairy.com forwarding (owner)"
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-17T21:25:02Z
updated: 2026-10-17T21:42:56Z
---

## Brief
The legal docs and DMCA notice use privacy@mytripfairy.com, but mytripfairy.com has no MX records, so mail to it bounces. Resend only sends (its records are on send.mytripfairy.com). Plan: ImprovMX free plan (forwarding, private aliases) → add MX mx1.improvmx.com (10) and mx2.improvmx.com (20) plus TXT 'v=spf1 include:spf.improvmx.com ~all' at the root in Vercel DNS; aliases privacy@, hello@ (and optionally copyright@) → your inbox. Test by sending to each.

## Acceptance

## Runs

## Updates
- 2026-10-17T21:25:02Z · created
- 2026-10-17T21:42:56Z · status: backlog → doing
- 2026-10-17T21:42:56Z · status: doing → review
- 2026-10-17T21:42:56Z · status: review → done (User confirmed 2026-10-17: ImprovMX MX + SPF added in Vercel DNS; forwarding works.)
