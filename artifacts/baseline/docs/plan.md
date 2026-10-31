# Plan — Baseline
Date: 2026-10-31
Status: Draft
Brainstorm: docs/brainstorm.md (2026-10-31)

## Overview

Baseline is a personal health app built on WHOOP data. It has one shared data layer and two ways to reach it:

- A **dashboard** for checking at a glance: today's numbers and trends against your own baseline.
- **Claude**, through an MCP server, for asking questions, working out patterns, and saving notes. It's available in Claude Code, the Claude desktop app, and claude.ai including the phone.

Claude can save **tags** (daily context WHOOP's API doesn't expose, such as alcohol, sick or travel) and **findings** (conclusions backed by evidence) back into Baseline. Over time those tags make "what moves my recovery?" answerable.

**Already done:** WHOOP login and token refresh (`src/whoop.js`, `src/auth.js`), a full-history sync to `data/*.json` (`src/sync.js`), offline tests, and a privacy policy (`docs/privacy.html`, published as an artifact).

## Goals & Success Criteria

| Goal | Done when |
|---|---|
| Claude can answer questions about your data from anywhere | On the claude.ai phone app, "how did I recover after pickleball days?" gets an answer worked out from real rows, with the sample size stated |
| Tags build up your own dataset | A tag saved through Claude ("2 drinks last night") shows on that day in the dashboard, and Claude can use it in later analysis |
| Glanceable dashboard | Opening the hosted dashboard on your phone shows today's recovery, sleep and HRV against your baseline, plus when the data was last synced |
| Runs without you | The hosted sync stays current for 14 days straight with no manual runs and no failed token refreshes |
| Honest numbers | Every displayed value says whether it's a WHOOP score or a Baseline calculation, and every finding shows its sample size and date range |

## Scope

### In Scope

- A Supabase Postgres store: raw WHOOP records, a `days` view, tags, findings, and the WHOOP tokens.
- Sync that upserts into the store, run on demand now and on a schedule once hosted.
- An MCP server with read tools and save tools for tags and findings: stdio locally, HTTP with OAuth when hosted.
- Claude Design pass and dashboard v1: Today, Baseline trends (with sleep folded in), and Findings.
- Hosting on Vercel, with a dashboard login, scheduled sync and a claude.ai connector.
- `CLAUDE.md` for the project, and a privacy policy update before any data leaves this Mac.

### Out of Scope (for now)

- The correlations tab ("what moves my recovery"). It waits until there are about 3 months of data and tags.
- A training-log tab and Strava integration.
- More than one user, or public sign-up.
- Native apps and push notifications.
- A free-form SQL tool for Claude (see Open Questions).

## Tech Stack & Architecture

```
                    ┌──────────── Vercel ─────────────────────────────┐
WHOOP API ─webhook─▶│ api/whoop-webhook ─┐                            │
          ◀─fetch───│ api/sync (cron) ───┼─▶ Supabase Postgres        │
                    │                    │    raw_* tables (jsonb)    │
claude.ai ──OAuth──▶│ api/oauth, api/mcp ┼─▶  days (view)             │
                    │                    │    tags, findings, tokens  │
browser ──login────▶│ web/ (dashboard) ──┘                            │
                    └─────────────────────────────────────────────────┘
Local: same src/ modules — `npm run sync`, `npm run mcp` (stdio) for Claude Code/Desktop
```

| Layer | Choice | Why | Alternatives considered |
|---|---|---|---|
| Runtime | Node 22, ES modules, no SDKs | Already in use. Trip Fairy proved that MCP and OAuth can run on `fetch` alone | — |
| Store | **Supabase Postgres from M1**, accessed through PostgREST with `fetch` (Trip Fairy's `restFetch` pattern) | The goal is hosted, so one schema serves local and hosted with no migration later. You already use Supabase, and the MCP can apply migrations | **SQLite locally, Postgres later**: two backends and a port job. **Stay on JSON files**: no tags or findings, and no way to host |
| Daily table | Postgres **view** `days`, with local dates taken from `timezone_offset` | Always consistent with the raw data, and nothing to keep in sync | Building the table in the sync: duplicated logic that can go stale |
| Raw data | One table per resource: WHOOP id, a few key columns, and the full record as `jsonb` | Nothing is lost when WHOOP adds fields, and the view picks out what it needs | Fully normalized columns: brittle |
| MCP | One set of tool handlers with two transports: stdio (local) and stateless Streamable HTTP (hosted, as in Trip Fairy's `server/mcp.mjs`) | Every surface sees the same tools | Separate local and hosted servers |
| MCP login | Port Trip Fairy's `server/oauth.mjs`: OAuth 2.1 with dynamic client registration and PKCE, consent behind the dashboard login | Already works with claude.ai connectors | Supabase's OAuth server, which Trip Fairy ruled out |
| Dashboard | Vite + React in `web/`. Chart library chosen in M4 | Familiar from Trip Fairy. Fits what Claude Design hands off | Next.js: more framework than a single-user app needs |
| Dashboard login | Supabase Auth with one allowed account. RLS on every table | Health data must never be public | Basic auth: no good path to the MCP consent page |
| Hosting | Vercel functions, a WHOOP v2 **webhook** for fresh data, and a daily **cron** to catch anything missed | Data arrives minutes after WHOOP scores it, and the cron fills gaps | Cron only: the free plan allows one run a day, so data would be stale |
| Secrets | `.env` locally; Vercel env vars when hosted. WHOOP tokens move into a Supabase table once hosted | Functions are stateless | — |

**Project layout (target):**

```
baseline/
  src/            whoop.js, auth.js, sync.js (exist) · store.js · days.js
  src/mcp/        tools.js (handlers) · stdio.js · http.js
  api/            sync.js · whoop-webhook.js · mcp.js · oauth.js     (M6–M7)
  web/            Vite + React dashboard                             (M5)
  supabase/migrations/
  test/
  docs/           brainstorm.md · plan.md · privacy.html
  CLAUDE.md
```

**AI resources:** a `CLAUDE.md` describing the data model and its quirks (M1), plus brain's `frontend` domain rules for `web/`.

## Milestones

| # | Milestone | Description | Dependencies |
|---|---|---|---|
| M1 | Store + daily view | Update the privacy policy, create the Supabase project and schema, sync upserts into raw tables, add the `days` view, check the sleep-need definition, write `CLAUDE.md` | — |
| M2 | Tags & findings | Tables plus store functions for tags (fixed vocabulary plus free notes) and findings (text plus evidence) | M1 |
| M3 | Local MCP server | Tool handlers and a stdio transport, connected to Claude Code and the Claude desktop app | M1, M2 |
| M4 | Design pass | Export real data, then take Today, Baseline trends and Findings to Claude Design, with notes on data honesty and missing-data states | M1 |
| M5 | Dashboard v1 (local) | Build the M4 design in `web/`, reading through the store | M2, M4 |
| M6 | Hosted app + scheduled sync | Deploy to Vercel, add Supabase Auth with RLS, move tokens into the DB with a refresh lock, add the WHOOP webhook and daily cron | M5 |
| M7 | Hosted MCP connector | HTTP transport and the OAuth port, added as a claude.ai custom connector and tested on the phone | M3, M6 |

## Task Breakdown

Kept at a high level for now. Expand each milestone when it starts.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Hosted functions refresh the WHOOP token at the same time (a webhook and the cron), and rotation kills the session | Med | High | Refresh inside a Postgres advisory lock or a "claim refresh" RPC, then re-read the token after getting the lock |
| Health data exposed through the dashboard, the API or the MCP | Low | High | RLS on every table, one allowed account, no anonymous keys in the client, webhook signatures verified, OAuth reused from a version already in production |
| Supabase free project pauses after a week without activity | Med | Med | The daily cron keeps it active. Upgrade if it pauses anyway |
| Weak findings presented as facts (n = 56 today) | High | Med | Findings store their sample size and method, the dashboard always shows them, and `CLAUDE.md` tells Claude to state uncertainty |
| WHOOP data quirks (`SCORED` with a null score, calibration days, cycles that aren't calendar days) break charts | High | Low | Handle them in the `days` view, design empty states in M4, and add a test fixture with null scores |
| WHOOP API changes or rate limits | Low | Med | Raw `jsonb` storage, 429 back-off (already built), webhooks reduce the number of polls |
| Privacy policy falls out of date | Med | Med | Updating the policy is a required step in M1 and M6 |

## Dependencies

- A Supabase project, created by you or through the Supabase MCP with your OK. The project URL and service key go in `.env`.
- The WHOOP developer app (done). A webhook URL is added in M6.
- A Vercel project (M6). A custom domain is optional.
- Claude Design access (M4).
- A claude.ai plan that supports custom connectors (M7).

## Open Questions

- **Storage choice:** does Supabase from M1 work for you? It means your WHOOP data leaves this Mac now, not at hosting time. If not, the fallback is SQLite until M6.
- **Tag vocabulary:** which tags to start with? Proposed: alcohol, caffeine-late, sick, travel, late-meal, stress, sauna, supplements, plus a free note.
- **Free-form SQL tool for Claude:** a read-only query tool would make deeper analysis possible, but it's harder to secure. Revisit after M3 shows whether the fixed tools are enough.
- **History:** is about 2 months all your WHOOP has? This decides when the correlations tab is worth building.
- **Sleep need:** check WHOOP's definition in M1. The current sum looks inflated at about 10 h a night.

## Decisions Log

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| App shape | One data layer, a dashboard and an MCP server | Brainstorm outcome | 2026-10-31 |
| Claude reach | Everywhere, phone included, so hosted | Brainstorm outcome | 2026-10-31 |
| Claude can save | Tags and findings | Gives Baseline the cause data WHOOP's API doesn't expose | 2026-10-31 |
| Daily table | Postgres view, not computed in the sync | Can't fall out of sync with raw data | 2026-10-31 |
| MCP and OAuth | Port Trip Fairy's dependency-free implementation | Already works with claude.ai connectors | 2026-10-31 |
| Tags | Fixed starter list that Claude can extend, plus a free note per tag | Keeps tags consistent enough to analyze without blocking new ones (minor decision, can be overridden) | 2026-10-31 |
| Sync | Webhook plus daily cron once hosted; on demand until then | Fresh data with a safety net | 2026-10-31 |
| Store | Supabase Postgres from M1 (**pending your confirmation**) | One schema, no migration later | 2026-10-31 |
