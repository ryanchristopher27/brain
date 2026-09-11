# Review — M1–M3 (segment model, patch/undo engine, timeline)

Date: 2026-09-05
Triggered by: /build completion (M1, M2, M3)
Scope: src/lib/{trip,migrate,storage,patch,history}.js · src/components/{TripEditor,Timeline,Sidebar}.jsx · src/App.jsx
Focus: All (plan adherence · code quality · security)

## Summary
Healthy. Implementation tracks the plan; all deviations were flagged during `/build`.
**Critical: 0 | Warning: 2 | Suggestion: 3.** The two Warnings are bounded and sit in
the M2/M3 code that **M4 builds directly on**, so they're fixed inline this session; the
suggestions are deferred to `/iterate`.

## Plan Adherence
- **M1** segment backbone, `v1→v2` migration, TripEditor segments, tripToContext — ✅ matches plan.
- **M2** `applyOps` pure reducer, op protocol, `parsePatch`, bounded history — ✅ matches plan;
  op-schema surface resolved and logged in the plan's Decisions Log.
- **M3** read-only segmented timeline with rollups — ✅ matches plan.
- Flagged-and-accepted deviations (not findings): legacy `AiPanel` still writes `trip.stops`
  (invisible until M4); `history.js` added as its own module; Timeline interim-mounted in App;
  small Sidebar label edit. All documented.
- No unresolved open questions leaking into shipped code (undo depth, op surface both decided).

## Code Quality
Consistent with existing patterns (factory helpers, `card`/`chip` classes, immutable updates).
Engine modules are pure and unit-tested (39 assertions across migration + patch/history). Two
correctness bugs found (below). No dead code beyond the intentional transitional `stops` field.

## Security
Local-first, no backend, no injection surface. React escapes all rendered strings; no
`dangerouslySetInnerHTML`. BYOK key in localStorage is the documented design posture (unchanged).
One hardening item: `applyOps` merged model-supplied `data` without protecting item identity (W2).

## Findings

### Critical
_None._

### Warning
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| W1 | [Timeline.jsx](../src/components/Timeline.jsx) `num()` | Cost rollup parser stops at the first non-digit, so thousands separators break it: `"$1,200"` → `1`. Per-segment `~cost` can be wildly understated. | Strip commas before matching. | ✅ Fixed |
| W2 | [patch.js](../src/lib/patch.js) `applyOps` add/update | `{...it, ...op.data}` lets a model-supplied `data.id` overwrite an item's identity → duplicate/rewritten ids break by-id updates, undo, and React keys. M4 feeds this untrusted-ish model output. | Drop `id` from `data` before merging (identity is engine-owned). | ✅ Fixed |

### Suggestion
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| S1 | [trip.js](../src/lib/trip.js) `tripToContext` | `segmentDayRanges(trip)` is rebuilt inside the segments `.map` (O(n²)). | Hoist the Map once before mapping. | ✅ Fixed (/iterate 2026-09-06) |
| S2 | [patch.js](../src/lib/patch.js) `reorder` | Segments whose id is absent from `data.order` keep their old `order`, which can collide with new indices. | After applying, renumber all segments 0..n by resulting order. | ✅ Fixed (/iterate 2026-09-06) |
| S3 | [App.jsx](../src/App.jsx) init | `loadTrips()` is called twice at startup (trips state + selectedId). | Initialize once and derive selectedId from it. | ✅ Fixed (M4 App rewire) |

## /iterate — 2026-09-06
- S1, S2, S3 resolved (S3 during the M4 rewire). +2 regression assertions for S2 reorder normalization.
- Dead code removed: `draftItinerary`, `buildPrompt`, `ITINERARY_INSTRUCTIONS`, and the `parseItinerary` alias in `aiClient.js` (all orphaned when `AiPanel` was retired in M4).
- No plan update needed — all quality fixes and dead-code removal, no scope/architecture change.

## Resolved This Session
- W1 — cost parser hardened against separators.
- W2 — `applyOps` no longer lets `data` override item `id`.

## Carried to /iterate
- S1 (perf, trivial), S2 (reorder normalization), S3 (double load). None block ship or M4.
Priority: S2 > S1 > S3.

---

# Review — N1–N5 (proposal → plan lifecycle)

Date: 2026-09-06
Triggered by: /build completion (N1–N5)
Scope: src/lib/{trip,migrate,storage,escalate,aiClient}.js · src/components/{Sidebar,TripEditor,ProposalView,PlanChat,Workspace}.jsx · src/App.jsx
Focus: All (plan adherence · code quality · security)

## Summary
Solid. The lifecycle matches the plan; the risky bits (v2→v3 split, snapshot id-remap, kind-gating,
kind-aware prompt) are all unit-tested. **Critical: 0 | Warning: 1 | Suggestion: 2.** One
data-integrity bug (orphaned plans on proposal delete) is bounded and fixed inline; two suggestions
carry to /iterate.

## Plan Adherence
- N1 model+migration, N2 nested nav + idea→proposal, N3 kind-gated editor, N4 snapshot escalation,
  N5 kind-aware chat — all built as specified; decisions logged in plan v2.
- Flagged-and-accepted deviations (not findings): id-remap placed in trip.js (not escalate.js);
  proposals reuse Workspace via ProposalView; proposal restriction enforced at prompt+UI level.

## Code Quality
Consistent, DRY (escalation and migration share `remapRecordIds`; escalation driven off
`SHARED_FIELDS`; prompt built from a shared `OP_PROTOCOL`). 44 unit assertions across migration,
patch, escalate, and prompt suites. No dead code or leftover stubs (escalate.js now implemented).

## Security
No new external surface. Records stay in localStorage (unchanged posture). React escapes rendered
strings. User content flows into the model prompt as data (self-authored; not rendered as HTML).

## Findings

### Critical
_None._

### Warning
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| W1 | [App.jsx](../src/App.jsx) `deleteTrip` | Deleting a **proposal** leaves its child plans in storage. They're excluded from the proposals list and nest under a now-missing parent → **unreachable orphan records** (can't be opened or deleted; silently bloat storage). | Cascade-delete a proposal's plans (also reset selection if a cascaded plan was open). | ✅ Fixed |

### Suggestion
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| S4 | [Timeline.jsx](../src/components/Timeline.jsx) + ProposalView | On a **proposal**, the timeline still shows day columns and allows drag-to-day, which sets an activity `day` the proposal editor deliberately hides. | Make the proposal timeline read-only (or hide day scheduling) — pass `onApplyOps` only for plans. | ✅ Fixed (/iterate 2026-09-06) |
| S5 | [patch.js](../src/lib/patch.js) `applyOps` | Proposal restriction is prompt+UI only; `applyOps`' field whitelist still permits committed fields, so a non-compliant model reply could set one (hidden) on a proposal. | Add a kind-aware guard that drops PLAN_ONLY_FIELDS / segment-commit / activity-schedule writes when the record is a proposal. | ✅ Fixed (/iterate 2026-09-06) |

## Resolved This Session
- W1 — `deleteTrip` now cascade-deletes a proposal's plans and clears selection if a cascaded plan was open.

## /iterate — 2026-09-06 (follow-up)
- S5 fixed: `applyOne` now self-guards by `trip.kind` — on a proposal it strips PLAN_ONLY_FIELDS
  from field updates, SEGMENT_PLAN_FIELDS from segment writes, ACTIVITY_PLAN_FIELDS (day/time/cost)
  from activity writes, and no-ops flight ops. New `ACTIVITY_PLAN_FIELDS` const in trip.js. +14 guard assertions.
- S4 fixed: `Workspace` passes `onApplyOps` to the timeline only for plans, so a proposal's timeline
  is read-only (no drag-to-schedule). Verified in-app (no draggable cards / drop targets).
- No plan update needed — quality/hardening fixes, no scope or architecture change.

---

# Review — F1–F2 (Ignav flight capability + snapshot schema)

Date: 2026-09-06
Triggered by: /build completion (F1, F2)
Scope: server/index.mjs · src/lib/{flights,trip,migrate}.js · vite.config.js · server/.env.example · .gitignore
Focus: All (plan adherence · code quality · security)

## Summary
Strong. Matches plan v3.1 (Ignav, server proxy, snapshot schema, normalize), verified against the
real Ignav API and saved responses. A v3→v4 migration duplication bug was caught **and fixed during
F2**. **Critical: 0 | Warning: 1 | Suggestion: 2.** The Warning is security-relevant (bounded) and
routed to /iterate; suggestions are minor.

## Plan Adherence
- F1: `/flights/health,search,airports`, Ignav key server-side, `.env` loader, search/airport caches — ✅.
- F2: v4 flight snapshot fields, `v3→v4` migration, pure `normalizeOffer`/`offerToLegs`, client fns — ✅.
- Ignav contract resolved against `openapi.json` + live calls (open question closed).
- `bookingUrl` is currently always `''` — populating it needs a `/flights/booking-links` call (Ignav
  requires `ignav_id`), which is a deep-link hand-off deferred to F3/later. Aligned with plan (booking
  = link-out, never in-app). Informational, not a defect.

## Code Quality
Zero-dep helper preserved (built-in `.env` parser, global `fetch`). DRY (`readBody`, single `ignav()`
client, shared cache helpers). Pure mappers unit-tested against real data (24 assertions). Naming
consistent. Minor vestigial field noted below.

## Security
Key handling is sound: from env/`.env`, sent only in `X-Api-Key` to Ignav, never logged (startup logs
"configured", not the value), never returned to the browser, `server/.env` gitignored. Airport query
is `encodeURIComponent`-escaped; the search endpoint (one-way vs round-trip) is chosen **server-side**,
so the client can't drive arbitrary Ignav paths. One exposure finding (W1) below.

## Findings

### Critical
_None._

### Warning
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| W1 | [server/index.mjs](../src/../server/index.mjs) `sendJson` | Helper sets `Access-Control-Allow-Origin: *`. The app calls via the Vite proxy (same-origin), so this header is **unneeded** — but it lets **any website the user visits call `localhost:8787` while the helper runs**, spending Ignav quota / invoking the AI. Pre-existing on `/ai`, but F1 puts a **billable API** behind it. | Reflect only `http://localhost:<port>` origins (or drop CORS entirely, since the proxy makes it same-origin). Small refactor to thread the request origin into `sendJson`. | Open → /iterate |

### Suggestion
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| S6 | [server/index.mjs](../server/index.mjs) caches | `searchCache`/`airportCache` only evict on next access after TTL — a long-running helper with many distinct searches grows unbounded. | Cap size (LRU) or periodic sweep. Low impact (local, restarts often). | Open → /iterate |
| S7 | [flights.js](../src/lib/flights.js) `offerToLegs` | Per-leg `stops` is always `0` (a segment is nonstop); real stop count lives in `normalizeOffer`. Vestigial on the leg. | Drop `stops` from the leg, or document that leg-level stops is always 0. | Open → /iterate |

## Resolved This Session
- v3→v4 migration duplication bug — fixed during F2 (split now gated on `kind` absence, not version).

## Carried to /iterate
- W1 (CORS exposure over a billable API — security, bounded), S6 (cache growth), S7 (vestigial field).
Priority: W1 > S6 > S7. None block continuing to F3.

## /iterate — 2026-09-06 (F1–F2 findings)
- W1 fixed: helper now gates on `Origin` — cross-origin requests get 403 before any Ignav call
  (localhost / no-origin allowed). Verified: evil origin → 403 (GET + POST), proxied app search → 200.
- S6 fixed: caches cap at 200 entries (evict oldest).
- S7 fixed: removed the vestigial per-leg `stops` (real stop count stays in `normalizeOffer`);
  dropped from `newFlight`, `offerToLegs`, and the v3→v4 migration default.
- No plan update — quality/security hardening; F2 was uncommitted so the leg-shape change is clean.

---

# Review — F6 (booking-link deep-links)

Date: 2026-09-06
Triggered by: /build completion (F6)
Scope: server/index.mjs · src/lib/{flights,trip}.js · src/components/{FlightSearch,PlanChat,TripEditor}.jsx
Focus: All (plan adherence · code quality · security)

## Summary
Clean. Booking deep-links proxy Ignav server-side; endpoint path verified live. **Critical: 0 |
Warning: 0 | Suggestion: 2.** One security-hardening suggestion applied inline (bounded); one UX
gap routed to /iterate. F6 was an approved add-on beyond plan v3.1 (bookingUrl had been deferred).

## Plan Adherence
- Matches the F6 tracker task: `/flights/booking-links` proxy, `getBookingLink`/`openBooking`,
  `ignavId` on the leg, Book buttons in results/chat/saved-flights. Deep-link hand-off only.
- Plan v3.1 didn't have an F6 section (booking was deferred); added on user request — noted here.

## Code Quality
Thin proxy consistent with search/airports; `getBookingLink` centralizes flatten+pick (prefer
airline); `openBooking` shared by cards. Minimal duplication. Documented expiry (424) limitation.

## Security
Helper forwards only `{ignav_id}` (not arbitrary body); origin gate + cache apply; key server-side.
Book is user-initiated; `window.open` uses `noopener,noreferrer` (no reverse-tabnabbing). One
hardening: validate the provider URL scheme before opening (S8, applied).

## Findings

### Suggestion
| # | Location | Issue | Recommendation | Status |
|---|----------|-------|----------------|--------|
| S8 | [flights.js](../src/lib/flights.js) `getBookingLink` | Opens a provider-supplied URL via `window.open`. A malformed/malicious provider URL (e.g. non-http scheme) shouldn't be opened. | Validate `^https?://` before returning/opening; else treat as no link. | ✅ Fixed |
| S9 | FlightSearch/PlanChat/TripEditor Book handlers | A failed Book (expired 424 / no links) gives **no user feedback** — the click silently does nothing. | Surface a brief "fare no longer available — search again" message. | Open → /iterate |

## Resolved This Session
- S8 — booking URL scheme validated before opening.

## Carried to /iterate
- S9 (silent Book failure — UX feedback). Non-blocking.

## /iterate — 2026-09-06 (S9)
- S9 fixed: all three Book handlers (FlightSearch results, PlanChat offer cards, saved plan
  flights) now surface a message on failure/expired instead of silently no-op'ing. Verified
  in-app: a saved flight with a stale ignav_id shows "Couldn't fetch a booking link — the fare
  may have expired." No plan update (UX polish).
