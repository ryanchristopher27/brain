---
id: e6f387
source: plan:trip-planner:D2
title: D2 — Additive magic-link auth
type: task
status: review
assignee: 
scoped_dir: .
created: 2026-09-11T14:06:17Z
updated: 2026-09-11T15:02:49Z
---

## Brief
Sign-in/out UI; logged-out stays fully local; session wiring

## Acceptance

## Runs

## Updates
- 2026-09-11T14:06:17Z · created
- 2026-09-11T15:00:41Z · status: backlog → doing (building)
- 2026-09-11T15:02:49Z · status: doing → review (built; send-path verified, signed-in state pending real login)
- 2026-09-11T15:02:49Z · comment: Additive magic-link auth. Account.jsx: signed-out → email + Send magic link; signed-in → email + Sign out; renders nothing when Supabase unconfigured. App: session state via supabase.auth.getSession + onAuthStateChange subscription; signIn=signInWithOtp(emailRedirectTo=origin), signOut. Mounted in Sidebar footer (footer text flips to 'Synced across your devices' when signed in). Strictly additive — logged-out unchanged, no sync yet (D3). Verified live: sign-in UI renders; Send fired the Supabase auth call (example.com → 'invalid' error surfaced correctly, proving the round-trip + error handling). Signed-in rendering + session persistence pending a real magic-link login (user to confirm; also needed for D3).
