---
id: 748055
source: web:trip-planner:remote-local-claude
title: Run local Claude Code helper from non-localhost
type: research
status: done
assignee: 
scoped_dir: .
created: 2026-09-20T00:02:23Z
updated: 2026-09-24T04:09:43Z
---

## Brief
Figure out how to reach the local 'claude -p' helper when the app isn't served from localhost (deployed site or phone). Options: tunnel (ngrok/cloudflared), LAN address + CORS, or a small auth'd relay. Ties into prod-ai-serverless decision.

## Acceptance

## Runs

## Updates
- 2026-09-20T00:02:23Z · created
- 2026-09-24T03:31:24Z · status: backlog → doing
- 2026-09-24T03:31:24Z · status: doing → review (Deployed site can use your Claude Code: direct calls to 127.0.0.1 with pairing code; helper hardened (loopback bind, Host check, origin allowlist, /ai only). Verified via curl gate tests + dev cross-origin real call; final Chrome LNA prompt step needs real Chrome after deploy.)
- 2026-09-24T04:05:15Z · comment: Published trip-fairy-helper@0.1.0 to npm; app deployed with 'Your Claude Code' + npx setup step. Remaining: user's real-Chrome LNA connection test.
- 2026-09-24T04:09:43Z · status: review → done (Verified end-to-end in real Chrome: Vercel site → local network permission → npx trip-fairy-helper → Claude Code.)
