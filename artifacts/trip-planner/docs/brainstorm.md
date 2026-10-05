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

---

## 2026-09-12 · Nocturne redesign + global assistant (desktop)

### Problem / Opportunity
The app works end-to-end but wears a plain slate/sky utility skin, and its AI lives *inside* the
plan pane. A Claude-design handoff ("**Nocturne**" system + expanded screens) reimagines Odyssai as
an **AI-first** product: a persistent, context-aware assistant beside every screen, a polished dark
identity, a map-centric Trip page, a signature dates-open flow, and richer Flights/Ideas/City views.
Crucially the handoff sits **on our existing architecture** (it ships our `pattern.md`; its
propose→apply→undo *is* our patch-ops + history), so this is a **UI/interaction redesign over the
engine we already have**, not a rebuild.

### Goals
- Adopt **Nocturne** (dark, low-chroma, single blurple accent) across the app.
- Make the assistant **always-present and context-aware** (desktop right rail on every screen).
- Add the handoff's screens/features: **map hero, day-by-day, dates-open date-finder, budget donut,
  weather strip, richer Flights, City/stop detail, Ideas grid.**
- **Reuse, don't rebuild** the engine: lifecycle, patch-ops/undo, local-first + Supabase sync, Ignav.
- **Desktop first**; mobile (tab bar + bottom sheet) a later phase.

### Audience
Ryan (primary), plus anyone he shares the deployed app with — now a visually finished product.

### Constraints
- Handoff `README.md` (in the design bundle) is the **source of truth** for values; `.dc.html` are
  references (ignore their "DC" runtime). Pull the exact token ramp from those files at build.
- Keep the whole existing stack intact (this is a layer над it); no regression to sync/auth/flights.
- Reconcile the demo's **one hardcoded Japan trip + fake ANA/ZIPAIR flights** → our **generic
  lifecycle + real Ignav**.

### Decided (locked via this brainstorm)
- **Full redesign**, scoped brainstorm→plan, **desktop first**.
- **Full global assistant rail** — rearchitect the shell to top-bar tabs (Ideas·Trip·City·Flights)
  + a persistent 342px context-aware assistant rail; it's the evolution of `PlanChat`.
- **Data fidelity:** date-finder = **real Ignav**; budget donut = **real** (our costs);
  **weather strip = LLM-derived** (agent narrates seasonal norms → temps); **Ideas match-% =
  LLM-derived** (agent scores fit vs preferences). No weather API, no fake scores — agent-native.

### Ideas & Directions

#### 1 · Nocturne token layer (re-skin)
The theme lives centrally in `index.css` component classes (`.card`/`.btn-*`/`.chip`/`.field`) +
the Tailwind theme, and the app is already on **Inter** — so redefining tokens re-skins most of the
app for free. Rewrite those to Nocturne: `--color-bg #161826` (wrap `#0f1017`), `--color-surface`,
`--color-divider`, `--color-text #e9e9ed`, accent 100–900 (500 = `#9184d9`), neutral 500–800,
assistant panel `#13151f`; **outlined** primary buttons; muted text `rgba(233,233,237,.45–.78)`.
**Dark-only** — Nocturne commits to one visual world, so drop the light-theme machinery. Add
**Phosphor** icons (new dep). Sweep the handful of hardcoded `slate-*/sky-*` utility usages.

#### 2 · Shell rearchitecture — top-bar tabs + global assistant rail (the big one)
Replace the sidebar + `mode` state with: a **top bar** (brand · breadcrumb · tab group · dates-status
pill), a **main content area** that routes on a `page` state (`ideas|trip|city|flights`), and a
**persistent assistant rail** (`342px`, `#13151f`) on every screen. The rail is `PlanChat` evolved:
**context-aware** (subtitle + suggestion chips per page), still answering + proposing edits.
**Proposal cards = our `applyOps` + `history`** (ops list is display metadata; Apply runs the effect,
Undo reverts) — the handoff's contract already matches ours. Assistant is `aiAvailable`-gated as today.

#### 3 · Trip page
Map hero (Leaflet route map) → day-by-day (segments as day cards, click a city → City page) →
flights section (dates-open two states) → viz row: **budget donut** (real, from flight + activity
costs via `conic-gradient`) + **weather strip** (LLM-derived seasonal temps).

#### 4 · Dates-open flow (signature)
Our **`lengthDays`** already models "planned by length." When no `startDate`: show the open-dates
banner + a **date-finder** — the same round-trip priced across a departure window as a bar chart
(**real Ignav**, cache the window). **Locking a departure sets `startDate`** and fills flights +
budget everywhere. Header pill toggles dashed "Dates open · N days" ↔ solid "{dep – ret} · Change."

#### 5 · Maps (Leaflet, new dep)
Dark OSM tiles via CSS filter `invert(1) hue-rotate(185deg) …`; dashed accent route polyline + glow
markers (Trip); POI markers (City). **Open question — geocoding:** segments are city names; the map
needs lat/lng. Options: **LLM provides coords** (agent-native, cache on the segment) vs OSM Nominatim
via the helper. Lean LLM-coords-cached for v1 to avoid another external dep.

#### 6 · Flights page
Restyle `FlightSearch` to the Nocturne flights page: route/date/travelers chips, **price-by-date
chart** (real Ignav), outbound/return lists, summary column. Reuses the Ignav layer + booking links.

#### 7 · City / stop detail
Per-segment page: POI map + overview + things-to-do / stay / food. Content is **agent-assisted**
(LLM fills suggestions) over our segment data. POIs need coords (same geocoding question).

#### 8 · Ideas page
Restyle brainstorm to the candidate grid: idea cards with **LLM match-%** badge, type tags, price/
best-month, Explore/Open actions → proposal/plan. Match-% is an agent call returning structured JSON.

#### 9 · LLM-derived data (weather + match-%)
New agent calls (editPlan-style, structured JSON out) for the weather strip (seasonal norms per
segment + month) and idea match scores. `aiAvailable`-gated; degrade gracefully (omit/neutral) with
no agent/key. Fits the agent-native identity and needs no new external API.

### Recommendations
1. **Token layer first** (R1) — re-skins the current app immediately, low risk, unblocks everything.
2. **Then the shell/rail** (R2) — the defining interaction and the biggest rearchitecture; do it
   behind the new top-bar shell so screens can be ported one at a time.
3. **Reuse the engine** — patch-ops/undo, Ignav, sync, lifecycle all stay; this is presentation +
   IA + a few agent calls.
4. **Two new deps only:** Leaflet + Phosphor. Dark-only (drop light theme).
5. **LLM-coords-cached** for maps in v1; Nominatim as a fallback if needed.

### Suggested Decisions (confirm in /plan)
- Dark-only Nocturne (drop the light-theme tokens) — recommend yes.
- New deps Leaflet + Phosphor — recommend yes.
- Map geocoding: LLM-provided coords cached on segments (recommend) vs Nominatim.
- Date-finder window size (e.g. 7 days) + Ignav caching budget.
- Mobile explicitly deferred to a later phase.

### Open Questions (for /plan)
- Exact Nocturne ramp values (extract from the `.dc.html`).
- Per-page assistant context: subtitles, suggestion-chip sets, and how "current page" is passed.
- Geocoding approach + where coords are stored/cached.
- Not-yet-designed states the handoff flags: empty/loading/error, booking hand-off, mobile City.
- How Ideas cards map to our idea/proposal records (Open → existing promote-to-proposal).

### Next Steps — what /plan needs
1. Confirm the suggested decisions (deps, dark-only, geocoding).
2. Extract the exact Nocturne tokens + type scale from the handoff HTML.
3. Define the shell contract (page router + top bar + global rail + assistant context API).
4. Sequence, e.g.: **R1 Nocturne tokens/icons → R2 shell + global assistant rail → R3 Trip page
   (map hero + day-by-day + budget donut) → R4 dates-open date-finder (real Ignav) → R5 Flights
   page → R6 City detail → R7 Ideas grid + LLM match-% + weather → R8 polish + missing states.**
   (Mobile = a separate later phase.)

---

## 2026-09-12 · Inter-city transportation ("how you get there")

### Problem / Opportunity
A trip knows its **cities** (segments, ordered, with coords) and the map draws a dashed line
between them — but that line carries no **mode, time, or cost**. The only travel concept,
`flights[]`, is air-specific and lumped in one "Flights & travel" section, not tied to the actual
A→B hops. So "how do I get from Tokyo to Kyoto?" has nowhere to live. We want the *how* of each
hop visible on the main page.

### Goals
- Represent each **hop** between consecutive stops with a **mode** (flight / train / bus / car /
  ferry / walk), duration, cost, and (for flights) booking.
- Make the *how* obvious on the main surfaces: **connectors between day cards**, **mode-styled map
  legs**, and a **"Getting around" list**.
- Let the trip know where it **starts and ends** (home origin/return), so the first/last hops and
  flight search have a real origin.
- Stay agent-native + local-first: LLM-derive ground transport (cached), Ignav for flights,
  manual override everywhere.

### Audience
Ryan + anyone he shares a trip with — the plan should read like an itinerary, travel included.

### Constraints
- `flight` is baked into the model (patch op target `flight`, migration defaults, PLAN_ONLY_FIELDS,
  aiClient op protocol) → generalizing needs a migration + protocol update, done carefully.
- No free real-time train/bus API worth integrating → ground transport is **LLM-estimated**
  ("typical" mode/duration/rough cost), same fidelity posture as weather/coords.
- Hops are between **adjacent** segments; the assistant can reorder the route, so legs must survive
  reordering.

### Decided (locked via this brainstorm)
- **Direction A** — generalize `flights[]` into a single **`travel[]`** array of legs, each with a
  `mode` (flight is one mode). One model, one "Getting around" section.
- **Trip start/end location** — add a home **origin** and **return** location to the trip; the
  first hop is origin→stop 1 and the last is stop N→return (return defaults to origin).
- **Non-flight transport = LLM-derived** (cached on the leg); flights stay real via Ignav; manual
  override always.

### Ideas & Directions

#### 1 · Data model — `travel[]` legs with `mode`
Rename `flights[]` → `travel[]`. Leg shape keeps the durable flight snapshot fields and adds:
`mode` ('flight'|'train'|'bus'|'car'|'ferry'|'walk'|'other'), `fromSegmentId`/`toSegmentId`
(linking the hop to the transition; sentinel `origin`/`return` for the home bookends), and the
existing from/to/date/carrier/times/duration/cost/bookingUrl/notes. Migration: existing
`flights[]` → `travel[]` with `mode:'flight'`. Patch op target `flight` → `travel` (with a
back-compat alias so old/loose model replies still land). PLAN_ONLY_FIELDS: `flights` → `travel`.

#### 2 · Trip start/end location (home)
Add `startLocation` and `endLocation` to the trip: `{ name, iata?, lat?, lng? }` (coords/IATA
LLM-derivable, like segment coords). `endLocation` defaults to `startLocation` (round trip).
Feeds: default **origin for flight search / date-finder**, **home markers** on the map, and the
**bookend hops** in Getting-around. General enough to live on proposals too (rough), with committed
times/cost plan-only.

#### 3 · Hop keying + reorder safety
Store each leg by `(fromSegmentId → toSegmentId)`. At render, resolve the leg for each **adjacent**
ordered pair; a pair with no stored leg is "unknown" → lazily derived. A reorder changes adjacency:
new pairs derive fresh legs, orphaned legs are harmless (optionally GC'd on save).

#### 4 · Data source (fidelity split)
- **Flights** → real Ignav (already wired; Getting-around's flight hops keep the search + booking).
- **Ground hops** → `deriveTransport(fromCity, toCity)` (LLM): `{ mode, durationMinutes, cost,
  note }`, cached on the leg — mirrors weather/coords. The agent also **infers the default mode**
  per hop (short intercity → train; ocean crossing → flight).
- **Manual override** — set mode/times/cost by hand per hop.

#### 5 · Display — day-card connectors (primary)
Between consecutive day-by-day cards, a small **connector**: mode icon + duration (`🚄 2h15`),
click → the hop's detail / search. Most literal answer to "how you get there," right in the flow.

#### 6 · Display — mode-styled map legs + home markers
Per-mode polyline styling (train solid, flight dashed, drive dotted) with a mid-line chip
(`🚄 2h15`); distinct **home** start/end markers. Makes the hero self-explanatory.

#### 7 · Display — "Getting around" section (evolved Flights & travel)
Each hop as a row (incl. home bookends): mode icon · from→to · duration · cost · per-hop action
("search flights" for air, "how do I get there?" to (re)derive ground). Replaces the flat flights
list; flight search + booking live here per-hop.

#### 8 · Editing
Manual mode/times/cost/booking per hop (TripEditor + a Getting-around inline editor); start/end
location fields; assistant ops can add/update/remove travel legs and set mode.

### Recommendations
1. Land the **model + migration** first (flights→travel, mode, start/end location) so everything
   else builds on it without churn.
2. Then **LLM-derive + lazy auto-fill** hops (cached), Ignav unchanged for air.
3. Ship display in impact order: **day-card connectors → map legs → Getting-around list**.
4. Keep the proposal/plan fidelity split (mode + rough duration on proposals; times/cost/booking on
   plans).

### Suggested Decisions (confirm in /plan)
- Leg keying by segment-pair (recommend) + orphan GC on save.
- Home location shape `{ name, iata?, lat?, lng? }`; `endLocation` defaults to `startLocation`.
- Whether a hop's duration affects the day math (recommend: **no** for v1 — display only).
- Op-protocol back-compat: accept both `flight` and `travel` targets during transition.

### Open Questions (for /plan)
- Migration details (flights→travel; keep localStorage keys) + escalation copying `travel`.
- IATA resolution for home + segments (LLM-derive nearest airport vs. user-entered).
- Icon set (Phosphor: AirplaneTilt, Train, Bus, Car, Boat, PersonSimpleWalk) + map leg styling.
- Do bookend home hops appear on proposals, or plans only?

### Next Steps — what /plan needs
Sequence, roughly: **T1 model+migration (travel[]+mode, start/end location) → T2 LLM-derive +
lazy auto-fill hops → T3 day-card connectors → T4 mode-styled map legs + home markers →
T5 Getting-around section (per-hop flight search/booking) → T6 editing + polish.**

---

## 2026-09-12 · Real accounts (password + Google, magic link as backup)

### Problem / Opportunity
Auth today is **magic-link only** (`supabase.auth.signInWithOtp` in `App.jsx`; a tiny `Account`
popover). It works but forces an email round-trip every time and doesn't feel like "an account you
log into." We want real accounts: **email + password** and **Google (OAuth)** as the primary ways
in, keeping **magic link** as a backup. Everything else — RLS, the sync engine, local-first — is
unchanged; a logged-in user is a logged-in user regardless of method.

### Goals
- Sign up / log in with **email + password**.
- One-click **Google** sign-in.
- Keep **magic link** available as a secondary option.
- A real **auth screen** (log in / create account) + a signed-in **account menu** (sign out,
  change password).
- No regression: signed-out = pure local; existing magic-link users carry over (same email = same
  Supabase user, so their synced trips just work).

### Audience
Ryan + anyone he shares the deployed app with — returning users who want to just log in.

### Constraints
- Build on existing **Supabase Auth** (already wired) — no new backend.
- OAuth + password-reset links need **redirect-URL allow-listing** (same localhost/Vercel step as
  magic links). Google provider must be enabled in the Supabase dashboard.
- **Email confirmation** is a Supabase project toggle (default: keep ON — verified emails; reset
  needs working email anyway).
- Assistant caveat: the auth UI is built by us, but real credentials/sign-up are user-performed;
  dashboard settings (providers, redirect URLs, confirm toggle) are user-run.

### Decided (locked via this brainstorm)
- **Primary methods: email+password + Google OAuth.** Magic link kept as a backup option.
- Default **email confirmation ON** (flip in dashboard if we want instant sign-up).

### Ideas & Directions

#### 1 · Auth flows (Supabase)
`signUp({ email, password, options:{ emailRedirectTo } })`, `signInWithPassword({ email, password })`,
`signInWithOAuth({ provider:'google', options:{ redirectTo } })`, `resetPasswordForEmail(email,
{ redirectTo })`, `updateUser({ password })`. Keep `signInWithOtp` for the magic-link fallback.
Session persistence + auto-refresh are already handled by the client — the win is the login *flow*.

#### 2 · Auth UI (the new surface)
A proper **auth modal/screen**: tabs **Log in / Create account**; a **Continue with Google** button;
email + password fields (show/hide); **Forgot password** (sends reset email); a subtle **"email me a
magic link instead"** fallback; clear inline error/success states (bad password, unconfirmed email,
rate limit). Replaces the tiny `Account` popover's form (the top-bar entry point stays).

#### 3 · Signed-in account menu
The cloud/account control becomes a small menu: email/display name, **Sign out**, **Change
password** (`updateUser`), and (later) "sign out everywhere." Optional display name/avatar is a
stretch.

#### 4 · Config + carry-over
Enable Google in Supabase; allow-list redirect URLs (localhost:5173/5174 + Vercel) for OAuth +
reset; decide the email-confirm toggle. Existing magic-link users: setting a password for the same
email attaches to the same user (trips carry over) — verify.

### Recommendations
1. Land the **flows** in the supabase/App layer first (additive to magic link).
2. Build the **auth modal** as the main deliverable (this is where the UX lives).
3. Add the **account menu** (sign out + change password).
4. Do **dashboard config + end-to-end verify** last (user-run steps + a real login test).

### Suggested Decisions (confirm in /plan)
- Methods: password + Google primary, magic link backup (locked).
- Email confirmation: keep ON (recommend) — reset needs email regardless.
- Providers: Google only for v1 (Apple/GitHub easy later).
- BYOK keys/settings stay **device-local** (not per-account) for now.

### Open Questions (for /plan)
- Password rules/strength UI (min length via Supabase; surface a hint).
- Reset-password landing: a dedicated in-app route/screen vs. Supabase-hosted.
- Whether to show a first-run "create account" nudge or keep auth opt-in.

### Next Steps — what /plan needs
Sequence, roughly: **U1 auth flows (password + Google + reset; keep magic link) → U2 auth modal
(log in / create account / Google / forgot / magic-link fallback) → U3 account menu (sign out,
change password) → U4 dashboard config + redirect URLs + end-to-end verification.**

---

## 2026-09-19 · Pricing & monetization (public launch)

### Problem / Opportunity
For a **public** launch, the app fronts real LLM cost for any user who doesn't bring their own
key. Non-AI features are ~free (local-first), but the AI — proposals, plans, and a high volume of
background derived-data calls — costs money per use. We need a monetization model that (a) lets
people try the magic, (b) lets power users bring their own key at zero cost to us, and (c) charges
sustainably for managed AI, without an unbounded-spend hole. A public server key with no metering
gets drained in a day.

### Goals
- Make managed AI a viable paid product with **positive unit economics** and **no uncapped spend**.
- Keep a **generous free taste** so the funnel stays wide (local-first app is free forever).
- Preserve **BYOK = free & unlimited** as the power-user pressure-release valve.
- Support the future **iOS app**, where there's no local `claude -p` escape hatch → managed tier.
- Reuse what exists: Supabase accounts/JWT, the `api/ai/*` serverless seam, per-record caching.

### Audience
- **Casual planners** (majority): 1 trip every few months, bursty. Want it to "just work." → managed.
- **Power/dev users** (desktop): already have a Claude subscription or API key. → BYOK / local CLI, free.
- **Mobile users**: no CLI, keychain-BYOK is awkward. → funnel to managed (strengthens economics).

### Constraints
- Usage is **bursty** (plan hard for days, quiet for months) — argues against pure monthly subs.
- Solo/early operator — payments + tax compliance overhead matters; prefer lower-ops options.
- One "proposal"/"plan" = **many** LLM calls (reasoning + geocode + weather + match% + transport).
- Stripe-style fees (~2.9% + 30¢) make tiny purchases uneconomic.
- BYOK secrets must **not** be custodied server-side (liability) — keep client-side/direct.

### Decided (leaning, via prior session discussion — confirm below)
- **Three-layer model**: non-AI free forever · BYOK free & unlimited · managed AI metered/paid.
- **Auth-gate + meter every managed call** through the Supabase JWT + `api/ai/plan.js` seam.
- **Model split**: cheap model for background calls, premium for reasoning; behind a **gateway**
  (Vercel AI Gateway / OpenRouter) with **hard spend caps** + caching.

### Ideas & Directions

#### 1 · Metering unit — internal tokens, external "credits"
Track true cost internally (tokens × model price). Expose a simple abstraction to users: **credits**
(or "planning actions"). One proposal/plan spends multiple internal calls but should read as a
predictable, chunky amount to the user. Meter **on success / tokens actually returned** — never
charge for a failed or unparseable call. Show an estimate before big actions ("~3 credits") for
trust. Open: fixed "action" pricing (simple, predictable, risks under-charging heavy trips) vs
true metered credits (fair, but variable and harder to predict).

#### 2 · Tier structure — free allowance → credits (subscription optional)
- **Free tier**: a monthly managed-AI allowance sized near **one full trip** — enough for the aha,
  not enough to abuse. Resets monthly.
- **Credit packs (primary)**: buy N-trips-worth; fits bursty usage (pay when planning). Packs sized
  above the Stripe-fee floor.
- **Subscription (secondary/later)**: a "pro/frequent traveler" tier only if demand shows up; don't
  lead with it. Bursty usage churns monthly subs.

#### 3 · Cost architecture (the supply side)
- **Shared cross-user cache** (biggest lever): derived data (weather-by-place-month, city coords,
  briefings) is identical across users → cache keyed on the *query*, not the user. The Nth planner
  of Paris pays ~nothing for shared facts.
- **Cheap/smart model split**: route background derived-data to a cheap model; reserve premium for
  proposals/plans. Keep a **quality floor** — if cheap output is bad (bad coords), fall back.
- **Gateway with caps**: Vercel AI Gateway (native to our deploy; budgets, caching, failover) or
  OpenRouter (one key, many models, easy cheap-model routing). Hard monthly spend cap either way.

#### 4 · BYOK handling + desktop-vs-mobile positioning
- **Keep BYOK client-side** (browser → Anthropic direct, as today). Don't pass keys through our
  server. Unlimited & free; zero cost to us; power-user valve.
- **Desktop**: local `claude -p` helper stays a free "power/dev path" (rides their Claude sub).
  Framed as advanced, not mainstream.
- **Mobile (iOS)**: no CLI, keychain-BYOK is awkward → mainstream funnel is **managed/paid**. This
  is the intended economics, not a gap.

#### 5 · Payments & compliance
- **Stripe direct**: max control, lower %, but we own tax (Stripe Tax helps) and more integration.
- **Merchant-of-Record (Paddle / Lemon Squeezy)**: they become seller of record and handle global
  VAT/sales tax — much less ops for a solo global launch, higher %. **Likely the right early call.**
- Credit packs must clear the fee floor; consider credit **expiry** policy (fairness + rev-rec).

#### 6 · Abuse & enforcement
- **No sign-in, no managed AI** — every managed call carries the Supabase JWT; server checks
  balance, decrements, logs tokens. 402 when out.
- **Per-user + global rate limits** and the gateway spend cap protect against runaway cost.
- **Free-tier multi-account abuse**: email confirmation is the first gate (have it); plan light
  device/heuristic checks rather than assuming honesty.

### Recommendations
1. **Ship the metering ledger first** — a Supabase-backed per-user balance + a usage log, enforced
   in `api/ai/plan.js`. Everything else (packs, tiers) sits on top. This also finally makes the
   server key safe to expose publicly.
2. **Put the serverless call behind a gateway** and add the **cheap/smart model split** +
   **shared cache** — the supply-side cost work that makes any price sustainable.
3. **Credits-first pricing** with a one-trip free allowance; subscription deferred.
4. **Use a Merchant-of-Record** (Paddle/Lemon Squeezy) for v1 payments to skip global tax ops.
5. **Keep BYOK client-side**; keep desktop CLI as the free power path; mobile → managed.

### Suggested Decisions (confirm in /plan)
- Metering unit: internal tokens, user-facing **credits** (lean); estimate shown before big actions.
- Tiers: **free allowance (≈1 trip/mo) + credit packs**; subscription later.
- Cost stack: **gateway + cheap/smart split + shared cross-user cache**, hard spend cap.
- Payments: **Merchant-of-Record** for v1 (vs Stripe direct) — confirm.
- BYOK: **client-side only**, never server-custodied.

### Open Questions (for /plan)
- Exact credit → action mapping (how many credits is a proposal? a full plan? a background call?).
- Free-allowance size + reset semantics; do purchased credits expire?
- Which cheap model for background calls (ties to provider research `348270`).
- MoR vs Stripe final call (fees vs ops); which MoR supports our regions/pricing shape.
- Shared-cache design: what's safe to share cross-user (facts yes; anything user-specific no).
- Quality-floor/fallback rule when the cheap model underperforms.

### Next Steps — what /plan needs
Rough sequence: **P1 metering ledger (Supabase balance + usage log, enforced in api/ai/plan.js;
makes the public server key safe) → P2 gateway + cheap/smart model split + shared cross-user cache
(supply-side cost) → P3 credit packs + Merchant-of-Record checkout → P4 free-tier allowance + rate
limits + abuse gates → P5 pricing/paywall UX (balance display, pre-action estimates, out-of-credits
flow) → (later) subscription tier.** Ties to tasks `bc5762` (pricing), `348270` (providers),
`aeaece` (serverless seam).

### Addendum (same session) — unit economics, metering shape, MCP entrypoint

**Unit economics (grounded in current Anthropic pricing — verify token sizes with `count_tokens`
during /plan).** Rates: Opus 5 $5/$25, Sonnet 5 $2/$10, Haiku 4.5 $1/$5 per MTok (in/out). Caching:
reads ≈ 10% of input price, writes ≈ 125% → caching the trip-context prefix cuts input ~90% on
turns 2+. Per-call estimates: reasoning (proposal/plan/chat edit) ≈ **$0.03 on Sonnet**, ~$0.07 on
Opus; background (weather/coords/match%/city/transport) ≈ **$0.003 on Haiku**. A full trip (~12
reasoning + ~34 background calls) ≈ **~$0.45 (Sonnet+Haiku)**, ~$0.90 (Opus reasoning); shared
cache drives the background portion toward ~$0. **Takeaway: a managed trip costs < $1.** A free
"1 trip/mo" tier is ~$0.50 CAC; a $5 pack covering ~3–5 trips has healthy gross margin even after
MoR/Stripe fees. Margins are wide → pricing is about packaging, not survival.

**Metering shape (decided-leaning):** meter the **free tier by COUNT — # prompts + # new
proposals/plans** (not tokens). Predictable, easy to explain, and it counts exactly the expensive
reasoning calls. Background derived-data calls are uncounted/absorbed (pennies + shared-cached).
Internally still log tokens for truth; users see e.g. "3 plans + 50 prompts left." Paid tier draws
the same countable units from a purchased balance.

**Payments (decided-leaning):** **Merchant-of-Record (Paddle / Lemon Squeezy)** for v1 — handles
global VAT/sales-tax registration + remittance (the real solo-launch pain), ~5% vs Stripe's
~2.9%+30¢. Stripe-direct only if wanting control/lower fees + willing to run Stripe Tax and own
registrations. Lemon Squeezy (Stripe-owned) is a clean on-ramp that can migrate to Stripe later.

**Direction 7 · MCP entrypoint (create trips from any chat client).** Expose the patch-op engine as
an MCP server (`create_proposal`, `add_segment`, `search_flights`, `apply_ops`) so users build trips
from Claude Desktop / any MCP client. Fits the AI-first identity; the op protocol is already a clean
tool API (near 1:1 mapping). Cost angle: reasoning runs in the user's own client on their
subscription → **near-zero AI cost to us** (BYO-LLM by another name; only storage + flight lookups
cost). Prereqs: **server-canonical data model** (Supabase as source of truth, not just localStorage)
and an **OAuth** story mapping the MCP session to a user account. Monetization: likely a paid/Pro
feature or metered on non-LLM costs; consistent with the BYOK "power users bring their own LLM"
philosophy. **Scope: later phase** (after core paid tier + server-canonical records). Candidate new
task.

**Open questions added:** MoR vs Stripe final call (fees vs control); exact free-tier counts (how
many prompts / plans per month); whether MCP entrypoint warrants server-canonical records sooner
(it's also useful for the iOS app and cross-device truth).

---

## 2026-09-26 · Flight-optimized trip planning (8517f3)

### Problem / Opportunity
Real fares work end to end (verified live 2026-09-26: DEN→LIS round trip → 38 itineraries, booking links
resolve, United direct first). But flights are searched in isolation: nothing uses the *shape* of the
trip to answer "which airports do I fly into and out of, on which dates?" The date-finder prices one
round trip over 7 departure days; the Flights page is a manual search.

### Goals
- Price the trip's two ends from its own shape: best way in to the first city and out of the last.
- Suggest dates (start + length) that make the whole trip cheaper, and show the tradeoffs.
- Keep fare lookups affordable and abuse-proof on the public site.

### Audience
Anyone planning a multi-city trip with a departure airport set (trip.startLocation / settings.home).

### Constraints
- Ignav: `POST /fares/search` takes 1–2 ordered legs with independent origin/destination → **open-jaw
  works**. No calendar/date-range endpoint → every (route, date) cell is its own search.
  Ignav quota/pricing not confirmed (pricing page is client-rendered) — open question.
- `/flights/*` on Vercel is **unauthenticated today**; an optimizer click can fan out to 20–60 searches.
- Local-first app; managed AI is credit-metered; the chat already applies undoable ops.

### Ideas & Directions
- **A. Book-end optimizer (core).** Compare round trip to the first city (+ ground backtrack from the
  last), open-jaw in-first/out-last (one 2-leg search), and optionally the reversed route. Each option:
  price + total travel time + stops + the extra ground leg (from existing hop estimates).
- **B. Gateway airports.** Per end, up to ~2 candidates: primary, same-metro alternates (LHR/LGW/STN),
  a nearby hub ≤ ~2h by ground. From a hub table + LLM proposal; capped for combinatorics.
- **C. Flexible dates.** Departure ±3 days × length ±1 → ~21 cells per route option, as a heat grid;
  locking a cell sets start + length together (dates editor already links them).
- **D. Reorder to fit gateways.** Suggest reversing / moving a hub-adjacent stop to an end, as an
  undoable AI edit. *Deferred past v1.*
- **E. LLM + fares.** Precomputed: a deterministic optimizer produces a compact fare summary the chat
  explains (cheap, testable, can't burn quota). Tool-style searches from the model: later, ≤1 per turn.
- **F. Cost & abuse control.** Sign-in required for live fares on the deployed site (same Supabase JWT
  check as /ai/plan); per-user daily search cap logged in usage events; shared server-side fare cache
  (Supabase, keyed route+dates+pax+cabin, ~6–12h TTL); one batch endpoint (`/flights/sweep`) that runs a
  grid server-side with bounded concurrency instead of N browser calls. Local helper stays unrestricted.
- **G. Freshness.** Cached prices labeled with age; re-verify on select (Ignav `price.status`); booked
  legs keep `priceAtSelection` (exists).
- **H. Intra-trip flight hops.** Out of v1 (per-hop search exists; later: "this 9h train has a $60 flight").

### Recommendations
v1 = **F → A → C + light B**, with **E precomputed**. D and H follow.

### Suggested Decisions (confirmed by user 2026-09-26)
- Fare access on the deployed site: **signed-in only**, per-user daily cap + shared fare cache; local
  helper unrestricted. No credits for sweeps in v1.
- v1 scope: **ends + dates + airports** — open-jaw vs round-trip, ±3-day × ±1-length grid, ≤2 airports
  per end, AI explains tradeoffs. Reordering later.

### Open Questions
- Ignav plan limits (searches/month, rate limit, cost per search) → sets the daily cap and grid size.
- Daily cap value, and whether anonymous visitors get a tiny taste (e.g. 3 searches/day by IP).
- Hub table source: curated JSON vs LLM-proposed + validated via `/flights/airports`.
- How "best" is scored: price only, or price + a time/stops penalty (user-tunable "cheapest ↔ easiest")?
- Where the optimizer lives in the UI: Flights page section, trip-page card, or both.
- Cache store: new Supabase table vs reusing ai_cache.

### Next Steps (what /plan needs)
Milestones roughly: FO1 flight gating + fare cache + sweep endpoint → FO2 book-end optimizer core
(pure, unit-tested option builder + scorer) → FO3 gateway candidates (hub table + LLM, capped) →
FO4 flexible-date grid UI + lock → FO5 chat integration (fare summary in context, tradeoff copy).

#### Addendum (2026-09-26) — pricing + accounts
- Ignav: first 1,000 requests free, then **$2 / 1,000** (~$0.002/search). A full 21-cell grid ≈ $0.04; a
  worst-case sweep (grid × 2 route shapes × 2 gateways ≈ 80 searches) ≈ $0.16; a 150/day cap bounds a
  heavy user at ~$0.30/day. The shared cache cuts most of it. Real risk is scripted abuse, not normal use.
- **No account wall for the app.** Accounts are required only for what costs us money (managed AI —
  already — and live fares on the deployed site). Rest stays open + local-first, with a "sign in to
  save & sync" nudge. Considered app-wide accounts (simpler gating, server-canonical data for iOS/MCP/
  chat history) — rejected for now: first-visit friction, contradicts the free local-first layer.
- **Backlog:** Supabase anonymous sessions (per-browser user id, upgradable to a real account) → a small
  signed-out "taste" (e.g. 3 fare searches / 2 AI turns), with IP rate limits or CAPTCHA.

## 2026-09-27 · Broader ideation: seasons, routes, options & versions (5705ac)

### Problem / Opportunity
Ideation today is narrow. A proposal becomes plans (whole-trip versions) by copying, but:
- Plans can't be compared.
- Weather is LLM-estimated highs.
- Each hop has one AI-chosen transport.
- Each city has one list of do/stay/food.

The brief asks for exploration: weather across seasons, wider travel options between cities,
browsable versions of stops and ordering, and alternatives for things to do, restaurants and stays.

### Goals
- Answer "when should I go?" with real climate data, per stop and for the whole route.
- Let a traveler see and compare different shapes of the same trip (cities, order, dates).
- Offer real choices inside a plan (how to get between cities, where to stay, what to do) without
  multiplying plans.
- Keep the audit, budget and assistant coherent: they only ever reason about what's picked.

### Audience
Travelers early in planning (proposal stage) who haven't fixed dates or a route. Secondarily,
travelers refining a plan who want to swap a hotel or a leg.

### Constraints
- The existing v4 record (`kind`, `proposalId`, `variantName`) and the ops / undo / audit engine.
  Changes must be additive and survive Supabase sync.
- Managed AI is credit-metered. Background calls run on gpt-oss-120b. Ignav searches cost
  ~$0.002 each.
- Must work at phone width (the phone polish pass just landed).

### Decided (via this brainstorm)
- **Two levels of alternatives, handled differently:**
  - Structural changes (stops, order, dates) → **plans**.
  - Contents (legs, stays, food, do) → **options on the item**: a shortlist with one picked.

  This avoids nested versions and a combinatorial explosion.
- **Versions = both** — quick throwaway alternatives to compare ("drafts" that aren't saved as
  plans), plus "Keep as plan" to promote any draft into a full plan that stays active alongside
  others.
- **Shortlists live on both proposals and plans**, with one pick per slot and swaps allowed anytime.

### Ideas & Directions

#### 1 · Season explorer (when to go)
- **Data:** real climate normals from Open-Meteo's historical archive (free, no key).
- **Per stop:** a 12-month strip with high/low, rainy days and sunshine.
- **Busy season:** a crowd hint from `holidays.js`.
- **Whole route:** a "Best: May, Sep–Oct" verdict.
- **Replaces** the LLM temperature estimate in `derive.js`: more accurate, and no AI cost.
- **Optional, on request only:** a fare-seasonality hint from a few sampled Ignav searches.

#### 2 · Travel options per leg
- Each hop holds 2–4 modes (train / bus / drive / flight) with time and cost ranges, and one picked.
- **Data:** flights come live from Ignav; ground transport comes from the LLM, as T2 does today.
- **Feeds:** the budget, the audit, and route comparisons.

#### 3 · Compare plans + quick versions
- **Compare:** plans and drafts side by side (stops, nights, dates, travel time, flight cost,
  weather fit, budget) with differences highlighted. On phones, swipeable cards.
- **Quick versions:** "Try a version where…" → the AI generates a draft. "Keep as plan" promotes
  it (reusing the snapshot escalation).

#### 4 · Route options
- "Other ways to do this trip" → 2–3 route drafts (fewer moves, coastal loop, add/swap a city).
- Each draft has a mini map, nights, total travel time and a rough cost.
- Shown in the compare view, reusing the fare optimizer's reversed-order search.

#### 5 · Shortlists for stays / food / things to do
- **Stays:** ~3 per city across price tiers (budget / mid / splurge), with one picked.
- **Food & do:** a candidate pool plus a planned set, with "Swap" and "More like this".
- **Assistant:** a new `pick`-style op so the assistant can change picks.

### Cross-cutting considerations
- **Cost:** alternatives are generated on request only, never automatically. They are
  credit-priced, with bulk generation on the background model.
- **Audit and budget** read only picked options; unpicked candidates are inert.
- **Size and sync:** cap options per slot (~5) and drafts per proposal (~3) so trip rows stay small.
- **Proposal vs plan tone:** exploration defaults to the proposal. In plans, picks feel settled but
  remain swappable.

### Recommendations (build order)
1. **Season explorer** — cheapest, most accurate, immediately useful at the proposal stage.
2. **Travel options per leg** — extends T2 and the flights work already built.
3. **Compare view + quick versions (drafts → Keep as plan)** — makes versions explorable.
4. **Route options** — plugs into the compare view.
5. **Shortlists** for stays / food / do.

### Suggested Decisions (confirm in `/plan`)
- Where drafts live: in the proposal record (recommended), not as plans until kept.
- Option shape: `options[]` + `pickedId` on travel legs and on POI slots — one shared pattern.
- Climate source: Open-Meteo archive, averaged over ~10 years and cached per coordinate.

### Open Questions (for `/plan`)
- Where the climate data is fetched and cached: the client straight from Open-Meteo, or the
  server with a shared cache.
- Credit price of "generate alternatives" (routes / drafts / shortlists).
- How the compare view handles more than 3 items on phones.
- Migration: do existing single-transport legs become a one-option list?

### Next Steps — what `/plan` needs
1. Data model for drafts and for `options[]` + `pickedId`.
2. Milestones, e.g. **BI1 season explorer → BI2 leg options → BI3 compare + drafts →
   BI4 route options → BI5 shortlists**.
3. The AI ops contract for generating and picking options.

## 2026-10-01 · One fluid trip + place/base stops + fixed-date anchors (#af9be2, #1858f1)

### Problem
- **Hard lifecycle.** A proposal and a plan are separate records; "Create plan" forks a snapshot that then drifts, starts a fresh chat, and is the only place dates, lodging, travel legs, activity times/costs, the date finder and Flights are allowed. To add a date or pick a hotel you must fork.
- **Stops assume "a city you sleep in".** Trips built around sights (Utah's Mighty 5) don't fit: Zion is visited but you sleep in Springdale; Capitol Reef is a half-day on a drive day (0 nights); Arches + Canyonlands share Moab. And lodging is plan-only, so "where do we sleep?" can't be explored early.
- **Fixed-date things** (a festival, a game, a wedding) have no way to anchor the trip.

### Decisions (user, 2026-10-01)
1. **One fluid trip.** No fork: a trip gains detail in place (idea → shaped → dated → booked → done) and every field can be filled whenever it's known. Its stage is derived from what's filled in. Versions remain optional alternatives — peers, one marked main.
2. **Place + base.** A stop is a place you go (city, park, region, event); it may name a separate base where you sleep ("sleeping in Springdale"), several stops may share a base (Moab), and a stop may be 0 nights (a day stop). City trips look exactly as today.
3. **Fixed-date anchors.** A stop or activity can be pinned to a date (and time); the date finder and the AI plan around anchors, and an anchor implies trip dates when none are set.

### Why this is cheaper than it sounds
Proposals and plans already share one record shape (`kind` + `proposalId`). The difference is gating (`PLAN_ONLY_FIELDS` etc.), the escalate fork, and per-kind prompts — so "fluid" is mostly removing restrictions; existing proposal + plans become versions of one trip with no data rewrite.

## 2026-10-01 · Research — real trip-data sources (#5c8933)

### Question
Which APIs/datasets give Trip Fairy real, verifiable places (things to do, stays, food), ratings/reviews, official links and booking links, to replace or validate today's AI-suggested places (city pages, BI5 shortlists, map layers, getting around)?

### Today
Places, prices and blurbs come from the LLM (derive.js city briefings) with coords checked against Nominatim; photos from Wikipedia/Openverse; getting-around from Wikivoyage + LLM; flights are real (Ignav, with booking links); climate from Open-Meteo.

### Candidates (checked 2026-10-01)
| Source | What it gives | Access & cost | Terms that matter | Fit |
|---|---|---|---|---|
| Google Places API (New) | Best coverage; ratings, reviews, photos, hours | Per-SKU free caps (10k Essentials / 5k Pro / 1k Enterprise per month), then e.g. Details Pro $17/1k, Enterprise (reviews+photos) $20/1k | Content **may not be shown on a non-Google map** (we use MapLibre; only Places UI Kit is exempt); only place_id cacheable indefinitely, lat/lng 30 days; Google logo + per-item attributions | Poor — conflicts with our map and caching |
| Foursquare Places API | 100M+ places; Pro fields (name, category, address, coords, phone, website); Premium (rating, price, hours, tips, photos) | 500 free Pro calls/mo (from 2026-06-01), then $15/1k; Premium $18.75/1k, no free tier | Storage/caching terms **not yet verified** | Good for validation (Pro) and on-demand detail (Premium) |
| Foursquare OS Places (dataset) | Same 100M+ POIs, 22 core attributes, monthly | Free, Apache 2.0, token via Places portal (Iceberg/Parquet) | Attribution | Good for bulk validation, but we'd host a lookup |
| Overture Maps Places | ~80M places (Meta, Microsoft, Foursquare, BrightQuery) with a confidence score | Free, CDLA Permissive 2.0 / Apache 2.0, monthly | No share-alike | Same as above; complementary |
| Tripadvisor Content → Terra API | Ratings, reviews, photos for 7.5M locations | Legacy 5k free/mo; Terra 1k free then undisclosed pay-as-you-go | AI/LLM use needs a signed order (legacy: internal testing only); only location_id cacheable; logos, link-backs, non-indexable display | Poor — Trip Fairy is AI-first |
| Yelp Fusion | Business data + reviews | $229–643/mo plans | US-centric | Poor — cost, coverage |
| OSM / Overpass | Free POIs, no ratings | Public instance: not for commercial apps (self-host or paid) | ODbL attribution, share-alike | Only via a hosted/paid instance |
| Wikivoyage | Curated see/do/eat/sleep listings with coords, prices, hours | Free (already used) | CC BY-SA attribution | Good free seed for places |
| Viator Partner API | Bookable tours & activities, availability | **Instant** basic API access with an affiliate account; free | 8% commission, 30-day window | Best for bookable things to do |
| GetYourGuide | Tours & activities | API needs ≥100k monthly visits; links via affiliate (7–8%, also through Travelpayouts) | — | Links only for now |
| Booking.com Demand API | Stays inventory + booking | Managed Affiliate Partner + account manager; partner registration paused | AI use needs written approval | Not reachable now |
| Expedia Rapid | Stays inventory + booking | Partner-only, approval + certification, months | — | Not reachable now |
| Stay22 | Stay deep links / maps / API across Booking, Expedia, Hotels.com, Vrbo | Self-serve; earns ~30% of Stay22's commission | — | Best for stay links + revenue now |
| Travelpayouts (network) | Links (some feeds/APIs) for Omio (6%), 12Go (4–5.5%), Hotellook (5–7%), GetYourGuide (8%), Klook | Self-serve | Per-brand API conditions | Good for train/bus/activity links |
| Rome2Rio API | Multimodal routes | Commercial agreement | — | Skip; keep Wikivoyage + estimates |

### Recommendation
1. **Validate first (R1):** run each AI-suggested place through Foursquare Pro (Place Match/search) — keep real ones with true coords, website and a stable id; flag or drop the rest. Cost at today's volume is inside the free 500/mo (≈20 lookups per city page; beyond that ≈$0.30 a city page). Seed places from Wikivoyage listings where a city has them. Bulk alternative later: an Overture / FSQ OS lookup we host.
2. **Book & earn (R2):** Viator API for bookable things to do on city pages (8%); Stay22 links on stays (Booking / Expedia / Vrbo); Omio / 12Go links on ground legs via Travelpayouts. Flights already link via Ignav.
3. **Enrich on demand (R3):** ratings, price, hours, photos from Foursquare Premium only when a place card is opened, stored only as its terms allow.
4. **Not now:** Google Places (non-Google-map clause, caching), Tripadvisor (AI-use restrictions), Yelp (cost/US), Booking Demand / Expedia Rapid (partner-gated), GetYourGuide API (traffic minimums), Rome2Rio (commercial agreement).

### Open before building
- Accounts the user signs up for: Foursquare developer, Viator affiliate, Stay22, Travelpayouts.
- Verify Foursquare's storage/caching terms (decides what we keep on the record).
- Disclosure: affiliate links need a short "we may earn a commission" note.

Sources: Google pricing (woosmap.com/blog/google-places-api-pricing), Google terms (developers.google.com/maps/documentation/places/web-service/policies, cloud.google.com/maps-platform/terms/maps-service-terms), Foursquare pricing (docs.foursquare.com/developer/reference/upcoming-changes, foursquare.com/pricing), FSQ OS Places (foursquare.com/resources/blog/data/evolving-fsq-open-source-places), Overture (docs.overturemaps.org/guides/places), Tripadvisor (tripadvisor.com/business/solutions/hotels/content-api, vorplabs.com/agent-tools/tripadvisor-content-api), Yelp (business.yelp.com/data/resources/pricing), Overpass (wiki.openstreetmap.org/wiki/Overpass_API), Viator (partnerresources.viator.com/travel-commerce/affiliate), GetYourGuide (partner.getyourguide.support/hc/en-us/articles/13981133907613), Booking (developers.booking.com/demand/docs/getting-started/prerequisites), Expedia (developers.expediagroup.com/rapid/setup), Stay22 (stay22.com/docs), Travelpayouts (travelpayouts.com/blog/train-affiliate-programs), Rome2Rio (apis.io/providers/rome2rio).
