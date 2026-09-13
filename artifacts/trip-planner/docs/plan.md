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
