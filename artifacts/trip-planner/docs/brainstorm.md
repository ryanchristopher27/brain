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
