# The Local-First Agent Stack

The reusable architecture pattern behind Odyssai — a React app that runs fully
offline from the browser, gets its intelligence from a locally-installed CLI
agent (with a BYOK fallback), and syncs across devices only when you sign in.
Every layer is **additive**: with no agent, no account, and no network, the core
still works.

Visual reference: https://claude.ai/code/artifact/8309dfcc-2741-42b3-918a-f446d370f9e5

## The layers

| # | Layer | Essence | Key pieces |
|---|-------|---------|------------|
| L1 | Local-first storage seam | localStorage is the working copy, behind one load/save seam | `storage.js` |
| L2 | Agentic edits | model returns `{reply, ops[]}` → pure `applyOps` reducer → undo/redo, all-or-nothing | `patch.js`, `history.js` |
| L3 | Switchable AI | local CLI agent (`claude -p`, no key) **or** BYOK; AI gated on agent-or-key, manual never gated | `aiClient.js`, `server/index.mjs` |
| L4 | Discriminated records | one schema + a `kind`; snapshot escalation with id remap; versioned migrations | `trip.js`, `escalate.js`, `migrate.js` |
| L5 | Server-side key proxy | secrets off the client; one core shared by dev helper + serverless | `server/ignav.mjs`, `api/flights/*` |
| L6 | Optional cloud sync | Supabase browser-direct + RLS, magic-link; LWW + tombstones + realtime; additive | `supabase.js`, `sync.js` |
| L7 | Deploy split | static SPA + serverless functions; `VITE_*` public vs server-only secrets | `vercel.json`, `.env` |

## Starter spec

Paste this into a new project's `/brainstorm` or `/plan` (or any fresh Claude
session) to bootstrap the same architecture.

```text
Build a LOCAL-FIRST, AGENT-NATIVE web app (React + Vite).

STORAGE — all user data in localStorage behind a single load/save seam. The app
works fully offline from that copy; everything else layers on top.

AGENTIC EDITS — the model returns JSON { reply, ops[] }; a pure
applyOps(record, ops) reducer applies them to a fresh object; a bounded snapshot
stack gives undo/redo; a bad op applies nothing (all-or-nothing), so a malformed
reply can never half-corrupt a record.

AI (switchable: auto | local | byok) — a tiny zero-dep local Node helper shells
out to a CLI agent (e.g. `claude -p`, no key, no per-call billing) behind /ai/*;
OR the browser calls the model directly with a user-provided key (BYOK). Gate AI
features on (agent reachable OR key present); NEVER gate manual create/edit.

DATA MODEL — one record schema with a `kind` discriminator for lifecycle stages
(e.g. proposal -> plan). "Escalate" one stage into another by snapshot-copy with
regenerated ids, so the source stays pristine and can spawn many variants.
Migrate by schemaVersion on load; hide stage-inappropriate fields in the UI.

KEYED THIRD-PARTY APIS — never call from the browser. A server-side proxy holds
the key and exposes /x/*. Share ONE core module between the dev helper and the
deployed serverless functions (rewrite /x/* -> /api/x/*) so the client path is
identical in dev and prod and the two can't drift.

OPTIONAL CLOUD SYNC (additive) — Supabase (Postgres + Auth + row-level security),
called browser-direct (public key + RLS enforces per-user access, so no data
backend to build). Magic-link accounts. localStorage stays the working copy; sync
via pull-merge on login + debounced push on change + delete tombstones +
record-level last-write-wins + a realtime subscription for live devices. Signed
out = pure local, no regression.

DEPLOY — static SPA + serverless functions on one host. Env split: VITE_* public
values compile into the client (e.g. Supabase URL + publishable key — safe by
design); every real secret stays server-side, read only inside the functions.
The local CLI agent is not hosted — the deployed build uses BYOK for AI.

PRINCIPLES — every layer is additive (no agent / no account / offline still
works); verify each integration against the real API before building on it; one
core module runs in both dev helper and serverless function; workflow is
brainstorm -> plan -> build -> review -> iterate with docs/ + a task tracker and
a commit per milestone.
```
