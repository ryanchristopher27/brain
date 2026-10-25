---
id: bca79a
source: adhoc:trip-planner:privacy-legal-audit
title: Privacy & legal risk research + Trip Fairy audit
type: research
status: done
assignee: 
scoped_dir: .
created: 2026-10-10T18:02:38Z
updated: 2026-10-10T18:21:09Z
---

## Brief
Research privacy laws/liability risks for small consumer apps (CalOPPA, CCPA/CPRA + state laws, GDPR/UK GDPR, COPPA, CAN-SPAM, breach notification, cookies, AI processing, public user content) and audit Trip Fairy's code and data flows against them; report with prioritized fixes

## Acceptance

## Runs

## Updates
- 2026-10-10T18:02:38Z · created
- 2026-10-10T18:02:38Z · status: backlog → doing (subagent started)
- 2026-10-10T18:11:25Z · comment: Report written: docs/research/privacy-legal-audit.md
- 2026-10-10T18:11:25Z · status: doing → review (Privacy/legal research + read-only code audit done. Top fixes: privacy policy + terms (CalOPPA applies now), self-serve account deletion/export, commit trips RLS + run Supabase advisor; then pin gpt-oss gateway routing, strip notes/lodging from friend view, add security headers.)
- 2026-10-10T18:21:09Z · status: review → done (Report delivered; follow-ups split into code fixes + legal docs tasks)
