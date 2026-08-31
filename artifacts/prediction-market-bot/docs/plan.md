# Plan — Prediction Market Bot
Date: 2026-05-19
Status: Draft
Brainstorm: ../brainstorm.md

---

## Overview

Build a systematic trading bot that identifies and exploits mispricings in economic indicator prediction markets on Kalshi. The core edge hypothesis: **financial futures markets (CME FedWatch, inflation swaps) are better calibrated than prediction markets on the same events.** When a meaningful divergence exists, trade Kalshi toward the futures-implied probability.

Start on Manifold (free, no-risk sandbox) to validate model calibration before committing capital. Deploy to Kalshi demo, then live with small initial capital (~$200–$300). Scale only as performance is validated.

---

## Goals & Success Criteria

**Primary goal:** Generate positive risk-adjusted returns trading economic indicator markets on Kalshi.

| Criterion | Target |
|---|---|
| Manifold paper-trading | Brier score better than market baseline over 20+ events |
| Kalshi live (3 months) | Positive net PnL after all fees |
| Calibration | Reliability diagram approaching the diagonal |
| Risk management | No single position exceeds 5% of bankroll (0.25× Kelly enforced) |
| Model edge | Minimum 5–8% probability edge before fees before placing any live bet |

---

## Scope

### In Scope (v1)
- Economic indicators on Kalshi: Fed rate decisions (primary), CPI, unemployment (expansion)
- Data collection pipeline: Kalshi historical prices, CME FedWatch, FRED, SPF consensus
- Local price archive: SQLite store collecting Kalshi prices from day one
- Backtesting harness: Walk-forward validation with strict point-in-time data
- Baseline model: CME FedWatch vs. Kalshi price divergence (zero ML required initially)
- Manifold paper-trading validation before live capital
- Execution: Maker-first limit orders on Kalshi demo → live
- Fractional Kelly position sizing (0.25×)
- Trade log, PnL tracker, calibration metrics

### Out of Scope (v1)
- Elections, weather (planned v2 seasonal overlay)
- NLP / news-driven repricing pipeline (v2)
- Polymarket (secondary, post-Kalshi validation)
- Market making / liquidity provision (post-v1)
- Cross-market arbitrage (deferred indefinitely)
- Cloud infrastructure (local first; scale to cloud if capital scales)

---

## Tech Stack & Architecture

### Language
Python 3.11+ — dominant ecosystem for data science and quant work, good Kalshi SDK support.

### Data & APIs
| Library | Purpose |
|---|---|
| `pykalshi` | Kalshi REST + WebSocket (chosen over official SDK for production-ready error recovery) |
| `fredapi` | FRED economic data (CPI, unemployment, GDP history) |
| `httpx` | CME FedWatch probability polling + other REST sources |
| `pandas` + `polars` | Time series manipulation; Polars for large historical loads |
| `sqlite3` (stdlib) | Local market price archive; migrate to Postgres if needed |

### Modeling
| Library | Purpose |
|---|---|
| `scikit-learn` | Calibrated classifiers, `calibration_curve`, Brier score |
| `statsmodels` | Econometric nowcast models |
| `lightgbm` | Gradient boosting for feature-rich expansion models |
| `scipy` | Statistical utilities |

### Backtesting
- Custom walk-forward harness first (avoid over-engineering before model is validated)
- PredictionMarketBench for microstructure simulation in a later pass

### Execution
- Maker limit orders only in v1 (4× fee reduction vs. taker)
- Kalshi demo API first; production after Manifold + demo validation
- RSA-PSS auth wrapper abstracted in `kalshi_client.py`

### Project Structure
```
prediction_market_bot/
├── data/
│   ├── collectors/          # Kalshi, FRED, CME FedWatch scrapers
│   ├── storage/             # SQLite archive + CSV exports
│   └── processors/          # Feature engineering, PIT joins
├── models/
│   ├── benchmarks/          # Futures-market baseline (CME FedWatch vs. Kalshi)
│   ├── nowcast/             # CPI, unemployment leading indicator models
│   └── evaluation/          # Brier, log-loss, calibration, ECE
├── backtest/
│   ├── harness.py           # Walk-forward engine
│   ├── simulator.py         # Bid-ask simulation, fee calculation
│   └── metrics.py           # PnL, Kelly analytics
├── execution/
│   ├── kalshi_client.py     # REST + WebSocket wrapper, retry logic
│   ├── order_manager.py     # Maker order posting, fill tracking
│   └── risk.py              # Kelly sizing, position limits, hard stops
├── config/
│   ├── settings.py          # API keys, thresholds (loaded from env)
│   └── markets.yaml         # Target market definitions and filters
├── scripts/
│   ├── collect_history.py   # One-shot historical data pull
│   └── run_bot.py           # Main entry point
└── tests/
```

---

## Milestones

| # | Milestone | Description | Dependencies |
|---|---|---|---|
| 1 | **Data Foundation** | Archive pipeline: Kalshi price snapshots, CME FedWatch polling, FRED pulls, SQLite store. Start collecting immediately — historical data is the binding constraint. | None |
| 2 | **Backtesting Harness** | Walk-forward engine with strict PIT enforcement. Bid-ask spread simulation (fills at ask/bid, never midpoint). Fee calculation using the probability-weighted formula. | M1 |
| 3 | **Baseline Model** | Compare CME FedWatch implied probability to Kalshi price. Identify gap, calculate edge vs. fees, output trade signal. Fed rate decisions only. | M1 |
| 4 | **Manifold Paper-Trading** | Run baseline model on Manifold Markets. Validate Brier score vs. baseline. Build calibration curve. Gate: must beat market baseline over 20+ events before proceeding. | M3 |
| 5 | **Nowcast Models** | CPI leading indicator model (BLS, Cleveland Fed nowcast, SPF). Unemployment model (ADP, initial claims, FRED). Walk-forward validated. | M2, M3 |
| 6 | **Kalshi Demo Execution** | Live execution on Kalshi demo environment. Maker order logic, fill tracking, partial fills, timeout handling. | M3 |
| 7 | **Kalshi Live (v1)** | Deploy to production with $200–$300 initial capital. Hard position limits, Kelly enforced. Monitor for 30 days before any sizing up. | M4, M5, M6 |
| 8 | **Monitoring & Iteration** | Performance dashboard (Brier, PnL, calibration over time). Model update loop. Automated edge-check before each event. | M7 |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Thin historical data for Kalshi economics markets | High | Medium | Start archiving from day 1; use futures benchmarks as proxy for "historical fair value" |
| Fee drag eats edge (taker orders) | Medium | High | Maker-only in v1; fee impact modeled explicitly in backtest simulator |
| Model overfit on thin backtest data | High | High | Walk-forward only; out-of-sample holdout; no parameter tuning on live period |
| Fed market already highly efficient | High | Medium | Brainstorm notes Kalshi has perfect modal record — edge must come from magnitude, not direction; focus on timing and limit-order strategy |
| Capital wipeout from mispricing or model error | Low-Medium | Very High | 0.25× Kelly enforced in code; hard per-bet cap of 5% bankroll; demo validation before live |
| Kalshi API downtime or changes | Low | Medium | Abstract API layer; exponential backoff; monitor API changelog |
| Regulatory changes | Low | High | CFTC-regulated — highest stability available for US; built into platform choice |

---

## Open Questions

These need resolution before the linked milestone begins:

- **M1:** What polling frequency for Kalshi prices in the pre-event window? (e.g., hourly, 15-min for last 48h before resolution)
- **M1:** How to automate CME FedWatch probability extraction? (HTML scrape vs. CME API vs. third-party feed)
- **M4:** What Brier score vs. market baseline constitutes sufficient edge to advance to live?
- **M5:** Which leading indicators have the strongest predictive signal for CPI vs. unemployment? (resolve with data experiments)
- **M6:** Maker order strategy: how far inside the spread to post limit orders? How long to hold before cancelling?

---

## Dependencies

| Dependency | Status | Notes |
|---|---|---|
| Kalshi account + API keys | Not yet confirmed | Generate from Kalshi dashboard Settings → API |
| Kalshi demo credentials | Not yet confirmed | Separate from production |
| FRED API key | Free, quick signup | api.stlouisfed.org |
| pykalshi install | Pending project init | `pip install pykalshi` |
| Manifold account | Not yet confirmed | Free, play-money |
| Historical Kalshi data | Start ASAP | Cannot be recovered retroactively |

---

## Decisions Log

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Platform order | Manifold → Kalshi → Polymarket | Manifold = free sandbox; Kalshi = CFTC-regulated, correct venue for US economics trading | 2026-05-18 |
| v1 event type | Economic indicators, Fed rate decisions first | Best free data, softest competition, futures benchmark available, clean outcomes | 2026-05-18 |
| Edge hypothesis | Futures-market benchmarking | CME FedWatch is free, sophisticated, and frequently diverges from Kalshi prices | 2026-05-18 |
| SDK | `pykalshi` over official SDK | Production-ready error handling; switch to official if institutional support needed | 2026-05-18 |
| Order type | Maker preferred, taker only when edge is large | 4× fee difference; at 50¢ taker break-even is ~4.5% edge vs. ~1% for maker | 2026-05-18 |
| Position sizing | 0.25× fractional Kelly | Protects against model error at small capital; a 2-point estimation error can flip borderline bets | 2026-05-18 |
| Backtesting framework | Custom walk-forward first, PredictionMarketBench later | Avoid over-engineering before model is validated | 2026-05-18 |
| Local vs. cloud | Local (3060 Ti / MacBook) first | No cloud cost before strategy is validated; scale if capital scales | 2026-05-18 |


---

---

# Plan — Dashboard & Control Plane (v1)
Date: 2026-06-03
Status: Active — reviewed and updated 2026-06-03
Brainstorm: brainstorm_dashboard.md

---

## Overview

Build a FastAPI backend + Streamlit frontend dashboard that serves two purposes, delivered in
two phases:

**Phase 1 (now):** Read-only monitoring dashboard. Answers "what data do I have, is the
collector healthy, and what does the model think right now?" Fully interactive in the UI sense
— market selectors, date filters, sortable signal tables, zoomable Plotly charts — but makes
no writes to the trading system.

**Phase 2 (before live capital):** Operational control plane. Adds write endpoints for risk
limit management, model deployment, order cancellation, and a kill switch. Adds auth middleware
for sharing with collaborators. Depends on `execution/order_manager.py` and `execution/risk.py`
being implemented first (M6).

The FastAPI backend is the architectural centerpiece: all data access and operational actions
go through it. Streamlit pages call the API rather than importing trading modules directly.
This keeps auth enforcement, audit logging, and the upgrade path to React in one place.

**Key architectural constraint:** The signals endpoint and model registry are designed to be
model-agnostic from day one. Every signal carries a `model_name` tag so the Signals page and
Control page can accommodate M5 nowcast models without retrofitting.

---

## Goals & Success Criteria

| Criterion | Target |
|---|---|
| Phase 1 | Dashboard runs locally with one command; all 5 monitoring pages render without errors |
| Data Explorer | FedWatch probability curves and FRED history visible with current data |
| Signals page | Replicates `run_signals.py` output with model column; updates on demand |
| Model Analysis | Renders gracefully with sparse data; shows next FOMC date in empty state |
| Architecture | No Streamlit page imports trading engine modules directly — all calls go through `client.py` → API |
| Share-readiness | CORS configured; auth stub in place; activating it in Phase 2 requires no structural changes |
| Collector health | Overview shows "COLLECTOR OFFLINE" badge if no snapshot in > 30 min |

---

## Scope

### In Scope — Phase 1
- FastAPI backend with read-only endpoints for all 5 monitoring pages
- CORS middleware configured in `api/main.py` (required for Streamlit → API cross-origin calls)
- Streamlit multi-page app: Overview, Data Explorer, Markets, Signals, Model Analysis
- Control page stub (displays current risk config and model registry; no writes yet)
- `dashboard/client.py` — typed httpx client with explicit timeouts and connection-error handling
- New `database.py` query methods required by the API (per-request connections, no singleton)
- `model_registry` table in SQLite — tracks model name, enabled state, last run time
- `trades` table in SQLite — unified log for backtest sim trades, Manifold paper trades, and future Kalshi live trades
- Backtest result caching endpoint — harness runs on schedule, not on every page load
- `scripts/run_dashboard.sh` — single launcher for both services; port configurable via settings
- Plotly Express charts throughout
- Manual refresh on all pages; per-page opt-in auto-refresh toggle

### In Scope — Phase 2 (planned, not built now)
- Write endpoints: risk limit editor, model enable/disable, kill switch, order cancellation
- Positions & Orders page — view open orders, fills, running P&L
- Manifold paper trading log page — surfaces M4 results
- Two-step confirmation pattern for all consequential actions
- API key auth middleware
- Audit log table in SQLite for all control actions
- Depends on: `execution/order_manager.py`, `execution/risk.py` (M6)

### Out of Scope
- React frontend (upgrade path if Streamlit outgrows; not needed now)
- Cloud deployment (local only in Phase 1)
- WebSocket real-time streaming (polling is sufficient)
- User management / roles (single-user in Phase 2; multi-user is post-v1)

---

## Tech Stack & Architecture

| Layer | Choice | Reasoning |
|---|---|---|
| API backend | FastAPI + uvicorn | Pure Python; async-ready; matches existing httpx patterns; clean OpenAPI docs for free |
| Frontend | Streamlit (multi-page) | Python-native; no JS; handles both monitoring and operational controls with careful state management |
| Charts | Plotly Express | Interactive (zoom, hover, pan); Streamlit-native via `st.plotly_chart`; handles all required chart types |
| Data access | `dashboard/client.py` → FastAPI → `Database` | Single seam for auth, audit, and future client swap |
| Auth | No-op stub (Phase 1) → API key header (Phase 2) | Designed in now; zero cost until sharing |
| CORS | `fastapi.middleware.cors.CORSMiddleware` | Required for Streamlit (8501) → FastAPI (8000) cross-origin requests |

### Request flow

```
Streamlit page
    └── dashboard/client.py (httpx, explicit timeouts)
            └── FastAPI (localhost:8000) + CORSMiddleware
                    └── database.py (per-request connections) / model registry / KalshiClient
                            └── SQLite (WAL mode) / Kalshi API / yfinance
```

### SQLite concurrency note
The collector daemon writes to the DB every 15 minutes while the dashboard reads concurrently.
WAL mode (already configured in `database.py`) handles this safely. All dashboard DB access
must use `Database._conn()` as a context manager — per-request connections, never a
module-level connection object held open.

### Directory structure

```
dashboard/
├── api/
│   ├── main.py              # FastAPI app; mounts all routers; configures CORS
│   ├── models.py            # All Pydantic request/response models
│   ├── deps.py              # Per-request DB factory and auth stub
│   ├── auth.py              # API key middleware (no-op in Phase 1)
│   └── routers/
│       ├── status.py        # GET /api/status (health + staleness), GET /api/collection/log
│       ├── markets.py       # GET /api/markets, /api/markets/{ticker}/history
│       ├── signals.py       # GET /api/signals (model-agnostic, tagged by model_name)
│       ├── data.py          # GET /api/fedwatch, /api/fred/{series_id}, /api/fred/series/list
│       ├── models_router.py # GET /api/models (registry), GET /api/backtest/latest
│       ├── trades.py        # GET /api/trades (Phase 1 read; Phase 2 adds write)
│       └── control.py       # Phase 2 write endpoints — returns 501 in Phase 1
├── client.py                # Typed httpx client; 30s timeout signals, 10s others; handles ConnectionRefused
├── app.py                   # Streamlit entry point and navigation
└── pages/
    ├── 1_Overview.py
    ├── 2_Data_Explorer.py
    ├── 3_Markets.py
    ├── 4_Signals.py
    ├── 5_Model_Analysis.py
    └── 6_Control.py         # Phase 2 (stub in Phase 1 — shows registry and config read-only)
```

---

## New DB Tables Required (add to `database.py` schema)

```sql
-- Unified trade log: backtest sim trades, Manifold paper trades, Kalshi live trades.
-- trade_type distinguishes the source; live trades will have order_id populated.
CREATE TABLE IF NOT EXISTS trades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_time      TEXT    NOT NULL,
    trade_type      TEXT    NOT NULL,   -- 'backtest' | 'paper_manifold' | 'kalshi_live'
    market_ticker   TEXT    NOT NULL,
    model_name      TEXT    NOT NULL,
    side            TEXT    NOT NULL,   -- 'yes' | 'no'
    order_type      TEXT,               -- 'maker' | 'taker'
    fill_price_cents INTEGER,
    quantity        INTEGER,
    fee_cents       REAL,
    p_model         REAL,
    p_market        REAL,
    outcome         REAL,               -- 1.0=YES, 0.0=NO, NULL=unresolved
    gross_pnl_cents REAL,
    net_pnl_cents   REAL,
    order_id        TEXT,               -- Kalshi order ID (live trades only)
    notes           TEXT
);

CREATE INDEX IF NOT EXISTS idx_trades_time  ON trades(trade_time);
CREATE INDEX IF NOT EXISTS idx_trades_model ON trades(model_name, trade_type);

-- Model registry: tracks which models exist, their enabled state, and last run metadata.
CREATE TABLE IF NOT EXISTS model_registry (
    name            TEXT    PRIMARY KEY,
    enabled         INTEGER NOT NULL DEFAULT 1,   -- 1=active, 0=disabled
    model_type      TEXT,                          -- 'baseline' | 'nowcast' | 'ensemble'
    series_tickers  TEXT,                          -- JSON array of applicable series
    config_json     TEXT,                          -- serialized model parameters
    last_run_time   TEXT,
    last_signal_count INTEGER,
    created_at      TEXT    NOT NULL
);

-- Backtest result cache: stores harness output so Model Analysis page doesn't recompute live.
CREATE TABLE IF NOT EXISTS backtest_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name      TEXT    NOT NULL,
    run_time        TEXT    NOT NULL,
    brier_score     REAL,
    brier_skill     REAL,
    ece             REAL,
    n_predictions   INTEGER,
    n_resolved      INTEGER,
    net_pnl_cents   REAL,
    result_json     TEXT,               -- full BacktestResults summary dict as JSON
    UNIQUE(model_name, run_time)
);

CREATE INDEX IF NOT EXISTS idx_backtest_model ON backtest_cache(model_name, run_time DESC);
```

---

## Milestones

| # | Milestone | Description | Dependencies |
|---|---|---|---|
| D1 | Foundation | Directory scaffold, new DB tables, DB query methods, launcher, settings | M3 complete |
| D2 | API Backend | All Phase 1 endpoints with Pydantic models, CORS, tested via /docs | D1 |
| D3 | Overview + Data Pages | Pages 1 & 2: health + staleness badges, FedWatch curves, FRED, heatmap | D2 |
| D4 | Markets + Signals Pages | Pages 3 & 4: inventory, price history, model-tagged signal table, edge histogram | D2 |
| D5 | Model Analysis Page | Page 5: calibration, Brier, P&L from cache; paper trading stub; graceful empty state | D2 |
| D6 | Control Stub + Polish | Page 6 stub, theme, error handling, auto-refresh toggles | D3–D5 |

---

## Task Breakdown

### D1 — Foundation

- [ ] Create `dashboard/` directory structure (api/, pages/, client.py, app.py)
- [ ] Add to `requirements.txt`: `fastapi`, `uvicorn[standard]`, `plotly`, `streamlit`
- [ ] Add `DASHBOARD_API_PORT=8000` and `DASHBOARD_UI_PORT=8501` to `config/settings.py`
- [ ] Add new DB tables to `data/storage/database.py` schema: `trades`, `model_registry`, `backtest_cache`
- [ ] Add new query methods to `database.py`:
  - `get_collection_status()` → last ok/error time per collector from `collection_log`; includes `seconds_since_last_snapshot` for staleness detection
  - `get_all_markets(series_ticker=None, status=None)` → all markets (not just active)
  - `get_market_history(ticker, limit=200)` → snapshot history for one market
  - `get_fedwatch_all(meeting_date=None)` → all FedWatch snapshots, optionally filtered
  - `get_fred_series_list()` → list of distinct series_ids present in `fred_observations`
  - `get_fred_latest()` → most recent value per tracked series
  - `get_model_registry()` → all rows from `model_registry`
  - `get_trades(trade_type=None, model_name=None, limit=200)` → trade log rows
  - `get_backtest_latest(model_name)` → most recent `backtest_cache` row for a model
- [ ] Seed `model_registry` with `fed_baseline` on first run (insert if not exists)
- [ ] Create `dashboard/api/deps.py` — `get_db()` dependency that opens a fresh `Database` per request (NOT a module-level singleton)
- [ ] Create `dashboard/api/auth.py` — no-op API key middleware stub; logs warning at startup if `DASHBOARD_API_KEY` env var is unset
- [ ] Create `scripts/run_dashboard.sh` — reads ports from settings; starts uvicorn and streamlit in parallel; prints URLs on startup

### D2 — API Backend

Configure CORS in `api/main.py`:
```python
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**`GET /api/status`** (router: `status.py`)
- Returns: per-collector `{last_ok, last_error, items_last_run, seconds_stale}`
- Includes `collector_offline: bool` flag (true if kalshi snapshot > 1800s stale)
- Returns: `active_markets`, `tradeable_signals`, `as_of`

**`GET /api/collection/log`** (router: `status.py`)
- Query params: `limit` (default 50)
- Returns: recent `collection_log` rows

**`GET /api/markets`** (router: `markets.py`)
- Query params: `series_ticker`, `status` (`active`|`settled`|`all`)
- Returns: list of `MarketRow`

**`GET /api/markets/{ticker}/history`** (router: `markets.py`)
- Query params: `limit` (default 200)
- Returns: list of `SnapshotRow`

**`GET /api/fedwatch`** (router: `data.py`)
- Query params: `meeting_date` (optional), `upcoming_only` (bool, default true — filters to meetings ≥ today)
- Returns: `FedwatchRow` list sorted by meeting_date then snapshot_time

**`GET /api/fred/series/list`** (router: `data.py`)
- Returns: list of series IDs present in DB (dynamic — derived from `fred_observations`, not hardcoded)

**`GET /api/fred/{series_id}`** (router: `data.py`)
- Returns: time series of `FredRow` observations

**`GET /api/signals`** (router: `signals.py`)
- Query params: `tradeable_only` (bool, default false), `model_name` (optional filter)
- Runs all enabled models from `model_registry`; tags each signal with `model_name`
- Caches result for 60s (signals are expensive to compute when multiple models exist)
- Returns: list of `SignalRow` (includes `model_name` field)

**`GET /api/models`** (router: `models_router.py`)
- Returns: list of `ModelRegistryRow` (name, enabled, type, last_run_time, last_signal_count)

**`GET /api/backtest/latest`** (router: `models_router.py`)
- Query params: `model_name` (default `fed_baseline`)
- Returns: most recent `BacktestCacheRow`; 404 if no cached result exists yet

**`GET /api/trades`** (router: `trades.py`)
- Query params: `trade_type`, `model_name`, `limit` (default 200)
- Returns: list of `TradeRow`

- [ ] Implement all 11 endpoints with Pydantic response models in `api/models.py`
- [ ] Mount all routers in `api/main.py`; configure CORS
- [ ] `control.py` router stubs — all routes return `HTTP 501 Not Implemented` with message "Available in Phase 2"
- [ ] Smoke test all endpoints via FastAPI's `/docs` at `http://localhost:8000/docs`

### D3 — Overview + Data Pages

**Page 1: Overview**
- [ ] Collector status cards: last Kalshi snapshot, last FedWatch, last FRED — color red if stale
- [ ] `COLLECTOR OFFLINE` banner (red) if `collector_offline=true` from `/api/status`
- [ ] Active signal count, active market count
- [ ] Collection log table (last 20 runs, color-coded ok=green / error=red)
- [ ] Auto-refresh toggle (60s via `st.rerun`; default OFF)

**Page 2: Data Explorer**
- [ ] FedWatch section:
  - Meeting date multiselect (default: upcoming meetings only, per `upcoming_only=true`)
  - Line chart: hike/hold/cut probability over time, one trace per meeting date per outcome
- [ ] FRED section:
  - Series selector populated dynamically from `GET /api/fred/series/list` (not hardcoded)
  - Line chart of selected series history
- [ ] Snapshot coverage heatmap:
  - Default view: series-level rollup (7 rows — one per series; color = % of markets in series with bid/ask data)
  - Drill-down: select a series to expand to per-market rows
  - x-axis = date, color = has bid/ask (green) / missing (gray)

### D4 — Markets + Signals Pages

**Page 3: Markets**
- [ ] Filterable market inventory table (filter by series, status)
- [ ] Market selector dropdown → price history chart (yes_bid, yes_ask, last_price over time)
- [ ] Summary stats: total markets, active, settled, % with snapshot data

**Page 4: Signals**
- [ ] Signal table columns: Model, Market, Meeting, Outcome, Model%, Market%, Edge%, Break-even%, Qty, Side
- [ ] `model_name` column — populated from `SignalRow.model_name`; filterable via selectbox
- [ ] Color coding: tradeable rows green, below-threshold rows gray
- [ ] Edge distribution histogram (all markets, all models)
- [ ] Meeting selector → FedWatch vs Kalshi overlay chart:
  - Dual-line: FedWatch probability vs Kalshi midpoint over snapshot history
  - One chart per selected outcome type (hold/cut/hike)
- [ ] Auto-refresh toggle (default OFF; independent of Overview page)

### D5 — Model Analysis Page

**Page 5: Model Analysis**

*Calibration & Performance (requires resolved markets):*
- [ ] Empty state condition: fewer than 5 resolved markets in `trades` table
- [ ] Empty state copy: "Calibration metrics will appear after 5+ markets resolve. Next FOMC resolution: [date from FOMC_MEETING_DATES]."
- [ ] Calibration reliability diagram (reads from `backtest_cache.result_json`)
- [ ] Brier score over time — one point per backtest cache entry
- [ ] Simulated P&L curve — from `trades` table where `trade_type='backtest'`
- [ ] Note: `BacktestHarness` does NOT run live on page load — reads from `backtest_cache` only

*Backtest cache refresh strategy:*
- [ ] Add a `scripts/run_backtest.py` one-shot script that runs the harness and writes to `backtest_cache`
- [ ] The page shows the `run_time` of the cached result with a "last updated" label
- [ ] Phase 2: add a "Re-run Backtest" button on the Control page that triggers this script

*Paper Trading section (M4 Manifold):*
- [ ] Section header: "Paper Trading — Manifold"
- [ ] Stub: "Paper trade results will appear here once M4 (Manifold validation) is underway."
- [ ] When M4 begins: reads from `trades` where `trade_type='paper_manifold'`; shows Brier score, win rate, P&L

### D6 — Control Stub + Polish

**Page 6: Control (stub)**
- [ ] Model registry table (read-only): model name, type, enabled/disabled, last run time, signal count
- [ ] Risk config display: current values from `config/markets.yaml` (read-only)
- [ ] Labeled Phase 2 stubs:
  - Model deployment toggles (enable/disable models)
  - Risk limit editor (min edge %, max position %, Kelly fraction)
  - Kill switch (scope TBD per open question 2)
  - Open orders panel
  - Positions & P&L panel
- [ ] Note on each stub: "Requires Phase 2 — depends on execution/order_manager.py (M6)"

**Polish**
- [ ] `.streamlit/config.toml`: dark theme, consistent brand colors
- [ ] `client.py` timeouts: 30s for `/api/signals` and `/api/backtest/latest`; 10s for all others
- [ ] `client.py` `ConnectionRefusedError` handler: `st.error("API unreachable. Run: bash scripts/run_dashboard.sh")`
- [ ] `st.set_page_config` with title and icon on every page
- [ ] All charts handle empty DataFrames without raising exceptions

---

## API Response Shapes (Pydantic models)

```python
# Full definitions live in dashboard/api/models.py

class CollectorStatus(BaseModel):
    collector: str
    last_ok: str | None        # ISO timestamp of last successful run
    last_error: str | None     # ISO timestamp of last error
    items_last_run: int | None
    seconds_stale: float | None  # seconds since last_ok; None if never run

class StatusResponse(BaseModel):
    sources: dict[str, CollectorStatus]
    collector_offline: bool    # True if kalshi snapshot stale > 1800s
    active_markets: int
    tradeable_signals: int
    as_of: str

class MarketRow(BaseModel):
    ticker: str
    series_ticker: str
    title: str
    status: str
    close_time: str | None
    result: str | None

class SnapshotRow(BaseModel):
    snapshot_time: str
    yes_bid: int | None
    yes_ask: int | None
    last_price: int | None

class FedwatchRow(BaseModel):
    snapshot_time: str
    meeting_date: str
    hike_prob: float | None
    hold_prob: float | None
    cut_prob: float | None

class FredRow(BaseModel):
    observation_date: str
    value: float | None
    vintage_date: str

class SignalRow(BaseModel):
    model_name: str            # e.g. "fed_baseline", "cpi_nowcast"
    market_ticker: str
    meeting_date: str
    outcome_type: str
    p_model: float
    p_market: float
    yes_bid: int | None
    yes_ask: int | None
    edge: float
    break_even: float
    tradeable: bool
    side: str
    kelly_qty: int
    snapshot_time: str | None

class ModelRegistryRow(BaseModel):
    name: str
    enabled: bool
    model_type: str | None
    series_tickers: list[str]
    last_run_time: str | None
    last_signal_count: int | None

class TradeRow(BaseModel):
    id: int
    trade_time: str
    trade_type: str            # 'backtest' | 'paper_manifold' | 'kalshi_live'
    market_ticker: str
    model_name: str
    side: str
    fill_price_cents: int | None
    quantity: int | None
    fee_cents: float | None
    p_model: float | None
    p_market: float | None
    outcome: float | None
    net_pnl_cents: float | None

class BacktestCacheRow(BaseModel):
    model_name: str
    run_time: str
    brier_score: float | None
    brier_skill: float | None
    ece: float | None
    n_predictions: int
    n_resolved: int
    net_pnl_cents: float | None
    result_json: str           # full summary dict
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| CORS blocks Streamlit → API calls | Certain without mitigation | Critical | `CORSMiddleware` configured in D1; tested in D2 smoke test |
| Streamlit session state causes duplicate API calls | Medium | Low | `st.cache_data(ttl=30)` for read endpoints; idempotent GETs are safe |
| Sparse data makes most charts empty on first run | High | Medium | Empty states with clear copy on every chart; no crashes on empty dataframes |
| Port conflicts (8000/8501 already in use) | Low | Low | Launcher reads ports from settings; error message if port busy |
| BacktestHarness slow on page load | High (without fix) | Medium | Harness never runs on page load — reads from `backtest_cache` only; `run_backtest.py` script updates the cache |
| Multiple models at M5 break signals endpoint | High (without fix) | Medium | Signals endpoint model-agnostic from day one; reads enabled models from `model_registry` |
| Phase 2 write endpoints accidentally included in Phase 1 | Low | High | `control.py` router returns `501 Not Implemented` for all write routes in Phase 1 |
| Dashboard reads stale data without knowing collector is down | High (without fix) | Medium | `/api/status` computes `seconds_stale` and `collector_offline`; Overview shows red banner |
| SQLite connection held open across requests | Low | Medium | `deps.py` uses `get_db()` dependency that opens fresh connection per request via `Database._conn()` |

---

## Dependencies

| Dependency | Status | Notes |
|---|---|---|
| `fastapi` | Not yet installed | Add to requirements.txt |
| `uvicorn[standard]` | Not yet installed | Add to requirements.txt |
| `plotly` | Not yet installed | Add to requirements.txt |
| `streamlit` | Not yet installed | Add to requirements.txt |
| M3 (FedBaselineModel) | Complete | Primary model for `/api/signals` in Phase 1 |
| SQLite DB with snapshot data | Accumulating | Some charts sparse initially; backtest cache empty until `run_backtest.py` runs |
| `execution/order_manager.py` | Not yet built (M6) | Required before Phase 2 Control page write endpoints |
| `execution/risk.py` | Not yet built (M6) | Required before Phase 2 kill switch and position management |

---

## Open Questions

1. **Auto-refresh default:** Opt-in toggle is the plan (default OFF). Confirm before D3.

2. **Kill switch scope (Phase 2):** Pause collector only, cancel open Kalshi orders only,
   or both? Must define before implementing the `/api/control/kill` endpoint.

3. **Config mutability (Phase 2):** Risk limit changes via dashboard write back to
   `markets.yaml` (simple, git-tracked) vs. runtime override rows in SQLite (auditable,
   no git churn). SQLite override table is recommended.

4. **Auth mechanism (Phase 2):** API key header (simple, sufficient for one collaborator)
   vs. `st.login()` OAuth (multi-user). Decide when sharing becomes imminent.

5. **Manifold trade logging (M4):** When M4 paper trading on Manifold begins, where do
   results land? Options: (a) log Manifold trades directly to the `trades` table with
   `trade_type='paper_manifold'`; (b) separate file/table. Recommend option (a) since the
   schema already supports it. Confirm before starting M4.

6. **Backtest cache refresh trigger:** `run_backtest.py` runs manually or on a schedule?
   Recommended: run manually after each resolved market event, or add to the collector's
   daily job. Confirm before D5.

---

## Decisions Log

| Decision | Choice | Reasoning | Date |
|---|---|---|---|
| Architecture | FastAPI + Streamlit | Auth seam, audit layer, Streamlit replaceability; pure Python | 2026-06-03 |
| Chart library | Plotly Express | Interactive, Streamlit-native, handles all required chart types | 2026-06-03 |
| Data access | All via client.py → API | No direct module imports in pages; enforces the auth/audit seam | 2026-06-03 |
| Phase 1 scope | Read-only, pages 1–5 + stub for 6 | Operational control not needed until live capital; monitoring is the urgent need | 2026-06-03 |
| Auto-refresh | Opt-in toggle per page | Avoids background requests when not actively monitoring | 2026-06-03 |
| Phase 1 interactivity | UI-interactive (filters, charts) only | Dropdowns, selectors, chart interactions in Phase 1; system writes in Phase 2 | 2026-06-03 |
| CORS | CORSMiddleware in api/main.py | Required for Streamlit → FastAPI cross-origin; localhost only in Phase 1 | 2026-06-03 |
| Signals endpoint | Model-agnostic with model_name tag | Accommodates M5 nowcast models without API changes; reads enabled models from model_registry | 2026-06-03 |
| Trade log | Unified `trades` table (trade_type field) | Single table handles backtest sim, Manifold paper, and Kalshi live trades; avoids schema proliferation | 2026-06-03 |
| Model registry | SQLite table | Enables enable/disable toggle in Phase 2; tracks last run and signal count; avoids config-file churn | 2026-06-03 |
| Backtest caching | `backtest_cache` table + `run_backtest.py` script | Harness too slow for page-load execution; cached results serve the Model Analysis page instantly | 2026-06-03 |
| Heatmap granularity | Series-level rollup with drill-down | 341 raw markets unworkable in a single chart; series rollup (7 rows) is readable | 2026-06-03 |
| FRED series list | Dynamic from DB (not hardcoded) | Stays in sync with markets.yaml without code changes when series are added | 2026-06-03 |
| DB connections | Per-request via get_db() dependency | WAL mode handles concurrent collector writes; no module-level singleton | 2026-06-03 |
| Ports | Configurable via settings.py | DASHBOARD_API_PORT / DASHBOARD_UI_PORT; launcher reads from settings | 2026-06-03 |
