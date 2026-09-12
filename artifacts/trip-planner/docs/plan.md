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
