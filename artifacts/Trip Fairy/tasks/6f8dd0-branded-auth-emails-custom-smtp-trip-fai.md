---
id: 6f8dd0
source: adhoc:trip-planner:branded-auth-emails
title: "Branded auth emails: custom SMTP + Trip Fairy templates"
type: task
status: done
assignee: 
scoped_dir: .
created: 2026-10-07T03:56:30Z
updated: 2026-10-08T03:46:21Z
---

## Brief
Blocked: Supabase only allows editing email templates on Pro or with custom SMTP. Plan: set up custom SMTP (e.g. Resend free tier) — verify mytripfairy.com DNS (SPF/DKIM) in the provider, add SMTP settings in Supabase (Authentication → Emails → SMTP Settings) with sender 'Trip Fairy <hello@mytripfairy.com>'; then paste supabase/templates/{confirmation,magic_link,recovery}.html with the subjects in supabase/templates/README.md; test with a signup. Also lifts the built-in sender's hourly email limit.

## Acceptance

## Runs

## Updates
- 2026-10-07T03:56:30Z · created
- 2026-10-08T03:38:14Z · status: backlog → doing (User set up Resend (DNS verified on Vercel: MX/SPF on send, DKIM, DMARC), Supabase custom SMTP, templates pasted. Testing next.)
- 2026-10-08T03:46:21Z · status: doing → review (Verified by user: confirm/reset/magic-link emails arrive from Trip Fairy via Resend; logo loads once the mail app allows external images)
- 2026-10-08T03:46:21Z · status: review → done (User confirmed everything works)
