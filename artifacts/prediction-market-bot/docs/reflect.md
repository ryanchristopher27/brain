# Reflect — M3 + Dashboard Scaffold (Sessions 1–3)
Date: 2026-06-04
Type: Milestone
Phase context: /brainstorm → /plan → review → /scaffold → hotfix

---

## Accomplished

- **M3 (Baseline Model) complete.** `models/benchmarks/fed_baseline.py` compares CME ZQ futures
  (via yfinance) against KXFEDDECISION Kalshi prices and generates typed `Signal` NamedTuples.
  First run produced 9 tradeable signals. `scripts/run_signals.py` provides a clean CLI view.

- **Kalshi snapshot collector fixed.** Kalshi switched their API to a fractional trading format —
  prices now return as `_dollars` string fields (e.g. `yes_bid_dollars: "0.9600"`) rather than
  integer cents. Rewrote `_parse_snapshot()` to use `_dollars_to_cents()` and eliminated the
  separate `get_orderbook()` call, halving API calls per snapshot cycle.

- **FedWatch data source resolved.** CME's web scrape was blocked. Switched to yfinance ZQ
  30-Day Fed Funds Futures with a month-over-month rate change methodology to avoid end-of-month
  amplification artifacts.

- **Dashboard Phase 1 scaffolded (D1 structural).** 26 files created across `dashboard/`:
  FastAPI backend with 7 routers and 11 endpoints, 6 Streamlit pages, typed `httpx` client,
  `run_dashboard.sh` launcher, backtest caching script, Pydantic models, CORS middleware,
  auth stub, and dark theme config. API boots cleanly; all 21 routes registered.

- **Pre-plan review caught 10 gaps** before any code was written. All incorporated into the plan:
  backtest caching strategy, model-agnostic signal tagging, per-request DB connections, staleness
  detection, CORS config, unified trades table, dynamic FRED series list, snapshot coverage
  heatmap design, empty-state copy for Model Analysis, Phase 2 control stubs.

---

## What Worked

**The brainstorm → plan → review → scaffold sequence.** Running an in-depth review of the plan
before scaffolding was the most valuable step. The review surfaced 10 gaps that would have been
expensive to retrofit into 26 already-existing files. The pattern: don't scaffold until the plan
has been stress-tested against the current codebase and the future roadmap.

**Model-agnostic signals from day one.** Every signal carries a `model_name` tag. The signals
endpoint reads enabled models from `model_registry` rather than hardcoding `fed_baseline`. When
M5 nowcast models land, no API changes are needed — just register a new model and it's served
automatically. This would have been painful to add later.

**All data through `client.py` → API.** Streamlit pages never import trading engine modules
directly. The seam is enforced structurally. Auth, audit logging, and a potential future React
frontend all benefit from this pattern without a refactor.

**Backtest caching by design.** The `BacktestHarness` takes 10–30 seconds to run. Designing the
Model Analysis page to read from `backtest_cache` (refreshed by `scripts/run_backtest.py`)
rather than running the harness live was a deliberate call made during planning — not a
performance fix added after noticing the page was slow.

---

## What Didn't Work

**The import error diagnostic took too long.** The final bug — `data.py` importing
`FedSeriesListResponse` instead of `FredSeriesListResponse` (one letter typo: Fed vs Fred) —
was a 30-second fix that took much longer because the diagnostic process assumed a complex root
cause (circular imports). The tell: "direct import works, router chain fails" is consistent with
a typo in the router's own import statement, not just circular imports. The faster diagnostic
would have been: `grep -n 'FredSeries\|FedSeries' dashboard/api/routers/*.py`.

**26 files scaffolded without end-to-end validation.** The scaffold is structural — the API
boots and routes register, but D1 (database.py additions) isn't complete. Endpoints touching
`trades`, `model_registry`, and `backtest_cache` will return empty or 404 until the schema
additions and query methods are wired. This is expected given the plan, but the gap between
"API boots" and "pages render real data" is still open.

---

## Decisions Reviewed

All major decisions held up against scrutiny during the pre-plan review. No reversals. Notable
ones confirmed:

- **FastAPI + Streamlit (not pure Streamlit):** The auth seam and replaceability of Streamlit
  justify the two-process overhead. Direction A (pure Streamlit) was explicitly ruled out
  because it's a dead-end for Phase 2 operational controls.

- **SQLite WAL mode + per-request connections:** The collector daemon writes every 15 minutes;
  the dashboard reads concurrently. WAL handles this without a connection pool. Enforcing
  per-request connections via `get_db()` dependency prevents the module-level singleton pattern
  that would cause "database is locked" errors.

- **Phase 2 controls as 501 stubs:** All write endpoints in `control.py` return HTTP 501 with
  a clear message pointing to M6. This is intentional — the routes exist and are documented in
  `/docs`, but won't fire accidentally.

---

## Lessons Learned

1. **"Fed" vs "Fred" typos are invisible to human reviewers.** When naming classes, prefix
   disambiguation matters. `FredSeriesListResponse` and a hypothetical `FedSeriesListResponse`
   are one character apart. Consider a `_` separator or a more distinct naming convention for
   similar-sounding economic data models.

2. **Import errors in router chains: check the router first.** When a class "definitely exists"
   in the source file but the import chain fails, look for a typo in the importing file before
   diagnosing circular imports. Circular imports produce different error messages (most often
   `partially initialized module`).

3. **Review step belongs between plan and scaffold.** The brainstorm captures intent; the plan
   captures design; the review stress-tests the plan against reality. Without the review pass,
   the scaffold would have been built on a plan with 10 known gaps.

---

## Surprises

- The Kalshi API format change (fractional `_dollars` fields) was entirely undocumented. The
  only way to discover it was inspecting live API responses. The fix was clean, but the
  discovery method was fragile — any future format change will similarly require live
  inspection rather than changelog reference.

- CME FedWatch blocking web scrapes was expected as a risk but arrived before it was formally
  planned around. The yfinance ZQ futures workaround is solid but is itself a scrape of a
  scrape — worth monitoring for breakage.

- 9 tradeable signals on the first run of `run_signals.py` was a meaningful validation that
  the edge hypothesis has substance. The model is working as intended before the dashboard
  even exists.

---

## Memory Updates

Worth persisting across sessions:

- **Kalshi API format:** Prices are `_dollars` string fields from `get_market()` endpoint, not
  integer cents. Use `_dollars_to_cents()` for conversion. Any new snapshot logic must use this.
- **FedWatch data source:** yfinance ZQ futures (`ZQN26.CBT` etc.) with month-over-month
  methodology. CME direct scrape is blocked.
- **Import error diagnostic shortcut:** When a class "exists" but router import fails, grep the
  router files for the import string before assuming circular imports.

---

## Next Steps

Prioritized in order:

1. **D1 — database.py additions** (critical path to real data):
   - Add `trades`, `model_registry`, `backtest_cache` tables to schema
   - Add 9 query methods
   - Seed `model_registry` with `fed_baseline` on first run

2. **D2 — wire API endpoints** to real DB query methods (currently stubs / inline queries)

3. **Run the dashboard** and validate all 6 pages render correctly with live data

4. **D3–D6 polish** — validate chart data, empty states, auto-refresh toggles

5. **M4 (Manifold paper trading)** — begin once dashboard shows signals are live and stable

---

## Suggested Next Phase

`/build` (inline, no skill needed) — the scaffold is in place and the plan is clean. Next
session should start with D1 (database.py schema additions) and end with a running dashboard
showing real data. No additional planning or brainstorming needed.

**Confidence check:** The one shaky area is the 60s in-process signal cache in `signals.py`
router — it uses a module-level tuple `_cache` which may not behave well under uvicorn's
worker model if `--workers > 1` is ever used. Acceptable for local Phase 1; worth noting
before any production deployment.
