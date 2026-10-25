---
id: ba4e28
source: adhoc:trip-planner:mcp-oauth-claude-ai
title: "MCP server: OAuth so it works as a claude.ai connector"
type: feature
status: done
assignee: 
scoped_dir: .
created: 2026-10-08T03:50:37Z
updated: 2026-10-09T02:00:11Z
---

## Brief
claude.ai custom connectors can't send a static bearer header; add the MCP authorization flow (OAuth 2.1 + PKCE, discovery metadata, dynamic client registration) on mytripfairy.com so users connect Trip Fairy from claude.ai and approve access while signed in

## Acceptance

## Runs

## Updates
- 2026-10-08T03:50:37Z · created
- 2026-10-08T03:50:37Z · status: backlog → doing (subagent started)
- 2026-10-08T03:54:08Z · comment: Research done (MCP spec 2026-07-28, Claude connector auth docs, Supabase OAuth server). Decision: self-hosted minimal AS with opaque tokens (Supabase OAuth tokens would be full-account session JWTs with no resource binding). Summary in docs/plan.md.
- 2026-10-08T04:01:05Z · comment: Server + UI built. npm test 362 pass, build ok. Curl walkthrough against real api/oauth.js + api/mcp.js (stubbed Supabase): 401 challenge -> PRM -> AS metadata -> DCR -> authorize 302 to consent -> approve -> token -> initialize/tools/list/list_trips; code reuse, refresh rotation, revoke all behave.
- 2026-10-08T04:04:40Z · status: doing → review (Self-hosted MCP OAuth (DCR + PKCE + rotating refresh) on branch feat/mcp-oauth. Tests 362 pass, build ok, smoke 101/101, consent smoke 9/9, curl walkthrough ok. Needs migration 0017_mcp_oauth.sql applied (+ optional OAUTH_ISSUER env) before deploy.)
- 2026-10-08T04:12:28Z · comment: 0017 applied 2026-10-07; live: AS metadata served, /api/mcp 401 carries WWW-Authenticate resource_metadata. Needs a real claude.ai connect test.
- 2026-10-09T02:00:11Z · status: review → done (User verified: claude.ai custom connector connects via OAuth and works (2026-10-08))
