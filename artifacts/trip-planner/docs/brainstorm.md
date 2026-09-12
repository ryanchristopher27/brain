# Trippin' — Brainstorm

## 2026-09-05 · Plan iteration workspace (chat + visualization + multi-city)

### Problem / Opportunity
The trips workspace is a centered scrolling form with a narrow, **one-shot** AI rail.
Each AI draft starts fresh (no memory), and "Add to trip" **appends** activities/stops/notes
— which duplicates and can't refine ("make day 3 lighter"). There's **no visualization** of
the plan, and **multi-city is thin**: `destinations[]` is a flat tag list and `activities`
hang off a *global* `day` number, so nothing ties activities to a city. The opportunity is to
turn the trips workspace into a place where a **persistent chat**, a **visual plan**, and a
**city-aware model** reinforce each other.

### Goals
- Iterate on an **entire plan** conversationally, with the chat sitting **next to the plan**.
- **Visualize** the plan and edit its individual aspects easily.
- Make the tool genuinely friendly to **multi-city / multi-country** trips.
- Preserve the existing posture: **local-first, no accounts, offline-capable**, switchable
  `auto | local | byok` AI. (Same ethos as Ryan's Boomin Beats.)

### Audience
Single user (Ryan) planning real trips, primarily wide-screen desktop; the app must still
degrade gracefully on narrow widths.

### Constraints
- **Local-first**: `localStorage` only (`trippin.trips.v1`, `trippin.settings.v1`), no backend DB.
- **Node 18.17** — React 18 / Vite 5 / Tailwind 3 pinned; do not pull Tailwind 4 / newer create-vite.
- AI is switchable; the local path is `claude -p --agent scout --output-format json` (read-only
  helper that emits JSON — the **client** applies changes, so no tool-use infra required).
- Must **migrate** existing localStorage trips (flat `activities[].day`) without data loss.

---

### Decided directions (locked via brainstorm)
- **Chat model → Agentic edits + undo.** Chat returns structured *patches* the app applies to
  the plan live, with a preview and an undo stack.
- **Visualization → Segmented timeline only (fully offline).** No real map provider; a
  city-banded, day-by-day board. (Real map / schematic route explicitly deferred.)
- **Layout → Three-pane: plan | timeline | chat**, collapsible; tabs on narrow widths.
- **Prerequisite → Segment-backbone data model (Direction C).** Both the timeline and the
  city-aware chat depend on it, so it's treated as settled, not optional.

### Ideas & Directions

#### C · Multi-city data model (the backbone — build first)
Introduce **segments (legs)** as the primary structure:
`segment = { id, city, country, arrive, depart, nights, order, lodging, notes }`.
- Activities gain `segmentId` (nullable = unassigned) and keep a **global trip `day`** (1..N);
  each segment spans a contiguous day range derived from `order` + `nights`/dates, so a card's
  `day` tells you both its band and its slot.
- `flights[]` become **inter-segment travel legs** (from-segment → to-segment) that render as
  connectors between bands.
- Per-segment rollups: nights, activity count, cost sum.
- **Migration** (`v1 → v2`): `stops[]` → `segments[]`; if no stops, seed one segment per
  `destinations[]` entry; existing activities bucket into whichever segment covers their `day`.

#### A2 · Agentic chat editing
Persistent, **per-trip** chat (`trippin.chat.<tripId>` in localStorage). The model receives the
current plan + conversation and returns a **patch document**:
`{ ops: [ { op: 'add'|'update'|'remove'|'move'|'reorder', target: 'activity'|'segment'|'field', ... } ], reply }`.
- Client computes a **diff preview**, user confirms (or auto-applies with one-click **undo**).
- **Undo stack** = prior trip snapshots (bounded depth).
- Tolerant parser (reuse `parseItinerary` posture) so scout's JSON-in-prose still applies.
- Keeps the old "draft a full itinerary from scratch" as one supported op set.

#### B1 · Segmented timeline (the visualization)
City-banded board: one band per segment (in `order`), showing its day range and day columns;
activity **cards** grouped by day. v1 = render + click-to-edit; **drag-between-days/segments**
is a fast follow. Travel legs shown as connectors between bands. Fully offline.

#### D · Three-pane layout
`plan (form) | timeline | chat`, each collapsible; on `< lg` collapse to tabs with chat dockable.
Reuses existing `TripEditor` as the "plan" pane; timeline and chat are new.

### Recommendations
1. **Build C first** — nothing else renders well without segments. Ship the migration with it.
2. **A2 patch protocol before the fancy chat UI** — get apply + preview + undo solid on a plain
   input, then dress it as chat.
3. **B1 read-only timeline first, drag second** — value lands early; DnD is additive.
4. Bump the storage key to **`trippin.trips.v2`** with a one-time migrate-on-load shim.

### Suggested decisions (confirm before / during `/plan`)
- **Auto-apply vs. confirm-each** for agentic edits (recommend: auto-apply + always-visible undo).
- **Undo depth** (recommend: last ~20 snapshots, in-memory + last-state persisted).
- **Drag-and-drop in v1 or v2** (recommend: v2).
- **Day semantics**: keep global `day` (recommend) vs. `dayInSegment`.

### Open Questions (for `/plan` to resolve)
- Exact **patch-op schema** and the scout **prompt** that reliably emits it (+ parser tolerance).
- Snapshot/undo strategy and where it lives (memory vs. localStorage).
- How **travel legs** render and edit on the timeline.
- Whether **budget/cost rollups** get their own visualization in this pass or later.
- Migration edge cases (trips with activities whose `day` exceeds derived segment ranges).

### Next Steps — what `/plan` needs
1. Finalize the **v2 trip schema** (segments + activity.segmentId) and the **migration** shim.
2. Specify the **patch-op protocol** + updated `aiClient` / server prompt for conversational edits.
3. Define the **three-pane layout** contract and the **timeline** component's props.
4. Sequence into milestones: **M1 model+migration → M2 patch/undo engine → M3 timeline →
   M4 chat UI + three-pane → M5 drag-and-drop.**

---

## 2026-09-06 · Proposal → Plan lifecycle

### Problem / Opportunity
Today everything is one flat **Trip** — loose vibe fields (destinations, interests, pace, rough
budget) sit right next to committed specifics (hard dates, flight carrier/confirmation, lodging).
There's no line between "kicking an idea around" and "this is the actual booked trip," and no way
to explore variants of the same trip. We want a lifecycle: **idea → proposal → plan**, where a
**proposal** is the general concept you iterate on, and a **plan** is a committed, concrete version
escalated from it.

### Goals
- A clear **proposal** (general) vs **plan** (committed specifics) distinction.
- Workflow: idea → iterate into a proposal → **escalate** into one or more plans.
- A proposal can spawn **multiple plans** ("May version" vs "September", "budget" vs "splurge").
- Reuse the M1–M5 workspace (segments, agentic ops, undo, timeline, chat) — don't rebuild it.

### Audience
Same single user (Ryan), planning real multi-city trips; wants to compare committed variants of
one concept without losing the general proposal.

### Constraints
- Local-first, `localStorage` only; switchable `auto|local|byok` AI; Node 18.17 / React 18 / Vite 5.
- Must migrate existing v2 trips with **no data loss**.
- Scope tightly to the lifecycle — reuse existing components; no whole-app redesign.

### Decided (locked via this brainstorm)
- **Separate linked records (B)**: a Proposal is its own record; Plans are their own records, each
  with a `proposalId` back-reference. One proposal → many plans.
- **Escalation = snapshot copy**: a new Plan deep-copies the proposal's shared fields (segments,
  interests, pace, budget, notes) with **regenerated ids**, then is fully independent. A
  "refresh from proposal" action is deferred (later milestone).
- **Navigation = proposals top-level, plans nested**: sidebar lists proposals; opening one shows
  its plans. Ideas now promote to **Proposals** (not straight to a plan).

### Ideas & Directions

#### 1 · Unified schema, discriminated by `kind` (recommended core)
Keep Proposal and Plan as the **same underlying record shape** with a `kind: 'proposal' | 'plan'`
discriminator and (on plans) `proposalId` + `variantName`. Proposals simply leave the committed
fields blank (segment `arrive/depart`, flight `carrier/confirmation`, lodging specifics, hard
`startDate/endDate`). **Why:** the entire M1–M5 engine (segments, `applyOps`, undo, timeline,
`PlanChat`) already operates on that shape — one schema means the whole engine is reused with
near-zero rework. The proposal/plan difference becomes **UI field visibility + escalation +
prompt tone**, not a second data model.

#### 2 · Storage & migration (v2 → v3)
One collection (`trippin.trips.v3`) holding both kinds; plans carry `proposalId`. Migration:
each v2 trip → a **Proposal**; if it shows *committed signals* (hard dates, or any flight/lodging
specifics) → also spawn one **Plan** snapshot child so nothing committed is demoted or lost. Keep
the v2 key as a backstop. Per-trip chat stays keyed by record id (proposals keep their id; new
plans start with an empty thread).

#### 3 · Editing surfaces per phase
- **Plan** → the existing three-pane workspace unchanged (dates, flights, lodging, timeline, chat, undo).
- **Proposal** → the *same* `TripEditor`/`Timeline`/`PlanChat`, with committed-only sections
  **hidden when `kind==='proposal'`** (no hard dates, no flight confirmations, no lodging specifics).
  The timeline already works from relative day ranges (nights), so it renders for proposals as-is.

#### 4 · Escalation flow
On a proposal: **"Create plan"** → name the variant (e.g. "September trip"), optionally set a start
date / range → creates a Plan (kind=`plan`, `proposalId`, snapshot with regenerated ids) and opens
the plan workspace. Repeat for more variants.

#### 5 · Agentic chat, kind-aware
Reuse the ops engine untouched (it edits a record by id). Branch the `editPlan` prompt on `kind`:
proposal chat stays **general** (no inventing hard dates/bookings); plan chat may commit specifics.

### Recommendations
1. **Unify on one schema** with `kind` + `proposalId` — the lever that keeps this small.
2. **Snapshot escalation** with regenerated ids; defer "refresh from proposal."
3. **Nested IA**; ideas promote to proposals; retire the flat "Trips" label.
4. **Reuse** TripEditor/Timeline/PlanChat, gating committed fields behind `kind`.
5. **Migration**: Proposal + conditional Plan snapshot; v2 backstop.

### Suggested Decisions (confirm before / during `/plan`)
- Unified single-schema + `kind` discriminator (recommend yes) vs two distinct schemas.
- Migration: Proposal + conditional Plan (recommend) vs Proposal-only.
- Proposal-level status: **skip** it (recommend) vs a light draft/ready flag. (`status` enum stays a *plan* sub-status.)
- Escalation requires dates? Recommend **optional** — create the plan, fill dates after.

### Open Questions (for `/plan`)
- Exact field partition: which fields are proposal-visible vs plan-only.
- Proposal editor = trimmed `TripEditor` (recommended) vs a new component.
- `editPlan` prompt branching for `kind`.
- Plan variant metadata (name, optional season/tag).
- Migration heuristic: precisely what counts as a "committed signal."

### Next Steps — what `/plan` needs
1. Confirm unified-schema + migration approach.
2. Define the **v3 record model** (`kind`, `proposalId`, `variantName`) + field partition + storage.
3. Specify **nested navigation/IA** and the **escalation** action contract.
4. Sequence milestones, e.g.: **N1 v3 model + migration → N2 nested IA + idea→proposal →
   N3 proposal editor (kind-gated fields) → N4 escalation (snapshot) → N5 kind-aware chat +
   polish.**

---

## 2026-09-06 · Live flight search (plan only)

### Problem / Opportunity
The plan's **Flights & travel** section is manual entry only. We want to **search real flights**
(routes, times, fares) and select an offer to fill a leg — turning a chore into a decision. Scoped
to **plans** (proposals carry no flights; the kind guard already enforces this).

### Goals
- From a plan, search real flight offers and **add a selected one to `flights[]`** in a click.
- Handle real itineraries (round-trips, connections), not just single one-way legs.
- Keep the API key **server-side**; browser never sees it.
- Graceful degradation: manual leg entry still works with no key / helper down / no results.

### Audience
Ryan, planning committed trips; wants realistic flight options + prices without leaving the app.

### Constraints
- **Deliberate posture shift (plans only):** proposals stay fully local/offline; a *plan* gains
  *optional* online search. Search requires the Node helper running (it already must for local AI).
- Flight APIs block browser-direct calls (CORS) and Amadeus uses OAuth2 → **server proxy required**.
- **HARD GUARDRAIL:** search + autofill ONLY. Never book, purchase, or enter payment/credentials.
  Selecting an offer just writes local `flights[]` legs.

### Decided (locked via this brainstorm)
- **Data:** search + prices (real offers).
- **Keys:** server-side proxy in `server/index.mjs`; browser calls `/flights/*`; key in `.env` (uncommitted).
- **Provider (recommended):** **Amadeus Self-Service** (free test tier, Flight Offers Search + Airport/City Search); Duffel / SerpApi as alternates — *verify current terms in /plan*.
- **Entry point:** inline search form in the Flights section first; **agent-chat search is a fast-follow**.
- **Offer mapping:** **flatten** each offer's segments into multiple `flights[]` legs (one per segment).

### Ideas & Directions

#### 1 · Provider + server proxy
Add endpoints to `server/index.mjs` (Vite already proxies `/ai → :8787`; add `/flights`):
- `POST /flights/search` → Amadeus Flight Offers Search (origin, dest, date, pax, optional return).
- `GET /flights/airports?q=` → Amadeus Airport & City Search for IATA autocomplete.
- Server caches the OAuth2 token (Amadeus tokens ~30 min) and reads `AMADEUS_CLIENT_ID/SECRET` +
  `AMADEUS_ENV` (test|prod) from `.env`. `/flights/health` reports configured/unconfigured.
- Respect rate limits (test tier is slow/limited): debounce, cap results, surface 429s cleanly.

#### 2 · Offer → flight-leg mapping
An Amadeus offer has `itineraries[].segments[]`. Flatten: each segment → a `flights[]` leg
`{ from, to, date, carrier, cost, notes }` with new ids. Carry the **total offer price** on the
first leg's `cost` (or a `notes` line like "Part of $520 round-trip"); keep departure/arrival times
and flight number in `notes`. `confirmation` stays empty (no booking). Consider a light optional
field or notes convention for booking-class/stops.

#### 3 · Inline search UI (v1)
A collapsible search panel atop the Flights section: origin/dest (with airport autocomplete),
date(s), travelers (default from trip), optional non-stop toggle → **results list** (carrier, times,
stops, price) → **"Add to trip"** appends the flattened legs (via the existing `add`/`flight`
patch op so it's undoable). Loading / empty / no-results / error / not-configured states.

#### 4 · Agent-chat search (fast-follow)
Once `/flights/search` exists, let PlanChat drive it ("find a cheap morning JFK→FCO on May 10"):
the helper exposes search to the scout agent (or the client interprets a search intent), results
come back, and the model proposes `add flight` ops the user applies. Deferred behind v1.

#### 5 · Failure & degradation
No key configured → panel shows a short "add `AMADEUS_*` to server/.env" hint, manual entry still
works. Helper down → same. No results / bad IATA → inline message, no crash. All search is additive;
nothing auto-replaces existing legs.

### Recommendations
1. **Amadeus + server proxy** with token caching; `/flights/search` + `/flights/airports` + `/flights/health`.
2. **Flatten offers → legs**, total price on the first leg, times/flight-no in notes.
3. **Inline form v1**, agent-chat search as a later milestone.
4. **Secrets in `server/.env`** (gitignored); never commit; document setup in README.
5. Keep it **additive + undoable** via the existing flight patch op; manual entry always available.

### Suggested Decisions (confirm in /plan)
- Amadeus vs Duffel vs SerpApi (recommend Amadeus; **verify current free-tier terms**).
- Extra leg metadata (stops/flight-no/times) as `notes` convention vs new `flight` fields (recommend notes for v1 to avoid a schema bump).
- Round-trip in one search (recommend yes — Amadeus supports it) vs two one-way searches.

### Open Questions (for /plan)
- Exact Amadeus request/response shape + test-vs-prod base URLs; token cache strategy.
- Airport autocomplete UX (debounce, min chars, caching common codes).
- Whether to persist the raw offer (for later re-pricing) or only the flattened legs (recommend legs only for v1).
- Rate-limit handling and result cap on the free tier.

### Next Steps — what `/plan` needs
1. Confirm provider + verify current terms; get test credentials.
2. Define `/flights/*` endpoint contracts + `.env` config + token cache.
3. Specify offer→legs mapping and the inline search UI contract.
4. Sequence milestones, e.g.: **F1 helper endpoints + token cache → F2 offer→legs mapping +
   flight patch op → F3 inline search UI (autocomplete, results, add) → F4 states/polish +
   README setup → F5 (later) agent-chat search.**

---

## 2026-09-11 · Cross-device sync (Supabase) — reverses local-first-only

### Problem / Opportunity
Trips live only in one browser's `localStorage` (per-origin), so they don't survive a browser
wipe and can't be reached from a second device (e.g. a phone). We want the **same trips on
laptop + phone**, while keeping the app's fast, offline **local-first** feel.

### Goals
- Access and edit the same trips across devices (laptop + phone).
- Keep **local-first**: the app stays fast/offline using `localStorage` as the working copy; a
  hosted DB is the durable, shared source of truth it syncs to.
- Minimal new surface — reuse the clean `loadTrips`/`saveTrips` seam in `storage.js`.

### Audience
Single user (Ryan) across their own devices. (Not multi-user sharing — but accounts give a clean
identity boundary and room to grow.)

### Constraints
- **Reverses a founding decision** ("local-first, `localStorage` only, no backend DB, no accounts").
  This is a deliberate pivot — record it in the plan's Decisions Log + architecture + README.
- Node 18 / React 18 / Vite 5 stack unchanged on the client.
- Cross-device ⇒ the store must be **hosted/reachable** (not the localhost helper or local SQLite).

### Decided (locked via this brainstorm)
- **Cross-device**, **local-first with the DB as backup/sync** (not fully server-only).
- **Accounts via Supabase Auth** + Postgres + row-level security; browser talks to Supabase
  directly (anon key is public by design; RLS enforces per-user access) — **no data backend to build**.
- **Deploy the web app** (static host, e.g. Vercel/Netlify) so any device loads it by URL.

### Ideas & Directions

#### 1 · Data model (Supabase Postgres)
One `trips` table, **one row per record** (proposal or plan): `id` (the app's record id),
`user_id` (`auth.uid()`), `kind`, `data` (**jsonb** — the whole trip record; the shape is already a
rich, versioned JSON object, so blob-store it rather than shredding into columns), `updated_at`
(timestamptz), `deleted` (bool tombstone). **RLS:** every row scoped to `user_id = auth.uid()`.

#### 2 · Auth (additive, preserves local-first)
Supabase Auth, **passwordless magic-link** recommended (no password to manage). Crucially,
**auth is optional**: logged-out ⇒ the app behaves exactly as today (pure local). Logged-in ⇒ the
sync layer activates. So we don't regress the local-only experience for casual use.

#### 3 · Sync engine (the real work)
Wrap the existing `storage.js` seam:
- **On login / load:** pull the user's remote rows, **merge with local by `updated_at`
  (last-write-wins per record)**, write the merged set to both local and remote.
- **On local change** (`saveTrips`): write `localStorage` immediately (unchanged), then **push**
  changed records to Supabase (debounced).
- **Deletes need tombstones** (`deleted=true` + `updated_at`) so a delete on one device isn't
  resurrected by the other's stale copy.
- **Realtime** (Supabase subscription for live multi-device updates) is a nice **later**
  enhancement; v1 = pull-on-login + push-on-change.
- Conflict model: **record-level last-write-wins** (field-level merge is out of scope).

#### 4 · Deployment
Build the Vite app to static assets, deploy to **Vercel/Netlify**; Supabase URL + anon key via env
(public, safe). This is what makes the phone able to load the app at all.

#### 5 · The helper ripple (headline decision) ⚠️
The deployed app can't reach the localhost `server/index.mjs`, so:
- **AI on the hosted app → BYOK** (Anthropic key, browser-direct; already built). The local
  `claude -p` helper stays a **local-dev convenience** — it cannot be hosted (it shells out to the
  user's own Claude Code).
- **Flight search on the hosted app → the Ignav helper must be hosted** (a small serverless
  function holding the Ignav key), **or flights are disabled on the hosted build**. This is the
  gnarliest scope question and must be decided in `/plan`.

#### 6 · Migration / first login
On first login on a device, **merge** existing local trips with whatever's already in the cloud
(same LWW rule), so nothing is lost and both devices converge.

### Recommendations
1. **Supabase browser-direct + RLS**, `trips` table as `jsonb` rows — least code, no data backend.
2. **Magic-link auth, additive** — logged-out stays fully local-first.
3. **Sync at the `storage.js` seam**: pull-merge-on-login + debounced push-on-change + tombstones + LWW.
4. **Deploy frontend to Vercel**; Supabase keys via env.
5. **v1 scope = trips only** (defer syncing ideas/brainstorm/chat).
6. **Helper ripple:** hosted AI = BYOK; **host the Ignav helper as a serverless function** (recommended) or defer flights on the hosted build.

### Suggested Decisions (confirm in /plan)
- Auth method: magic-link (recommend) vs email+password vs OAuth.
- Sync scope: trips only for v1 (recommend) vs also ideas/chat.
- Ignav helper: host it (serverless) now vs flights hosted-disabled for v1.
- Realtime live-sync: defer (recommend) vs include in v1.

### Open Questions (for /plan)
- Exact `trips` schema + RLS policies + indexes.
- Where login/account UI lives, and the logged-out→logged-in transition (first-login merge).
- Sync triggers, debounce interval, and tombstone lifecycle.
- Serverless hosting for the Ignav helper (Vercel function? Supabase Edge Function?) + where its key lives when hosted.
- Env/config split (Supabase public keys in the client build; Ignav secret server-side).

### Next Steps — what /plan needs
1. Confirm the suggested decisions (esp. the Ignav-helper hosting call).
2. Provision a Supabase project; define schema + RLS.
3. Specify the sync layer contract around `loadTrips`/`saveTrips` + first-login merge.
4. Sequence milestones, e.g.: **D1 Supabase project + schema/RLS + client → D2 auth (additive,
   logged-out stays local) → D3 sync engine (pull-merge / push / tombstones / LWW) + first-login
   migration → D4 deploy frontend + env → D5 hosted flights (Ignav serverless) / AI BYOK wiring →
   D6 (later) realtime live-sync.**

### 2026-09-11b · AI capability tiers — "sits on top of your CLI agent"
Refines the AI/helper model above (and cleanly resolves the "helper ripple"). Positions the app as
a GUI on top of a locally-installed agent CLI, with graceful fallbacks.

**Decided:**
- **AI-only gate (not a hard view-only tier):** manual create/edit of ideas, proposals, and plans is
  **always available** on any device with no agent and no key. Only the **AI features** —
  brainstorm chat, agentic proposal/plan edits, and itinerary drafting — require **either** a
  reachable **CLI agent** (local Claude Code helper) **or** a **BYOK** key.
- **Claude Code first, built to expand:** v1 detects/uses `claude -p` (as today); shape the helper
  so more agent CLIs can be added later without a rewrite.

**Tier signal:** already essentially computed — `isLocalAvailable()` (helper reachable + `claude`
present) OR a BYOK key ⇒ "AI enabled." The new work is having this **drive the UI**: when AI is
unavailable, disable/hide AI affordances (chat send, agentic-edit, draft) with a hint —
*"Enable AI: run a CLI agent locally, or add an API key in Settings"* — while leaving manual
editing fully functional.

**Extensibility shape (for later):** a small **agent registry** in the helper — `name → { cmd, args,
detect }` — with `/ai/health` reporting which agents are present and the engine routing to a chosen
one. v1 registry = `{ claude }`. Adding `gemini`/`codex`/etc. later becomes a registry entry, not a
rewrite.

**Distinctions to keep straight:**
- **Flight search is NOT AI-gated.** Inline search (F3) hits the Ignav helper directly; only
  *chat-driven* search (F4) rides the AI turn. So flight availability depends on the **Ignav helper
  being reachable** (hosted or local), independent of the AI tier.
- **Composition with cross-device:** identity/sync (Supabase accounts) = *whose* trips + *cross-device*;
  the AI tier = *can this device run AI*. They stack: phone loads the deployed app, signs in, edits
  manually + views synced trips, AI via BYOK; laptop with Claude Code gets AI free via the local agent.

**Open questions (for /plan):**
- Exactly which affordances are "AI" and get gated vs always-on (draft/chat/agentic-edit = gated;
  manual forms, timeline, DnD, add-leg = always on).
- Where the "enable AI" hint/CTA lives, and whether logged-in-but-no-AI differs from logged-out.
- Minimal helper shape that anticipates the agent registry without over-building for v1.
