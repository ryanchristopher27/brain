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
