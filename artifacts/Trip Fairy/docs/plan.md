# Plan — Trippin' Plan-Iteration Workspace

Date: 2026-09-05
Status: Draft
Brainstorm: [docs/brainstorm.md](brainstorm.md) (2026-09-05 section)

## Overview
Rebuild the **trips workspace** so a persistent chat, a visual plan, and a city-aware data model
reinforce each other. Today it's a centered scrolling form with a **one-shot** AI rail that
appends (and duplicates) on apply, no visualization, and only a flat notion of destinations. The
new workspace is a **three-pane** surface — editable plan · segmented timeline · agentic chat —
built on a **segment (leg) backbone** that makes multi-city/country trips first-class. Local-first,
offline, switchable AI posture is preserved throughout.

## Goals & Success Criteria
- **Iterate on the whole plan via chat next to it.** The chat remembers the conversation and
  returns *structured patches* that change the plan live, each with **undo**.
  - ✅ "Make day 3 lighter" / "swap Florence for Bologna" / "add a food night in Lisbon" visibly
    edit the plan, and one click reverts.
- **Visualize the plan.** A city-banded, day-by-day timeline renders segments and their activities.
  - ✅ A 3-city trip shows three bands with correct day ranges and activities under the right days.
- **Multi-city friendly.** Segments are the backbone; activities belong to a city; per-segment
  rollups (nights, cost, count).
  - ✅ Creating "Rome 3n → Florence 2n → Venice 2n" needs no manual day arithmetic.
- **No regressions to posture.** Fully offline, `localStorage` only, `auto|local|byok` intact,
  Node 18.17 / React 18 / Vite 5 / Tailwind 3 pinned.
  - ✅ Existing v1 trips load and migrate with zero data loss.

## Scope
### In Scope
- v2 trip schema: **segments[]** + `activity.segmentId`; `v1→v2` migration shim.
- **Patch-op protocol** + client applier with **preview + undo stack**.
- Conversational, **per-trip chat** persisted in `localStorage`.
- **Segmented timeline** component (read-only render first).
- **Three-pane layout** (plan | timeline | chat), collapsing to tabs on `< lg`.
- Updated `aiClient` prompt path for conversational edits (reuses generic `/ai/plan`).

### Out of Scope (this pass)
- Real geographic **map** / geocoding (deferred; would break pure-offline).
- **Drag-and-drop** on the timeline → M5, gated behind the read-only version landing first.
- Dedicated budget/cost **dashboard** (rollups shown inline; no separate viz).
- Server/helper changes beyond prompt content; accounts, sync, hosting.

## Tech Stack & Architecture
Unchanged stack: **React 18 + Vite 5 + Tailwind 3**, `localStorage`, `claude -p --agent scout`
(local) / Anthropic BYOK. Key architectural decisions:

- **Segments are the backbone.** `segment = { id, city, country, arrive, depart, nights, order,
  lodging, notes }`. Activities gain `segmentId` (nullable) and keep a **global trip `day`** (1..N);
  each segment owns a contiguous day range derived from `order` + `nights`/dates. Chosen over
  `dayInSegment` because it keeps "move a card" = "change one number" and avoids cross-segment
  renumbering. `flights[]` become inter-segment travel legs (from→to segment).
- **Client applies AI edits; the model only proposes.** scout is read-only and just emits JSON, so
  the reused `/ai/plan` endpoint is enough. The model returns
  `{ reply, ops: [ {op, target, ...} ] }`; a **tolerant parser** (same posture as `parseItinerary`)
  extracts it, a pure `applyOps(trip, ops)` reducer produces the next trip, and a bounded
  **snapshot stack** powers undo. Auto-apply + always-visible undo (no per-edit confirm dialog).
- **Migration on load.** Bump to `trippin.trips.v2`; a one-time shim maps `stops[]`→`segments[]`
  (or seeds one segment per `destinations[]` entry), then buckets orphan activities by `day` into
  the covering segment. Read v1, write v2, keep v1 key untouched as a backstop for one release.
- **Timeline is derived, not stored.** It computes bands/day-ranges from segments; no redundant
  state to keep in sync.

Primary modules (new/changed):
- `src/lib/trip.js` — v2 schema, `newSegment()`, segment↔day range helpers.
- `src/lib/migrate.js` — v1→v2 shim (new).
- `src/lib/patch.js` — patch-op types + `applyOps()` reducer (new).
- `src/lib/aiClient.js` — `editPlan(trip, messages)` conversational path + patch parser.
- `src/lib/storage.js` — v2 keys, per-trip chat persistence.
- `src/components/Timeline.jsx` — segmented board (new).
- `src/components/PlanChat.jsx` — per-trip agentic chat (new).
- `src/components/Workspace.jsx` — three-pane shell (new; wraps TripEditor + Timeline + PlanChat).
- `src/App.jsx` — mount Workspace in `trips` mode; wire undo stack.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| M1 | Segment model + migration | v2 schema (`segments[]`, `activity.segmentId`), helpers, `v1→v2` shim; TripEditor edits segments | — |
| M2 | Patch + undo engine | Patch-op protocol, `applyOps()` reducer, bounded snapshot undo stack, tolerant parser | M1 |
| M3 | Segmented timeline | Read-only city-banded, day-by-day board with per-segment rollups | M1 |
| M4 | Agentic chat + three-pane | Per-trip persistent chat, `editPlan()` prompt path, three-pane layout (tabs on narrow) | M2, M3 |
| M5 | Timeline drag-and-drop | Drag activity cards between days/segments → emits patch ops | M3, M4 |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Migration corrupts/loses existing trips | Med | High | Pure shim + unit-check on real localStorage dump; keep v1 key as backstop; migrate-on-read only |
| scout emits patch JSON unreliably | Med | High | Strict schema in prompt + tolerant parser; on parse-fail, show model's reply and apply nothing (never partial) |
| Auto-apply makes a bad edit | Med | Med | Always-visible undo; bounded snapshot stack; diff summary in chat before/after |
| Three-pane too cramped on laptop | Med | Med | Collapsible panes; tabs < lg; timeline as the collapsible middle |
| Global `day` drifts from segment ranges after edits | Low | Med | `applyOps` re-derives/clamps day ranges; helper is single source of truth |

## Dependencies
- Local helper running (`npm run ai`) or a BYOK key — unchanged.
- No new npm packages required for M1–M4 (DnD lib decision deferred to M5; prefer native HTML5 DnD to stay dep-light).

## Open Questions
- Exact **patch-op schema** surface (which `target`s: `activity|segment|field|flight`?) — resolve at M2 start.
- **Undo depth** and whether the stack persists across reload (recommend in-memory ~20 + persist last state).
- Timeline **orientation** (horizontal bands vs. vertical) — decide at M3 with a quick mock.
- M5 DnD: native HTML5 vs. a small lib — decide when M5 starts.

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Chat interaction | Agentic edits + undo | Most direct "iterate on aspects"; client applies scout JSON, no tool-use infra | 2026-09-05 |
| Visualization | Offline segmented timeline | Best effort-to-payoff; preserves local-first (no map provider) | 2026-09-05 |
| Layout | Three-pane, tabs on narrow | Matches "chat next to plan" + "visualize" literally | 2026-09-05 |
| Data model | Segment backbone, global `day` | Makes multi-city real; move = change one number | 2026-09-05 |
| Storage version | Bump to `trippin.trips.v2` | Clean migration boundary; v1 kept as backstop | 2026-09-05 |
| Apply mode | Auto-apply + visible undo | Smoother iteration than per-edit confirm dialogs | 2026-09-05 |
| Server changes | None | `/ai/plan` is generic; only prompt content changes | 2026-09-05 |

---

# Plan — Trippin' Proposal → Plan Lifecycle (v2)

Date: 2026-09-06
Status: Draft
Brainstorm: [docs/brainstorm.md](brainstorm.md) (2026-09-06 · Proposal → Plan lifecycle)

## Overview
Add a lifecycle to Trippin': **idea → proposal → plan**. A **proposal** is the general concept you
iterate on (destinations/segments, interests, pace, rough budget/length); a **plan** is a committed
variant escalated from a proposal (real dates, flights with carrier/confirmation, lodging specifics,
concrete day-by-day). One proposal can spawn **many plans** ("May" vs "September", "budget" vs
"splurge"), each a **snapshot** copy that is independent thereafter. The lever that keeps this small:
Proposal and Plan share **one record schema** discriminated by `kind`, so the entire M1–M5 engine
(segments, `applyOps`, undo, timeline, `PlanChat`) is reused — the new work is a schema split,
kind-gated UI, nested navigation, and an escalation action.

## Goals & Success Criteria
- **Proposal vs plan is real.** A record is a proposal or a plan; committed fields only appear on plans.
  - ✅ A proposal never shows/requires hard dates, flight confirmations, or lodging specifics.
- **Escalation works and is non-destructive.** Creating a plan snapshots the proposal; later proposal
  edits don't touch existing plans.
  - ✅ From a proposal, "Create plan" produces an independent plan with copied segments/interests/
    pace/budget (ids regenerated); editing the proposal afterward leaves that plan unchanged.
- **Multiple plans per proposal.** ✅ A proposal lists ≥2 named plan variants, each independently editable.
- **Nested navigation.** ✅ Sidebar lists proposals; opening one reveals its plans; ideas promote to proposals.
- **No data loss on migration.** ✅ Every existing v2 trip survives as a proposal (plus a plan snapshot
  when it carried committed detail); v2 key retained as backstop.
- **Engine reuse, no regressions.** ✅ Timeline, agentic chat, undo, and DnD work on both kinds unchanged.

## Scope
### In Scope
- v3 record model: `kind: 'proposal' | 'plan'`, `proposalId`, `variantName`; `v2→v3` migration.
- Nested IA: proposals top-level → plans nested; ideas promote to **proposals**.
- Kind-gated editor: committed-only sections hidden when `kind === 'proposal'`.
- Escalation action: snapshot a proposal into a new named plan (ids regenerated).
- Kind-aware `editPlan` prompt (proposal chat stays general; plan chat may commit specifics).

### Out of Scope (this pass)
- **"Refresh/sync from proposal"** into an existing plan (deferred; snapshot is one-way for now).
- Cross-plan **comparison/diff** views.
- Any change to the AI transport/server, booking integrations, or export.
- Proposal-level status workflow (the existing `status` enum stays a *plan* sub-status).

## Tech Stack & Architecture
Unchanged stack. Key decisions:

- **One schema, discriminated by `kind`.** Proposal and Plan are the same record shape (the current
  v2 trip) plus `kind`, and — on plans — `proposalId` and `variantName`. Proposals leave committed
  fields blank (`startDate/endDate`, segment `arrive/depart`, flight `carrier/confirmation/date`,
  lodging specifics). Chosen over two distinct schemas so `applyOps`, `segment*` helpers, `Timeline`,
  `PlanChat`, and the undo stack are reused verbatim. **Field partition** is enforced in the UI and
  the escalation/migration helpers, not by a second type.
- **Snapshot escalation.** `escalateToPlan(proposal, {variantName, startDate?})` deep-copies the
  shared fields with **regenerated ids** (segments + their referencing `activity.segmentId` remapped),
  sets `kind:'plan'`, `proposalId`, `status:'planned'`. Independent thereafter.
- **Storage v3.** Single collection `trippin.trips.v3` holding both kinds. `loadTrips` migrates
  v2→v3 on read; v2 key retained. Per-record chat stays keyed by record id.
- **Migration v2→v3.** Each v2 trip → a **proposal**; if it shows a *committed signal*
  (`startDate`/`endDate` set, or any flight, or any segment with a date/lodging) → also create one
  **plan** snapshot child so committed detail lands in a plan, not a proposal. v2 backstop kept.
- **Nested IA in `App`.** Sidebar sections: Ideas | Proposals. Selecting a proposal shows a proposal
  view with its plans; selecting a plan opens the existing `Workspace`. `promoteIdea` now creates a
  proposal.

Primary modules (new/changed):
- `src/lib/trip.js` — `KINDS`, `kind`/`proposalId`/`variantName`, `newProposal`/`newPlan` helpers, field-partition constants, `SCHEMA_VERSION → 3`.
- `src/lib/escalate.js` — `escalateToPlan()` snapshot with id remap (new).
- `src/lib/migrate.js` — extend with `v2→v3` (proposal + conditional plan).
- `src/lib/storage.js` — v3 key + migrate-on-read.
- `src/lib/aiClient.js` — `editPlan` prompt branch on `kind`.
- `src/components/Sidebar.jsx` — proposals list + nested plans.
- `src/components/ProposalView.jsx` — proposal detail: kind-gated editor + its plans list + "Create plan" (new).
- `src/components/TripEditor.jsx` — hide committed-only sections when `kind === 'proposal'`.
- `src/components/Workspace.jsx` — accepts a plan; breadcrumb back to parent proposal.
- `src/App.jsx` — proposals/plans state, selection (proposal vs plan), escalation wiring.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| N1 | v3 model + migration | `kind`/`proposalId`/`variantName`, `newProposal`/`newPlan`, field partition, `v2→v3` shim (proposal + conditional plan), storage v3 | — |
| N2 | Nested navigation + idea→proposal | Sidebar proposals list with nested plans; `promoteIdea` → proposal; App selection for proposal vs plan | N1 |
| N3 | Kind-gated proposal editor | `ProposalView` + hide committed-only sections in `TripEditor` when `kind==='proposal'`; reuse Timeline/chat | N1, N2 |
| N4 | Escalation (snapshot) | `escalateToPlan()` with id remap; "Create plan" flow (name + optional start date); open plan workspace | N1, N3 |
| N5 | Kind-aware chat + polish | `editPlan` prompt branch on kind; breadcrumbs; empty states; verification pass | N3, N4 |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| v2→v3 migration loses committed detail | Med | High | Proposal + conditional plan snapshot; unit-test the committed-signal heuristic on real dumps; keep v2 backstop |
| Snapshot id remap leaves dangling `segmentId` | Med | High | Single remap map for segments; reassign `activity.segmentId` through it; unit-test orphan-free copy |
| Field partition drifts between UI and escalation/migration | Med | Med | Single source-of-truth `PROPOSAL_FIELDS`/`PLAN_ONLY_FIELDS` consts in trip.js used everywhere |
| Nested IA over-complicates App state | Med | Med | Keep one flat records array + derived selectors (proposals, plansFor(id)); selection = one id + kind |
| Chat invents bookings on a proposal | Low | Med | Kind-branched `editPlan` prompt; proposal prompt forbids hard dates/confirmations |

## Dependencies
- No new npm packages. Builds entirely on the M1–M5 engine and existing AI transport.

## Open Questions
- Exact **field partition** (e.g. is rough per-day activity allowed on a proposal, or plan-only?).
- **Committed-signal** heuristic precision for migration (which fields count).
- `ProposalView` layout — reuse the three-pane shell (plan pane = trimmed editor) vs a lighter bespoke view.
- Plan **variant metadata** beyond `variantName` (season/tag?) — likely defer.

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Proposal↔plan relationship | Separate linked records (B) | Enables multiple committed variants per concept | 2026-09-06 |
| Escalation semantics | Snapshot copy, ids regenerated | Plans are independent forks; proposal stays pristine | 2026-09-06 |
| Data model | One schema, `kind` discriminator | Reuses M1–M5 engine wholesale; difference is UI+escalation | 2026-09-06 |
| Navigation | Proposals top-level, plans nested | Mirrors parent→children model | 2026-09-06 |
| Idea promotion | Ideas → proposals | Lifecycle starts general, not committed | 2026-09-06 |
| `status` enum | Stays a *plan* sub-status | No proposal-level status workflow this pass | 2026-09-06 |
| Storage version | Bump to `trippin.trips.v3` | Clean migration boundary; v2 kept as backstop | 2026-09-06 |
| Refresh-from-proposal | Deferred | Snapshot one-way keeps N-scope bounded | 2026-09-06 |

---

# Plan — Trippin' Live Flight Search (v3)

Date: 2026-09-06
Status: **Superseded by v3.1** (Amadeus Self-Service is shutting down July 2026; provider changed to Ignav, AI-search promoted to in-scope, durable snapshot schema added). Kept for history.
Brainstorm: [docs/brainstorm.md](brainstorm.md) (2026-09-06 · Live flight search)

## Overview
Add **live flight search** to a trip **plan's** Flights section: search real offers (routes, times,
fares) and add a selected one to `flights[]`. The API key stays **server-side** in the existing Node
helper (`server/index.mjs`); the browser calls `/flights/*` (proxied like `/ai`). Offers are
**flattened** into one `flights[]` leg per segment and added via the existing `add`/`flight` patch op
(undoable). **Search + autofill only — never book, purchase, or enter payment.** Proposals are
unaffected (flight ops already no-op on proposals).

## Goals & Success Criteria
- **Search real flights from a plan.** ✅ Enter origin/dest/date(s)/pax → get real offers with
  carrier, times, stops, price.
- **One-click add, undoable.** ✅ Selecting an offer appends its segment legs to `flights[]` as one
  undo step; existing legs are untouched.
- **Real itineraries.** ✅ A round-trip / connecting offer becomes multiple legs correctly mapped.
- **Key stays server-side.** ✅ No credential ever reaches the browser or the repo (`server/.env`, gitignored).
- **Graceful degradation.** ✅ No key / helper down / no results → clear message, manual entry still works.
- **No posture regression.** ✅ Proposals stay offline & flight-free; plans gain *optional* online search.

## Scope
### In Scope
- Helper endpoints: `POST /flights/search`, `GET /flights/airports?q=`, `GET /flights/health`, with
  OAuth2 **token caching** and a tiny built-in `.env` loader (no dep).
- `offerToLegs()` mapping (Amadeus offer → `flights[]` legs).
- Inline **FlightSearch** UI in the plan's Flights section (form + airport autocomplete + results + add).
- Vite `/flights` proxy; `.env` gitignore; README setup.

### Out of Scope (this pass)
- **Agent-chat flight search** (F5 — deferred fast-follow once endpoints exist).
- **Booking / ticketing / payment** (hard guardrail — never).
- Persisting raw offers / re-pricing; fare-rule detail; seat maps; multi-city (>round-trip) search.
- A `flight` schema change — extra detail (times, flight number, stops) rides in `notes` for v1.

## Tech Stack & Architecture
No new npm deps. Key decisions:

- **Provider: Amadeus Self-Service** (test env `test.api.amadeus.com`): OAuth2 client-credentials →
  `GET /v2/shopping/flight-offers` (search) + `GET /v1/reference-data/locations` (airport lookup).
  Chosen for a real free test tier and priced offers. Duffel/SerpApi are alternates. **Verify current
  terms + get test creds at F1** (external dependency — a live account is required).
- **Server proxy (required):** flight APIs block browser CORS and Amadeus needs a token exchange, so
  the helper holds `AMADEUS_CLIENT_ID/SECRET/ENV` and exposes `/flights/*`. Uses Node 18's global
  `fetch` — keeps the helper zero-dep. **Token cached in-process** with its `expires_in`.
- **Config loading:** Node 18.17 has no `--env-file`, so add a ~10-line `.env` parser to the helper
  (reads `server/.env`) rather than pulling in `dotenv`. `server/.env` is **gitignored**.
- **Offer → legs:** `offerToLegs(offer)` (pure, in `src/lib/flights.js`) flattens
  `itineraries[].segments[]` into legs `{ from, to, date, carrier, cost, notes }` (new ids); total
  price on the first leg's `cost`; times/flight-number/stops in `notes`; `confirmation` stays empty.
- **Add path = patch op:** FlightSearch emits one batch of `add`/`flight` ops through `onApplyOps`
  (threaded App → Workspace → TripEditor → FlightSearch) so a multi-leg add is a single undo step.
  Manual "+ Add leg" stays as-is.

Primary modules (new/changed):
- `server/index.mjs` — `/flights/search`, `/flights/airports`, `/flights/health`; token cache; `.env` loader; URL/query parsing.
- `src/lib/flights.js` — `searchFlights()`, `searchAirports()` (client → `/flights/*`) + `offerToLegs()` (pure) (new).
- `src/components/FlightSearch.jsx` — inline search panel (form, autocomplete, results, add) (new).
- `src/components/TripEditor.jsx` — mount FlightSearch atop the Flights section (plan only); accept `onApplyOps`.
- `src/components/Workspace.jsx` — thread `onApplyOps` into `TripEditor`.
- `vite.config.js` — proxy `/flights` → `:8787`.
- `.gitignore` — add `.env` / `server/.env`. `README.md` — Amadeus setup.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| F1 | Helper endpoints + token cache | `/flights/health,search,airports` in server/index.mjs; Amadeus OAuth2 token cache; `.env` loader; verify creds/terms | — |
| F2 | Offer → legs mapping | `offerToLegs()` (pure) + client `searchFlights`/`searchAirports` in src/lib/flights.js | F1 |
| F3 | Inline search UI | FlightSearch panel (form, airport autocomplete, results list, add-as-legs via patch op) in the plan Flights section | F2 |
| F4 | States, polish, README | loading/empty/no-results/not-configured/error states; `.env` gitignore; README setup | F3 |
| F5 | Agent-chat search (deferred) | PlanChat drives `/flights/search`; model proposes add-flight ops | F3 |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Amadeus terms/tier changed or creds hard to get | Med | High | Verify + obtain test creds at F1 before building UI; keep provider behind the `/flights` seam so swapping to Duffel/SerpApi is contained |
| Secret leaks into repo | Low | High | `server/.env` gitignored before any key added; key only ever in the helper; never logged |
| Test-tier rate limits / slowness | Med | Med | Debounce autocomplete, cap results, handle 429 with a clear message |
| Offer shape richer than single-leg model | Med | Med | Conservative segment→leg flatten; extra detail in `notes`; no schema change |
| Helper down / not configured breaks the section | Med | Low | `/flights/health` gates the panel; manual entry always available; friendly hint |

## Dependencies
- **Amadeus Self-Service account + test API credentials** (external; user obtains at F1).
- Node 18 global `fetch` (present). No npm packages.

## Open Questions
- Exact Amadeus request params/response fields to map (confirm at F1 against live responses).
- Airport autocomplete UX: min chars, debounce, caching common IATA codes.
- Result cap + sort (price vs duration) for v1.
- Round-trip in one search (Amadeus supports `returnDate`) vs two one-way searches — lean single search.

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Provider | Amadeus Self-Service (verify) | Real free test tier + priced offers; behind a swappable seam | 2026-09-06 |
| Key handling | Server proxy in helper | CORS + OAuth2 make browser-direct infeasible; keeps secret off client | 2026-09-06 |
| Config | Built-in `.env` parser | Node 18.17 lacks `--env-file`; preserves zero-dep helper | 2026-09-06 |
| Offer mapping | Flatten segments → legs | Handles round-trips/connections on the current single-leg shape | 2026-09-06 |
| Leg detail | Times/flight-no/stops in `notes` | Avoids a `flight` schema bump for v1 | 2026-09-06 |
| Add path | `add`/`flight` patch op batch | One undoable step; reuses the engine; plan-only via kind guard | 2026-09-06 |
| Entry point | Inline form first | Reliable/structured; agent-chat (F5) deferred | 2026-09-06 |
| Booking | Never | Search + autofill only; no payment/credentials | 2026-09-06 |

---

# Plan — Trippin' Live Flight Search (v3.1)

Date: 2026-09-06
Status: Draft
Brainstorm: [docs/brainstorm.md](brainstorm.md) (2026-09-06 · Live flight search) + Flight Integration Spec v1.1 (user, 2026-09-06)
Supersedes: v3 (above). **Why:** Amadeus Self-Service is shutting down July 2026; provider → **Ignav**;
AI-driven search promoted from deferred to **in-scope**; durable per-flight **snapshot schema** added.

## Overview
Add **live flight search** to a trip **plan** via a shared **server-side capability** (in the Node
helper) used by *both* an inline search UI and the AI chat. Search real offers (Ignav), show
structured results, and attach a selected flight to `flights[]` as a **durable snapshot** (airline,
flight numbers, times, airports, duration, stops, price-at-selection, booking URL) that stays useful
after the offer expires. Provider credentials stay server-side. **Search + autofill only — booking is
a deep-link hand-off, never in-app payment.** Proposals remain flight-free (kind guard).

## Goals & Success Criteria
- **Focused search** (origin, dest, date(s), pax, cabin, stops) → structured results. ✅
- **Add to a plan as a durable snapshot** shown with airline/numbers/times/airports/duration/stops/price. ✅
- **AI chat can search + add** flights via the *same* server capability, **confirming before it mutates** the trip. ✅
- **One-way + round-trip** supported; **credentials server-side only**. ✅
- **Resilient**: graceful handling of provider errors, empty results, rate limits, not-configured. ✅
- **Offer lifetime**: saved flight stays informative after the price/offer expires; optional refresh later. ✅

## Scope
### In Scope
- Shared server capability in `server/index.mjs`: `POST /flights/search`, `GET /flights/airports?q=`, `GET /flights/health`.
- Ignav client (API key from `server/.env`) + normalization; short-term identical-search cache.
- **Durable flight snapshot** — extend the `flight` leg shape (structured fields + `bookingUrl` + `priceAtSelection`); `v3→v4` migration.
- Inline **FlightSearch** UI (standalone + contextual/pre-filled from a plan) → results → add via `add`/`flight` patch op.
- **AI chat flight search**: client-orchestrated loop (search intent → `/flights/search` → results back → propose add-flight ops) with **confirm-before-apply**.

### Out of Scope (v1)
- In-app booking/payment/ticketing (deep-link hand-off only).
- Multi-city / open-jaw; seat maps; ancillaries; live status/delay tracking (optional later enrichment).
- Real tool-calling / MCP rewire of the AI layer (client-orchestrated loop instead).

## Tech Stack & Architecture
No new npm deps (Node 18 global `fetch`). Key decisions:

- **Provider: Ignav.** Self-serve REST, real data on a free tier (1,000 req, no card), fares +
  **booking links** (matches the no-in-app-booking non-goal), one-way/round-trip, cabin/stops
  filters, and an airport search. Auth is an **API key** (header) — no OAuth2 token exchange (simpler
  than Amadeus). Kept behind the `/flights` seam so Duffel/LetsFG remain swappable. *Verify current
  request/response shape at F1.*
- **Shared server capability (required):** the helper holds `IGNAV_API_KEY` and exposes `/flights/*`
  (proxied like `/ai`). Both the UI and the chat call the same endpoints — one normalization, one
  credential boundary. Built-in `.env` parser (Node 18.17 lacks `--env-file`); `server/.env` gitignored.
- **Durable snapshot schema (v3→v4):** extend the flight leg to
  `{ id, from, to, date, carrier, flightNumber, departAt, arriveAt, durationMinutes, stops, cabin,
  cost, priceAtSelection, currency, bookingUrl, confirmation, notes }`. A round-trip/connecting offer
  maps to multiple legs (one per segment); total price + `bookingUrl` on the first leg. Additive +
  defaulted on read; trivial `v3→v4` migration. `confirmation` stays empty (no booking).
- **AI chat = client-orchestrated loop** (app has no tool-calling; chat is `claude -p` → JSON ops).
  The model returns a `search_flights` intent in its JSON → client calls `/flights/search` → results
  summarized back into a follow-up turn → model returns `add`/`flight` ops → **client shows a confirm
  card, then applies** (undoable). This is an explicit **exception to global auto-apply**, for
  flight adds from chat only (higher-stakes, paid-API data).
- **Add path = patch op:** both UI and (post-confirm) chat add legs via the existing `add`/`flight`
  op, plan-only via the kind guard; one batch = one undo step.

Primary modules (new/changed):
- `server/index.mjs` — `/flights/*`; Ignav client; `.env` loader; identical-search cache.
- `src/lib/flights.js` — `searchFlights()`, `searchAirports()`, `normalizeOffer()`/`offerToLegs()` (pure) (new).
- `src/lib/trip.js` — extend `newFlight` with snapshot fields; `SCHEMA_VERSION → 4`.
- `src/lib/migrate.js` — `v3→v4` (default new flight fields).
- `src/components/FlightSearch.jsx` — inline search panel (standalone + contextual) (new).
- `src/components/TripEditor.jsx` — mount FlightSearch in the plan Flights section; accept `onApplyOps`; render richer legs.
- `src/components/PlanChat.jsx` — flight-search loop + confirm-before-apply card.
- `src/lib/aiClient.js` — `search_flights` intent in the plan-edit prompt + the follow-up turn.
- `vite.config.js` — proxy `/flights`. `.gitignore` — `.env`. `README.md` — Ignav setup.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| F1 | Shared server capability (Ignav) | `/flights/health,search,airports` in helper; Ignav API-key client from `.env`; identical-search cache; verify Ignav API | — |
| F2 | Snapshot schema + normalize | Extend flight leg (snapshot fields), `v3→v4` migration; `normalizeOffer`/`offerToLegs` + client `searchFlights`/`searchAirports` | F1 |
| F3 | Inline search UI | FlightSearch panel (standalone + contextual/pre-filled), results, add-as-legs via patch op; richer leg display | F2 |
| F4 | AI chat flight search | Client-orchestrated search loop in PlanChat + confirm-before-apply for flight adds | F2 |
| F5 | States, polish, README | error/empty/rate-limit/not-configured states; `.env` gitignore; README Ignav setup | F3, F4 |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Ignav API shape/terms differ from assumptions | Med | High | Verify request/response + auth at F1 against live calls (free tier, no card); keep provider behind `/flights` seam |
| Secret leaks into repo | Low | High | `server/.env` gitignored before any key; key only in helper; never logged |
| Per-request cost / slow searches | Med | Med | Identical-search cache, debounce autocomplete, cap results, loading states, avoid repeat calls |
| Chat loop mutates trip unexpectedly | Low | Med | Confirm-before-apply card for chat flight adds; undoable; concise results in context |
| Snapshot schema drift vs existing legs | Low | Med | Additive fields defaulted on read; trivial `v3→v4`; single `newFlight` source of truth |

## Dependencies
- **Ignav account + API key** (external; free tier, obtained at F1). No npm packages.

## Open Questions
- Exact Ignav request params + response fields → map at F1 against live responses.
- Airport autocomplete UX (min chars, debounce, caching common codes).
- Confirm-card UX for chat adds (inline in thread vs modal).
- Result cap + sort (price vs duration); round-trip in one call vs two.

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Provider | Ignav (was Amadeus) | Amadeus Self-Service shutting down Jul 2026; Ignav is self-serve, real free-tier data, booking-as-link fits non-goals | 2026-09-06 |
| AI integration | Client-orchestrated loop | App has no tool-calling; fits existing `claude -p` → JSON-ops pattern; no AI-layer rewrite | 2026-09-06 |
| Chat apply | Confirm before applying | Spec requires it; paid-API + committed data warrant a check; explicit exception to global auto-apply | 2026-09-06 |
| Snapshot | Extend flight leg (v3→v4) | Durable detail must survive offer expiry; supersedes v3's "notes only" | 2026-09-06 |
| Provider seam | `/flights/*` normalized | Swappable to Duffel/LetsFG; one credential boundary + one normalization for UI & chat | 2026-09-06 |
| Booking | Deep-link hand-off only | Never in-app payment/ticketing | 2026-09-06 |

---

# Plan — Trippin' Cross-Device Sync + AI Capability Tiers

Date: 2026-09-11
Status: Draft
Brainstorm: [docs/brainstorm.md](brainstorm.md) (2026-09-11 · Cross-device sync; 2026-09-11b · AI capability tiers)

## Overview
Make trips reachable across the user's devices (laptop + phone) while keeping the app **local-first**,
and formalize an **AI capability tier** so the app "sits on top of" a locally-installed CLI agent.
Two composable layers:
1. **Sync:** a hosted **Supabase** DB (Postgres + Auth + row-level security) is the shared source of
   truth; `localStorage` stays the fast, offline **working copy** and syncs to it. The web app is
   **deployed** so any device can load it.
2. **AI tier (AI-only gate):** manual create/edit of ideas/proposals/plans is **always available**;
   the **AI features** (brainstorm chat, agentic edits, itinerary draft) require **a reachable CLI
   agent** (local Claude Code helper) **or** a **BYOK** key — else they're disabled with a hint.

**This reverses the founding "local-first, no backend, no accounts" decision** — a deliberate pivot,
recorded below.

## Goals & Success Criteria
- **Same trips across devices.** ✅ Sign in on laptop + phone → both show/edit the same trips.
- **Local-first preserved.** ✅ Logged-out (or offline) the app works exactly as today from
  `localStorage`; sync is additive.
- **No data lost on convergence.** ✅ First login merges local + cloud (last-write-wins per record);
  deletes propagate (tombstones), not resurrect.
- **AI-only gate.** ✅ With no agent and no key: manual editing works, AI affordances are disabled
  with an "enable AI" hint. With a local CLI agent OR a key: AI works.
- **Hosted app loads anywhere.** ✅ Deployed by URL; AI on the hosted build = BYOK; flights degrade
  gracefully (local-only for v1).
- **No secret leakage.** ✅ Supabase anon key is public-by-design (RLS enforces access); the Ignav
  key never reaches the client bundle.

## Scope
### In Scope
- Supabase project: `trips` table (jsonb rows) + RLS; `@supabase/supabase-js` client.
- **Additive magic-link auth** (logged-out = current local-only behavior).
- **Sync engine** at the `storage.js` seam: pull-merge on login, debounced push on change,
  tombstones, record-level LWW; first-login merge/migration.
- **AI-tier gating** in the UI (manual always on; AI features gated by agent-or-key + hint CTA).
- **Deploy** the Vite frontend (Vercel) with Supabase public env vars.

### Out of Scope (v1)
- **Hosted flight search** — the Ignav proxy isn't deployed yet, so flights are **local-only** on the
  hosted build (graceful "not configured" state). Serverless proxy is a later milestone (D6).
- **Realtime live-sync** (Supabase subscriptions) — later (D7); v1 is pull-on-login + push-on-change.
- Syncing **ideas / brainstorm / per-record chat** — trips only for v1.
- **Multiple agent CLIs** — Claude-Code-first; registry shape only, others later.
- Multi-user **sharing**; field-level conflict merge.

## Tech Stack & Architecture
Client stack unchanged (React 18 / Vite 5). New: **`@supabase/supabase-js`** (first runtime dep
beyond React). Key decisions:

- **Supabase, browser-direct + RLS.** Postgres + Auth managed; the browser talks to Supabase with
  the **public anon key** and RLS scopes every row to `auth.uid()` — so there's **no data backend to
  build or deploy**. Chosen over a custom backend (which we'd have to host) precisely because
  accounts + RLS remove that need.
- **`trips` table = one jsonb row per record.** Columns: `id` (the app's record id, PK),
  `user_id` (`auth.uid()`), `kind`, `data` (jsonb — the whole versioned trip object; don't shred a
  rich evolving shape into columns), `updated_at` (timestamptz), `deleted` (bool tombstone).
  RLS policies: select/insert/update/delete where `user_id = auth.uid()`.
- **Sync wraps the existing seam.** `loadTrips`/`saveTrips` stay the local core; a new `sync.js`
  reconciles: on login/load → pull rows, **merge by `updated_at` (LWW per record)**, write both
  sides; on local change → write local now, **debounced push** of changed rows; deletes write a
  **tombstone** locally + remotely. `App` triggers pull on auth change and push on `trips` change.
- **Auth is additive.** Magic-link (passwordless). Logged-out ⇒ no Supabase calls, pure local
  (no regression). Logged-in ⇒ sync activates. First login **merges** local trips up.
- **AI tier signal (already ~computed).** `aiAvailable = isLocalAvailable() || settings.anthropicKey`.
  Thread it through so AI affordances (PlanChat send, agentic-edit entry, Brainstorm chat, draft)
  disable + show a hint when false; manual forms/timeline/DnD/add-leg are never gated. Helper keeps a
  small **agent-registry shape** (v1 = `{ claude }`) so more CLIs slot in later.
- **Deploy.** `vite build` → static host (Vercel). Env: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
  (public). On the hosted build the local helper is unreachable, so `flightsConfigured()` returns
  false → flight search shows its existing not-configured state (no crash); AI uses BYOK.

Primary modules (new/changed):
- `src/lib/supabase.js` — client init from env (new).
- `src/lib/sync.js` — pull/merge/push, tombstones, LWW, first-login merge (new).
- `src/lib/storage.js` — local core unchanged; add delete-tombstone tracking for sync.
- `src/components/Account.jsx` (or Settings section) — magic-link sign-in/out, sync status (new).
- `src/App.jsx` — auth state, sync triggers, compute + pass `aiAvailable`.
- AI-gated components — `PlanChat`, `Brainstorm`, `Workspace`/`ProposalView` (disable AI entry when `!aiAvailable`).
- Deploy config — `.env` (VITE_ vars), host config, README.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| D1 | Supabase project + schema + client | Provision project; `trips` jsonb table + RLS; `supabase.js` client from env | — |
| D2 | Additive auth (magic-link) | Sign-in/out UI; logged-out stays fully local; session wiring | D1 |
| D3 | Sync engine + first-login merge | pull-merge on login, debounced push, tombstones, LWW; merge local↔cloud | D1, D2 |
| D4 | AI capability-tier gating | `aiAvailable` (agent or key) gates AI affordances + hint; manual always on; agent-registry shape | — |
| D5 | Deploy frontend + env | Vite build to Vercel; Supabase public env; hosted AI=BYOK; flights degrade to local-only | D1, D3 |
| D6 | Hosted flights (serverless Ignav) | Deploy `/flights/*` proxy as a serverless fn (key in host env) → flights cross-device | D5 |
| D7 | Realtime live-sync | Supabase subscriptions for live multi-device updates | D3 |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| RLS misconfigured → cross-user data leak | Med | High | Strict `user_id = auth.uid()` policies; test a 2nd account can't read another's rows before D5 |
| LWW drops a concurrent edit | Med | Med | Record-level LWW by `updated_at` (accepted v1); tombstones for deletes; realtime (D7) shrinks the window |
| Ignav secret leaks into client bundle | Low | High | Ignav stays strictly in the helper/serverless fn; only `VITE_SUPABASE_*` (public) in the client |
| Auth regresses local-only users | Low | Med | Auth strictly additive; logged-out path unchanged and tested |
| New ops burden (Supabase + deploy) | High | Low | Accepted pivot cost; free tiers; document setup in README |
| Local `claude -p` helper can't be hosted | — | — | Accepted: hosted AI = BYOK; local run keeps the free-agent path |

## Dependencies
- **Supabase project** (free tier) — provisioned at D1 (external).
- **`@supabase/supabase-js`** npm package (new).
- **Vercel** (or similar) account for D5 (external).
- Existing Ignav helper unchanged; its hosting is D6.

## Open Questions
- Exact `trips` schema/indexes + the four RLS policies.
- Delete-tombstone lifecycle (retention/GC) and how local deletes are tracked in `storage.js`.
- Account UI placement (Settings vs a header control) and logged-in-but-no-AI vs logged-out messaging.
- Debounce interval + push batching for many rapid edits.
- Serverless target for D6 (Vercel function vs Supabase Edge Function) + where the Ignav key lives then.

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Local-first-only → backend | Adopt Supabase + accounts | Cross-device requires a hosted, reachable store; reverses the founding decision (deliberate) | 2026-09-11 |
| Data backend | Supabase browser-direct + RLS | Managed Postgres/Auth; anon key public + RLS ⇒ no backend to build/deploy | 2026-09-11 |
| Posture | Local-first, DB as sync | Keep offline/fast working copy; DB is durable shared truth | 2026-09-11 |
| Auth | Magic-link, additive | Passwordless; logged-out stays pure local (no regression) | 2026-09-11 |
| Conflict model | Record-level LWW + tombstones | Pragmatic v1; field-merge out of scope | 2026-09-11 |
| AI access | AI-only gate (agent OR key) | Manual editing always free; AI needs a local CLI agent or BYOK | 2026-09-11 |
| Agents | Claude-Code-first, registry shape | Build on `claude -p`; add other CLIs later without rewrite | 2026-09-11 |
| Hosted flights | Local-only for v1 | Keep deploy lean; graceful not-configured degrade; serverless proxy = D6 | 2026-09-11 |
| Realtime | Deferred (D7) | v1 pull-on-login + push-on-change is enough | 2026-09-11 |
| Sync scope | Trips only (v1) | Ideas/brainstorm/chat later | 2026-09-11 |
| Deploy target | Vercel (static Vite build) | Simple static host; Supabase public env vars | 2026-09-11 |

---

# Plan — Odyssai: Nocturne Redesign + Global Assistant (v5, desktop)

Date: 2026-09-12
Status: Active — R1–R8 implemented & verified 2026-09-12
Brainstorm: [docs/brainstorm.md](brainstorm.md) (2026-09-12 · Nocturne redesign + global assistant section)

## Overview
A **UI/interaction redesign over the engine we already have** — not a rebuild. The Claude-design
handoff ("Nocturne") reimagines Odyssai as an AI-first product: a persistent, context-aware
assistant beside every screen, a polished dark identity, a map-centric Trip page, a signature
dates-open flow, and richer Flights/Ideas/City views. The handoff ships our own `pattern.md`, and
its propose→apply→undo **is** our patch-ops + history — so the lifecycle, sync, Ignav, and accounts
all stay; this layer is presentation + information architecture + a few structured agent calls.

Scoped **desktop first**. Mobile (bottom tab bar + Ask-Odyssai sheet, already designed in the
handoff) is a deliberately deferred later phase.

## Goals & Success Criteria
- **Nocturne applied** app-wide: dark-only, low-chroma, single blurple accent `#9184d9`, Inter,
  Phosphor icons, 8px radii, outlined primary buttons. No stray slate/sky utilities remain.
- **Assistant is always-present + context-aware**: a persistent 342px right rail on every page,
  with per-page subtitle + suggestion chips; still answers **and** proposes edits (Apply/Undo).
- **New screens shipped**: Trip (map hero + day-by-day + budget donut + weather strip), Flights
  (search + price-by-date chart + summary), City/stop detail (POI map + overview), Ideas grid
  (match badges). Shell is top-bar tabs (Ideas · Trip · City · Flights) over a `page` router.
- **Signature dates-open flow**: a plan with no `startDate` shows the open-dates banner + a
  date-finder bar chart (real Ignav across a departure window); locking a departure sets
  `startDate` and fills flights + budget everywhere.
- **Data fidelity honored**: date-finder + budget donut = real; weather strip + Ideas match-% =
  LLM-derived (agent-native, structured JSON out, `aiAvailable`-gated, degrade gracefully).
- **No regression**: lifecycle, patch-ops/undo, local-first + Supabase sync, auth, Ignav all keep
  working; localStorage keys unchanged; signed-out = pure local.

## Scope
### In Scope
- Nocturne token layer in `index.css` + Tailwind theme; Phosphor + Leaflet deps.
- Shell rearchitecture: top bar + tab group + dates pill; `page` router; global assistant rail.
- Trip / Flights / City / Ideas pages (desktop), ported onto existing records + engine.
- Dates-open date-finder (real Ignav window, cached) + header pill toggle.
- Leaflet dark maps (route map on Trip, POI map on City) with LLM-provided cached coords.
- Two new LLM calls: weather strip + Ideas match-% (structured JSON, gated, graceful).
- Missing states the handoff flags: empty / loading / error, booking hand-off.

### Out of Scope
- Mobile layouts (tab bar, Ask-Odyssai sheet, bottom sheet) — later phase.
- Any change to the sync/auth/Ignav/lifecycle engine beyond additive fields (segment coords).
- Real weather API, real match-scoring service, real geocoding service (all LLM-derived/cached).
- Light theme (Nocturne is dark-only; the light-theme machinery is removed).

## Tech Stack & Architecture
- **Unchanged core**: React 18 + Vite 5 + Tailwind 3; localStorage seam (`storage.js`); patch-ops
  (`patch.js`) + `history.js`; lifecycle (`trip.js`/`escalate.js`/`migrate.js`); Ignav
  (`flights.js` + `server/ignav.mjs` + `api/flights/*`); Supabase sync (`supabase.js`/`sync.js`).
- **New deps**: `leaflet` (maps) + `@phosphor-icons/react` (icons). Dark-only, so light tokens drop.
- **Shell**: `App.jsx` loses `mode`, gains `page` (`ideas|trip|city|flights`) + `activeCityId`.
  New `components/Shell.jsx` (top bar + tab group + dates pill + body flex row), `components/
  AssistantRail.jsx` (PlanChat evolved: takes a **page-context** prop → subtitle + chip set;
  same ops/Apply/Undo). Screens become `pages/` components rendered by the router.
- **Assistant context API**: rail receives `{ page, record, activeCity }`; it derives the subtitle,
  the suggestion-chip set, and the system-context passed to `editPlan`. Existing per-record chat
  history keys are reused. Assistant `aiAvailable`-gated exactly as today.
- **Maps/geocoding**: segments store optional `lat`/`lng` (new v5 fields). When missing and an
  agent/key is available, one structured LLM call fills coords for a record's stops (cached on the
  segment; never re-fetched). No coords + no agent → map shows a graceful placeholder. Nominatim
  via the helper is the documented fallback if LLM coords prove unreliable.
- **LLM data**: `aiClient.js` gains `deriveWeather(record)` and `scoreIdeas(ideas, prefs)`, both
  returning structured JSON (same discipline as `editPlan`); results cached on the record/idea.
- **Migration**: bump `SCHEMA_VERSION` to 5; add nullable `lat`/`lng`/`weather`/`coordsFetched`
  fields; no destructive change (v4 records load unchanged).

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| R1 | Nocturne token layer | Rewrite `index.css` tokens + Tailwind theme to Nocturne (dark-only); add Phosphor; sweep hardcoded slate/sky utilities. Re-skins the current app in place. | — |
| R2 | Shell + global assistant rail | Top bar (brand · breadcrumb · tabs · dates pill) + `page` router + persistent 342px `AssistantRail` (PlanChat evolved, context-aware). Port existing views behind it. | R1 |
| R3 | Trip page | Map hero (Leaflet route map + LLM coords) → day-by-day day cards → flights section → viz row (real budget donut + LLM weather strip). | R2 |
| R4 | Dates-open date-finder | Open-dates banner + date-finder bar chart (real Ignav across a 7-day window, cached); lock-departure sets `startDate` + fills flights/budget; header pill toggle. | R3 |
| R5 | Flights page | Restyle `FlightSearch` to Nocturne flights page: route/date/traveler chips, price-by-date chart, outbound/return lists, summary column. Reuse Ignav + booking links. | R2 |
| R6 | City / stop detail | Per-segment page: Leaflet POI map + overview + quick-facts; agent-assisted things-to-do/stay/food (Overview built, other tabs stubbed). | R2, R3 |
| R7 | Ideas grid + LLM data | Restyle Brainstorm to the candidate grid with match badges (LLM match-%) + type tags + price/best-month; wire weather strip LLM call. Open → existing promote-to-proposal. | R2 |
| R8 | Polish + missing states | Empty/loading/error states, booking hand-off, focus/hover/pressed system, motion (rise/pulse), attribution, final detector/design pass. | R3–R7 |

## Task Breakdown (mid depth)
**R1 — Nocturne tokens**
- Extract the full ramp from the handoff into CSS custom props: `--color-bg #161826` / wrap
  `#0f1017` / `--color-surface` / `--color-divider` / `--color-text #e9e9ed`; accent 100–900 (500
  `#9184d9`); neutral 500–800; assistant panel `#13151f`; muted `rgba(233,233,237,.45–.78)`.
- Restyle `.card`/`.btn-*`/`.chip`/`.field` (outlined primary buttons; accent hover/pressed/focus).
- Remove light-theme tokens/machinery; add Phosphor; replace ad-hoc slate/sky utility usages.

**R2 — Shell + rail**
- `Shell.jsx`: 52px top bar (brand 17/600 -0.02em · `/` 30% · breadcrumb 13px · tab pills
  active `accent-800`/`accent-100` · dates pill right); body flex row, main `flex:1` scroll +
  `AssistantRail` 342px `#13151f`; max width 1180 centered.
- `App.jsx`: replace `mode` with `page` + `activeCityId`; keep session/tombstone/sync effects.
- `AssistantRail.jsx`: port `PlanChat` thread + proposal cards + input; add `pageContext` →
  subtitle + suggestion chips; route free text by keyword to intent as today.

**R3 — Trip page**
- `pages/TripPage.jsx`: map hero (Leaflet), day-by-day day cards (segments; Kyoto-style card →
  City page), flights section (two states), viz row.
- Budget donut (`conic-gradient` from real flight + activity costs; "$3.3k+ / — set dates" before
  dates). Weather strip (5 bars from `deriveWeather`).
- `lib/geo.js`: fill+cache stop coords via LLM; graceful placeholder when unavailable.

**R4 — Date-finder**
- Open-dates banner when no `startDate`; date-finder bar chart = round-trip priced across a 7-day
  departure window (real Ignav, cached per window); cheapest bar highlighted.
- Tapping/locking a bar sets `startDate`+`endDate` (from `lengthDays`) → flights + budget fill.
- Header dates pill toggles dashed "Dates open · N days" ↔ solid "{dep – ret} · Change".

**R5 — Flights page** — restyle `FlightSearch`: chips, price-by-date chart, outbound/return lists,
260px summary column (total, per-traveler, CO₂ line, add-to-trip, keep-tracking). Reuse Ignav.

**R6 — City page** — `pages/CityPage.jsx`: POI map (things-to-do dots / stays squares), overview
paragraph + tag row + quick-facts card; tabs (Overview built, rest stubbed); agent-assisted content.

**R7 — Ideas page** — `pages/IdeasPage.jsx`: candidate grid, idea cards w/ match badge
(`scoreIdeas` LLM), type tags, price-pp + best-month footer, Explore/Open → proposal.

**R8 — Polish** — states, booking hand-off, motion, focus system, attribution, design detector pass.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM coords wrong/hallucinated | Med | Med | Cache once; show label; Nominatim-via-helper fallback documented; markers tolerate approx placement |
| Date-finder = many Ignav calls | Med | Med | Small window (7); cache per (route, window); reuse round-trip search; only on demand |
| Shell rearchitecture regresses sync/auth | Low | High | Keep all App effects intact; port views behind new shell one at a time; manual two-session check |
| Weather/match LLM adds latency/cost | Low | Low | Gated + cached + graceful omit; never blocks manual use |
| Handoff gaps (empty/error/booking) underspecified | Med | Low | R8 owns them explicitly; reuse existing S9 booking feedback |

## Dependencies
- `leaflet` + OSM tiles (dark CSS filter; attribution kept). `@phosphor-icons/react`.
- Existing: Ignav key (flights/date-finder), agent-or-BYOK (assistant, coords, weather, match-%).

## Open Questions
- LLM coord accuracy at city granularity — validate in R3; fall back to Nominatim if poor.
- Exact per-page suggestion-chip copy (draft in R2, refine per page).
- Date-finder window size default (7) + whether to let the user widen it.

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Redesign shape | Layer over existing engine, not rebuild | Handoff ships our pattern.md; propose/apply/undo == our patch-ops | 2026-09-12 |
| Platform scope | Desktop first; mobile deferred | User-decided in brainstorm | 2026-09-12 |
| Theme | Dark-only (drop light machinery) | Nocturne commits to one visual world | 2026-09-12 |
| New deps | Leaflet + Phosphor only | Maps + icon set the design requires | 2026-09-12 |
| Geocoding | LLM-provided coords cached on segments | Agent-native, no new external dep; Nominatim fallback | 2026-09-12 |
| Weather + match-% | LLM-derived, gated, cached, graceful | User-decided; agent-native, no weather/scoring API | 2026-09-12 |
| Date-finder + budget | Real (Ignav + our costs) | User-decided fidelity split | 2026-09-12 |
| Assistant | Global context-aware rail = PlanChat evolved | Reuse thread/ops/undo; add page-context | 2026-09-12 |
| Schema | Bump to v5; add nullable lat/lng/weather/coordsFetched | Non-destructive; v4 loads unchanged | 2026-09-12 |

---

# Plan — Odyssai: Inter-city Transportation (v6)

Date: 2026-09-12
Status: Active — T1–T6 implemented & verified 2026-09-12
Brainstorm: [docs/brainstorm.md](brainstorm.md) (2026-09-12 · Inter-city transportation section)

## Overview
Make **how you travel between stops** first-class. Generalize the air-only `flights[]` into a single
**`travel[]`** array of legs, each with a **mode** (flight/train/bus/car/ferry/walk); add a trip
**start/end location** (home) so the first/last hops and flight search have a real origin;
LLM-derive non-flight hops (cached, like weather/coords) while flights stay real via Ignav; and
surface the *how* on the main page — connectors between day cards, mode-styled map legs, and an
evolved **"Getting around"** list. Additive and local-first; proposals show mode + rough duration,
plans add times/cost/booking.

## Goals & Success Criteria
- One `travel[]` model with `mode`; existing `flights[]` migrate in as `mode:'flight'` with no data
  loss; patch ops + escalation + AI protocol updated (with `flight`→`travel` back-compat).
- Each adjacent stop pair shows a hop (mode + duration) that **survives route reorders** (keyed by
  segment pair, re-derived on adjacency change).
- Ground hops are **LLM-derived + cached**; flights keep real Ignav search/booking; every hop is
  manually editable.
- Trip carries **startLocation/endLocation**; flight search/date-finder default their origin from it;
  home markers appear on the map; bookend hops (home→first, last→home) show in Getting-around.
- The *how* is visible without opening an editor: day-card connectors + map leg labels.

## Scope
### In Scope
- Model: `travel[]` + `mode`; `startLocation`/`endLocation`; v6 migration; patch/escalate/aiClient updates.
- `deriveTransport()` (LLM) + lazy auto-fill of missing hops (cached), agent-inferred default mode.
- Display: day-card connectors, mode-styled map polylines + labels + home markers, Getting-around list.
- Editing: per-hop mode/times/cost/booking (TripEditor + Getting-around inline); start/end fields; assistant ops.
### Out of Scope
- Real train/bus schedule APIs (LLM estimate only).
- Multi-modal single-hop breakdowns (e.g. train + transfer) — one primary mode per hop for v1.
- Hop duration feeding the day math (display-only in v1).
- Mobile-specific transport UI beyond what the responsive layout already gives.

## Tech Stack & Architecture
- **Model (`lib/trip.js`)**: rename the factory to `newTravelLeg` (keep `newFlight` as an alias),
  add `mode` + `fromSegmentId`/`toSegmentId` (sentinels `'origin'`/`'return'` for home bookends);
  add `startLocation`/`endLocation` `{ name, iata, lat, lng }` to `newTrip`. `PLAN_ONLY_FIELDS`:
  `flights`→`travel`. `SCHEMA_VERSION` → 6.
- **Migration (`lib/migrate.js`)**: `flights[]` → `travel[]` (each `mode:'flight'`); default
  `startLocation`/`endLocation` to null; `ensureArrays` learns `travel`. Idempotent; keeps
  `trippin.*` localStorage keys.
- **Patch (`lib/patch.js`)**: `ITEM_KEYS`/`ITEM_FACTORIES` gain `travel`; accept op target `travel`
  **and** legacy `flight` (aliased to `travel`); proposals still strip committed leg fields.
- **Escalation (`lib/escalate.js`)**: copy `travel` (was `flights`); carry start/end location.
- **AI (`lib/aiClient.js`)**: op protocol documents `travel` legs with `mode`; flight-search intent
  unchanged. **`lib/derive.js`**: `deriveTransport(fromCity,toCity,settings)` → `{ mode,
  durationMinutes, cost, note }`, cached on the leg; graceful/gated like weather.
- **Flights (`lib/flights.js`)**: `offerToLegs` sets `mode:'flight'`; unchanged otherwise.
- **UI**: `components/TravelConnector.jsx` (day-card connector), `OdMap` per-mode polyline styling +
  home markers + leg labels, `pages/TripPage.jsx` Getting-around section (evolved Flights & travel)
  + start/end location, `components/TripEditor.jsx` per-hop editor + home fields. Phosphor icons:
  AirplaneTilt, Train, Bus, Car, Boat, PersonSimpleWalk.
- **Hop resolution helper**: `travelForPair(record, fromSegId, toSegId)` + a builder that walks the
  ordered segments (plus home bookends) to produce the render list; orphaned legs GC'd on save.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| T1 | Model + migration | `travel[]` + `mode`, `startLocation`/`endLocation`, v6 migration (flights→travel), patch/escalate/aiClient updates (flight→travel back-compat) | — |
| T2 | LLM-derive transport | `deriveTransport()` + lazy auto-fill of missing hops (cached, gated, agent-inferred mode); Ignav unchanged for flights | T1 |
| T3 | Day-card connectors | `TravelConnector` between day-by-day cards — mode icon + duration; click → hop detail/search | T1, T2 |
| T4 | Map legs + home markers | Per-mode polyline styling + mid-line labels; home start/end markers from start/end location | T1, T2 |
| T5 | Getting-around section | Evolved Flights & travel: hop rows incl. home bookends; per-hop flight search/booking (Ignav) + "how do I get there?" | T1, T2 |
| T6 | Editing + polish | Per-hop mode/times/cost/booking (TripEditor + inline); start/end location fields; assistant ops; empty/loading states; verify | T3, T4, T5 |

## Task Breakdown (mid depth)
**T1** — bump schema to 6; add fields + factories + aliases; migrate `flights`→`travel`; update
`patch.js` targets (travel + flight alias) and `PLAN_ONLY_FIELDS`; `escalate.js` copies travel +
home; `aiClient.js` op protocol wording; `ensureArrays` includes `travel`. Unit-check migration
idempotency + that a v5 record with flights loads as travel.
**T2** — `deriveTransport()` prompt (mode/duration/cost/note, strict JSON); a lazy effect on
TripPage filling missing adjacent-pair hops (cached via onPatch), skipping flight hops (leave for
Ignav) and respecting `aiAvailable`; agent default-mode inference in the same call.
**T3** — `TravelConnector` component; insert between day cards (horizontal) and between itinerary
groups; graceful "add travel" when unknown.
**T4** — OdMap: accept per-leg `mode` for styling + a label; render home markers (distinct icon)
from start/end location; keep numbered stop markers + focus behavior.
**T5** — Getting-around list: build the ordered hop list (home → stops → home); per-hop row with
actions; flight hops open the existing search/booking; ground hops show derived info + re-derive.
**T6** — TripEditor: per-hop editor (mode select, times, cost, booking) replacing the flat flights
editor; start/end location inputs (with LLM coord/IATA fill); assistant `travel` ops end-to-end;
polish + in-app verification.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| flights→travel migration breaks saved plans | Med | High | Idempotent migrate + keep newFlight alias + verify v5-with-flights loads; localStorage keys unchanged |
| AI replies still target `flight` | Med | Med | Accept `flight` as alias for `travel` in patch.js |
| Reorder orphans/mismatches hops | Med | Med | Key by segment pair; resolve per adjacent pair; GC orphans on save |
| LLM transport wrong/variable | Med | Low | "Typical" framing; manual override; cached once; graceful when no AI |
| Home IATA ambiguous for flight search | Low | Med | LLM nearest-airport suggestion + user-editable origin |

## Dependencies
- Existing: Ignav (flight hops), agent-or-BYOK (derive transport, home coords/IATA), Phosphor icons.
- No new external APIs.

## Open Questions
- LLM accuracy for mode/duration at intercity granularity — validate in T2; manual override covers gaps.
- Home IATA resolution (LLM nearest-airport vs. explicit entry) — settle in T6.
- Whether home bookend hops show on proposals or plans only — recommend plans only (air/commit-ish).

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Transport model | Generalize `flights[]`→`travel[]` with `mode` | One model/section; matches reality | 2026-09-12 |
| Trip endpoints | Add start/end location (home) | Real origin for hops + flight search; map bookends | 2026-09-12 |
| Ground-transport data | LLM-derived, cached, manual override | No free schedule API; agent-native like weather | 2026-09-12 |
| Hop keying | By (fromSegmentId→toSegmentId), resolved per adjacent pair | Survives route reorder | 2026-09-12 |
| Op back-compat | Accept `flight` as alias for `travel` | Loose/old AI replies still apply | 2026-09-12 |
| Day math | Hop duration is display-only in v1 | Keep scope tight; avoid reflowing day ranges | 2026-09-12 |
| Schema | Bump to v6 (travel[], mode, start/end location); additive | v5 records migrate; no data loss | 2026-09-12 |

---

# Plan — Odyssai: Real Accounts (v7 · password + Google, magic-link backup)

Date: 2026-09-12
Status: Active — U1–U4 implemented; dashboard config + real-login test are user-run (2026-09-12)
Brainstorm: [docs/brainstorm.md](brainstorm.md) (2026-09-12 · Real accounts section)

## Overview
Add real login accounts on top of the existing Supabase Auth: **email + password** and **Google
OAuth** as the primary ways in, with **magic link** kept as a backup. Ships a proper auth screen
(log in / create account) and a signed-in account menu (sign out, change password). RLS, the sync
engine, and local-first are unchanged — a logged-in user is a logged-in user regardless of method,
and existing magic-link users carry over (same email = same Supabase user).

## Goals & Success Criteria
- Create an account and log in with **email + password**; **Continue with Google** works one-click.
- **Magic link** still available as a secondary option; **Forgot password** sends a reset email.
- Signed-in **account menu**: email, sign out, change password.
- No regression: signed-out = pure local; a magic-link user who sets a password keeps their trips.
- Clear error/success states (bad credentials, unconfirmed email, rate limit).

## Scope
### In Scope
- Supabase flows: signUp, signInWithPassword, signInWithOAuth(google), resetPasswordForEmail,
  updateUser(password); keep signInWithOtp.
- Auth modal UI (tabs + Google + password + forgot + magic-link fallback + states).
- Account menu (sign out, change password); reset-password landing handling.
- Config guidance (Google provider, redirect URLs, email-confirm) — user-run, documented.
### Out of Scope
- Providers beyond Google (Apple/GitHub) — easy later.
- Passkeys/WebAuthn; "sign out everywhere"; profile avatars.
- Per-account sync of BYOK keys/settings (stay device-local).
- Any change to RLS / sync / data model.

## Tech Stack & Architecture
- **`lib/supabase.js` / `App.jsx`**: add auth helpers alongside the existing `signIn`(otp)/`signOut`
  — `signUpPassword`, `signInPassword`, `signInGoogle`, `sendReset`, `changePassword`. Session
  state + sync effects unchanged (they key off `session.user.id`).
- **`components/Auth.jsx`** (new): the auth modal — Log in / Create account tabs, Continue with
  Google, email+password (show/hide), Forgot password, "email me a magic link instead," inline
  errors. Opened from the top-bar account control.
- **`components/Account.jsx`**: becomes the signed-in **account menu** (email, sign out, change
  password) + the trigger that opens `Auth` when signed out.
- **Reset landing**: `resetPasswordForEmail(redirectTo=origin)`; on load, if a recovery session is
  present, show a "set a new password" state (reuses the Auth modal). Detected via Supabase's
  `onAuthStateChange` `PASSWORD_RECOVERY` event.
- **Config (user-run)**: enable Google in Supabase Auth providers; add redirect URLs
  (localhost:5173/5174 + Vercel) for OAuth + reset; email-confirm toggle (default ON).

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| U1 | Auth flows | supabase/App helpers: signUp, signInPassword, signInGoogle, sendReset, changePassword (keep magic link); PASSWORD_RECOVERY handling | — |
| U2 | Auth modal | New `Auth` UI: log in / create account tabs, Continue with Google, password (show/hide), forgot password, magic-link fallback, error/success states | U1 |
| U3 | Account menu | Signed-in menu (email, sign out, change password); reset-password "set new password" state | U1, U2 |
| U4 | Config + verify | Google provider + redirect URLs + email-confirm (user-run, documented); end-to-end verification (build + UI states; user does real login) | U1–U3 |

## Task Breakdown (mid depth)
**U1** — add the five helpers to the supabase layer; wire an `onAuthStateChange` branch for
`PASSWORD_RECOVERY`; keep `signInWithOtp`. No UI yet.
**U2** — `Auth.jsx` modal: tabbed form, Google button, validation (email format, min password
length hint), forgot-password action, magic-link fallback link, loading + inline errors; open it
from the account control when signed out.
**U3** — `Account.jsx` signed-in menu: email/name, Sign out, Change password (updateUser), and the
recovery "set a new password" flow after a reset link.
**U4** — write setup steps (dashboard: Google keys, redirect URLs, confirm toggle); verify build +
every UI state; confirm carry-over (magic-link user → set password → same trips). Real credential
entry is user-performed.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OAuth/reset redirect not allow-listed | Med | High | Documented URL list (localhost + Vercel); surfaced like the magic-link fix |
| Email-confirm blocks first login unexpectedly | Med | Med | Default ON but documented; clear "check your email" state; toggle is one dashboard switch |
| Existing magic-link user duplicated | Low | High | Same email attaches to same user — verify carry-over in U4 |
| Password reset UX confusion | Med | Low | Dedicated PASSWORD_RECOVERY "set new password" state in-app |
| Assistant can't enter credentials | — | — | Build + UI-state verify; user performs real sign-up/login |

## Dependencies
- Supabase project (existing) + Google OAuth credentials (user creates in Google Cloud + Supabase).
- Redirect URLs allow-listed (existing localhost/Vercel list + reset/OAuth).

## Open Questions
- Password strength UI (min length hint) — settle in U2.
- Reset landing: in-app modal state (recommended) vs. Supabase-hosted page.
- First-run "create account" nudge vs. keeping auth opt-in (recommend opt-in).

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Methods | Email+password + Google primary; magic link backup | User-decided; covers "real login" + "just let me in" | 2026-09-12 |
| Email confirmation | Keep ON (default) | Verified emails; reset needs email anyway; one dashboard toggle | 2026-09-12 |
| Providers | Google only for v1 | Highest coverage; Apple/GitHub easy later | 2026-09-12 |
| BYOK/settings | Stay device-local | Not account data; avoid scope creep | 2026-09-12 |
| Backend | Reuse Supabase Auth; RLS/sync unchanged | Additive; a session is a session | 2026-09-12 |

---

# Plan — Odyssai: Monetization & Pricing (v8 · metered managed AI)

Date: 2026-09-19
Status: Draft
Brainstorm: docs/brainstorm.md § 2026-09-19 "Pricing & monetization (public launch)" (+ addendum)

## Overview

Make managed AI a paid, abuse-safe product for a public launch, while keeping the app free to use
without AI and free for BYOK power users. Builds directly on what exists: Supabase Auth + sync, and
the `api/ai/plan.js` serverless seam already shipped. The keystone is a **metering ledger** that
gates the managed serverless endpoint — until that exists, exposing a server-side Anthropic key
publicly is an unbounded-spend hole, so P1 is both the first revenue primitive and the safety fix.

Three-layer model (from brainstorm): **non-AI features free forever · BYOK free & unlimited (client-
side, never metered) · managed AI metered/paid.** Unit economics are wide (~<$1/managed trip), so
this is a packaging problem: meter the countable expensive actions (prompts + new proposals/plans),
absorb the pennies (background derived-data), and sell credits.

## Goals & Success Criteria
- **Safe public server key:** no managed AI call runs without an authenticated user with balance.
- **Metered:** every managed call decrements a per-user balance atomically and is logged.
- **Free taste:** a monthly allowance (~1 trip) with no payment; resets monthly.
- **Paid path:** buy credits via a Merchant-of-Record; balance top-up is reflected immediately.
- **Honest UX:** users see remaining balance, an estimate before big actions, and a clear
  out-of-credits flow — never a silent failure.
- **BYOK untouched:** BYOK users bypass metering entirely (client-side direct call).

## Scope
### In Scope
- Supabase-backed credit ledger + usage log; atomic consume; JWT-gated enforcement in `api/ai/plan.js`.
- Cheap/smart model split + gateway + shared cross-user cache (supply-side cost control).
- Credit packs + Merchant-of-Record checkout + balance top-up webhook.
- Free-tier monthly grant + rate limits + basic abuse gates.
- Paywall/pricing UX: balance display, pre-action estimate, out-of-credits flow.

### Out of Scope (this plan)
- Subscription tier (deferred; credits-first).
- **MCP entrypoint** (later phase; referenced below — depends on server-canonical data + OAuth).
- iOS app (separate task; shares the server-canonical-data question).
- Turning localStorage into the canonical store (only billing state must be server-authoritative now).

## Tech Stack & Architecture

- **Ledger in Supabase (Postgres).** Two tables: a per-user **balance** row and an append-only
  **usage_events** log. Reuses the existing Supabase project; RLS: users can *read* their own
  balance/usage, but **only the server (service role) may mutate** — the browser can never grant
  itself credits.
- **Atomic consume via a Postgres RPC** (`consume_credits(kind, cost)`): check-and-decrement in one
  transaction, returns new balance or raises `insufficient`. Prevents double-spend races.
- **Enforcement at the serverless seam.** `api/ai/plan.js` extracts the Supabase access token
  (`Authorization: Bearer`), resolves the user (`supabase.auth.getUser(jwt)`), calls `consume_credits`
  **before** the model call, and logs tokens after. No token / no balance → 401 / 402, and the
  Anthropic call never fires. **Managed AI now requires sign-in** (a deliberate change from today's
  anonymous serverless call).
- **Credits as the single currency, displayed as counts.** Internally: a balance of credits; each
  action has a configurable credit cost (`prompt`, `new_proposal`, `new_plan`). UI *shows* it as
  "~N prompts / M plans left." Background derived-data calls are **uncounted** (absorbed; cheap +
  shared-cached). This unifies free-grant and purchased credits under one ledger.
- **Supply-side cost (P2):** route background calls to a cheap model (Haiku), reasoning to a
  premium model, behind a **gateway** (Vercel AI Gateway or OpenRouter) with a hard spend cap;
  add a **shared cross-user cache** keyed on the query (not the user) for facts (weather-by-place-
  month, city coords/briefings) so repeated planning of the same place is ~free.
- **Payments (P3):** **Merchant-of-Record** (Paddle / Lemon Squeezy) — they own global tax. A
  webhook credits the user's balance on successful purchase. No card data touches us.
- **BYOK stays client-side.** BYOK requests never hit `api/ai/plan.js`; nothing to meter.

Reasoning for the big calls: **Supabase ledger** (vs a new DB) reuses auth + RLS + the row the user
already has; **server-only mutation** is the whole security model; **MoR over Stripe** trades ~2pts
of fees for zero global-tax ops — the right call for a solo public launch (revisit at scale).

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| P1 | Metering ledger + enforcement | Supabase balance + usage log + atomic consume RPC; JWT-gate `api/ai/plan.js`; client sends token; 401/402 flows. Makes the public key safe. | Supabase (exists), `api/ai/plan.js` (exists) |
| P2 | Supply-side cost stack | Gateway + cheap/smart model split + shared cross-user cache + hard spend cap. | P1 |
| P3 | Credit packs + MoR checkout | Pack SKUs, MoR checkout, purchase webhook → balance top-up. | P1 |
| P4 | Free tier + abuse gates | Monthly credit grant + reset; per-user & global rate limits; multi-account abuse mitigations. | P1 |
| P5 | Paywall / pricing UX | Balance display, pre-action estimate, out-of-credits flow, pack purchase entry points. | P1, P3, P4 |

## Task Breakdown (P1 — mid depth; keystone, next to build)

- **P1.1 — Schema + RLS (Supabase migration).**
  - `billing_balance`: `user_id (pk, fk auth.users)`, `credits int`, `granted_at`, `updated_at`.
  - `usage_events`: `id`, `user_id`, `kind` (`prompt`|`new_proposal`|`new_plan`|`background`),
    `credits_spent int`, `model text`, `input_tokens int`, `output_tokens int`, `cost_usd numeric`,
    `created_at`. Append-only.
  - RLS: `select` own rows; **no** client `insert/update/delete` (service role only).
- **P1.2 — Atomic consume RPC.** `consume_credits(p_kind text, p_cost int)` SECURITY DEFINER:
  transactionally check `credits >= p_cost`, decrement, return new balance; raise `insufficient`
  otherwise. (Cost passed by server, not client.)
- **P1.3 — Server billing helper** (`server/billing.mjs`): a Supabase **service-role** client;
  `resolveUser(jwt)` → user or throw 401; `consume(userId, kind, cost)` → new balance or 402;
  `logUsage(userId, {...tokens, model, cost})`. Service-role key from `process.env` (never shipped).
- **P1.4 — Enforce in `api/ai/plan.js`.** Read `Authorization: Bearer`; resolve user (401 if none);
  map action `kind` (from request) → configured cost; `consume` (402 if insufficient) **before** the
  Anthropic call; on success capture `usage` and `logUsage`. Config table of costs in one module.
  Refund/skip-charge if the model call throws (meter on success).
- **P1.5 — Client sends the token + action kind.** `src/lib/aiClient.js` `callLocal()` attaches the
  current Supabase access token and a `kind` for the call; handle 401 ("sign in to use AI") and 402
  ("out of credits") distinctly. BYOK path unchanged.
- **P1.6 — Seed + verify.** A way to grant starter credits (manual/SQL for now; P4 automates the
  monthly grant). End-to-end test: signed-in with balance → works + decrements + logs; zero balance
  → 402, no Anthropic call; no token → 401; BYOK → unmetered.

**P1 acceptance criteria:**
- Managed call with valid JWT + balance succeeds; `billing_balance.credits` drops by the action cost;
  a `usage_events` row is written with token counts.
- Zero/insufficient balance → HTTP 402, friendly message, **Anthropic never called**.
- Missing/invalid JWT on a managed call → HTTP 401.
- Concurrent calls can't overspend (atomic RPC verified).
- BYOK requests are unaffected (never reach the serverless endpoint).

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Client grants itself credits | Med | High | Service-role-only mutation; RLS blocks client writes; cost set server-side |
| Double-spend under concurrency | Med | Med | Atomic check-and-decrement RPC (SECURITY DEFINER), not read-modify-write |
| Server key drained before P1 lands | Med | High | Don't expose managed AI publicly until P1 gates it; keep BYOK/self-key only until then |
| Charged for failed AI calls | Med | Low | Meter on success; refund/skip on model error |
| Free-tier multi-account abuse | Med | Med | Email confirmation (exists) + P4 rate limits + soft device heuristics |
| Credit→action mapping wrong (mis-priced) | Med | Med | Measure real token sizes with `count_tokens`; make costs config, not hardcoded |
| MoR lock-in / fees at scale | Low | Med | Abstract checkout; Lemon Squeezy → Stripe migration path noted |

## Dependencies
- Supabase project (exists) — new tables + RPC + `SUPABASE_SERVICE_ROLE_KEY` in Vercel env.
- `api/ai/plan.js` serverless seam (exists) + `ANTHROPIC_API_KEY` (from v-prior task `aeaece`).
- P3 needs a Merchant-of-Record account (user-created) + webhook endpoint.
- P2 needs a gateway account (Vercel AI Gateway / OpenRouter) + spend cap config.

## Open Questions
- **Exact credit→action mapping** (prompt vs new_proposal vs new_plan costs) — settle after measuring
  token sizes with `count_tokens` on real prompts.
- **Free-tier size** (credits/month; "≈1 trip" = how many prompts + plans) — product call.
- **MoR final pick** (Paddle vs Lemon Squeezy) vs Stripe-direct — confirm before P3.
- **Server-canonical data** — MCP entrypoint + iOS both want Supabase as source of truth; only
  *billing* state must be server-authoritative for this plan, but flag whether to pull records
  server-canonical sooner (would reshape P-later + those features).

## Decisions Log
| Decision | Choice | Reasoning | Date |
|----------|--------|-----------|------|
| Metering model | Credits (single currency), displayed as counts | Unifies free grant + purchases; flexible costs | 2026-09-19 |
| Free-tier unit | Count prompts + new proposals/plans | Predictable, counts the expensive calls | 2026-09-19 |
| Enforcement point | JWT-gated `api/ai/plan.js` + service-role mutation | Reuses auth; only server can grant/spend | 2026-09-19 |
| Managed AI requires sign-in | Yes (change from anon serverless) | Can't meter an anonymous caller | 2026-09-19 |
| Payments | Merchant-of-Record for v1 (vs Stripe) | Zero global-tax ops for solo launch | 2026-09-19 |
| Pricing shape | Credits-first; subscription later | Bursty usage; avoid churn | 2026-09-19 |
| BYOK | Client-side, never metered | No secret custody; power-user valve | 2026-09-19 |
| MCP entrypoint | Out of scope (later phase) | Needs server-canonical data + OAuth | 2026-09-19 |

---

## Rebrand — Odyssai → Trip Fairy
Date: 2026-09-22

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Product name | **Trip Fairy** (wordmark `trip fAIry`, "AI" in accent) | Play on words that puts the AI in the name; replaces Odyssai | 2026-09-22 |
| Palette | Sky: accent `#38bdf8` on slate grounds (`#0b0f14` / `#141a22` / `#1c242e`) | Supplied with the logo; replaces Nocturne's blurple `#9184d9` | 2026-09-22 |
| Logo | Continuous dashed flight path → paper plane (`public/brand/`, `src/components/Brand.jsx`) | The mark takes `currentColor`, so it follows the accent token | 2026-09-22 |

Earlier sections keep the Odyssai name as a historical record.

## Map redesign — MapLibre + OpenFreeMap
Date: 2026-09-22

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Map engine | MapLibre GL (lazy-loaded chunk) replaces Leaflet | Vector tiles let the basemap be styled with Trip Fairy's own tokens (vs. CSS-inverting OSM raster tiles); globe projection; the engine stays out of the main bundle | 2026-09-22 |
| Basemap tiles | OpenFreeMap (`tiles.openfreemap.org`), custom style in `src/lib/mapStyle.js` | Free incl. commercial, no key, no request limits; attribution required (compact "i" control). CARTO Dark Matter now needs a key and its free tier targets non-commercial use | 2026-09-22 |
| Symbols | Numbered stop pins · home plane badge · POI icons (ticket / bed-square / fork, food in warm tone) · great-circle legs dashed per mode with midpoint mode badges | Each marker says what it is at a glance; labels avoid collisions; popups built as text (closes an HTML-injection path from AI blurbs) | 2026-09-22 |

Risk: OpenFreeMap is donation-funded community infrastructure. The style points at one tile URL, so switching providers (self-hosted OpenFreeMap, MapTiler, Stadia) means editing one file.

## Pricing — outcome-based reasoning charges
Date: 2026-09-25

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| How to price "build" turns | **Outcome-based, server-side**: every reasoning turn costs 1 up front; after the reply, `server/outcome.mjs` counts what it added (≥4 activities → new_plan 5; ≥2 stops → new_proposal 3) and charges the difference; drains to 0 if the balance can't cover it | Pricing by the trip's emptiness at send time charged 5 for *every* message on an empty plan (even "change the dates") and let the client pick its own rate. The server now prices only from its own read of the model output. | 2026-09-25 |
| Background (free) calls | Size cap + per-user daily cap (`BACKGROUND_MAX_PROMPT_CHARS`, `BACKGROUND_MAX_PER_DAY`), no migration | The client chooses `kind`; relabeling reasoning as background would otherwise be free cheap-model completions | 2026-09-25 |

## City page — "Getting around" (R6.1)
Date: 2026-09-25

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Source of truth | Model-generated, but grounded in Wikivoyage's "Get in" / "Get around" wikitext when a page resolves (`src/lib/wikivoyage.js`), with visible CC BY-SA attribution | Free, no key, and materially reduces the model's tendency to invent fares/passes vs. asking it cold | 2026-09-25 |
| Caching | localStorage, ~30-day TTL, cache misses too (`tf.wikivoyage.v1.<placeKey>`) | Matches the existing geocode cache pattern; the "Get around" facts change slowly | 2026-09-25 |
| Data shape | `segment.detail.gettingAround = { summary, modes[], pass, apps[], airport[] }` | Additive to the existing `detail` cache — doesn't bump `detail.v` (still 2) so it can be backfilled onto older briefings via `deriveGettingAround()` without a full re-derive | 2026-09-25 |

## Trip-level "Good to know" cautions
Date: 2026-09-25

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Real-data facts | Public holidays (Nager.Date, free, no CORS issue) + US State Dept advisories via a new `api/advisories.js` proxy (upstream has no CORS) | Zero-cost, zero-AI facts a traveler actually wants; only ever shown at advisory level ≥2 | 2026-09-25 |
| Country codes | `Intl.DisplayNames` region table (built once, name→ISO2) + a small alias list (USA, UK, Czechia, Türkiye, South Korea…) | Segments store `country` as free text; no existing geocoder field gives ISO2 cheaply | 2026-09-25 |
| AI notes generation | User-initiated button (`lib/cautions.js` via a new `askPrompt` in `lib/aiClient.js`, kind `'prompt'`), not automatic | Costs a credit on managed AI under the outcome-based pricing model — must not fire on every trip view | 2026-09-25 |
| Staleness | `record.cautions = { items, sig, at }`; sig fingerprints ordered stops + dates + home | Keep showing old notes with a quiet "trip changed — Refresh" nudge rather than silently going stale or auto-spending a credit | 2026-09-25 |
| Persistence | `onRevise` (the same undoable "latest record" path `TripAudit`'s one-click fixes use) | Generation is async and user-initiated, same shape as an audit fix — not a manual field edit (`onChange`) or a silent cache fill (`onPatch`) | 2026-09-25 |

---

# Plan — Trip Fairy: Flight-Optimized Planning (v9)
Date: 2026-09-26
Status: Active
Brainstorm: docs/brainstorm.md → "2026-09-26 · Flight-optimized trip planning (8517f3)" + addendum

## Overview
Use the trip's own shape to pick flights: compare flying a round trip to the first city against an
open-jaw (in to the first city, out of the last), across a small flexible-date grid and up to two
airports per end, and have the assistant explain the tradeoffs. Builds on what's live: Ignav fares +
booking links (verified 2026-09-26), the date-finder, the Flights page, `trip.startLocation`, linked
start/end/length, `travel[]` hops with ground estimates, and Supabase auth + usage metering (v8).

## Goals & Success Criteria
- A multi-city plan with a departure airport shows a ranked set of "how to get there and back" options
  (price, total flight time, stops, extra ground leg) within ~10s of asking, from cache in <1s after.
- Picking an option + date cell sets start/length and adds the legs to `travel[]` in one undoable step.
- The chat can answer "why this one?" / "what if I leave Friday?" from the fare summary without
  triggering new searches.
- Live fares on the deployed site require sign-in; a signed-in user can't exceed the daily cap; repeat
  views of the same route/dates hit the shared cache (≥50% hit rate on a repeated sweep).
- Ignav spend stays within ~$0.30/user/day worst case.

## Scope
### In Scope
- FO1 gating + fare cache + server-side sweep endpoint
- Book-end options: round trip to first city vs open-jaw first/last (reverse route shown as an option,
  not applied)
- Gateway candidates: ≤2 airports per end (curated hub table + validated LLM suggestions)
- Flexible-date grid: departure ±3 days × length ±1 (~21 cells per option), lock a cell
- Precomputed fare summary in the assistant's context; tradeoff copy
### Out of Scope (later)
- Reordering stops to fit gateways (as an undoable AI edit)
- Intra-trip flight hops optimization
- Model-initiated searches (tool-style) — maybe ≤1 per turn later
- Anonymous sessions / signed-out taste; credits for sweeps
- Price alerts / tracking

## Tech Stack & Architecture
No new stack. Pieces:
- **Server (shared core + Vercel fn + local helper, same pattern as `server/ignav.mjs`):**
  `server/fares.mjs` — auth gate (reuses `resolveUser` from `server/billing.mjs`), daily cap (counts
  `usage_events` kind `fare_search`), cache (new `fare_cache` table, service-role only), and
  `sweep(cells)` running Ignav searches with bounded concurrency (4) and per-cell cache.
  Endpoints: `POST /flights/search` (gated + cached), `POST /flights/sweep` (new), existing
  airports/booking-links (airports stays open: cheap + needed for autocomplete; booking-links gated).
  Local helper: unrestricted, in-memory cache, same sweep code.
- **Client:** `src/lib/flights.js` sends the Supabase bearer token (same helper as aiClient); new
  `src/lib/fareOptimizer.js` — pure: build candidate "shapes" (round-trip / open-jaw × gateways) and
  date cells, call sweep, score + rank, produce a compact summary. UI: a "Best way there & back" card
  on the Flights page (and a small entry point on the trip page).
- **Scoring:** price + a time/stops penalty ($ per extra hour/stop, one "cheapest ↔ easiest" slider),
  plus the extra ground leg's estimated cost/time from existing hop estimates.
- Why not client-side fan-out: N browser calls can't be capped or cached server-side coherently, and
  exposes quota. Why not a precomputed nightly job: fares are too route/date specific.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| FO1 | Fare gating, cache & sweep | Sign-in required for live fares on Vercel, per-user daily cap, shared `fare_cache`, `POST /flights/sweep` (server-side grid, bounded concurrency); client sends auth + handles 401/429 | v8 billing (auth, usage_events) |
| FO2 | Book-end optimizer core | Pure `fareOptimizer.js`: candidate shapes (round trip vs open-jaw, reversed), cell generation, scoring with ground-leg cost, ranked options + summary; unit-tested | FO1 |
| FO3 | Gateway airports | ≤2 airports per end: curated hub/metro table + LLM suggestions validated via `/flights/airports`; cached per city | FO2 |
| FO4 | Flexible-date grid UI | "Best way there & back" card: option list + ±3×±1 heat grid, freshness label, lock → sets start/length + adds legs (undoable) | FO2, FO3 |
| FO5 | Assistant integration | Fare summary in the trip context for the chat; tradeoff explanations; suggestions use existing ops | FO4 |

## Task Breakdown

### FO1 — Fare gating, cache & sweep (mid-depth)
1. **Migration `0005_fare_cache.sql`:** `fare_cache(cache_key text pk, value jsonb, created_at)` —
   key = sha256 of normalized request (legs, pax, cabin, max_stops, market); RLS on, no policies
   (service role only). Index on `created_at` for pruning.
2. **`server/fares.mjs`:**
   - `gate(req)` → `{ userId }` or throws 401 (no/invalid token) / 429 (over cap). No-op when billing
     isn't configured (open path, same as `/ai/plan`) and in the local helper.
   - `withinFareLimit(userId, n)` — counts today's `fare_search` usage rows; `FARE_MAX_PER_DAY`
     (default 150). A sweep reserves its uncached cell count up front; over-cap → 429 with remaining.
   - `cachedSearch(body)` — read-through cache, TTL `FARE_CACHE_TTL_HOURS` (default 8); stores the
     trimmed itineraries (top ~15 by price) to keep rows small.
   - `sweep(cells, opts)` — cells = [{ legs, pax, cabin }]; max `FARE_SWEEP_MAX_CELLS` (default 90);
     concurrency 4; per-cell result `{ key, cheapest, best, count, cached, error? }`; logs one usage
     row per *uncached* cell (`kind: 'fare_search'`, `cost_usd: 0.002`, `cached` flag).
3. **Endpoints:** `api/flights/search.js` + new `api/flights/sweep.js` + `booking-links.js` go through
   `gate`; `server/index.mjs` routes sweep locally (no gate). `vercel.json` rewrite already covers
   `/flights/:path*`. Search moves to `/fares/search` (2-leg capable) for open-jaw; keep round-trip
   compatibility.
4. **Client:** `flights.js` attaches the bearer token; maps 401 → "Sign in to search live fares" (with
   the existing sign-in entry), 429 → "Daily fare-search limit reached — resets at midnight UTC".
   Flights page + date-finder show those states instead of a raw error.
5. **Verify:** stubbed-fetch harness (pattern of the credit harness): no token → 401 and Ignav not
   called; cap reached → 429 and Ignav not called; cache hit → no Ignav call + no usage row; sweep with
   mixed cached/uncached cells charges only uncached; concurrency never exceeds 4. Then one real
   signed-in sweep on the deployed site.
6. **Docs/env:** `server/.env.example` gets `FARE_MAX_PER_DAY`, `FARE_CACHE_TTL_HOURS`,
   `FARE_SWEEP_MAX_CELLS`; README note; apply migration (user runs it in Supabase, as with 0001–0004).

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Ignav rate limits a 60–90 cell sweep | Med | Med | Concurrency 4, cache, partial results stream back; cells that fail show "—" and can be retried |
| Sweep latency too slow for the UI | Med | Med | Fill the grid progressively (return cheapest cells first / poll), cache aggressively, default to a 7×1 row first and expand on demand |
| Open-jaw prices misleading vs separate one-ways | Low | Med | Also price two one-ways for the top option and show the cheaper |
| Stale cached prices | Med | Low | Show "as of Nh ago"; re-search the chosen cell before adding legs |
| Signed-out users hit a wall on Flights | High | Low | Clear sign-in prompt; non-fare parts of the app stay open; anonymous-session taste on the backlog |
| Gateway suggestions wrong (closed/tiny airports) | Med | Low | Validate every code via `/flights/airports`; curated table first; ≤2 per end |

## Dependencies
- Supabase migration applied by the user (0005).
- Vercel env: existing `SUPABASE_URL` / service key / `IGNAV_API_KEY`; new optional FARE_* vars.
- Ignav `/fares/search` (1–2 legs) — verified in openapi.json 2026-09-26.

## Open Questions
- Default "cheapest ↔ easiest" weight ($/hour, $/stop) — start at $25/h, $40/stop, tune by feel.
- Grid default: full ±3×±1 immediately, or a 7-day row first with "expand"? (Leaning row first.)
- Should the trip page show a compact "cheapest way there & back" teaser once cached?

## Decisions Log
| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Account wall | None for the app; sign-in only for live fares + managed AI | Keeps the free local-first layer and first-visit experience; gates only what costs money | 2026-09-26 |
| Fare access | Signed-in on the deployed site; local helper unrestricted | `/flights/*` was open to anyone; sweeps multiply quota use | 2026-09-26 |
| Cost model | No credits for fare searches in v1; daily cap (150) + cache | $0.002/search makes normal use negligible; the cap stops scripted abuse | 2026-09-26 |
| Where sweeps run | Server-side `/flights/sweep`, concurrency 4 | Cap + cache coherently, one request from the browser | 2026-09-26 |
| LLM + fares | Precomputed summary in context; no model-initiated searches in v1 | Cheap, testable, can't burn quota | 2026-09-26 |
| Open-jaw | Ignav `/fares/search` with 2 legs | Supported per openapi (1–2 ordered legs, independent endpoints) | 2026-09-26 |
| Anonymous sessions | Backlog | Worth it for signup conversion later; needs abuse controls | 2026-09-26 |
| Sweep time budget (FO1 build) | Server stops starting searches after 45s; rest return `pending`, client re-requests | Measured live: round trip ~3.4s, 4-cell sweep ~10s, **open-jaw ~26s/search** — a 21-cell open-jaw grid can't fit one request; re-requests make the grid fill progressively and finished cells come back from cache | 2026-09-26 |
| Fare rows vs AI rate limit (FO1 build) | Migration 0005 redefines `recent_usage_count` to skip `fare_search` | It counted every usage row, so one sweep would have rate-limited the user's AI for a minute | 2026-09-26 |
| Airport autocomplete | Stays open (not gated) | Needed before sign-in makes sense; the helper already caches it; low volume | 2026-09-26 |
| Fare totals (FO2) | Ignav prices are the total for all travelers (verified: 2 adults = 2×); scores are per traveler (fare ÷ travelers + per-person ground + $25/h + $40/stop, × `ease`) | Keeps penalties comparable to what one person pays; UI shows totals | 2026-09-26 |
| Backtrack cost (FO2) | Use the trip's own leg for that pair if it has numbers, else distance: ≤700 km train (~80 km/h, $0.12/km), beyond that a short flight | No extra AI call or credit; labeled as an estimate | 2026-09-26 |
| Tests (FO2) | `npm test` = `node --test tests/` (built-in runner, no new deps); pure modules get real tests in the repo | Scratch harnesses weren't re-runnable by anyone else; mutation-checked the new suite | 2026-09-26 |
| Gateway sources (FO3) | Curated table (metros + airport-less places) → Ignav airport search filtered to the stop's country + same city, minor fields skipped → AI suggestions only when both are empty, each verified via Ignav + ≤250 km | Airport search is name-based ("Florence" → Florence SC, not FLR); the table covers the known traps; AI fills the long tail without trusting it blindly | 2026-09-26 |
| Airport access legs (FO3) | Nominatim-geocode each airport (name → code → city fallbacks), distance → ~60 km/h + 20 min, $0.15/km; counted in the score; unlocatable → `unknown`, no access cost | A "nearby hub" isn't free (KIX is 81 km from Kyoto); OSM names don't always match Ignav's | 2026-09-26 |
| Traveler override (FO3) | `segment.gateways` (codes) wins over suggestions; set by the FO4 UI | The traveler knows their airports | 2026-09-26 |
| Staged pricing (FO4) | 1) every route on one anchor date → 2) best two routes × 7 days → 3) on request, best route × ±1 day length; reversed-stop routes only for the primary airports and informational | 12 routes × 7 days would be ~84 searches and minutes of open-jaw latency; staging keeps a first answer ~30–45s and a full grid ~2 min, most repeats from cache | 2026-09-26 |
| Using an option (FO4) | `applyOption`: dates + length + one flight leg per home hop (named like the hops, airports/connections in fields + notes), replacing old home-hop legs; saves the chosen airports on the stops; one `onRevise` step (⌘Z undoes all) | Legs must sit on the route or the trip audit flags them; one undo for one decision | 2026-09-26 |
| Card resets (FO4) | Reset priced results only when stops/airports/home/travelers change — not dates or length | "Use these" changes the dates itself; cells stay valid for their own dates | 2026-09-26 |
| Assistant + fares (FO5) | `lib/fareStore.js`: the card saves a diverse set of ≤10 priced options (cheapest overall, top by rank, best + cheapest per route and per length) per trip, keyed to the trip's shape, expiring with the 8h fare cache; the edit prompt gets them with short refs + rules; no model-initiated searches | The chat explains real tradeoffs without spending searches; "use the cheapest" must see the actual cheapest | 2026-09-26 |
| Chat can use an option (FO5) | New op `{op:'use', target:'fareOption', id:'F2'}`, applied in App before other ops via `applyFareOps` → the same `applyOption` as the card; one AI edit (Apply / Undo); refs never shown to the traveler | Setting dates alone would leave flights out of sync; one path for card and chat | 2026-09-26 |

## Guests — signed-out taste (anonymous sessions)
Date: 2026-09-26

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Mechanism | Supabase anonymous sign-in, started lazily on a signed-out visitor's first live-fare or managed-AI call (then retry); browsing never creates one; if disabled in Supabase, fall back to the sign-in prompt | Keeps the no-account-wall decision; existing per-user ledger/caps apply unchanged | 2026-09-26 |
| Allowance | 3 one-time AI credits, 25 fare searches/day, 40 background calls/day; no monthly top-up | Enough to see one comparison + a couple of assistant turns | 2026-09-26 |
| Abuse control | Per-IP daily cap on all guest usage (150 rows), IP stored only as a salted hash (`usage_events.ip_hash`); plus Supabase's own anonymous sign-in rate limit | Anonymous users are free to mint; per-user caps alone don't bound cost | 2026-09-26 |
| Guest → account | Normal sign-up/sign-in (no identity linking); trips live in the browser and merge on sign-in; `ensure_free_grant_v2` gives the signup grant if the same user id ever becomes permanent | Avoids Supabase manual-linking config; the trips promise holds via the existing merge | 2026-09-26 |
| CAPTCHA | Not in v1 | The IP cap bounds cost; add Turnstile if abuse shows up | 2026-09-26 |

## Chat history per trip (a44747)
Date: 2026-09-26

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Model | Many conversations per trip; the assistant works in one — the latest unless idle 6h (then the next message starts a new one), "New chat", or "Continue" (pinned) | Short prompts + a browsable history; user picked button + 6h idle | 2026-09-26 |
| Where | "Chats" tab in the trip bar (count): list newest first with date, messages, changes applied / flights chosen; open → transcript with timestamps and what each reply proposed/applied; Continue, Delete, Clear all | User picked a tab over a rail dropdown | 2026-09-26 |
| Brainstorm link | Promoting an idea attaches the brainstorm as "How this trip started" (read-only); plans also list their proposal's conversations | Keeps the trail from idea → proposal → plan | 2026-09-26 |
| Storage | `lib/chats.js` module store (useSyncExternalStore), one localStorage key, old per-trip threads migrated once; synced to `trip_chats` (0007, RLS own rows) like trips — LWW by updatedAt, tombstones, pull-merge on sign-in, debounced incremental push | Local-first + cross-device, no new sync model | 2026-09-26 |
| Privacy / retention | Only the owner can read (RLS); kept until deleted; deleting a trip deletes its chats; flight-offer lists trimmed to 5 when saved | Chats can hold personal plans; keep rows small | 2026-09-26 |

## Trip audit layer 2 — AI consistency pass (da94b7)
Date: 2026-09-26

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Scope | `lib/auditAi.js`: user-initiated ("Check with AI", 1 credit on managed AI) — finds what the deterministic audit (layer 1) can't: wrong-city activities, travel-time/pace mismatches, budget contradictions, seasonal/closure timing, chat asks the plan ignores, missing basics (no lodging) | Same posture as `lib/cautions.js` — never auto-spend a credit; deterministic checks stay free and instant | 2026-09-26 |
| Fix protocol | Issues carry ops from the same patch protocol the assistant uses, restricted to a safe subset (update/move/remove activity, update segment, update field) — restated in the prompt since `aiClient.js`'s `OP_PROTOCOL` isn't exported | Reuses `applyOps` (one undoable step via `onRevise`) instead of inventing a second apply path | 2026-09-26 |
| Validation | `runAiAudit` normalizes defensively: drops issues with no title, caps at 6, and drops individual ops whose id doesn't exist in the record or whose op/target isn't in the allowed subset — an issue can still surface with `ops: []` (no Fix button) rather than being dropped entirely | A model slip (invented id, wrong target) shouldn't sink an otherwise-real finding, but must never reach `applyOps` unvalidated | 2026-09-26 |
| Caching | `record.aiAudit = { issues, sig, at }`, written via the same `onRevise` path as everything else (like `cautions`) — no special "not a user edit" carve-out exists for AI-derived caches in this codebase, so this doesn't invent one | Consistent with the one precedent (`GoodToKnow`/`cautions.js`) rather than adding new undo-history semantics | 2026-09-26 |
| Fingerprint | `aiAuditSig`: stops+nights, dates, activities (id/name/day/segment/time), pace, budget, travelers, interests — notes/lodging text excluded | Matches what the prompt actually reasons over; avoids "stale" nags for cosmetic edits | 2026-09-26 |
| Fixing/dismissing | Fixing an AI issue applies its ops **and** strips that issue from the cached list in one `onRevise` (so it doesn't linger looking unresolved); "Fix all" pools deterministic + AI issues; Dismiss (×) removes an issue from the cache without touching the trip | The cached AI list, unlike `auditTrip()`, isn't recomputed live from the record, so resolution has to be explicit | 2026-09-26 |
| Testability | `runAiAudit(record, settings, { ask })` takes an injectable `ask` (defaults to `askPrompt`) instead of mocking the `aiClient` module | No existing ESM-mocking convention in this test suite; this keeps `auditAi.test.mjs` network-free without inventing one | 2026-09-26 |
| Verified live | Ran a real check through the local helper (`npm run ai`, no mocks) against a deliberately inconsistent trip — got back a wrong-city activity, a budget contradiction, and a missing-lodging issue, all with valid ops on real ids | Confirms the prompt + normalization work against actual model output, not just mocks | 2026-09-26 |

## Free official data (87dfc0)
Date: 2026-09-26

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Exchange rates | `lib/fx.js`: Frankfurter (ECB) as primary, `open.er-api.com` merged in only for currencies Frankfurter lacks (e.g. VND); cached in localStorage 12h, in-flight dedupe per base, `deps` injection (`fetch`/`storage`/`now`) for tests, never throws | Matches the research doc's ranked shortlist; per-currency fallback (not whole-source) keeps ECB's better-trusted numbers wherever it has them, and avoids a second network call on every load | 2026-09-26 |
| Where shown | A compact "Money" card on the City page (Overview, right rail): "1 {trip currency} ≈ N {local}", rate date, and a source credit link (Frankfurter or ExchangeRate-API, whichever actually served that currency) | Where a traveler is actually converting prices in their head; understated, not a new budgeting surface | 2026-09-26 |
| Budget math (`lib/budget.js`) | **Not** touched — left as-is | It already assumes every cost string is in the trip's own currency (no per-item currency field to convert from); wiring real FX into it would mean inventing a mixed-currency-costs feature that doesn't exist today. Flagged here per the task's "skip and note" instruction | 2026-09-26 |
| Country facts | One-time build (`scripts/build-country-facts.mjs`) queries Wikidata SPARQL (P2853 plug, P2884 voltage, P1622 driving side, P474 calling code, P38→P498 currency, P2852 emergency number) for all sovereign countries → `src/data/countryFacts.json` (196 countries, ~25.5 KB) | REST Countries is dead (confirmed in research doc); Wikidata is CC0 and doesn't need a runtime call/key; baking it avoids a live SPARQL dependency in the shipped app | 2026-09-26 |
| Plug-letter mapping | Wikidata's P2853 values are plug *standards* (e.g. "BS 1363", "Europlug"), not IEC letters — mapped by hand (`PLUG_LETTER` in the build script) from the ~14 distinct items actually used by sovereign countries; a few ambiguous items (e.g. the catch-all "British and related types" item, which doesn't resolve to one letter) and known Wikidata gaps (India's Type M, South Africa's full set, Thailand entirely untagged) are hand-fixed in `MANUAL_OVERRIDES`, noted in the script's comments | Wikidata doesn't have a clean "IEC plug letter" property; the override list is small and reviewed against the task's own sanity list (JP, GB, US, PT/FR/DE, AU, IN, BR all check out) | 2026-09-26 |
| Mains frequency | Not a queryable Wikidata property for this — heuristic (`≤127V → 60Hz, else 50Hz`) with a short hand-checked `FREQ_OVERRIDES` list for exceptions (Japan's 50/60 split grid, Brazil, South Korea, etc.) | Good enough for "will my charger work" without a data source that doesn't exist | 2026-09-26 |
| Where shown | City page Overview: a "Practical" card (plug letters + voltage/Hz, driving side, calling code + emergency number). Good to know: one `Plug` line per country whose plugs or voltage differ from the traveler's home, only when home resolves to a country | Understated, not gating anything on AI | 2026-09-26 |
| Home → country | `lib/countryFacts.js#homeCountryCode`: tries the home name as a country name first (rare), else a small hand-built table of ~50 major hub-airport IATA codes → ISO2 | `settings.home`/`trip.startLocation` store a city + airport code, not a country, and there's no live geocode call available cheaply here; explicitly best-effort — unresolvable homes just skip the comparison (per the task's own allowance) | 2026-09-26 |

## AI settings + model picker
Date: 2026-09-27

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Default | "Trip Fairy" (id `auto`) — our routing: the right model per kind of task (server/llm.mjs modelsForKind); background work (places, weather…) always uses it | Most people shouldn't have to think about models | 2026-09-27 |
| Catalog | Server-side `server/models.mjs` (auto, Sonnet 5, Haiku 4.5, gpt-oss-120b, Opus 5.5 premium); published on /ai/health with availability; api/ai/plan.js refuses anything outside it (400 model_unavailable); MODELS_DISABLED env to pull one | The server is the security boundary — no arbitrary expensive models on our key | 2026-09-27 |
| Pricing | Tiered: premium ×3 on the whole turn (base + outcome surcharge); everyday models and auto unchanged | User picked tiered; keeps Opus-heavy use paying its way | 2026-09-27 |
| Scope | Per conversation (saved on the conversation / brainstorm session); new chats start on the provider's default | User picked per conversation | 2026-09-27 |
| Allow list | Settings → AI: per-provider checkboxes (Trip Fairy always on) + default for new chats; stored in settings (allowedModels/defaultModel); a blocked or unavailable pick falls back to the default | A preference, not security | 2026-09-27 |
| Own Claude Code / key | Same picker with Claude models; "Trip Fairy" = Haiku for background, Sonnet for edits/chat, done client-side; non-Claude picks never sent there | Consistent UX across providers | 2026-09-27 |
| Settings | Tabbed: General · AI · Account & credits | Room for the AI controls; credits/sign-in in one place | 2026-09-27 |

## Bot check for guests + email sign-in (2026-09-27)

Anonymous guest sessions cost nothing to create, so the per-IP cap was the only
brake on scripted abuse of the guest allowance. Supabase's built-in "Bot and
Abuse Protection" (Cloudflare Turnstile) now guards session *creation*:
`src/lib/captcha.js` renders an invisible, single-use Turnstile check and passes
its token on guest sign-in, email sign-up / log-in, magic link and password
reset. Google OAuth isn't covered (Google does its own checks).

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Where to enforce | Supabase Auth CAPTCHA, not our API | Stops bot sessions from existing at all; no server code; the per-IP cap stays as a second layer | 2026-09-27 |
| Widget | Turnstile, `interaction-only` | Free, no puzzles for most people; a box appears only when Cloudflare is unsure | 2026-09-27 |
| Rollout | Off until `VITE_TURNSTILE_SITE_KEY` is set | Deploy the key first, then enable CAPTCHA in Supabase — the reverse order breaks sign-in | 2026-09-27 |

---

# Plan — Broader ideation: seasons, routes, options & versions (5705ac)
Date: 2026-09-27
Status: Draft
Brainstorm: docs/brainstorm.md → "2026-09-27 · Broader ideation"

## Overview
Make the early, undecided stage of a trip explorable:
- **When to go:** real climate normals, per stop and for the whole route.
- **Other shapes of the trip:** throwaway drafts and plans, compared side by side.
- **Real choices inside a plan:** leg modes, stays, food, things to do — each a shortlist with one
  pick.

Builds on the proposal → plan lifecycle (N1–N5), T2 leg options, and the fare optimizer (FO1–FO5).

**Reality check against the code (2026-09-27):**
- Legs already carry `options[]` (v6) with an on-demand "compare ways to get there" panel on
  TripPage. BI2 is therefore small: finish and unify, don't build.
- Weather today is an LLM guess of one high per city (`derive.js deriveWeather`).

## Goals & Success Criteria
- A proposal with open dates shows, per stop, 12 months of typical high/low, rainy days and
  sunshine, plus a route verdict ("Best: May, Sep–Oct"). No AI call is involved.
- A dated trip shows real normals for its month. The LLM weather call is gone, with the LLM kept
  only as a fallback.
- Two or more alternatives (plans or drafts) can be compared on one screen with differences
  highlighted, including on phones.
- "Try a version where…" produces a draft in one step. "Keep as plan" promotes it.
- Every item with alternatives uses one shape (`options[]` + `pickedId`). Audit, budget and the
  assistant read only the pick.

## Scope
### In Scope
- Climate normals service with a shared cache, a when-to-go UI and a route verdict (BI1).
- Unify leg options with live flight fares and the pick semantics (BI2).
- Compare view, drafts, and "Keep as plan" (BI3).
- AI route alternatives as drafts (BI4).
- Shortlists for stays / food / do, with a `pick` op (BI5).

### Out of Scope
- Crowd or price seasonality from paid data. Fare seasonality stays an on-request sample
  (BI4 at most).
- School-holiday calendars — only public holidays exist (`holidays.js`).
- Nested versions of versions. Drafts don't have drafts.
- Real-time forecasts. Normals only; a forecast for trips under 14 days out is a later add.

## Tech Stack & Architecture
Same stack: React/Vite client, `server/*.mjs` shared by the dev helper (127.0.0.1:8787) and Vercel
`api/*`, and Supabase.

**Climate data — decision needed.** Three candidates:
| Source | Accuracy (Lisbon Jan / Jul highs; real ≈ 15 / 28 °C) | Cost / terms | Verdict |
|---|---|---|---|
| **Open-Meteo archive** (ERA5, ~10 km), 10-year daily → monthly means | 14.6 / 27.7 ✔ | Free tier is **non-commercial**; commercial use needs their paid API plan | **Recommended.** Cache per ~0.1° cell forever, so calls stay tiny. `OPEN_METEO_API_KEY` switches to the commercial endpoint. |
| NASA POWER climatology (0.5° grid) | 18.1 / 32.4 ✘ (coarse cells mix coast and inland) | Free, public domain | Fallback only |
| Keep the LLM | unverifiable | AI credits | Last-resort fallback |

**Flow:** client → `GET /climate?lat&lng` → `server/climate.mjs`:
1. Snap to a 0.1° cell.
2. Look up Supabase `climate_normals`.
3. On a miss, fetch the 10-year daily archive (~135 KB, ~1 s) and reduce it to 12 months of
   `{hi, lo, rainDays, sunH}`.
4. Store the result.

The client also caches per cell in localStorage. Normals don't change, so there is no TTL.

**Options pattern (BI2/BI5):** `options[]` + `pickedId` on the item. The picked option's fields
stay mirrored on the item itself, so every existing reader (audit, budget, map, prompts) keeps
working unchanged.

**Drafts (BI3/BI4):** `drafts[]` on the proposal record (capped at 3). Each draft is a light trip
shape: `{id, name, stops:[{city,country,nights}], startDate?, summary, metrics}`. "Keep as plan"
runs the existing snapshot escalation.

## Milestones
| # | Milestone | Description | Dependencies |
|---|-----------|-------------|--------------|
| BI1 | Season explorer | Climate normals service + shared cache; 12-month when-to-go per stop; route "best months" verdict; replaces LLM weather (LLM kept as fallback) | Migration 0008 (user OK); climate-source decision |
| BI2 | Leg options, finished | Unify `options[]` + `pickedId` on legs; live Ignav fare as the flight option; options visible on proposals; audit/budget read the pick | — |
| BI3 | Compare + drafts | `drafts[]` on proposals; compare view for plans + drafts (phone cards); "Try a version where…" → draft; "Keep as plan" | BI1 (weather-fit metric), BI2 (travel-time metric) |
| BI4 | Route options | "Other ways to do this trip" → 2–3 AI route drafts with travel time, rough cost, weather fit; optional sampled fares via the fare optimizer | BI3 |
| BI5 | Shortlists | `options[]` + `pickedId` for stays (price tiers) and do/food pools; Swap / More like this; a `pick` op for the assistant | BI2 pattern |

## Task Breakdown

### BI1 — Season explorer (mid-depth)
**Server**
- `server/climate.mjs`:
  - `cellOf(lat,lng)` → 0.1° key.
  - `fetchNormals(cell)` → Open-Meteo archive for the last 10 full years:
    `temperature_2m_max/min`, `precipitation_sum`, `sunshine_duration`.
  - `reduceMonthly(daily)` → 12 × `{hi, lo, rainDays (≥1 mm), sunH}`, rounded.
  - `getNormals(lat,lng)` → cache-first.
  - Uses the customer endpoint + key when `OPEN_METEO_API_KEY` is set.
- `supabase/migrations/0008_climate_normals.sql`:
  - Table: `cell text pk, lat, lng, months jsonb, source text, years text, fetched_at`.
  - RLS: public read, service-role write.
- `api/climate.js` + a vercel.json rewrite `/climate`. The dev helper gets the same route; the
  Vite proxy gets `/climate` → 127.0.0.1:8787.
  - Response cache: `s-maxage=31536000, immutable`.
  - Validate lat/lng ranges; 400 otherwise.

**Client**
- `src/lib/climate.js`:
  - `loadNormals(lat,lng)` with a localStorage cell cache and in-flight de-dupe.
  - `monthScore(m, prefs)`: comfortable highs (~18–28 °C by default; warmer when interests include
    beach), penalizing rainy days.
  - `routeVerdict(stopsNormals)` → best months across all stops, and their spread.
  - All pure and unit-tested.
- `WeatherStrip` becomes **When to go**:
  - **Dated trip:** that month's hi/lo + rain days per stop from normals, labeled "typical ·
    May (2015–2024)".
  - **Dates open / proposal:** a 12-month row per stop (a colour cell per month, best months
    marked) plus a route verdict line.
  - Tapping a month opens the dates popover. Holiday markers come from `holidays.js` when dated.
- Fallback chain: normals → existing LLM `deriveWeather` → the neutral placeholder.
- Audit: the weather cache signature changes to the normals source, so the audit doesn't flag
  stale LLM weather.
- Assistant context: add a compact normals summary for the trip's stops, so the chat can answer
  "when should I go?" from data.

**Acceptance**
- Lisbon normals are within ~1 °C of published values.
- A second load of the same city makes no network call.
- A proposal with open dates shows 12 months and a verdict.
- A dated plan shows its month.
- There is no AI call for weather when normals load.
- Works at 375 px.
- Tests cover `reduceMonthly`, `monthScore` and `routeVerdict`.

### BI2–BI5
High-level only for now; expand when each starts.

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Open-Meteo commercial terms | High (we sell credits) | Med | Paid plan via env key before public launch; the cache keeps call volume tiny; NASA POWER as an emergency fallback |
| Archive fetch slow (~1 s × stops) on first view | Med | Low | Parallel per stop, shared cache, skeleton UI |
| Coordinates missing on a stop | Med | Low | Stops are already geocoded (`lib/geo.js`); otherwise the LLM fallback |
| Options/drafts bloat synced trip rows | Med | Med | Caps (5 options/slot, 3 drafts); drafts hold no activities |
| Unpicked options leak into audit/budget/prompts | Med | Med | The pick is mirrored onto the item; readers never read `options[]` |
| Alternative generation burns credits | Med | Med | On request only; priced per action; background model for bulk |

## Dependencies
- Supabase migration 0008 — applied only with your OK.
- Open-Meteo (paid plan for commercial use — your call and account).
- Existing: `lib/geo.js`, `holidays.js`, T2 leg options, fare optimizer, escalation snapshot.

## Open Questions
- Climate source and plan: Open-Meteo paid now, at launch, or NASA POWER until then?
- Month-score preferences: fixed comfort band, or tuned by trip interests (beach, ski)?
- Compare view on phones: cards vs a two-column diff.
- Credit prices for "generate a version / routes / shortlist".

## Decisions Log
| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Alternatives model | Plans + drafts for structure; `options[]` + `pickedId` for contents | Avoids nested versions; one shared pattern | 2026-09-27 |
| Drafts | Throwaway, stored on the proposal, "Keep as plan" promotes | User wants both quick comparison and durable versions | 2026-09-27 |
| Shortlists | Proposals and plans, one pick, swap anytime | User choice | 2026-09-27 |
| BI2 scope | Finish/unify existing leg options rather than build | `options[]` + panel already shipped (v6) | 2026-09-27 |
| Pick mirroring | The picked option's fields are copied onto the item | Every existing reader keeps working | 2026-09-27 |
| Climate cache | Server + Supabase per 0.1° cell, no TTL; plus a client cache | Normals are static; minimizes paid calls | 2026-09-27 |

**BI1 update (2026-09-28):** Open-Meteo's pricing page shows three things.
- Historical data needs the **Professional** plan; Standard excludes it.
- A 10-year fetch counts as ~260 calls, since every 2 weeks of data is one call. The free tier
  (10k calls/day) therefore covers ~38 *new* cells a day.
- CC BY 4.0 attribution is required. It is now shown on the When to go card.

Migration 0008 is applied, and a production write was verified.

**BI2 shipped (2026-09-28).** A reality check showed `options[]` and the options panel already
existed, on proposals too, and that the budget already read the pick through mirrored fields. BI2
therefore became `src/lib/legOptions.js`:
- **`pickLegOption`:** switching away from a chosen flight stashes its details in that option's
  `snapshot` and clears the flight-only fields; switching back restores them. This fixes a real bug
  where a train leg kept a stale booking link.
- **Chosen flights show as themselves** in the panel ("your flight").
- **Flights page / "Use these dates" picks** keep the replaced leg's alternatives
  (`inheritOptions`).
- **Refreshed estimates never overwrite** a live fare or a stashed flight (`mergeOptions`).
- **"Check live flight price" on dated plans:** one Ignav one-way search at 1 adult, to compare
  with the per-person estimates. The hop date comes from the day model.
- **Assistant mode changes** (`update travel {mode}`) go through the same pick.
- **Option order** stays stable as the pick changes.

**Known and pre-existing, not changed:** the budget adds per-person estimates to all-traveler
chosen fares without scaling by traveler count.

### BI3 — Compare + drafts (mid-depth, 2026-09-28)
**Data**
- `proposal.drafts[]`, at most 4 per proposal. Each draft is
  `{ id, name, summary, prompt, baseId, createdAt, stops: [{ city, country, nights, lat, lng }], startDate?, month? }`.
- Drafts live on the root proposal, even when drafted from one of its plans (`baseId` records
  which). They hold no activities and no legs, and are additive to the synced record.

**Generation.** "Try a version where…" → `askPrompt`, priced as one reasoning turn (1 credit on
managed AI). The draft JSON has no `ops`, so outcome pricing stays at 'prompt'.
- **Prompt input:** the base trip context, climate normals when cached, and the request.
- **Reply:** `{ name, summary, stops, startDate?, month? }`. Parse, validate and cap it
  (`lib/drafts.js normalizeDraft`).

**Compare view** — a new "Versions" tab (`page=versions`).
- **Columns:** the proposal, then its plans, then its drafts.
- **Rows:** route (cities that differ from the first column are highlighted), nights / stops /
  moves, when (dates or month) with weather fit from BI1 normals, travel time between stops (real
  legs where they exist, otherwise a distance-based estimate), budget (`computeBudget`), and summary.
- **Phones:** snap-scrolling cards with the same rows.

**Actions**
- **Open:** plan or proposal.
- **Keep as plan:** a draft becomes a plan via `draftToPlan`. It snapshots the base and replaces
  its stops with the draft's. Activities follow their city when that city survives; others are
  dropped. The draft is then removed.
- **Discard:** delete the draft.

**Acceptance**
- A Lisbon + Porto proposal, asked for "a version with Seville instead of Porto", gets a draft whose
  columns show the swap highlighted.
- "Keep as plan" opens the new plan with Seville, and Lisbon's activities are kept.
- Works at 375 px.
- Pure logic (`normalizeDraft`, `draftToPlan`, metrics) is unit-tested.

**BI3 shipped (2026-09-28).**
- **Code:** `src/lib/drafts.js` holds the pure logic (normalize, cap, `draftToPlan`,
  `versionMetrics`). `src/pages/VersionsPage.jsx` is the new "Versions" tab.
- **Verified live:**
  - Drafted "we swap Porto for Seville" (1 credit): Lisbon 4 + Seville 4, ~5h36 between stops,
    "Best: May".
  - "Keep as plan" opened a new plan with coordinates. It kept the home → Lisbon leg and
    removed the draft.
- **Change from the plan:** budgets compare *on the ground* (stays + food + activities). Travel is
  shown separately ("+ $1.3k travel so far" / "not priced yet") because drafts have no legs, so a
  total would flatter them.
- **Phones:** section tabs tightened so five fit at 375 px (a scrolling row would clip the Cities
  dropdown); cards snap with 16 px scroll padding.

**BI4 shipped (2026-09-28).**
- **"Other ways to do this trip":** one `askPrompt` call (1 credit) returns 3 route drafts, each
  with an `angle`. `normalizeRoutes` drops repeats and the current route.
- **"Price flights from <home>" on a draft:** one live Ignav search. It is a round trip when the
  route starts and ends at the same airport and returns home, otherwise open-jaw. The dates are
  the trip's own, else the 15th of the draft's month / the route's best month, at least 3 weeks
  out (`sampleDates`). The fare is stored on the draft as
  `fares: { price, currency, dep, ret, sampled, route }`.
- **Verified live on the Portugal proposal:**
  - Routes: "Lisbon Slow Stay" (Fewer moves), "Porto, Douro & Guimarães" (Northern swap),
    "North to South" (Better order, via Coimbra).
  - "North to South" priced at DEN→OPO · LIS→DEN, $1,880 for 2, sampled Sep 15–23, 2027.

**BI5 shipped (2026-09-28).** A reality check showed the candidate pools already existed
(`segment.detail.pois`: 4–5 stays, 6–8 food / do per stop), so BI5 adds the *picks* on top rather
than a new `options[]` structure. The code is in `src/lib/shortlist.js`.
- **Stays:** one per stop in `segment.stayPick`. On plans it is mirrored into `lodging`, but a
  hand-typed lodging is never overwritten. Stays carry Budget / Mid-range / Splurge tiers.
- **The budget's lodging** uses the picked stay's quoted price. It reads the trip-currency amount,
  taking the middle of a range: "~$65–90 (€60–80)" → $78. If there's no quote it uses the price
  level's norm; stops without a pick keep the $120 norm.
- **Food / things to do:** `poi.picked` puts a place on the traveler's list, with a "My list"
  filter. Picks sort first.
- **Swap / More like this:** a background AI call per click; only new, same-kind places are kept.
- **"Refresh suggestions"** now keeps listed places and the picked stay.
- **Assistant:** the new op `{ op:'pick', target:'place', data:{ segmentId, name, on } }`. Its
  context lists stays with prices, the pick, and the list, and its proposal cards read
  "Stay at …" / "Add to your list …".
- **Verified live:**
  - Picked Casa Amora → lodging $892.
  - Listed Time Out Market → "More like this" added 3 food halls.
  - Asked the assistant "pick the cheapest stay in Lisbon" → it proposed the correct pick ops;
    Apply switched the stay.

---

## Pricing display: per traveler or trip total (2026-09-28) — replaces #3a7a04's "group total"

**Decision.** Money is normalized **per traveler** internally, and totals are derived (× travelers).
The traveler chooses which leads in Settings → General → **Show prices**: *Per traveler* (default)
or *Trip total*. The other figure shows underneath in smaller text whenever there's more than one
traveler. This replaces the group-total approach from commit deaefac rather than stacking on it.

| Source | Basis → per traveler |
|---|---|
| Chosen Ignav fare (`priceAtSelection`), hand-typed leg cost | total → ÷ travelers |
| AI travel estimate, live one-way check (`derived` / `costBasis:'pp'`) | already per person |
| Activity cost marked "pp" / "per person" | already per person |
| Plain activity cost | total → ÷ travelers |
| Food norm | per person per day |
| Stays | per night per **room** → × `rooms` ÷ travelers |

- **Rooms:** a new trip field `rooms`, defaulting to ceil(travelers / 2) and editable next to
  Travelers ("we assume 2 per room"). The assistant can set it, and it's in the assistant and
  trip-audit context.
- **Budget target (`trip.budget`) is per traveler.** It's compared per traveler, or as target ×
  travelers in Trip total mode. The labels and AI prompts say so. Existing budget values aren't
  migrated.
- **One formatter:** `src/lib/price.js` (`priceLines`, `formatMoney`) and
  `src/components/Price.jsx` (stack / inline / short variants; the mode comes from
  `PriceModeContext`, provided by App from `settings.priceMode`). Used by the budget donut, leg
  headers and option chips, Flights results, the Best-way card (cells, list, trade-off notes), the
  date finder, Versions cards (on the ground, travel so far, draft fares), and the city-page stay
  cards (per-traveler nightly price).
- `computeBudget` returns `perTraveler` and `total` for every segment, plus `travelers` and `rooms`.
- **Settings are stored per device,** like every other setting today; there's no account-level
  settings sync yet.
- **Verified:** unit tests; the smoke test (now also covering flight results and Trip total mode);
  the browser at desktop and 375 px with 1, 2 and 3 travelers, 1 vs 2 rooms, and both modes.

**Follow-ups (2026-09-28).**
- **Activity prices** in the itinerary go through the shared `<Price>` too ("pp" costs stay per
  traveler; plain costs are totals ÷ travelers). Non-numeric costs like "Free" show as written.
- **Light / dark mode:** Settings → General → Theme = Dark (default, the original look) / Light /
  System.
  - `src/lib/theme.js` sets `<html data-theme>`, and an inline script in `index.html` applies the
    saved theme before first paint, so there's no flash.
  - `src/index.css` has a `[data-theme="light"]` palette over the same tokens. The accent and
    neutral ramps are inverted, so tinted chips and bubbles flip correctly.
  - The basemap has a light palette (`tripFairyMapStyle(theme)`), and maps rebuild on a theme
    change.
  - Settings previews the theme live; Cancel restores the saved one.
  - The few hard-coded dark colours (image placeholders, title shadows) now use tokens.

**Quick fixes (2026-09-28).**
- **Implausible travel options** (e.g. a 58h "drive" Denver → Lisbon) are dropped when derived and
  hidden in the options panel. Ground modes are capped by their own estimate: walk 6h,
  car/bus/train 24h, ferry 48h. The current pick is always shown.
- **Typed costs** in the trip editor pick their basis from the text: "pp" means per person,
  otherwise it's a trip total. A typed cost on an AI-estimated leg stops counting as per person.
  Placeholders and hints explain this.
- **Installed-app colours** follow the theme: the startup script and `applyTheme` set
  `theme-color`, the iOS status-bar style, and the `dark` class.
- **Production** at mytripfairy.com was checked and serves all of today's work (theme script,
  climate endpoint, AI health, latest bundle and lazy map chunk).

---

# Plan — My trips page (#1f2a81)
Date: 2026-09-28 · Status: Active

**Goal.** One place for everything you've planned: a list like Home's plus a map of every trip's
stops and route, each trip in its own colour, filterable.

**Model**, in pure `src/lib/myTrips.js`:
- **A "trip"** is a root proposal plus its plans. Orphan plans count as their own trip.
- **The lead version** decides what a trip shows: the most advanced plan (completed > booked >
  planned, then most recently edited), else the proposal. Status, dates, length, countries and the
  map route all come from it.
- **Colour:** trips get stable colours from an 8-hue palette that reads on both themes, assigned
  in list order (newest first).
- **Filters:** a text search (title, cities, countries); status (idea / planned / booked /
  completed); when (upcoming / past / dates open, relative to today); country; length (≤ 7,
  8–14, 15+ days).
- **Summary counts:** trips, countries, cities (a first step towards profile stats, #958e19).

**UI**
- **A global page** (`?page=mytrips`, like Home, with no trip bar), reached from a **My trips**
  tab in the header. Home's "Your trips" gets a "See all" link.
- **Map:** trip-coloured stop dots, with each trip's route as coloured lines. There are no
  travel-mode badges on the overview; clicking a stop opens that trip.
- **List:** a colour swatch, lead-version facts and a plan count. Filters are chips / selects
  that wrap on phones.
- **The assistant** on this page behaves like Home (brainstorm).

**Map changes:** legs take an optional `color`, a `badges` prop turns mode badges off, and a new
marker kind `trip` is a small coloured dot.

**Acceptance.** Every trip is listed and mapped in matching colours, filters narrow both,
clicking opens the trip, it works at 375 px and in light / dark, pure logic has tests, and a
smoke-test step covers it.

**My trips shipped (2026-09-28).**
- **New code:** `src/lib/myTrips.js` (pure, 4 tests, mutation-checked) and `src/pages/MyTripsPage.jsx`.
- **Map support:** coloured legs, `badges={false}`, and the `trip` marker kind in
  MapCanvas / OdMap / index.css.
- **Entry points:** a header tab and Home's "See all on the map →".
- **Verified in the browser** with 3 trips (idea / planned / completed) at desktop and 375 px, in
  light and dark: colours match between rows and routes, country / when / search filters narrow
  both the list and the map, a map dot or a row opens the trip, and back returns to My trips.
- **Smoke test:** the new page's layout plus two flow checks (35 checks in all).
- **Small follow-ups if wanted:** highlight a trip's route when hovering its row; remember filters
  between visits.
- **Map-led layout (2026-09-28, at Ryan's request):**
  - **Like a trip's overview:** the globe is a full-bleed sticky backdrop filling the page, and the
    title, counts and filters sit on a gradient over its bottom edge.
  - **Scrolling:** the list rises over the map as you scroll, while the map dims and re-frames the
    trips into the part still visible.
  - **Wheel zoom:** scrolling up at the top zooms the map (wheelMode 'atTop').
  - **No locations yet:** when no trip has a map location, the page keeps a plain layout instead of
    an empty globe.
- **Scroll-zoom on My trips goes straight out (2026-09-28).** MapCanvas `zoomOut` is `'home'`
  (the default: a trip page glides back to the trip's framing as you zoom out) or `'straight'`
  (My trips: zoom out around the current centre, stopping at the overview zoom). The smoke test
  checks both behaviours with real wheel events, and a deliberate break was caught.
- **Scroll lag fixed (2026-09-28).** My trips was re-framing the globe (cameraForBounds + jumpTo)
  on every scroll frame, because its covered strip grew with scrollTop. That moved the map 49
  times in one scroll sweep and made scrolling up into the scroll-to-zoom stutter. The strip is now
  fixed at the title + filters (it only changes on resize); dimming still follows the scroll. A new
  smoke check asserts the map doesn't move while the page scrolls, and it catches the old code.
- **Same landing scale before the content scrolls (2026-09-28)**, on both My trips and trip pages.
  - **The rule:** scrolling down at the top never moves the content until the map is back at its
    landing scale — the landing zoom (My trips, keeping its centre) or the full landing framing (a
    trip).
  - **Handled cases:**
    - zoomed in: it steps back out, as before;
    - zoomed out past the landing view or dragged away: it eases back first;
    - the content scrolled another way (scrollbar, keys): the map snaps back (catch-all).
  - **Wheel handling moved** from the map container to the page's scroll area (capture), so
    scrolls over the title, filters or list are gated too.
  - **A drag-inertia bug fixed:** easeTo's interruption of a still-coasting drag fired an
    immediate moveend that ended the return early.
  - **Checks:** 3 new smoke checks (41 in all); removing the gate or the catch-all is caught.
- **Landing size fixed for real (2026-09-28).** On the globe, MapLibre keeps the planet the same
  apparent size across latitudes by shifting the zoom *number* (≈ log2 of the cosine ratio; seen
  when a small drag changed zoom 6.861 → 6.840). My trips' straight zoom-out stopped at the
  landing zoom number, so after zooming in at another latitude it came back too big (1.87× at
  65°N vs a 39°N landing). The gate now uses the landing zoom at the current latitude
  (`landingZoom`). A new smoke check compares the globe's on-screen size at the moment the content
  starts scrolling with the landing view (±4%); it fails on the old code.

---

# Plan — Home page as a trip finder (#51a4c7)
Date: 2026-09-29 · Status: Active

**Direction (Ryan):** Home is about finding new trips.
- **Top:** a centred prompt input.
- **Below:** big, visual trip-suggestion panels that update with each prompt; any panel becomes a
  proposal with "Make it a trip".
- **Right:** "Trip qualities", everything specified so far (inferred from the prompts), plus
  fields the traveler can set by hand (when, length, travelers, budget per traveler, pace, flying
  from, vibe) and **options per prompt** (2–6, a saved setting).
- **Also on Home:** a "Saved for later" row.
- **Assistant:** hidden on Home, the chat transcript is secondary ("Show conversation" / History),
  and the top option is a rich card while the others are compact and expand on click.

**Model**, in pure `src/lib/tripFinder.js`:
- **Qualities** `{ month, length, travelers, budget (per traveler), pace, from, vibe[], travel,
  avoid[] }`. The AI returns what the conversation implies; manual fields override (and are marked
  as set by you).
- **Each prompt returns** `{ reply, qualities, trips: N × { title, summary, stops:[{city, country,
  nights, lat, lng}], highlights[], cost:{low, high} per traveler, gettingThere, why, tags[] } }`,
  validated and capped (`normalizeFinderReply`).
- **Make it a trip:** `tripToProposal` gives segments with nights and coordinates, length,
  interests, travelers, budget per traveler, pace, the home start, and notes from the summary and
  highlights; the conversation is attached.
- **Saved for later** reuses the ideas store: an idea can carry a full `trip` snapshot, and old
  ideas still render in compact form.

**Priced as today:** one chat turn (1 credit on managed AI) per prompt or "Update options".
Photos (the existing image lookup) and weather (BI1 climate normals for the chosen month) are free
and client-side. Cost ranges go through the shared price formatter (per traveler / trip total),
which is a first step on the price-ranges item (#5738f9).

### Build notes — 2026-09-29
- Shipped as planned: centered prompt, N option cards (featured "Best fit" + compact cards with More), qualities panel with hand-set overrides (pinned, persisted in `tf.finder.manual.v1`), "Options per prompt" 2–6 (`settings.finderCount`), "Update options" when qualities/count change, Saved for later, "Make it a trip" → new proposal with the option's stops, nights and coords.
- Side assistant hidden on Home; IdeasPage removed (its saved ideas live in "Saved for later").
- Costs use the new `PriceRange` (per traveler / trip total aware) — groundwork for #5738f9.
- Verified: 158 unit tests; smoke 45/45 incl. 4 finder steps with a mocked model (hand-set length + count reach the prompt; save; make-a-trip stops); real-model run; phone (dark) + desktop (light) screenshots.

### Revision — 2026-09-29 (layout + persistence)
- Full-width layout: options in the middle, laid out to fit one screen (3 across; 4 across on wide screens; 5–6 as two rows of slimmer cards); the right column holds trip qualities (compact one-line rows), the conversation, and saved for later.
- "Options per prompt" moved under the chat bar.
- The finder is a chat: the latest conversation (with each round's trip options) is restored on reload (App resumes `lastBrainstorm`); "New search" starts fresh. Earlier rounds' options can be viewed again from the conversation.
- Smoke: reload keeps the chat + options; viewing an earlier round and back.

### Revision — 2026-09-29 (design pass, frontend domain rules)
- Register: Product (the tool disappears into the task; photos carry the personality).
- Options: wide horizontal cards (photo left), two columns on xl; with an odd count the Best fit spans both. No image hover-zoom (motion rule).
- Side panel: flush right, full height, one surface split by dividers (no floating cards):
  trip qualities (only known values as rows; each marked "from the chat" or "pinned by you" with a pin toggle; unset fields as "+ Add" chips), the conversation (chat bubbles; each reply carries an "N options" round marker, the one on screen highlighted; auto-scrolls), saved for later as a disclosure.
- Phones: "Trip qualities" / "Conversation" tabs above the options.
- Detector clean on HomePage.jsx.

### Revision — 2026-09-29 (side panel tabs + photo fix)
- Side panel is one column with three tabs (Trip qualities · Conversation · Saved), with counts; the last tab is remembered. Phones use the same tabs, folded until tapped. Proper tablist semantics + arrow keys.
- Missing trip photos — cause: a page of cards fires many Wikipedia lookups at once; Wikipedia answered some with 429 (rate limit), those fell back to Openverse, whose thumbnail proxy often returns 424, so the card showed a broken image. Fix in lib/images.js (shared by Home, Trip, City, My trips): Wikipedia lookups queue (≤2 in flight) and retry 429s with backoff; disambiguation pages skipped; "City, Country" title tried first (right Lagos); found photos cached in memory + localStorage (`tf.cityimg.v1`); Openverse uses the direct image URL; `imgFallback` swaps a failed thumbnail for the full image. Burst of 12 cities: 6 → 11 on Wikipedia, 0 broken. Test: tests/images.test.mjs (mutation-checked).

## Stop order — 2026-09-29
- Bug: asking Trip Fairy to add a stop "at the beginning" put it at the end. The segment `add` op always appended (`order: list.length`), and the model couldn't reorder in the same reply because it can't know the new stop's id. Fix: `add` on segment takes `position: 'start'|'end'|index` or `before`/`after` an existing segment id (an unknown id fails the whole reply rather than silently appending); the op protocol + a rule tell the model to use it.
- One shared reorder in lib/trip.js (`reorderStops`, `moveStop`, `insertStop`, and `reverseStops` on top): activities keep their place within their stop (their global day shifts — previously a manual move left them on the old days), stops whose days changed lose per-stop arrive/depart, and an estimated leg between two swapped stops flips instead of being cleared and re-estimated. Used by the Trip page, the assistant's ops, and the fare optimizer's reversed route.
- Manual reorder: stop cards on the Trip page are draggable (drop marker shows where it lands); the Edit-mode ‹ › buttons are larger (touch/keyboard path).
- Tests: tests/stops.test.mjs (mutation-checked); smoke drags a stop there and back and checks the picked bus survives.

### Fix — 2026-09-29: "(trip.destinations || []).join is not a function"
- Cause: the assistant's `update field` op copied model values onto the record unchecked; a reply sent `destinations` as one string ("Lisbon, Porto"), which was saved, and every later chat on that trip crashed building its prompt (`tripToContext`).
- Fix: list fields (`destinations`, `interests`) are coerced to string lists at the op boundary (lib/patch.js), and records already saved with text are repaired on load (migrate) and on cloud pull (sync). Test in tests/stops.test.mjs (mutation-checked).

# Review — Trip AI harness: what the model gets each turn (#050346)
Date: 2026-10-01 · Status: findings, awaiting decisions

## Inventory
| Call | Builder | Sent as | Contents |
|---|---|---|---|
| Trip chat (edit) | aiClient `buildEditPrompt` | 'prompt' (metered) | fixed instructions (op protocol + kind rules + flight-search rules) ‖ cache break ‖ `tripToContext` + weather normals + shortlist + segment/activity id lists + fare options (plans) + the WHOLE conversation (reply text only) |
| Home finder | tripFinder `buildFinderPrompt` | 'chat' | qualities + pinned list + whole conversation + JSON schema |
| Brainstorm (My trips rail) | aiClient `buildBrainstormPrompt` | 'chat' | instructions ‖ whole conversation |
| Versions: draft / routes | drafts `buildDraftPrompt` / `buildRoutesPrompt` | 'prompt' | `tripToContext` + request |
| Background (free) | derive/geo/shortlist/cautions/auditAi | 'background' / 'prompt' | per-task, capped at 12k chars (tests/promptSizes) |

Measured (Iberia fixture: 5 stops, 25 activities, 4 legs, 12 messages): edit prompt ≈ 9.2k chars (~2.3k tokens) — fixed 3.7k (cached on Claude) + trip/chat 5.5k. Finder ≈ 2k.

## Findings
**Correctness (fix)**
1. Travel legs are listed without ids, yet the protocol offers update/remove travel by id → those ops always fail, and (all-or-nothing) sink every other change in the reply. `origin`/`return` pseudo-ids appear only in a rule.
2. The model never learns what happened to its proposed changes: the transcript carries reply text only, not whether the ops were applied, left unapplied, or failed (and why). It can claim "I added Madrid" after the traveler ignored or the app rejected it.
3. No date anywhere: "next spring", "in 3 weeks", season advice and past-date checks are guesses.
4. Detail the model can't see but may overwrite or contradict: stop lodging / notes / arrive–depart; activity time and notes; leg cost, booked vs estimated, flight number/times. (Fixture had lodging set — not in the prompt.)
5. Field updates are type-unchecked beyond the list fix: travelers / rooms / lengthDays / budget can arrive as text ("2 people") — same bug class as the destinations crash.

**Efficiency / clarity**
6. Stops and activities are listed twice (context, then the id lists) — ~40% of the variable part. One listing with ids inline.
7. "Destinations: (none specified)" shows while stops exist — contradicts the stop list. Only show destinations when there are no stops.
8. The conversation is sent whole every turn, unbounded. Keep the last ~12 turns verbatim and say how many earlier ones were dropped (the trip state carries the result of those).
9. The op protocol advertises plan-only fields (lodging, time, cost) to proposals, which their rules then forbid (the app strips them anyway) — mixed signals. Tailor the protocol line per kind.

**Cleanup**
10. `scoreIdeas` / `buildMatchPrompt` (derive.js) have no callers since the Ideas page went.

## Recommendation
Do 1–8 as one change (one shared context builder for the edit prompt, ids inline, date + outcome annotations, numeric coercion in patch, transcript cap), with tests on the prompt text; 9–10 alongside as they're small. Expected: variable part ≈ −35% on mid-size trips and the failure modes above gone.

### Harness fixes — 2026-10-01 (all 10 findings, one change)
- New `src/lib/context.js`: `tripToContext(trip, { ids, today })` (moved out of trip.js) lists the trip once — stops with lodging / notes / arrive–depart, activities nested under their stop with day / time / per-traveler cost / notes, travel legs with ids, stop-id ends ("origin"/"return" = home), flight details, per-traveler cost and estimate vs set-by-traveler — plus `Today:` (local date). Destinations only when there are no stops.
- `transcriptText`: last 12 messages, a note for dropped ones, and after each reply what became of it: changes applied / NOT applied / FAILED (reason), trip options shown, flight results shown. Used by the trip chat, brainstorm and the Home finder (which also gets today's date).
- Op protocol per kind: proposals no longer see dates/status/lodging/activity day-time-cost/travel ops; a rule tells the model to check outcomes before saying a change was made, and that numbers are numbers.
- patch.js: whole-number fields (travelers, rooms, lengthDays, nights, day, durationMinutes) coerced; unparseable ones dropped rather than stored as text.
- Removed dead `scoreIdeas` / `buildMatchPrompt` / `prefsKey` / `prefsFromContext` / `deriveTransport`.
- Size (Iberia fixture): trip+chat 5.5k → 5.3k chars while carrying far more; proposal instructions 3.5k → 3.0k; plan instructions 3.7k → 3.9k (cached). Long chats now stop growing past 12 messages.
- Tests: tests/harness.test.mjs (7, mutation-checked); smoke mock keys on the new prompt header.

# Plan — Fluid trips, place + base stops, anchors (#af9be2, #1858f1)
Date: 2026-10-01 · Status: Draft · Brainstorm: docs/brainstorm.md 2026-10-01

## Milestones
| # | Milestone | Description | Dependencies |
|---|---|---|---|
| FT1 | One fluid trip | Drop proposal/plan field gating (dates, status, travel, lodging, activity day/time/cost allowed on any version); date finder + Flights on any version; derived stage chip (idea · shaped · dated · booked · done) replaces Proposal/Plan labels; "Create plan" → optional "New version" (copy); root + versions are peers with a `mainVersionId` (default: today's lead version); one stage-aware AI prompt ("don't invent dates/bookings unless asked") instead of proposal/plan prompts; Versions/My trips/top bar read "versions". No data rewrite. | — |
| FT2 | Place + base stops | Segment gains `placeType` (city · park · region · event), optional `base` { name, lat, lng } (where you sleep) and 0-night day stops. Day math: a 0-night stop shares its day with the next stop. Trip page: "sleeping in X", "day stop"; shared bases grouped; map shows base (bed) pins when they differ from the place. Budget lodging counts nights at the base. AI: ops + context carry base/placeType/0 nights; finder/drafts may return bases. Mighty 5 fixture in tests + smoke. | FT1 (lodging no longer plan-only) |
| FT3 | Fixed-date anchors | Activities (and stops via arrive/depart) can be pinned: `anchor: { date, time? }`. Anchors show as pinned; with no trip dates, an anchor implies them (start = anchor date − its day + 1); the date finder only offers windows containing every anchor; AI context marks FIXED items and is told never to move them. | FT1 |

## Decisions Log
| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Lifecycle | One fluid trip, versions as peers | Hard fork blocked early dates/lodging and split chats; record shapes were already shared | 2026-10-01 |
| Event trips | Place + optional base, 0-night stops | Smallest change; city trips unchanged; fixes Mighty 5 | 2026-10-01 |
| Anchors | Yes, pin activities/stops to dates | Festivals/games/weddings drive the whole trip's dates | 2026-10-01 |
| Migration | None (kind kept in data, ignored by UI) | Same shape already; avoids a risky rewrite of synced data | 2026-10-01 |

### FT1 built — 2026-10-01
- `src/lib/versions.js`: `tripStage` (idea · shaped · dated · booked · done; booked/done from the traveler's status or a past end date), `versionName` (root = "Original"), `mainVersion` (root.mainVersionId, else furthest along, then most recent), `nextVersionName`, `newVersion` (full copy of any version with fresh stop/activity/leg ids, references remapped). Stored `kind` stays ('proposal' = root, 'plan' = version) — no data rewrite.
- Removed the gating: `PLAN_ONLY_FIELDS` / `SEGMENT_PLAN_FIELDS` / `ACTIVITY_PLAN_FIELDS` / `SHARED_FIELDS` and the proposal strip in patch.js; lib/escalate.js deleted (`draftToPlan` → `draftToVersion` on top of `newVersion`); stays mirror into lodging on any version; audit's dates/late-activity checks run on any version.
- UI: trip bar shows versions as peers with a stage dot and "+ Version" (copies the version you're on); opening a trip lands on its main version; Flights, the dates pill and the date finder work on every version; the Trip page header shows version · stage; the trip editor shows dates, lodging, legs and activity day/time/cost everywhere with a "Booking" select (still planning · booked · done); Versions shows each card's stage, a Main badge and "Make main", and "Keep as version"; My trips filters by stage.
- AI: one instruction set for every version (no proposal/plan prompts), with "Stage:" in the trip context and a rule not to invent dates/bookings before there are dates unless asked; flight search on any version.
- Tests: tests/versions.test.mjs + updated myTrips/drafts/shortlist/fareStore/harness; smoke adds two fluid-trip steps (49/49).

### FT2 built — 2026-10-01
- Stops gain `placeType` (city · park · region · event) and `base` { name, lat, lng } — where you sleep when it isn't the place (`normalizeBase`, `sleepsIn`, `stopShape` in lib/trip.js). 0 nights = a day stop: it takes no days of its own and shares its day with the next stop (`segmentDayRanges`); `segmentForDay` gives a shared day to the overnight stop.
- Trip page: park/region/event icon on the stop card, "Day stop", "Sleep in <base>"; one bed pin per base town on the map (shared bases → one pin); bases geocoded like stops (`geocodeBases`: Nominatim, then the AI; deduped by town).
- Editing: stop rows in the editor and the city page's stop details have "Kind of place" and "Sleeping in"; nights can be 0.
- AI: the trip context lists place type, day stops and "sleeping in"; the op protocol takes `placeType` and `base` (a town name; same name keeps coords, "" clears); a rule explains places vs bases and 0-night stops. The finder and drafts may return bases, place types and day stops; city briefings suggest stays in the base town (none for a day stop).
- Tests: tests/places.test.mjs (Mighty 5; mutation-checked); smoke adds a Mighty 5 trip (day stop, "Sleep in", 2 bed pins for 3 based stops) — 50/50.
- Known, not FT2: a trip with no dates and no length shows "? days" rather than summing nights.

### FT3 built — 2026-10-01
- `src/lib/anchors.js`: `anchor: { date, time }` on activities and stops. `anchorWindow` intersects what each anchor allows for the start date (a stop: date − (its first day − 1); an activity with a day: date − (day − 1); an activity without a day: within its stop, or the trip) → { earliest, latest, exact, conflict }. `syncAnchors` applies it: an exact window sets an undated trip's dates (length from dates / lengthDays / nights), and on a dated trip anchored activities land on their day. Runs after every assistant reply (applyOps), manual edit and date lock.
- The date finder opens its window where anchors allow, greys out (can't lock) departures that leave one out, and says what's fixed; the Flights page's date options skip those departures. The trip check flags anchors that conflict or fall outside the dates.
- UI: "Fixed date" on activities (trip editor) and stops (city page stop details, "there from"); a pin + date on anchored activities in the itinerary and "Fixed · <date>" on stop cards.
- AI: anchored items read "FIXED: …" in the trip context, plus when the trip must start; the protocol takes "anchor":{"date","time"} / null; a rule says never move them or set dates that leave them out.
- Fixed a day-arithmetic bug before it shipped (noon-UTC day numbers rounded a day late).
- Tests: tests/anchors.test.mjs (7, mutation-checked); smoke pins Porto to Dec 5 on the undated original → Dec 1–8 — 51/51.

### FT1 follow-up — 2026-10-01: folding old proposal → plan forks
- `collapseForks` (lib/versions.js): a root with no dates + a version still auto-named "Plan N" with the same stops in the same order, where the root has no activity the version lacks, folds into one record — the root keeps id / title / createdAt / drafts (re-pointed) / chats, takes the version's content (stop/activity/leg references intact; city caches the version lacked come from the root's same stop); the version is tombstoned so every device drops it, and its conversations move to the trip (`moveTripChats`). Anything else stays a version. Idempotent; runs on load (App) and in the sync merge (pullMerge), and a selection on a folded version moves to its trip.
- Against the saved trips (read-only check, 2026-10-01): Utah's Mighty Five (Plan 1, dated, shorter nights) → one trip; Greece 10-Day Getaway (Plan 1) → one trip; Western Balkans (Plan 2 folds; Plan 1 via Tirana stays a version); Japan Ski Trip unchanged (named alternative); single trips unchanged.
- Tests: versions.test.mjs (fold + what stays), chats.test.mjs (chats move); smoke: an old fork folds on load, a named version stays — 52/52.

## Trip map layers — 2026-10-01 (#842d31)
- `src/lib/mapLayers.js`: places to stay / things to do / food & drink from each stop's page (segment.detail.pois with coordinates; none for stays on a day stop) as map markers per layer, with the traveler's picks (their stay, their list) marked; "Only what I picked"; counts per layer; the choice remembered per browser (`tf.tripmap.layers.v1`).
- `MapLayersControl` in the trip map's control column (stack icon → panel). Layer markers are `fit:false` + `draggable:false`: MapCanvas frames the trip on its own markers and no longer re-frames when only those change, so a zoomed-in view stays put while layers switch.
- Picked places get a filled pin (CSS `.tf-mk--picked`).
- Also: `plannedDays` (dates → length → nights) for "Dates open · N days" and the trip header — no more "? days" on trips without a length; anchors use it too.
- Tests: tests/mapLayers.test.mjs; smoke: switching "Places to stay" shows both stays, the pick stands out, the camera doesn't move — 53/53.
- Not in this change: activities as a layer (they have no coordinates of their own yet).

### Small items — 2026-10-01
- City maps (#81665b): a plain scroll over a city map zooms it (`wheelMode="always"`); touch screens keep one-finger page scrolling ('cooperative').
- Trip map — your activities: an activity named like a place on a stop's page borrows its location (its own stop first) and shows as "Your activities", on by default; the place doesn't show twice. Hand-typed activities with no matching place aren't mapped yet (real locations come with DATA-R1).
- My trips globe (#50fa0f): each trip's name as a pill in its colour over the middle of its route, a link to the trip; pills that would overlap another hide until you zoom in; far-side ones fade with the globe.
- Data-source work tabled as DATA-R1 / R2 / R3 (#c6996a, #edfda3, #1dba4c).
- Tests: mapLayers + myTrips; smoke: trip names visible and open the trip, city map zooms without scrolling the page — 55/55.

## Plan — Trip Fairy loading animations (#b2d6f3)

**Concept.** Build the loader from the brand mark itself (`TripFairyMark`, components/Brand.jsx)
rather than a generic spinner: the mark bobs gently (±3px, 2.2s ease-in-out loop) while three small
sparkles orbit it (3.6s linear) and twinkle on staggered delays (opacity + scale, 1.8s ease-in-out).
Transform/opacity only, per motion rules. No bounce/elastic — the bob and orbit are continuous
loops, not entrances, so they stay on a plain ease-in-out rather than an ease-out-expo (which
reads as a one-shot settle, wrong for something that repeats forever).

**Component — `src/components/FairyLoader.jsx`.**
`<FairyLoader variant="inline" | "block" | "typing" size label lines className />`
- `inline`: icon only (`role="status" aria-label={label}`), sized to sit next to the caller's own
  visible text or inside a button in place of an icon.
- `typing`: icon + its own text in a row — the "assistant is replying" bubble shape.
- `block`: icon + text, centered, padded — a self-contained empty-panel state.
- `lines`: optional array of short status strings the loader rotates through every 2.2s (pure
  selection logic in `src/lib/loaderLines.js::pickStatusLine`, unit-tested). Only used where the
  wait is genuinely open-ended (an AI call) and only with generic-but-honest lines ("Weighing a few
  options…", "Almost there…") — never a line that claims a specific step isn't actually happening.
  Falls back to `label` when omitted or when there's only one line.
- Reduced motion: `@media (prefers-reduced-motion: reduce)` in index.css drops all three keyframe
  animations; the mark sits still and the sparkles hold at a fixed low opacity (no flashing, still
  reads as "something is happening" without motion).

**Loading spots changed** (grep for `loading`/`busy`/`animate-spin`/`animate-pulse`/the old copy
found these; each got the loader judged by role):
- `AssistantRail.jsx` — "Thinking…" dot replaced with `variant="typing"`, rotating lines.
- `HomePage.jsx` (Home trip finder) — the history list's busy row, the phone-panel busy line, the
  empty trip-options panel (now `variant="block"`), and the send button's spinner (now
  `variant="inline"`) all switched; all open-ended AI waits use the same rotating lines.
- `VersionsPage.jsx` — "Draft it" and "Other ways to do this trip" buttons swap their icon for
  `variant="inline"` while busy (kept their existing "Drafting…" / "Finding other routes…" copy).
- `CityPage.jsx` — the city-briefing loading row switched to `variant="typing"` with rotating lines.
- `TripAudit.jsx` / `GoodToKnow.jsx` — the two "AI check" buttons (`aiBusy`) swap `CircleNotch` for
  `variant="inline"` for brand consistency. Left as-is: the audit's per-issue "fix" buttons
  (`CircleNotch`, local patch apply, not an AI wait) and DateFinder's fare-pricing skeleton bars —
  those are genuine content skeletons (interaction-design rule: skeletons for content loading, not
  center-screen spinners), so a mark animation there would be the wrong vocabulary, not an upgrade.

**Motion/reduced-motion rules applied:** `transform`/`opacity` only; no layout properties; ease
in/out, no elastic; every animation has a reduced-motion stop (index.css, near `.fairy-loader__*`);
loader never gates content visibility — it only ever shows *while* `busy`/`loading` is true and the
content it describes is absent, same as the copy it replaces.

### Built — 2026-10-02
- `src/components/FairyLoader.jsx` (`inline` / `block` / `typing`) + `src/lib/loaderLines.js`
  (`pickStatusLine`, unit-tested in `tests/loaderLines.test.mjs`) + keyframes in `src/index.css`
  (`.fairy-loader__mark` bob, `.fairy-loader__orbit` rotation, `.fairy-loader__sparkle` twinkle;
  reduced-motion block freezes all three).
- Wired into: `AssistantRail.jsx` (Thinking…), `HomePage.jsx` (finder history row, phone busy line,
  empty trip-options panel, send-button spinner), `VersionsPage.jsx` (Draft it / Other ways to do
  this trip button icons), `CityPage.jsx` (briefing loading row), `TripAudit.jsx` + `GoodToKnow.jsx`
  (AI-check button icons). DateFinder's fare skeleton bars and the audit's per-issue fix spinners
  were left alone — they're content skeletons / local patch-applies, not AI waits.
- Tests: `tests/loaderLines.test.mjs` (2 cases); full suite 198/198. `npm run build` passes (pre-
  existing chunk-size warning only, unrelated).
- Smoke: added "home: the fairy loader shows while finding trips, then clears" (asserts
  `role=status` appears then disappears around the Home finder call, using a one-time 600ms delay
  on the mocked `/ai/plan` finder request) — 56/56.
- Visual check (playwright-cli, mocked `/ai/plan` with an artificial delay): desktop dark (inline
  send-button loader + block empty-panel loader, rotating status line), desktop dark with
  `prefers-reduced-motion: reduce` (mark and orbit frozen, sparkles held at fixed opacity, text
  still rotates), and mobile (390x844) forced light theme (both the phone-panel typing-style line
  and the block panel, accent-colored mark reads fine on the light surface). AssistantRail's and
  CityPage's `typing` variant render through the same `Mark`/`Sparkles` code path validated above,
  not screenshotted separately.
- Not done: no rotating lines on the lightweight button-icon spots (Versions draft/routes, audit/
  GoodToKnow checks) — those waits are short enough that a static icon swap reads better than text
  that might not finish a cycle.

# Plan — On-trip section: calendar + packing (#a34d09)
Date: 2026-10-02 · Status: Built · Branch: feat/on-trip-calendar-packing

## Goals
Give a trip a day-by-day calendar (whole trip / a range of days / one day at a
time) and a packing list seeded from the trip itself — both reading the
existing record (stops, bases, day stops, travel, activities, anchors,
climate normals) so they're correct the moment a trip has stops, no extra
data entry.

## Scope
- Calendar: a pure schedule builder (no AI) over `segments`/`travel`/
  `activities`; dated trips show real dates, undated trips show day numbers;
  a day stop sharing its day with the next overnight stop shows both ("Day
  stop: X — sleeping in Y"); travel legs land on the day they happen
  (arrival day, except the trip's final leg home which lands on the last
  stop's last day); activities sort by time; anchored activities show their
  pin; activities with no day yet are listed separately, not dropped.
- Packing: a deterministic generator (no AI) — essentials, clothing scaled to
  trip length (capped at a week — laundry) and traveler count, gear from
  place types (park → hiking gear) / activity categories (outdoor, nightlife,
  paid food → dinner outfit) / interests (beach, ski), and a weather pass
  from the climate normals (lib/climate.js) for the trip's month (cold →
  layers, hot → sunscreen, rainy → rain jacket). Saved as `record.packing`
  (new, additive, nullable field — no schema bump) so checks/custom items
  sync like everything else; "Refresh suggestions" only adds what's missing,
  never touches what the traveler already checked, unchecked, or added.
- Both read live record data — no placeholders — and respect the app's
  existing tokens/themes/reduced-motion (reused `.card`/`.field`/`.tab`/`.chip`
  classes, no new CSS).

## Data model changes
- `record.packing?: PackingItem[]` — `{ id, name, category, reason, quantity?,
  checked, custom? }`. Additive/nullable like `weather`/`drafts`/`image`
  before it — no `SCHEMA_VERSION` bump, no migration.
- No other fields changed; the calendar is entirely derived (no stored shape).

## UI layout
- `lib/onTrip.js`: `scheduleDays(trip)` → one entry per trip day; `unscheduledActivities(trip)`.
- `lib/packing.js`: `generatePacking(trip, normalsBySeg)` (pure) + `mergePacking(existing, generated)`.
- `pages/CalendarPage.jsx`: "Whole trip" (with a from/to day range filter) vs
  "Day by day" (prev/next through one day at a time) tabs; a day card shows
  where you are, where you sleep, travel, and activities.
- `pages/PackingPage.jsx`: items grouped by category with checkboxes, reasons,
  remove, add-a-item, and "Refresh suggestions"; auto-generates once on first
  visit (`onPatch`, like the weather cache — not a user edit); toggling/adding/
  removing go through `onChange` (undoable, like any other trip edit).
- Trip bar (`Shell.jsx`): a 5th/6th top-level tab overflowed the 375px budget
  (the CSS comment already flagged "five section tabs must fit"), so Calendar
  + Packing are one "On the trip" dropdown (icon-only on phones, same pattern
  as the Cities menu) rather than two more tabs.

## Milestones
| # | Milestone | Description |
|---|---|---|
| CAL1 | Day-by-day schedule builder | `lib/onTrip.js`, pure, dated + undated, day stops, travel-day placement, anchors |
| CAL2 | Calendar page | Whole trip / range / single day, phone-friendly |
| PACK1 | Packing generator | `lib/packing.js`, pure, essentials/clothing/gear/weather, mutation-checked |
| PACK2 | Packing page | Persisted on `record.packing`, checkbox/add/remove/refresh |

## Built — 2026-10-02
- `src/lib/onTrip.js`, `src/lib/packing.js`, `src/pages/CalendarPage.jsx`, `src/pages/PackingPage.jsx`; wired into `App.jsx` (`calendar`/`packing` pages) and `Shell.jsx` (On the trip menu).
- Tests: `tests/onTrip.test.mjs` (11 — schedule dated/undated/day-stops/travel-days/unscheduled activities, packing hiking/clothing-scale/climate/merge), each mutation-checked against the logic it covers. Full suite 207/207.
- Build: `npm run build` clean.
- Smoke: `scripts/smoke/smoke.js` — Calendar + Packing added to the per-page layout sweep (phone + desktop) and three feature steps (whole-trip schedule + the Dec 3 dinner, day-by-day stepping, a packing toggle surviving reload). 62/62. Screenshots checked manually (desktop 1280 + phone 375, dark + light) — layout and both themes read cleanly.
- Not built: the optional "Suggest more with Trip Fairy" AI pass on packing (spec said optional, kept out to keep the generator small and fully deterministic/testable).

### Fix — 2026-10-04: lapsed Claude Code sign-in ("Your Claude Code" engine)
- Symptom: chat replied "Failed to authenticate: OAuth session expired and could not be refreshed" — the helper's `claude -p` had an expired CLI login.
- Helper core (`packages/helper/lib/core.mjs`, used by `npm run ai` and the npm package): failures that look like login trouble (`isLoginError`) become a 503 `{ code: 'claude_login' }` with "Your Claude Code needs you to sign in again: open a terminal, run `claude`, then type /login. Or use Trip Fairy's AI for now."
- App (`aiClient.callHelper`) → typed error `helper_login`; the assistant rail and the Home finder show a "Use Trip Fairy's AI instead" button (switches `aiEngine` to 'auto'). Other screens show the clear message.
- Helper package bumped to 0.1.2 (the user publishes to npm with 2FA). Tests: tests/helperLogin.test.mjs (fake `claude` on PATH; mutation-checked).

### Polish — 2026-10-04: calendar, packing, map names
- Calendar is a real calendar now: a Sun–Sat grid over the trip's weeks (rows of Day 1–7 without dates), each day with its stop as a coloured band (named where a stop's run starts / a week starts), travel, the first two activities and "+N more"; out-of-trip days dimmed; phones show bands + dots. Pick a day → the day panel (prev/next). "List" view: an agenda grouped by stop. `calendarWeeks` in lib/onTrip.js (tested).
- Packing: an always-visible "Add items" box that takes a typed list ("sunglasses, 2 wool socks, phone charger"), previews how it read it, and files each item by a best guess (`parseQuickAdd`, `guessCategory` in lib/packing.js; tested) or a chosen category; "Add to <category>" inside each group; − / + counts; progress bar; Hide packed. An item already on the list gets its count updated instead of a duplicate.
- Trip map: "Road & place names" in the map layers panel — hidden-by-default detail labels in the map style (road names/numbers, villages/suburbs/hamlets, towns from regional zoom, airports with codes, peaks with elevation, park names), toggled by `setDetailLabels`; trip stops still win label collisions.
- Smoke 67/67 (calendar grid + day panel + list, packing typed list + per-category add, the names toggle); 215 unit tests.

- 2026-10-04: the map toggle is called "More labels" (hint: roads, towns, parks, airports) — "Road & place names" read oddly.
- 2026-10-04: "More labels" is on every map now — one shared, remembered setting (`lib/mapPrefs.js` `useMoreLabels`, live across open maps; carries over the old trip-map choice). OdMap shows a toggle button (signpost) in its controls on the city maps, My trips and expanded views; the trip map keeps it in its layers panel (`labelsToggle={false}`). Smoke 68/68.

## Plan — Price ranges for flights & transport (#5738f9)
- Problem: AI-estimated legs show one confident number ("$30 pp") for what is really a spread. Real fares (Ignav live, chosen/booked flights) are exact and must stay so.
- Data: estimated legs and their `options[]` gain `costLow`/`costHigh` (per person, USD, integers). `cost` stays and becomes the midpoint when a valid range exists — the budget, audit, fare optimizer and older readers keep one number. Legs/options without a range (older data, hand-typed) render exactly as before.
- Validation (`normRange`/`normOption` in lib/derive.js): swap inverted ends; drop the range if an end is missing, non-positive or the spread is > 10x (keep `cost` as given).
- Where a range is legal (`estimateRange` in lib/legOptions.js): only when the leg/option is not live, not chosen, not a real flight and `derived !== false`. Live fare (`withLiveFare`), picking a snapshot flight, and hand-editing the cost (TripEditor) all clear the range.
- UI: Getting-around row and option chips use `PriceRange` (per-traveler / total mode honoured, `short` form with full text in the tooltip); "est" label unchanged. Live/booked prices keep `Price` and no "est".
- AI context (`tripToContext`): `~30–50 USD pp · estimate` for ranged estimates.
- Budget decision: unchanged — uses `cost` (the midpoint). A low/high budget band would be a separate feature.
- Flights page spread of results: not built (see built notes).
- Tests: tests/priceRanges.test.mjs; smoke: range/older/live steps.

### Built — 2026-10-04 (#5738f9)
- Branch `feat/travel-price-ranges`. Prompt asks for `costLow`/`costHigh`; `normOption` validates; `pickLegOption`/`currentAsOption`/`withLiveFare` carry or clear ranges; TripPage threads them when creating legs; TripEditor clears them on a manual cost.
- Shown on the Trip page "Getting around" rows and the options chips; context lists them for the chat. Not shown on other pages because no other page displays estimated leg prices (Home finder cards already used `priceRangeLines`).
- Not built: Flights-page "cheapest–typical" spread — the search returns few itineraries and a spread of 2-3 offers reads as false precision next to the exact list already shown.
- Tests: 223/223 (8 new, mutation-checked: inversion swap, live clears range, `estimateRange` real-fare guard, context range). Build clean. Smoke 70/70 (range on an estimated leg and flight, older cost-only leg unchanged, live fare single and unlabelled; "$30 pp" assertion became "$25–35 pp", total-mode assertion now the range × 2). Screenshots of Getting around at 1280 and 375 checked.


## Plan — Packing: Suggest more with Trip Fairy (#b9506f)
- Goal: a user-initiated "Suggest more with Trip Fairy" on the packing page. It asks the model only for trip-specific items NOT already on the list; the traveler picks (add one / add all / dismiss). Nothing is added automatically.
- Pure functions in `lib/packing.js`: `buildSuggestPrompt(trip, items, {normals})` (trip context via `tripToContext`, climate normals text, current list names) and `normalizeSuggestions(parsed, items)` (unknown category -> `guessCategory`, drops items already on the list or repeated, trims lengths, quantity 2-20 or null, caps at 10, bad JSON -> `[]`). `suggestPacking(...)` wraps `askPrompt` (priced as a credit on managed AI, like cautions) - no change to `aiClient.js`.
- Reply shape: `{ "items": [ { "name", "category", "reason", "quantity"? } ] }`, strict JSON.
- Calls: `askPrompt`, because it is user-initiated and costs a credit on managed AI.
- Marking: added items carry `source: 'ai'` (reason stays the model's plain reason); the list shows a small sparkle on them. Added through the same `addItems` path (dedupe by name, count bump).
- UI: button in the header next to Refresh; a panel above the list with FairyLoader while waiting, rows with Add, an "Add all" and "Dismiss"; errors with the same call-to-action as Home (`needs_credits` -> Get credits, `needs_auth`/`needs_account` -> Sign in, `helper_login` -> Use Trip Fairy's AI). Added rows leave the panel.
- App.jsx: PackingPage gets `settings`, `aiAvailable`, `onNeedCredits`, `onNeedAuth` (one-line edit).
- Tests: tests/packingSuggest.test.mjs; smoke step with a canned `/ai/plan` branch.

### Built — 2026-10-04: Packing: Suggest more with Trip Fairy (#b9506f)
- `lib/packing.js`: `buildSuggestPrompt`, `normalizeSuggestions`, `suggestPacking` (via `askPrompt`; `aiClient.js` untouched). `PackingPage.jsx`: header button, suggestions panel (Add / Add all / Dismiss, FairyLoader, error CTAs as on Home), sparkle on items with `source: 'ai'`. `App.jsx`: one line passing `settings`, `aiAvailable`, `onNeedCredits`, `onNeedAuth`, `onSettings`.
- Decisions: marking is a `source: 'ai'` field (reason stays plain, so it reads naturally); suggestions use `addItems` (dedupe by name, count bump), saved as custom items and undoable; button disabled when AI is unavailable; empty reply shows "Nothing new to suggest"; a failed call keeps the list untouched. Dedupe compares names ignoring case/punctuation (not plurals - ceiling: a fuzzy match would be the upgrade).
- Tests: `tests/packingSuggest.test.mjs` (6; cap, dedupe, category fallback, list-in-prompt, weather-in-prompt mutation-checked). Suite 221/221. Build clean.
- Smoke 69/69 (new step: nothing added before a click, add one lands in its category and leaves the panel, add all, quantity kept, prompt carries list + place + weather). Screenshots checked at 1280 + 375, dark + light; fixed the phone header buttons overflowing (now wrap).


## Plan — Clear conversation / start fresh (#cfe01e)
**Goal.** One obvious, consistent way to start over wherever there is a conversation, with nothing lost by accident.

**Decisions**
- **Pattern: Undo toast, not a confirm dialog.** Starting over is cheap and reversible (the old conversation is only set aside), so a blocking confirm is friction. A bottom-centre toast ("Search cleared" / "Chat cleared. Find it in History.", with an "Undo" button, 8 s) is used everywhere. One shared store + component (`lib/undoToast.js`, `components/UndoToast.jsx`), mounted once in App.
- **One label: "Start over"** (verb + object implied by context; the title says what it clears). Home's "Start a new search" and the rail's "New chat" are both replaced, so there is a single vocabulary. Merging "New search" into it is deliberate: the old split (new search keeps hand-set qualities) was invisible and surprising; "Unpin all" in the qualities tab still clears pins alone.
- **Home "Start over"** clears the current conversation, its trip options and the hand-set qualities (`tf.finder.manual.v1`). Undo restores all three (same conversation id, messages, model, pins). Shown whenever there is a conversation or any pinned quality, in the prompt's options row (visible on phones too).
- **Rail "Start over"** (trip/city/flights/versions pages) = `newChat`: the old conversation stays in History; Undo continues it again. New pure helper `startOver(tripId)` in `lib/chats.js` returns an undo function (or null when there is nothing to clear); unit-tested.
- Never touched: saved-for-later ideas, trips, History entries (only the traveler's explicit delete removes those).
- Touch targets >= 44px on the toast's Undo; visible focus rings; `role="status"`; toast replaces any earlier one.

**Files.** `src/lib/chats.js`, `src/lib/undoToast.js`, `src/components/UndoToast.jsx`, `src/components/AssistantRail.jsx`, `src/pages/HomePage.jsx`, `src/App.jsx` (small), `tests/chats.test.mjs`, `scripts/smoke/smoke.js`.

### Built — 2026-10-04 (#cfe01e)
- `lib/undoToast.js` + `components/UndoToast.jsx` (one toast, 8 s, `role="status"`, 44px Undo, mounted once in App; centred with a wrapper because `.animate-rise`'s fill-forwards transform cancels `-translate-x-1/2`, which the existing "Trip Fairy updated" toast also trips over, not touched here).
- Home: "Start over" (Eraser icon) in the prompt's options row, on phones and desktop; shown when there is a conversation or a pinned quality. Clears the conversation, options and pins; Undo restores all three (same session id, so no duplicate in History). Replaces "Start a new search". Saved ideas untouched.
- Rail: "New chat" renamed "Start over"; `startOver(tripId)` in `lib/chats.js` returns an undo; the old conversation stays in History, Undo continues it again. Rail on My trips uses App's `newBrainstorm`, now returning an undo too.
- Tests: `startOver` unit test (216/216). Build clean. Smoke 70/70 (+Home start over/undo, +rail start over/History/undo). Screenshots checked: Home phone before/after (toast), Home desktop after Undo, rail desktop with toast. Toast copy shortened after the phone shot showed it truncating.
- Not done: no phone-width rail screenshot (the drawer is not reached by the smoke path); Home "Start over" is small text beside the option count by design (quiet, undoable).

## Profile info — username + picture (2026-10-04, #382202)

- `supabase/migrations/0010_profiles.sql` (not yet applied): `public.profiles` (user_id pk → auth.users, username, avatar_path, updated_at); unique index on `lower(username)`; check `^[A-Za-z0-9_.]{3,24}$`; RLS: any authenticated user can read, only the owner can insert/update. Public-read `avatars` bucket (1 MB, webp/jpeg/png) with storage policies limiting writes to the `<uid>/` folder.
- `src/lib/profile.js`: pure validators (username, avatar file, square crop, initials) + a small store (`subscribe`/`getProfile`) so the header menu and Settings stay in sync. Avatars are center-cropped to 256×256 WebP (JPEG fallback) via canvas, uploaded to `<uid>/avatar-<ts>.webp`, the old file deleted best-effort. Originals over 5 MB or non-images are rejected before decoding.
- `src/components/Avatar.jsx`: reusable `<Avatar profile email size>` (image, or initials if none / load fails) and `useProfile(session)`. Used by the Account menu (avatar button, username + email, "Edit profile") and Settings → Account & credits (Profile section; saves immediately, inline validation, "taken" from the unique index).
- Guests get no profile UI. Without 0010 applied, a failed profile read resolves to null and the UI shows email/initials; saves show a generic error.

## City page layout: the map stays in view (#8e0756) — 2026-10-04

**Decision.** One map per city page, never scrolled away. The map moved out of the hero / Overview body and is shared by every tab (Overview, Things to do, Places to stay, Food), showing the active tab's located places (all kinds on Overview) plus the stop itself.
- **Wide (page area >= 880px, measured on `<main>`, so the assistant rail counts):** two columns. Left: back, hero (photo, or just the name when there is none), tabs, content. Right: a sticky map (`top-6`, height = `--main-h` - 48px, measured the way TripPage does), so it fills the viewport and never scrolls off. The Overview's side cards stack under the text in this layout.
- **Narrow / phone:** the tabs row is sticky (`top-0`), with a collapsible "Map · N places" bar and a 150px map strip under it (open by default, Hide / Show, `aria-expanded`; collapsed it unmounts). The strip uses cooperative gestures, so a finger or wheel over it scrolls the page. The map's own expand button still gives the full-screen map.
- **Interactions (shared state in CityPage):** hovering or keyboard-focusing a card sets `hoverId` -> marker `is-hover` (ring + label). Clicking a card, or its "Show on map" button (keyboard path), sets the selection -> marker `is-active`, centred (`centerFocus`) and pulsed (`is-pulse`, only without reduced motion; the pan is instant under reduced motion). Clicking a marker selects its card and scrolls it into view (`scroll-margin` clears the sticky block on phones); from the Overview it opens the place's tab. A marker whose card is hidden by chip filters clears them. The selection clears on a tab change. Picked stays / list items keep `tf-mk--picked`.
- **Code:** `cityMarkers()` in `lib/mapLayers.js` (pure, tested); MapCanvas gets `hoverId` / `focusTick` / `centerFocus` and a marker `actionLabel` ("Show X" instead of "Open X"); PlaceList gets hover / select props. Marker popups on this page are gone (markers are buttons now); the cards carry the same Map / Street View links.
- **Not changed:** briefing, Quick facts, Practical, Money, weather, Getting around, add-to-list, pick stay, swap / more, explore links, Edit (stop details + all list editing), refresh / stale banner, drag-to-correct pins, "More labels", expand map.
- **Checked:** smoke covers the map beside each tab with its marker count, picked style, hover / focus / click / marker-click classes and attributes, filter clearing, and the phone strip collapsing under sticky tabs. Known limit: the filter chips hide cards but not their markers.

- Repo renamed on GitHub: ryanchristopher27/trip-planner -> ryanchristopher27/trip-fairy (2026-10-04, tracker #70bfba). Local folder unchanged. Helper package.json repository URL updated; ships with next helper release.

## Profile stats (2026-10-04, #958e19)

- `src/lib/stats.js` (pure, tested in `tests/stats.test.mjs`): `tripStats(records, {tombstones})` groups with `buildTrips`, so a trip counts once by its main version; tombstoned trips are excluded. Gives trips made, trips taken (main version stage `done`), upcoming (dated/booked, starts today or later), countries and cities from taken trips' stops, nights away (dates, else stop nights), straight-line distance (home -> stops -> home, home only when it has coordinates; `haversineKm`) and the longest trip. `usageStats(rows)` turns `usage_events` rows into messages (prompt / new_proposal / new_plan), credits all-time and this month, and the most-used model; `fetchUsage()` reads the user's own rows (RLS) and returns null for signed-out, guest or failure.
- `src/components/ProfileStats.jsx`: "Your travels" panel in Settings -> Account & credits under Profile (reads local trips itself; Settings.jsx change is an import plus one line). Shows for anyone with trips; the AI usage block appears only for signed-in non-guest users and stays hidden if the read fails.
- Units: there is no distance setting, so miles when Temperature units is F, else km. Distance is labelled "straight-line".
- Limits: usage read capped at 5000 rows (upgrade path: a SQL aggregate view); a trip is "taken" only by its main version; no one-line summary in the Account menu (not added).

## MCP server: let an AI app read and edit trips (#edb7a6) — 2026-10-04

**Options.**
- *Where it runs.* (a) Local stdio server in the npm helper: no hosting, but every user installs and pairs it, it needs their Supabase session on disk, and it can't serve claude.ai-style remote connectors. (b) Hosted remote MCP on Vercel (`api/mcp.js`, Streamable HTTP, JSON-RPC): one URL for Claude Code / Desktop (via `mcp-remote`) / other clients; the data and the sync engine are already server-reachable. (c) Both. **Chosen: (b).**
- *Protocol code.* Official `@modelcontextprotocol/sdk` vs. a small hand-rolled subset. The SDK's HTTP transport pulls in a web framework and zod for what is four methods here; our endpoint is stateless and answers plain `application/json`. **Chosen: hand-rolled** (`initialize`, `ping`, `tools/list`, `tools/call`, notifications → 202, batches), no new dependency, fully unit-testable without a server. Revisit the SDK if we add resources, prompts, SSE or OAuth.
- *Auth.* (a) The user's Supabase session JWT: expires in an hour and can't be pasted into an app config. (b) Personal access tokens made in Settings (**chosen**): `tfm_` + 32 random bytes, generated in the browser, only the SHA-256 stored in `mcp_tokens`, shown once, named, revocable, last-used stamped, max 10 per user, none for guests (RLS). (c) OAuth (needed for claude.ai's "custom connector" UI, which can't send a static header): bigger; left as a follow-up.

**Design.**
- `server/mcp.mjs` holds everything; `api/mcp.js` only adapts req/res (`/mcp` rewrite too). Token → hash → `mcp_tokens` row (service key) → `user_id`. Every `trips` / `mcp_edits` request is filtered `user_id=eq.<owner>` (the service key bypasses RLS, so this file is the only fence; a test asserts it for every call).
- Tools: `list_trips`, `get_trip` (the in-app `tripToContext` text with ids), `list_versions`, `apply_ops`, `preview_ops`, `create_version`, `undo_last_edit`. No delete tool. `trip_id` is a root id (a version id also resolves); `version_id` defaults to the trip's main version, as My trips opens it.
- Edits run the in-app `applyOps` (+ `syncAnchors`) on the record's `data` (all-or-nothing), then write `data` with `updatedAt = max(now, old + 1)` and `updated_at` to the same instant, so LWW sync accepts it and Realtime pushes it into an open app. The write is conditional on the row's `updated_at` not having moved since the read (an app edit in between is a reported conflict, not a clobber).
- Undo: the previous `data` is saved to `mcp_edits` before each `apply_ops` (newest 20 per record kept). `undo_last_edit` restores this token's latest snapshot with a fresh stamp (so sync accepts the older content), refuses if the trip moved since the edit unless `force`.
- Guardrails: ops validated against op/target and per-target data-key allowlists (no ids, coordinates, images, cached city detail, or nested blobs; strings <= 2000 chars; <= 50 ops; request <= 64 KB); result must fit the 256 KB row limit; `create_version` respects the 100-row ceiling; 60 calls/min per token (`MCP_RATE_PER_MIN`), counted from `usage_events` kind `mcp_call` (0 credits, new `token_id` column), fails closed; ids are format-checked before they reach a PostgREST filter; tool failures are `isError` results, not HTTP 500s; internal errors never echo details.
- Settings → Account → "Connect an AI app" (`ConnectAI.jsx`): create, show-once with Copy and Claude Code / Desktop snippets, list with last used, two-click Revoke.

**Not done / limits.** No OAuth (claude.ai's connector UI won't work; Claude Code `--header` and Claude Desktop through `mcp-remote` do). Can't delete trips, set coordinates or images, run AI, or edit chats/drafts. The app's in-memory state wins if it has an unsynced edit newer than the MCP write (LWW). A created version is removed in the app. Migration `0012_mcp_tokens.sql` must be applied before any of this works.

## 2026-10-04 — Distance units setting (km / mi)
- New `settings.distanceUnits` ('mi' | 'km'), Settings → General next to Temperature. `lib/units.js` holds `cleanDistanceUnits`, `distanceIn`, `fmtDistance` (display only; internal math stays km).
- Defaulting: `loadSettings` derives it from `tempUnits` when unset/invalid (°F → mi), so existing users see no change.
- Used by: profile stats, BestWayCard airport chips, airport-pick notes (`tripAirportPicks`), and the "~N from town" note written by `applyOption`. Assistant prompts untouched (no settings seam in `buildEditPrompt`; `fareSummary` is unused in src).

## 2026-10-04 — Friends (#78d712)
- **What.** Request/accept friendships by exact username (Account menu → Friends). A friend's trips open read-only (summary view: map, dates, stops, travel, per-stop plan, versions) with a "Viewing @name's trip · read-only" banner and an optional "Copy to my trips" (new root, fresh ids, nothing booked, confirmations cleared). Per-trip "Hide this trip from friends" in the trip's edit panel (`hideFromFriends` on the root record; syncs like any field). Guests get a sign-up prompt, no friends UI.
- **Deviation: RPC instead of a trips SELECT policy.** Friends never get table access to `trips`; they call `friend_trips(friend)` (security definer): requires an accepted friendship (unfriend revokes at once), returns only live, un-hidden rows (a hidden root hides all its versions; tombstones never leak), and strips `drafts`, travel-leg `confirmation` / `bookingUrl` and the flag itself. A policy would make every plain `select * from trips` (sync pull, Realtime) return friends' rows, and RLS can't hide fields inside the jsonb.
- **Sync pitfall.** Even so, sync no longer trusts RLS alone: `fetchRemote` filters `user_id = me`, `mergeRemote`/`ownRows` drop any row that isn't mine before `mergeSets`, and the Realtime handler ignores other users' rows (the channel was already `user_id=eq.<me>`). Friends' trips live only in `FriendsPage` state, never in the trips store/localStorage or `pushChanges`. Tests in `tests/friends.test.mjs`.
- **Read-only view is not TripPage.** TripPage writes back derived data (geocoding, weather, audits) as it renders; guarding every path was more invasive and riskier than a purpose-built summary with no write path.
- **Abuse.** `friendships_guard` caps pending outgoing requests at 50; column grants make requester/addressee/created_at immutable and only `status` updatable; only the addressee can accept; either party can delete. Username lookup uses the already-readable profiles.
- **Not done / limits.** No block list (a declined user can re-request; capped at 50 pending). No live updates of the friends page (refreshes on open and on window focus). Notes, budget and activity notes in a visible trip are readable by friends: hide the trip if that matters. Friends see a trip as of its last sync. Migration `0014_friends.sql` must be applied (untested against a database here).

## 2026-10-05 — Collaborative trips (#3ffad6)
- **What.** The owner shares a trip (root + all versions) with accepted friends as editors. Trip bar "Share" pill (owner: invite / remove / cancel; member: who is on it / Leave trip). Invites arrive on the Friends page (Accept / Decline); accepted trips show in My trips under "Shared with me" and open in the normal TripPage (manual edits, the assistant's ops, drafts, versions) with a conflict/offline banner.
- **Ownership stays single.** Shared rows keep `user_id = owner`. Access is `public.trip_members` (migration `0015_trip_members.sql`; root trip id, role 'editor', status pending|accepted). Same reasoning as 0014: no new SELECT/UPDATE policy on `trips`; members read and write through security-definer RPCs (`shared_trip_rows` / `shared_trips`, `trip_collaborators`, `my_trip_invites`, `save_shared_trip`, `create_shared_version`). Writes keep id / kind / proposalId and the owner's `hideFromFriends`, are capped at 256 KB, and stamp `updated_at` / `data.updatedAt` on the server clock so the owner's LWW sync and Realtime accept them.
- **Deviation: invite only accepted friends** (reuses the friends system, blocks spam). Caps: 20 people per trip, 50 pending invites per owner. Unfriending deletes the pair's memberships (trigger), so access ends at once.
- **Deviation: editors can't delete** trips or versions (owner only, normal tombstone push); the Delete button is hidden on shared trips. Editors can create versions (at most 30 per trip this way; they count toward the owner's 100-row ceiling).
- **Live updates: broadcast + poll, not postgres_changes** (RLS hides the owner's rows from members). After a save settles, a client announces on `trip:<rootId>` (no trip data in the message) and the others refetch through the RPC; a 15 s poll and a refetch on focus are the safety net. No new publication config.
- **Conflicts.** `save_shared_trip(id, data, expected_updated_at)` never overwrites: a stale `expected` returns the current row. The client (`lib/collab.js`) rebases with a three-way merge (base = last server copy, mine, theirs): per field, per `id` for stop / activity / travel lists, as sets for string lists. Non-overlapping edits merge and re-save silently. A true conflict keeps their version, stashes mine, and shows a banner ("Use my version" re-saves it, checked again; "Keep theirs" dismisses; the text names what clashed). Nothing is dropped silently. Remote changes that arrive while there are unsaved edits go through the same rebase. The undo history reseeds when a collaborator's change lands (an older undo step would revert their work).
- **Sync isolation.** Shared rows live only in `sharedStore` (memory), never in the trips store / localStorage / `pushChanges`; `sync.js ownRows` still drops any row that isn't mine; tests assert it. Silent derived patches (coordinates, weather, audit repairs) on a shared trip are local only and never saved by themselves.
- **Owner side.** A DB trigger skips an UPDATE older than the stored row on a shared trip (a stale device can't wipe a collaborator's edit). The owner's own pushes stay record-level LWW against collaborators (their copy gets collaborators' changes through the existing Realtime channel); routing owner edits through the RPC too is the follow-up.
- **Assistant.** Works on shared trips: its applied ops go through the same `updateTrip` -> shared save path. **MCP** (`server/mcp.mjs`) stays owner-only (it scopes every query by `user_id`).
- **Not done / limits.** No "viewer" role yet (the role check leaves room). The conflict banner doesn't say who changed it (no per-edit author is stored). No presence / cursors. Invites aren't pushed live (the Friends page refreshes on open / focus). A member's chats stay private and per-user. Migration `0015_trip_members.sql` must be applied (not run against a database here).
- Test users: `SHARES` in `scripts/test-users/personas.mjs` (Ava shares "Portugal in spring" with Ben as an accepted editor, pending invite to Cleo); `seed.mjs` creates the rows on re-seed.

## 2026-10-06 — Owner edits of a shared trip use the checked save (#6ccb2e)
- **Gaps closed.** (1) An owner edit from a stale local copy overwrote a collaborator's change (owner pushes were LWW upserts). (2) Clock skew: owner pushes were device-stamped, collaborators server-stamped, so an owner whose clock ran behind could have an edit skipped by the stale guard.
- **Design.** A second instance of the collab store (`ownerStore` in `lib/sharedTrips.js`, same `createSharedStore`) holds the owner's rows of trips with at least one ACCEPTED member (new RPC `owner_shared_rows`). Owner edits go through `save_shared_trip`, which now accepts the row's owner as well as accepted editors (server stamp, expected-stamp conflict, same three-way merge, same banner; the limit message reads "your limit" for the owner). Unlike `sharedStore`, these rows also stay in `trips` (offline persistence): `App` dual-writes edits and mirrors the store's copies (server stamp, merged collaborator changes, new versions) back into `trips`; the store's returned data + `updated_at` are what the next save's `expected` uses.
- **Out of the LWW push.** `pushChanges(trips, tombstones, exclude)` skips live rows in the owner store (they still count toward the ceiling); `pushRows` is the pure part (tested). Tombstones are never excluded.
- **Accepted members only, not pending invites.** An invitee can't write, so with only invites out the owner is the sole writer and nothing can conflict; routing every edit through an RPC would add latency/failure modes for nothing. The trip joins the checked path when someone accepts (detected by the 15 s poll / focus / Realtime on the trip's rows).
- **Server guard now stricter (0016).** For a trip with an accepted member, `trips_shared_stale_guard` lets through tombstones (the old guard could skip a device-stamped delete older than a collaborator's server stamp) and the checked RPCs (transaction-local flag `tripfairy.checked_save`); it skips any other UPDATE from the owner's own session (so an old cached bundle on another device can't clobber), and still skips stale writes from other callers (service role / MCP). Reason: the client routing alone can't cover the window between a member accepting and the owner's client learning of it, nor older app versions. A skipped upsert reports no error; the client self-heals: when a row first enters the owner store, a local copy stamped later than the server's and different in content is treated as an unsaved edit and saved through the check (`localFor`).
- **Versions.** `create_shared_version` also allows the owner, so a new version of a shared trip is server-stamped, not an LWW insert.
- **Realtime / broadcast.** For a row in the owner store, the `trips-sync` handler no longer applies the row by LWW: it ignores the echo of my own save (stamp compared numerically) and otherwise refetches the root through the store (merge-aware). The owner joins and announces on `trip:<rootId>` like an editor (`useSharedSync(userId, root, store)`).
- **Unsharing.** When the last member leaves, `owner_shared_rows` stops returning the rows, the store drops them, `ownedKey` changes and the normal push resumes. The owner path of the RPC needs no membership, so a save in flight at that moment still lands.
- **Deletes.** `deleteTrip` calls `ownerStore.forget(ids)` and sends the tombstone through the normal push; the guard lets it through.
- **MCP.** No change: it uses the service role (not the owner's session), PATCHes with an `updated_at` equality check (conflict = refusal) and stamps `max(now, prev+1)`, so the new guard lets it through; the owner's client picks the change up through Realtime and rebases any unsaved edit.
- **Limits.** Clock skew still matters in one corner: an owner OFFLINE edit on a clock BEHIND the server's last stamp, with a collaborator save in between, is treated as stale when the trip is next loaded (no base copy to merge from). A member's acceptance isn't pushed live to the owner (poll 15 s / focus); edits in that window are skipped by the guard and re-sent through the RPC once the owner store loads the trip. Migration `0016_owner_shared_save.sql` must be applied (not run against a database here).

## 2026-10-06 — Assistant + AI-applied fares follow distance/temp units (#506ff2)
`unitsLine(settings)` (lib/units.js) is added to the edit, brainstorm, finder, city-briefing and places prompts (after CACHE_BREAK where one exists; fixed prefix unchanged). `applyFareOps(record, ops, { units })` threads `settings.distanceUnits` into `applyOption`, so "~N from city" fare notes use the setting.

## 2026-10-06 — Trip companion + Today (#6c742b)
- **Today** (`pages/TodayPage.jsx`, derivation in `lib/today.js` `tripDayFor(trip, todayIso, nowHm)`): first entry of the "On the trip" menu. While the trip is under way the "On the trip" button lands on it (a dot marks it; once in the section the button opens the menu). During: day N of M, stop, next up (with Directions / Map), today's schedule (past items struck through by the device clock), where you sleep (base / lodging), the next travel leg with the traveler's own details, quick links. Before: "Starts in N days" with a day-1 preview. After: "Trip over" with a link to the calendar. Undated: "Add dates to use On the trip". Local date throughout (`todayIso`). Map links are built by `lib/links.js` (new `directionsUrl`), never model text.
- **Companion chat** (on Today, during the trip only): `buildCompanionPrompt` / `companionAsk` in `lib/aiClient.js`, context in `lib/companion.js` (today's stop + plan, next up, where you sleep, next leg, picked places for the stop, device time, units, interests; no ids, no plan listing). Plain-text replies, no edit protocol; asked to change the plan it points to the trip assistant. Its own thread: chats with `mode: 'companion'` (one current thread per trip, 6 h idle like the assistant, Start over). They are excluded from `tripConversations` / `tripUserMessages`, so they never show in the assistant's History, get continued by it, or tailor plan suggestions; they sync through `trip_chats` unchanged (`data.mode`), no migration. The planning rail is hidden on Today while the trip is under way (the companion replaces it; Overview has the assistant).
- **Pricing.** Sent as a `chat` turn: 1 credit up front on managed AI, same as a brainstorm turn, any engine (helper / BYOK / managed). No new server kind: the server still classifies the reply, so a companion reply that did build a plan would be charged as one (a client-chosen `companion` kind that skipped outcome pricing would let anyone get plans for 1 credit).
- **Location.** Off by default; "Use my location" calls `navigator.geolocation.getCurrentPosition` once, rounds to 2 decimals (~1 km), attaches it to the next message's context only, then forgets it. Held in component state: not in the chat record, localStorage or sync. Refused / unsupported: a note, chat still works.
- **Limits.** Hours/addresses come from the model's memory (the UI says they may be out of date); the chat has no live place lookup. Companion threads aren't browsable after Start over (kept and synced, no history view yet). A day with two travel hops shows the first. Today needs the browser open (no notifications). Chat only in "during" state.

## 2026-10-06 — Sign-out clears the account's data from the device (#042819)
- **Root cause.** `signOut` only ended the Supabase session. Trips, tombstones, chats and the rest lived in localStorage with no notion of whose they were, so they stayed visible to the next person on the device, and the first-login merge (`pullMerge`) would have uploaded them into whatever account signed in next.
- **Ownership stamp** (`trippin.owner.v1` = `{ uid, dirty }`, `lib/accountData.js`). Absent = anonymous data (made signed out / as a guest): it belongs to the device and merges into the account on first sign-in, as before. Present = that account's data; `dirty` = changes not yet pushed. Sign-in rules (`decideOwnership`): no stamp → merge, then stamp; same account → merge; a different account's synced data → wiped, new account loads fresh; a different account's UNSYNCED data → set aside in `trippin.stash.v1` (never merged into the new account) and merged back when that account signs in again; a guest session while an account's data is on the device → no sync at all (never push it under a guest). Guests get no stamp, so guest → permanent account conversion is unchanged. Sync (pull, debounced push, Realtime, chats, shared stores) starts only after the stamp is settled (`syncId` in `App`). Signed-in users from before this change have no stamp, so their first load stamps them (their data is theirs); data left by an older sign-out can't be recognised.
- **Sign-out of a real account.** Cancel the debounce, push trips + tombstones + chats now, flush the shared/owner stores (every row must read `saved`). If any of it fails: in-app confirm "Some changes haven't synced yet — sign out anyway and lose them?" (Stay signed in / Sign out and lose them; no `window.confirm`). Then `auth.signOut()`, then clear.
- **Cleared:** trips (v3 + the v2/v1 backstops), tombstones, chats (+ old per-trip threads), home-finder conversation / saved ideas / chosen qualities, per-trip caches (`tf.fares.v1.*`, `tf.gtk.open.*`), undo history, selected trip, in-memory chats/fares/profile/shared + owner stores, profile cache, broadcast + Realtime channels (the sync effects tear down when `syncId` goes null), credit balance, repair notes. Settings: the BYOK key (a secret tied to the person; also a BYOK engine falls back to managed) and the home city (personal). **Kept:** theme, units, price mode, AI engine choice, local-helper URL + token (the device's own pairing), allowed/default models, map prefs, rail width, finder tab, and public caches (city images, advisories, geocode, climate, wikivoyage, holidays, fx, gateways). Lands on Home, signed out.
- **Guest sign-out.** A guest's trips belong to the device (no stamp), so nothing is cleared; the app has no guest sign-out button anyway (the pill says "Sign up").
- **Session ended without a click** (expiry, or another tab). No session means no flush. If the stamp says `dirty: false` the data is already in the cloud: cleared ("You were signed out."). If `dirty: true` it stays on the device, still stamped as that account's, with a notice; signing into the SAME account merges it up, a different account stashes it (above). `dirty` is flipped by the app as changes happen and as pushes succeed (a push only clears it if nothing changed meanwhile). Limit: while signed out in this state the device shows that account's unsynced trips.
- **Multiple tabs.** The deliberate sign-out writes a short-lived marker (`trippin.signout.v1`) before ending the session so other tabs don't treat the auth event as an expiry. Every tab listens for `storage` events on the stamp: if another tab changed whose data this is, the tab reloads from storage instead of writing its stale memory back over the cleared keys.
- **Tests.** `tests/signout.test.mjs` (keys cleared vs kept, settings, ownership matrix incl. guest, merge refusal, flush failure, expiry, stash). `npm run smoke:signout` (`scripts/smoke/signout.js`): needs a dev server with FAKE Supabase env (`scripts/smoke.sh`); all Supabase traffic is mocked and the session is a stub.
- **Not done / limits.** Offline sign-out always asks (the flush always upserts every live trip). A BYOK key entered while signed out (no account) is the device's and is not cleared by a later sign-out of an account only if the account never had it; settings are cleaned on every account sign-out. Other tabs reload (losing their <1.5 s of unsaved typing) rather than reset in place.

## 2026-10-07 — MCP OAuth: Trip Fairy as a claude.ai connector (#ba4e28)

### Research (before coding)
Sources: MCP authorization spec, latest revision 2026-07-28 ([overview](https://modelcontextprotocol.io/specification/latest/basic/authorization), [AS discovery](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/authorization-server-discovery), [client registration](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization/client-registration)); Anthropic [Authentication for connectors](https://claude.com/docs/connectors/building/authentication) and [Building custom connectors via remote MCP servers](https://support.anthropic.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers); Supabase [OAuth 2.1 Server](https://supabase.com/docs/guides/auth/oauth-server) / [getting started](https://supabase.com/docs/guides/auth/oauth-server/getting-started).

What the spec requires of us (server = OAuth 2.1 resource server; AS may be co-hosted):
- **Protected Resource Metadata (RFC 9728) is mandatory**, with `authorization_servers` (≥1). Discovery via `WWW-Authenticate: Bearer resource_metadata="…"` on the 401, or the well-known URI with path insertion (`/.well-known/oauth-protected-resource/api/mcp`, then root). `scope` in the challenge is SHOULD.
- **AS metadata** via RFC 8414 (`/.well-known/oauth-authorization-server` for a path-less issuer) or OIDC discovery. `issuer` must equal the issuer used to build the URL. `code_challenge_methods_supported: ["S256"]` must be advertised (PKCE S256 mandatory).
- **Client registration:** Client ID Metadata Documents are now SHOULD; **Dynamic Client Registration (RFC 7591) is deprecated but MAY**, kept for compatibility. Pre-registration also allowed.
- **Resource indicators (RFC 8707):** clients MUST send `resource` (canonical MCP URL) on authorize and token requests; servers MUST only accept tokens issued for them (audience), 401 on invalid/expired.
- **RFC 9207:** AS SHOULD return `iss` in the authorization response and advertise `authorization_response_iss_parameter_supported`.
- Tokens only in the `Authorization` header, never the query string. Public clients: refresh tokens must rotate (or be sender-constrained). Consent screens should show the redirect host, with an extra warning for loopback-only redirects.

What Claude (claude.ai / Desktop / mobile; same infra as Claude Code) does:
- OAuth with DCR or CIMD by default. Uses **CIMD only if** AS metadata has `client_id_metadata_document_supported: true` **and** `"none"` in `token_endpoint_auth_methods_supported`; else DCR via `registration_endpoint`. DCR registers a new client on every fresh connection (expect many clients). Returning `401 invalid_client` from the token endpoint makes Claude re-register.
- Callback: `https://claude.ai/api/mcp/auth_callback` (may become `https://claude.com/api/mcp/auth_callback`; allowlist both if allowlisting). Claude Code uses a loopback `http://localhost:<port>/callback` / `127.0.0.1` — match port-agnostically.
- Always PKCE S256. Requests the 401's `scope`, else PRM `scopes_supported`; appends `offline_access` only if the AS lists it.
- Needs a real **401** (ignores `WWW-Authenticate` on 200); uses only the first `authorization_servers` entry; PRM `resource` must equal the URL the user typed.
- `/token` must accept `application/x-www-form-urlencoded`; `/register` is JSON. Refresh: reactive on 401 and proactive ≤5 min before expiry; return `invalid_grant` for a dead refresh token; rotate and return the new refresh token in the same response. Timeouts: 10 s (discovery/registration/token), 30 s (refresh).

Supabase's built-in OAuth 2.1 server (beta, all plans, no extra charge; DCR toggle; app hosts the consent page via `supabase.auth.oauth.getAuthorizationDetails/approveAuthorization/denyAuthorization`). **Not used**, because:
1. Its access tokens are ordinary Supabase session JWTs for the user. A token handed to claude.ai would also work directly against our PostgREST/RPCs/Realtime with the public anon key — i.e. full account access, not "the MCP tools". Self-hosted opaque tokens only open `/api/mcp`.
2. No documented RFC 8707 `resource`/audience binding (aud stays `authenticated`), so the MCP server couldn't tell an MCP token from any session JWT (spec: MUST validate audience).
3. Redirect URIs are exact-match only (Claude Code's port-varying loopback needs port-agnostic match); no CIMD mentioned.
4. Beta, dashboard switch + config on the live project (the agent may not touch it), and asymmetric signing keys recommended — more moving parts than ~400 lines of server code.

**Uncertain:** whether Vercel passes the original path (`/mcp`) or the rewritten one (`/api/mcp`) in `req.url` (we key the advertised resource on it; we tell users to enter `/api/mcp`, which is unambiguous). CIMD (now the spec's preferred mechanism) is left for later — DCR is what claude.ai falls back to and avoids server-side fetches of client URLs (SSRF surface).

### Design (self-hosted minimal AS)
- Issuer = the site origin (`https://mytripfairy.com`). One Vercel function `api/oauth.js` (Hobby has a 12-function cap; this is the 12th) behind rewrites: `/.well-known/oauth-protected-resource[/…]`, `/.well-known/oauth-authorization-server`, `/oauth/register|authorize|token|revoke|consent`. Logic in `server/oauth.mjs`.
- `/oauth/authorize` validates client + exact redirect URI (else an error page, never a redirect), then redirects to the app's consent page `/?page=oauth-consent&…`. The page (signed-in, non-guest) POSTs `/oauth/consent` with the user's Supabase JWT in `Authorization` (verified with `resolveUser`; not a cookie, so no CSRF) → server re-validates everything and mints a 5-minute single-use code bound to client, redirect URI, PKCE challenge, resource, scope, user.
- `/oauth/token`: `authorization_code` (+PKCE S256) and `refresh_token` (rotation, compare-and-swap). Opaque tokens (`tfo_` access 1 h, `tfr_` refresh 30 days sliding), only SHA-256 hashes stored. One grant row per connection in `mcp_oauth_grants`; `server/mcp.mjs` resolves `tfo_` via grants (expiry + resource check) and `tfm_` via `mcp_tokens` as before.
- Settings → Connect an AI app lists connected apps with Disconnect (RLS delete) and the claude.ai steps.

### Built
- **Endpoints** (all via `api/oauth.js` → `server/oauth.mjs`; rewrites in `vercel.json`): `GET /.well-known/oauth-protected-resource[/api/mcp|/mcp]`, `GET /.well-known/oauth-authorization-server`, `POST /oauth/register` (JSON), `GET /oauth/authorize`, `POST /oauth/consent` (app only), `POST /oauth/token` (form or JSON), `POST /oauth/revoke`. Discovery/register/token/revoke send `Access-Control-Allow-Origin: *`; token responses `Cache-Control: no-store`.
- **MCP 401** now: `WWW-Authenticate: Bearer resource_metadata="<origin>/.well-known/oauth-protected-resource/api/mcp", scope="trips"` (+ `error="invalid_token"` when a token was sent). `tfo_` tokens resolve through `mcp_oauth_grants` (expiry + resource must be this origin's `/api/mcp`, `/mcp` or origin); `tfm_` tokens unchanged. Rate limit and undo are per connection (grant id; `mcp_edits.grant_id`).
- **Migration `0017_mcp_oauth.sql`** (must be applied; not run here): `mcp_oauth_clients`, `mcp_oauth_codes` (service-role only), `mcp_oauth_grants` (owner may select listing columns only + delete), `mcp_edits.grant_id`.
- **Consent page** `/?page=oauth-consent&…` (`src/pages/OAuthConsentPage.jsx`, mounted by `main.jsx` instead of the app): app name (flagged as self-chosen), return host, a loopback warning, what it can / can't do, log in / create account for signed-out and guest users (a Google or magic-link round trip resumes the request via sessionStorage, `lib/oauthConsent.js`), Approve / Deny.
- **Settings → Account → Connect an AI app**: claude.ai steps + copyable server URL, "Connected apps" (name, connected, last used, Disconnect), personal tokens below as before.
- **Security.** PKCE S256 only; exact redirect match (loopback port-agnostic); registration accepts https or loopback http only; codes single-use (DELETE…RETURNING; a failed exchange burns the code), 5 min, bound to client/redirect/challenge/resource/user; refresh rotation by compare-and-swap, 30-day sliding; RFC 9207 `iss` on every authorization response; approval needs the user's Supabase JWT in a header (no CSRF), guests refused; DCR rate limit 10/IP/hour and 500/hour overall (fail closed); 20 codes/user/10 min; at most 20 connections per user (oldest dropped); only SHA-256 hashes stored; PKCE compared with `timingSafeEqual` (token lookups are by hash).
- **Config.** Optional `OAUTH_ISSUER=https://mytripfairy.com` pins the issuer (otherwise the forwarded host — preview deploys get their own issuer/audience). `MCP_DCR_PER_IP_HOUR`, `MCP_DCR_PER_HOUR`, `MCP_CODES_PER_10MIN` tune limits.
- **Tests.** `tests/mcpOauth.test.mjs` (stubbed Supabase); `npm run smoke:oauth` (consent page, fake Supabase server).
- **Limits / follow-ups.** No CIMD (claude.ai falls back to DCR; each fresh connection registers a client — unused clients aren't pruned yet). Custom-scheme redirect URIs (e.g. some IDEs) are refused. No refresh-token reuse detection beyond rotation (a replayed old refresh token just fails; the grant isn't revoked). One scope (`trips`, read + write). Claude Code's own CIMD/loopback flow is supported only through DCR + loopback matching (untested against the real client). Whether Vercel exposes `/mcp` vs `/api/mcp` in `req.url` is unverified; users should enter `/api/mcp`.

## 2026-10-08 — Daily database cleanup (#e863fb)
`supabase/migrations/0019_cleanup_job.sql` (not applied by the agent): `public.run_cleanup(p_dry)` scheduled by **pg_cron** inside Supabase at 09:15 UTC (`tripfairy-daily-cleanup`) — no Vercel function (Hobby 12-function cap). Each step is its own guarded block (one failure doesn't stop the rest); results go to `public.cleanup_runs` (90 days kept, RLS on, no policies). `public.cleanup_preview()` runs every delete and rolls it back, returning exact counts. Execute is revoked from public/anon/authenticated/service_role.

| Table | Rule | Why |
|---|---|---|
| mcp_oauth_codes | expired > 1 day | 5-minute single-use codes |
| mcp_oauth_grants | refresh expired > 1 day | can never refresh again; `mcp_edits.grant_id` is set null, undo history kept |
| mcp_oauth_clients | > 7 days, no grants, no live codes | abandoned claude.ai DCR registrations |
| mcp_edits | > 30 days | undo refuses stale edits anyway; no per-trip floor (cheap simplicity) |
| fare_cache | > 2 days | TTL 8h |
| ai_cache | > 45 days | pure cache |
| climate_normals | kept | 10-year averages, tiny, costly to refetch |
| trips / trip_chats | `deleted` and > 180 days | tombstones propagate deletes; too short resurrects trips on long-offline devices |
| friendships / trip_members | pending > 90 days | unanswered requests/invites |
| usage_events | > 13 months | caps read only 24h/30d; rest is cost analytics (year over year) |
| auth.users | anonymous, no sign-in/usage/trip/chat activity 60 days, no profile, 500/run | cascades to their rows incl. usage_events (accepted: small, old); `last_sign_in_at` ignores token refresh, hence the activity checks |

Not cleaned: avatar storage objects (not doable from SQL), credit_purchases (financial record). Check it ran: `select * from public.cleanup_runs order by ran_at desc limit 10;` Preview: `select public.cleanup_preview();` Job status: `select * from cron.job_run_details order by start_time desc limit 5;`

## Trip marketplace (#e00e20) — 2026-10-08

Publish a trip as a public **snapshot**; signed-in users browse and copy.

### Decisions (the user's)
- A published trip's page (`?page=published&id=…`) is public to anyone with the link, no account. **Browsing (`?page=marketplace`, "Explore" in the top nav) and copying need a real (non-guest) account.**
- Publishing copies the trip at that moment; the author chooses when to "Update published version" or unpublish. Unpublished/hidden → "This trip is no longer published."

### Design
- **Client** (`src/lib/publish.js`): `buildSnapshot(trip)` is an *allowlist* (not "strip these"): title, destinations, stops (city, country, nights, placeType, base name, lat/lng at 4 decimals), activities (name, category, stop, day, optional HH:MM), travel legs between stops (mode, duration rounded to 15 min), interests, pace, travelers, length in days. Stops/activities/legs get snapshot-local ids (`s1`, `a1`, `t1`). Left out: dates, budget/costs, every notes field, lodging, bookings (confirmation, links, price, flight numbers/times, ignavId), drafts, chats, home/start/end, hideFromFriends, real ids, images/briefings. `buildSnapshot` is idempotent, so a copy re-cleans whatever the server returned. Copy = `snapshotToRecord` → existing `copyAsMyTrip` (fresh ids, new root, status idea, no dates).
- **UI**: `PublishControl`/`PublishDialog` (pill next to Share in the trip bar; owner, non-guest; title, description ≤ 500, tags ≤ 8, preview rendered by the same `PublishedPlan` the public page uses, plain "Left out" list, Publish / Update / Unpublish, public link + Copy). `PublishedTripPage` (map via `OdMap`, day-by-day, author avatar + @username, copies, Copy / Sign up CTA, Report). `MarketplacePage` (cards with city cover via `images.js`, search, country/length/tag filters, newest/most copied, Load more; signed-out teaser). `ReportDialog`.
- **No new serverless function** (Hobby 12-function cap). Everything is the Supabase client against RLS + RPCs.
- **Migration `0018_marketplace.sql`** (not applied by the build; the orchestrator asks the user). Tables `published_trips`, `published_trip_copies`, `published_trip_reports`. Only the **author can SELECT** `published_trips`; everyone else reads through security-definer RPCs that return public columns only: `public_trip(id)` (anon + signed in), `browse_published_trips(...)` and `published_facets()` (non-guest signed-in only). So `author_id` and `source_trip_id` never leave the DB. Author writes via column grants (insert: source_trip_id/title/description/tags/snapshot; update: title/description/tags/snapshot/status); `hidden` is unreachable for authors (policies + trigger), and a hidden row is frozen (no edit, no delete) so re-publishing can't dodge moderation. A BEFORE trigger validates the snapshot (key whitelist per object, types, enums, ranges, ≤ 200 chars per string, counts, ≤ 128 KB), checks tags, caps (30 published, 100 rows per author), rate-limits (20 snapshot writes/author/hour, 15 s between updates of one trip), and **derives** `length_days`, `countries`, `cities` from the snapshot. `record_published_copy(id)` counts one copy per user per trip (not the author, 30/user/hour). Reports: insert-only table, one per reporter per trip, 20/user/day, only for published trips you don't own; **5 distinct reporters auto-hide** a trip (status `hidden`; service role restores or deletes).
- Verified the migration for real in an in-memory Postgres (`scripts/db/marketplace-check.mjs`, 48 checks: RLS, grants, anon/guest/other-user denial, validation rejects, rate limits, auto-hide).

### Choices worth knowing
- Search is plain `ILIKE` on title/description (LIKE wildcards escaped), offset paging (24/page, +1 row to detect "more"). Fine to thousands of trips; at scale add `pg_trgm`/tsvector and keyset paging.
- One published row per (author, source trip). The snapshot is of the *selected version* at publish time; `source_trip_id` is its root's id.
- Report reasons are a text CHECK (spam, offensive, personal_info, other), not a Postgres enum.
- Published rows live only in component state / the table — never in the trips store, localStorage or `lib/sync.js`. Only the copy the user makes enters their data.

### Limitations
- No link previews / SEO: the app is a client-rendered SPA, so shared links unfurl as the generic site card.
- Free-text fields (title, description, activity names, base names) are author-written and unmoderated until reported; no automatic profanity/link filtering. They are rendered only as text.
- Auto-hide at 5 reports can be brigaded by 5 throwaway accounts (each needs a confirmed email); restoring is a service-role update.
- A trip deleted locally stays published until unpublished (the snapshot is independent). Deleting an account removes its published rows (FK cascade).
- Cover images are resolved client-side from the first stop's city (Wikipedia/Unsplash path in `images.js`), so a card can show a placeholder first.
- Smoke covers the browser flows against a fake Supabase; RLS itself is covered by the PGlite check, not by the browser run.

## 2026-10-10 — My trips highlights the current trip (#fac390)
The separate "You're on a trip" card is gone from My trips (Home keeps it). The in-progress trip's row gets an accent ring (`data-current="true"`), a "Current · Day N" pill instead of Booked/Dated, and an "Open Today" footer; in-progress trips sort first (own + Shared with me). One helper, `stageLabelFor(trip, today)` in lib/today.js ("Current" while `tripDayFor` is 'during', never for done; stored status untouched), also used on the trip header, friend trip view and the main version on Versions. Map markers unchanged.

## Privacy fixes (#bedf85) — 2026-10-10

From `docs/research/privacy-legal-audit.md`. No new serverless function (Hobby cap). **Migration `0021_privacy.sql` is not applied** — the orchestrator asks the user.

### What changed
- **Delete account (H2).** Settings → Account → *Your data* → "Delete account": an inline confirm (type `DELETE`; no `window.confirm`) listing what goes, that shared trips disappear for collaborators, that purchased credits are forfeited and that it can't be undone. `src/lib/privacy.js deleteMyAccount()` removes `avatars/<uid>/*` through Storage (objects don't cascade from SQL), then calls the RPC `delete_my_account()` (0021: security definer, caller = `auth.uid()`, refuses guests, not callable by anon), which deletes the caller's trips and `auth.users` row; every other user table cascades. The app then runs the sign-out cleanup (`resetAccountState`, a local-scope sign-out) and lands on Home with a toast. Guests get "Clear this device's data" instead (ends the guest session, wipes local trips/chats; their server rows go with the 60-day guest cleanup).
- **Purchase records survive deletion.** `credit_purchases.user_id` → nullable, FK `on delete set null` (was cascade). Reason: it's a financial record, and `grant_purchase()` relies on the `order_id` row to ignore retried Lemon Squeezy webhooks — with cascade, a retry after deletion would try to re-grant.
- **Download my data (H2).** Same section: a JSON file built in the browser from what RLS lets the user read — account basics (id, email, sign-in methods, dates), profile, all trip rows (versions + tombstones), chats, friendships, trip memberships, own published trips, credit balance + purchases + usage events, MCP tokens (name/hint/dates) and OAuth app grants (name/scope/dates). Explicit column lists (never `*`, never hash columns) plus a recursive scrub of hash/secret-shaped keys; PostgREST paging at 1000 rows. A table that can't be read is listed under `incomplete`.
- **Friends see less (M2).** `friend_safe_trip()` (0021) now also strips notes (trip/stop/activity/leg), lodging and *picked* stays, budget, costs/prices, home/start/end locations and the packing list. Dates, places, activities, flight numbers/times stay (friends plan together). The client mirrors it (`friendSafe` in `src/lib/friends.js`) and fills the stripped fields with empty defaults so the view and "Copy to my trips" never see `undefined`. Friends page copy says what friends see. No per-trip "show details" opt-in (not cheap enough to do well — later, if asked).
- **Security headers (M3).** `vercel.json` → all routes: `X-Frame-Options: DENY`, `Content-Security-Policy: frame-ancestors 'none'; base-uri 'self'; object-src 'none'`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Content-Type-Options: nosniff`, `Permissions-Policy: geolocation=(self), camera=(), microphone=(), payment=(), usb=()`. **Follow-up:** a full script/style/connect CSP (MapLibre blob workers, Google Fonts, Supabase incl. realtime wss, Turnstile, OpenFreeMap, Wikipedia/Wikimedia, Openverse + its image hosts, Nominatim, Open-Meteo, fx/holiday APIs, Lemon Squeezy) — ship as `Content-Security-Policy-Report-Only` first, watch a preview deploy, then enforce.
- **AI routing pinned (M1).** Every Vercel AI Gateway request (chat-completions and the Anthropic Messages endpoint) carries `providerOptions.gateway.only` = providers on Vercel's ZDR list: `anthropic, bedrock, vertex, openai, azure, groq, togetherai, fireworks, baseten` (gpt-oss-120b on the gateway is served by baseten, bedrock, fireworks, groq, parasail, nebius, togetherai, cerebras — cerebras is excluded). Env: `GATEWAY_ALLOWED_PROVIDERS` (comma list; `*` = no pin), `GATEWAY_ZDR=1` adds per-request `zeroDataRetention: true` — **Pro/Enterprise only, so off by default; on Hobby the pin is the protection, not ZDR**. Direct Anthropic calls are unchanged. Docs: https://vercel.com/docs/ai-gateway/models-and-providers/provider-options, https://vercel.com/docs/ai-gateway/security-and-compliance/zdr.
- **Retention (L1).** `run_cleanup()` (0021, create-or-replace; every 0019 step kept) also nulls `usage_events.ip_hash` older than **7 days** (the guest per-IP cap reads 24h). The OAuth client-registration IP hash now uses the same salted hash as guests (`saltedIpHash` in `server/guest.mjs`, `IP_HASH_SALT`).
- **Marketplace coordinates (M4).** `buildSnapshot` rounds stop and base lat/lng to **2 decimals (~1 km)**; "Exact locations" added to the left-out list. The 0018 validator accepts any number, so no DB change.
- **`trips` in the repo (H3).** 0021 section 1: `create table if not exists public.trips` (id text pk, user_id uuid not null default auth.uid() → auth.users on delete cascade, kind default 'proposal', data jsonb, updated_at default now(), deleted default false), RLS on, and the four owner-only policies created **only if the table has no policy for that command** (so production's live policies are untouched — a no-op there), plus `revoke truncate, trigger, references … from anon, authenticated`. For a from-scratch replay, run 0021 section 1 before 0014 (0014–0020 reference `trips`).
- **Fail-closed AI (L5).** `api/ai/plan.js` returns 503 when billing env is missing **and** `VERCEL_ENV === 'production'`; local dev and previews keep the open path.

### Verification
- `npm test` 406 (was 389): export assembly/scrub, friendSafe + copy tolerance, publish rounding, gateway provider options, fail-closed AI, 0021 static guards.
- `scripts/db/privacy-check.mjs` (PGlite; `npm i --no-save @electric-sql/pglite`): replays 0001–0020 on stub auth/storage/cron, applies 0021 twice, then 19 checks — delete_my_account (anon denied, guest refused, every user row gone incl. friendships/memberships/published/MCP, purchase kept with user_id null, other user untouched), friend_safe_trip output, run_cleanup (no step errors, all steps present, ip_hash nulled after 7 days), trips policies (one per command after two runs) and grants.
- Smoke: main 105, signout 19 (+3: download file has no hashes/secrets, delete flow order list→remove→rpc then Home + toast, guest clear), market 25, oauth 9. Build OK.

### Not done / for the user
- Apply 0021. Before relying on deletion in production, confirm the postgres role can delete from `auth.users` (0019's guest cleanup does the same: `select errors from public.cleanup_runs order by ran_at desc limit 5` should show no `guest_users` error), and that no `storage.objects.owner` FK blocks it (the client removes avatars first either way).
- `server/fares.mjs gateFares` also runs open when billing env is missing (live fares, Ignav cost) — same fail-closed treatment would be a one-liner.
- Deleted-account data remains in Supabase backups for their retention window, and in Lemon Squeezy (merchant of record) — say so in the privacy policy.

## 2026-10-10 — Privacy Policy + Terms drafts, in-app legal pages, sign-up agreement (#4515e5)

**Not legal advice. Drafts for a lawyer to review.**

- `docs/legal/privacy-policy.md` and `docs/legal/terms.md` were written from the privacy audit (`docs/research/privacy-legal-audit.md`), the code, and the privacy-code agent's facts: gateway provider allowlist, no ZDR claim, guest IP hashes kept 7 days, what account deletion removes and keeps, what friends see, 1 km published pins. `docs/legal/README.md` lists the placeholders, the open TODO facts, and what to update when sub-processors, retention, AI context or visibility change.
- In-app: `?page=privacy` / `?page=terms` (`src/pages/LegalPage.jsx`, lazy-loaded, imports the .md files with `?raw`). `src/lib/legalMarkdown.js` is a tiny parser that turns a Markdown subset into plain data with no HTML at all. Links are allowed only for http(s), mailto and `/?page=`; `<!-- -->` drafting notes are dropped. Tests: `tests/legalMarkdown.test.mjs`.
- Links: `src/components/LegalLinks.jsx`, a footer on Home, Explore and published trips, plus the signed-in account menu and the OAuth consent page. A plain click navigates in-app (`tf:open-page`); the consent page opens a new tab.
- Sign-up (`Auth.jsx`): a required "I'm 13 or older (16+ in the EU/UK) and agree to the Terms and Privacy Policy" checkbox. Create account stays disabled until it's ticked. A "By continuing…" line under Continue with Google appears in both modes. That line is the only change to log in, and it also covers magic-link sign-up.
- The visible "Draft — last updated [DATE]" line stays in both docs until the lawyer signs off. Remove it then.
- Settings → Account → Your data (the privacy agent's branch) doesn't link to these pages yet. Reconcile on merge.

## Stays vs visits — decision (2026-10-12)

Tracker #279087. From Eric's Sedona/Grand Canyon/Zion test: parks and events were getting their own overnight stops. The data model already supports place types, a separate sleep town (`base`) and 0-night day stops (FT2); the gap is presentation and AI behaviour. Options weighed: A two lanes (visits row + "Sleeping in" lane), B stays-first list with visits nested, C clearer labels only. **Chosen: A** — smallest change that shows both "what we see" and "where we sleep" at a glance; B may be revisited with the trip library (#812ee5).

| # | Milestone | Description |
|---|---|---|
| SV1 | Sleeping-in lane | Bars under Day by day spanning nights per sleep town |
| SV2 | AI rule | Parks/events within ~2 h of the base become day visits (finder + assistant) |
| SV3 | One-tap toggle | "Make this a day visit" / "Stay overnight here" on a stop |
| SV4 | Audit flag | Flag overnight park/event stops near the previous town, one-click fix |

### Stays vs visits built — 2026-10-12

- SV1: `sleepLane` (lib/housing.js) → bars under Day by day (`data-testid="sleep-lane"`), same columns as the cards (invisible 0-height connectors keep widths equal, so they scroll together). Tokens `--color-sleep` / `--color-sleep-tint` (light + dark), Tailwind `sleep`. A bar spans stops with one sleep town, across a day stop between them; tap opens the first stop's city page (stay picker).
- SV2: `VISIT_RULE` (lib/trip.js, ~50 tokens) in the assistant rules (before CACHE_BREAK) and the finder prompt. Eval case `ed-day-visit` (Sedona/Zion, `expect.ok`).
- SV3: `lib/stays.js` — `dayVisitOps` / `stayOvernightOps` / `stayToggle`; buttons on Day by day cards (Edit mode) and the city page; applied through `applyAiOps` (one undo step). Freed nights go to the previous overnight stop (the next one if none).
- SV4: audit issue "N km from <town>, where you already sleep" with a `day-visit` action built from the latest record when applied (so fix-all composes). Threshold `DAY_VISIT_KM` = 150 km straight-line between the stop's pin and the previous sleep point (base pin, else that stop's pin); skipped without coordinates, and when the stop already sleeps in the same town.
- Known: no road-time check (straight-line only); a stop with no pin isn't flagged.

## Trip Fairy Plus — decision (2026-10-17)

Tracker #4d1c36. Design doc: https://claude.ai/code/artifact/80296f72-8795-4abb-8616-842de0954780 (competitor prices in docs/research/competitor-scan.md, costs in docs/research/free-tier.md §2 and §9). **Chosen:** an optional Plus plan alongside the free tier (60 signup / 20 monthly) and credit packs — $4.99/month or $39/year, 150 AI credits a month (no rollover), fare caps 150/day + 1,000/month, smart loading at launch; price alerts, PDF/Maps export and offline added later. Defaults where undecided: no free trial at launch; a one-trip pass revisited after usage data. Blocked on the LLC bank account + Lemon Squeezy switch (#7f2e41).

| # | Milestone | Description |
|---|---|---|
| SUB1 | Lemon Squeezy product | Owner: "Trip Fairy Plus" subscription with monthly + yearly variants |
| SUB2 | Subscription webhooks + plan record | Handle created/updated/cancelled/expired/payment_failed; one migration (needs OK) |
| SUB3 | Monthly grant + caps by plan | Refill gives 150 to active subscribers; fare caps read the plan |
| SUB4 | Settings → Credits: Plus card | Subscribe, manage/cancel via LS customer portal; tiers info page (#dca3f2) |
| SUB5 | Smart loading as the first perk | #9a14e8, Plus-only |

## Trip library — decision (2026-10-17)

Tracker #812ee5. Options page: https://claude.ai/artifact/RK7ZwMhqopUGxCptmCQN6e. **Chosen: A + C's pieces** — a cross-trip **Saved** library (trip versions, saved ideas, bookmarked places; search + filter by type and trip), place bookmarks from chat cards and city pages (places not yet in a trip allowed), the assistant can save an alternative or a place from the chat, and "Versions" is renamed "Alternatives" with the main plan clearly marked. Versions keep their current storage; the library is a view over them plus a small synced bookmarks store. Ask Eric which "rough edges" he meant.

| # | Milestone | Description |
|---|---|---|
| LIB1 | Bookmarks store | Synced per-account list of saved places (name, kind, city/country, coords, blurb, source trip), like trips/chats; privacy: own-only |
| LIB2 | Save buttons | Bookmark on chat place cards and city-page places; saved state shown |
| LIB3 | Saved page | Menu entry; one searchable, filterable list of versions, ideas and bookmarks across trips; open / add to a trip / remove |
| LIB4 | Assistant saves | New assistant actions: save an alternative of the trip (like MCP create_version) and save a place; cards to open/compare |
| LIB5 | Alternatives rename | "Versions" → "Alternatives" across UI and copy; main plan clearly marked; easier switching |

**Built (branch feat/trip-library, 2026-10-17).**
- LIB1 — `public.saved_places` (migration `0022_saved_places.sql`, **review before applying**): PK (user_id, id), owner-only RLS, server LWW guard (a stale write is skipped), limits (data ≤ 20 KB as jsonb text — the client caps 16 KB of JSON — and ≤ 2,000 live rows per user; tombstones exempt), `ON DELETE CASCADE` from `auth.users` (so `delete_my_account()` removes it), old tombstones purged by `run_cleanup()`. Checked by `scripts/db/saved-places-check.mjs` (PGlite). Client: `src/lib/savedPlaces.js`; local key `trippin.saved.v1` (cleared on sign-out, kept in the stash across an account switch, in the data export). Until the migration is applied the table is a 404 / `42P01` / `PGRST205`: sync switches itself off quietly and bookmarks stay on the device; signing out with unsynced bookmarks asks first (the usual "sign out without syncing?" dialog) instead of dropping them. Saved places are private: never part of a trip record, so never in friend views, shared trips or published snapshots.
- LIB2 — bookmark toggle on chat place cards and city-page places (`SaveButton`); Undo toast on save and remove.
- LIB3 — Saved page (`?page=saved`, `src/pages/SavedPage.jsx`, view built by `src/lib/library.js`): alternatives (every version but the main plan), saved ideas (still device-local, like on Home) and bookmarks; search, type chips, trip filter; place detail with Map link; "Add to a trip" reuses `cardToOps` and runs as a normal edit of any trip with Undo.
- LIB4 — edit-plan contract gains optional `actions`: `save_alternative` ({ name, ops } → new version with the ops applied; the plan is untouched and stays the main plan) and `save_place` (a place card). ~180 tokens in the cached static instructions. The transcript tells the model what was saved.
- LIB5 — "Versions" → "Alternatives" in UI/assistant/MCP copy (identifiers like `kind: 'plan'`, `proposalId`, `?page=versions`, `create_version` unchanged); "Main plan" badge on the trip bar and Alternatives page; a strip on a non-main alternative with "Back to the main plan" / "Make this the main plan". New names are "Alternative N" (older "Version N" names stay).

## View links (share without an account) — built 2026-10-18 (#aa49dc), migration 0023 NOT applied
- The Share dialog's owner gets "Share a link": one live read-only link per trip, `/?page=view&t=<64 hex>`, opens signed out (`pages/ViewTripPage.jsx`), "Sign up to copy this trip" / "Plan your own trip" for visitors, "Copy to my trips" for signed-in ones (the marketplace copy flow + duplicate-name prompt).
- Data: `trip_view_links` (owner-only select, revoke-only update, no direct insert) + RPCs `create_view_link` (rotates), `refresh_view_link`, `revoke_view_link`, `view_trip` (anon + signed in; bumps `view_count`). The link holds the **marketplace snapshot** (`buildSnapshot` allowlist, re-validated server-side by 0018's `published_snapshot_error`), built from the trip's main plan and refreshed whenever the owner opens the Share dialog. Not a live read of `trips`: one allowlist in JS instead of a second copy in SQL. Hiding a trip from friends, deleting it or deleting the account shuts its link.
- Before 0023 is applied the Share dialog has no link section and `?page=view` says "This link isn't available".
- Link previews: the SPA has one static OG/Twitter set in `index.html` (site name, description, icon). Per-link titles/images need server-rendered tags: an existing `api/*` function plus a `vercel.json` rewrite for `?page=view` (we're at the 12-function cap, so it would have to share a function), or the Pro plan's higher cap.
- Place pins (#286f4f): a city page view no longer re-geocodes places that already have coordinates. `geocodeCityPois` first-geocodes only coordinate-less places and audits only places flagged `geoUncertain`; "Check this city's place pins" in the stop's edit panel runs the full `auditPoiGeo` on demand. Nothing sets `geoUncertain` yet (the place prompt doesn't ask the AI for it).

## Indexable published-trip pages (#2c0bbd) — built 2026-10-24, no migration
- Canonical URL `/trips/<slug>-<id>` (`src/lib/tripUrl.js`: slug from the title, id = `published_trips.id`; the id decides, a stale/missing slug 301s to the current one). Old `?page=published&id=` links still open and the address bar is rewritten to the canonical path.
- `GET /trips/:path*` → `/api/data?op=trip-page&p=…` and `GET /sitemap.xml` → `/api/data?op=sitemap` (`server/tripPages.mjs`, folded into `api/data.js`; still 8 functions). The trip page fetches the deployment's built `index.html`, swaps in the trip's `<title>`, description, canonical, Open Graph/Twitter tags and JSON-LD (TouristTrip + ItemList of stops, BreadcrumbList), and puts a readable summary in `#root` (the SPA replaces it on boot). Unknown/unpublished/hidden → 404 + `noindex`; a Supabase outage → 503 `no-store` (never a cacheable 404). `Cache-Control: s-maxage=600, stale-while-revalidate=3600` (sitemap 1 h).
- Privacy: one trip is read through the anon `public_trip(id)` RPC (same columns the public page shows). The sitemap needs a list, which anon can't make (`browse_published_trips` is signed-in only), so it reads `id,title,updated_at` of `status='published'` rows with the server key (SUPABASE_SECRET_KEY, already set for billing). If you'd rather keep that off the service key, add an anon-callable `published_index()` RPC (a migration) and switch `fetchSitemapRows`.
- OG image is the site card: the snapshot has no photos (publishing strips them), so there is no per-trip lead image yet.
- Seed content: `scripts/seed/marketplace-trips.json` (20 trips) + `scripts/seed/publish-seed.mjs` (dry run by default; `--apply` with a dedicated account's credentials). Checked by `tests/seedTrips.test.mjs` (JS allowlist) and `scripts/db/seed-check.mjs` (0018 `published_snapshot_error` + guard trigger in PGlite).
- Owner steps: add the site in Google Search Console, submit `https://mytripfairy.com/sitemap.xml`, run the seed script, and decide the seed account's username/avatar.
