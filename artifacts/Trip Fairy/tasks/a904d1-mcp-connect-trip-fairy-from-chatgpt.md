---
id: a904d1
source: adhoc:trip-planner:mcp-chatgpt
title: "MCP: connect Trip Fairy from ChatGPT"
type: feature
status: review
assignee: 
scoped_dir: .
created: 2026-10-09T02:00:11Z
updated: 2026-10-26T03:26:16Z
---

## Brief
Let ChatGPT users connect to Trip Fairy's MCP server (https://mytripfairy.com/api/mcp, OAuth already working for claude.ai). Research and support: ChatGPT connector / apps (MCP + OAuth; check current requirements, e.g. developer mode or Apps SDK, and any OAuth/discovery differences from claude.ai). Add setup steps to Settings → AI → Connect an AI app.

## Acceptance

## Runs

## Updates
- 2026-10-09T02:00:11Z · created
- 2026-10-26T03:16:09Z · status: backlog → doing
- 2026-10-26T03:26:16Z · status: doing → review (No server change needed: our OAuth already meets ChatGPT's documented requirements (DCR, S256 PKCE, RFC 9207 iss on every redirect, resource indicator, 401 resource_metadata challenge) — new test replays ChatGPT's flow (both redirect URIs, default OIDC scopes, iss, token, protocol 2025-11-25 negotiates down). Live metadata checked. Setup steps added to Settings → AI → Connect an AI app and the help page. Owner test: ChatGPT Settings → Security and login → Developer mode; Settings → Plugins → + → https://mytripfairy.com/mcp.)
