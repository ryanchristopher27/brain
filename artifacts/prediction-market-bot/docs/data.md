# Data Pipeline — Prediction Market Bot
Date: 2026-05-19
Status: Draft

---

## Overview

The data pipeline is the foundation of the entire system. Without a clean, point-in-time-safe historical archive, neither the backtest nor the live model is trustworthy. **Start collecting on day one — you cannot recover historical data retroactively.**

There are two categories of data:

1. **Market data** — Kalshi prices, orderbook snapshots, trade history
2. **Fundamental data** — economic indicator source data used to build models (FRED, CME FedWatch, SPF, etc.)

All data is written with a `collected_at` timestamp and never mutated. Queries reconstruct the world as it appeared at any past moment by filtering `collected_at <= as_of_timestamp`.

---

## External Data Sources

### 1. Kalshi REST API

**Base URL (production):** `https://external-api.kalshi.com/trade-api/v2`
**Base URL (demo):** `https://external-api.demo.kalshi.co/trade-api/v2`
**Auth required:** No for market data; RSA-PSS signed headers for portfolio/orders.

**What we collect:**

| Endpoint | Data | Collection schedule |
|---|---|---|
| `GET /markets?series_ticker={series}` | Active markets matching target series | On startup + hourly |
| `GET /markets/{ticker}/orderbook` | Full orderbook (YES bids → implied NO asks) | Every poll interval |
| `GET /historical/markets/{ticker}/candlesticks` | OHLCV price history | Backfill on first run; then daily for the 3-month window |
| `GET /historical/trades` | Individual trade records | Backfill on first run |
| `GET /events` | Event definitions, resolution criteria | On market discovery |
| `GET /historical/cutoff` | Partition timestamp (live vs. historical) | On startup |

**Key data structure — orderbook:**
```
YES bid side only (binary market implied):
  yes_bids: [[price_cents, quantity], ...]   # price in integer cents
  no_dollars: [[price_cents, quantity], ...]  # derived: NO = 100 - YES_ask
```
Best bid (highest YES bid) and best ask (lowest YES ask from NO side) are derived. Midpoint = `(best_bid + best_ask) / 2`. **Never fill at midpoint in simulation.**

**Polling schedule:**
- Normal: every 60 minutes
- Pre-resolution (< 48 hours to settlement): every 15 minutes
- Active event window (same day as resolution): every 5 minutes via WebSocket ticker channel

**Rate limits:** 200 read tokens/sec (Basic tier), each request costs 10 tokens → 20 requests/sec burst. For polling 10 markets every 60 min, actual rate is negligible. Pre-resolution polling is still well within limits.

---

### 2. Kalshi WebSocket API

**Endpoint (production):** `wss://external-api-ws.kalshi.com/trade-api/ws/v2`
**Max connections:** 5 concurrent.

**Channels used:**

| Channel | Purpose | Auth |
|---|---|---|
| `ticker` | Real-time bid/ask updates | No |
| `orderbook_delta` | Incremental orderbook changes | No |
| `market_lifecycle_v2` | Open → closing → settled transitions | No |
| `fill` | Order fill confirmations (execution layer) | Yes |
| `market_positions` | Position updates (execution layer) | Yes |

**Connection strategy:**
- Single WebSocket connection per environment (demo / live) — multiplex all channel subscriptions
- Subscribe to `ticker` for all active target markets on connect
- Subscribe to `orderbook_delta` for markets within 48h of resolution
- Reconnect with exponential backoff on disconnect: 2s → 4s → 8s → max 60s
- On reconnect: resubscribe to all channels and issue a REST reconciliation call

**Storage:** WebSocket `ticker` events are written to the same `market_prices` table as REST polls. `orderbook_delta` events are used to maintain an in-memory orderbook (not persisted — too much volume).

---

### 3. CME FedWatch

**URL:** `https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html`
**Data:** Probability distribution over Fed rate outcomes (hike 25bp, hold, cut 25bp) for each upcoming FOMC meeting, derived from 30-Day Federal Funds futures contracts.

**Why this matters:** FedWatch is the most sophisticated publicly available probability estimate for Fed rate decisions. When Kalshi's market price diverges from FedWatch, that divergence is our trade signal.

**Collection method:**
- CME provides a public API for this data (undocumented but stable). URL:
  `https://www.cmegroup.com/CmeWS/mvc/ProductCalendar/V2/FedWatch?quoteCodes=...`
- Alternatively: scrape the FedWatch page HTML (more brittle). Prefer the API endpoint.
- If CME API changes, fallback to parsing the JSON embedded in the page source.

**Collection schedule:** Every 30 minutes during market hours (9am–5pm ET weekdays). Once daily overnight.

**Data structure captured:**
```
meeting_date: date              # FOMC meeting date
collected_at: datetime          # When we pulled this
hike_25bp_prob: float          # P(rate hike +25bp)
hold_prob: float                # P(rate unchanged)
cut_25bp_prob: float           # P(rate cut -25bp)
implied_rate: float             # Futures-implied target rate
source: str                    # "cme_fedwatch"
```

**Data validation:**
- Sum of probabilities must be within 0.5% of 1.0 (rounding from CME's display)
- `meeting_date` must be a known FOMC date (validate against published FOMC calendar)
- Values must be in [0, 1]

---

### 4. FRED (Federal Reserve Economic Data)

**URL:** `https://api.stlouisfed.org/fred/`
**API key:** Free at api.stlouisfed.org. Set as `FRED_API_KEY` env var.
**Library:** `fredapi` Python package.

**Series collected:**

| FRED Series | Description | Frequency | Lag |
|---|---|---|---|
| `FEDFUNDS` | Effective Federal Funds Rate | Monthly | ~1 week after month-end |
| `CPIAUCSL` | CPI All Urban Consumers | Monthly | ~2 weeks after reference month |
| `CPILFESL` | CPI Less Food & Energy (Core CPI) | Monthly | Same as CPI |
| `UNRATE` | Unemployment Rate | Monthly | First Friday of following month |
| `PAYEMS` | Total Nonfarm Payroll (NFP) | Monthly | Same release as UNRATE |
| `GDPC1` | Real GDP (Chained 2017$) | Quarterly | ~30 days after quarter end |
| `PCE` | Personal Consumption Expenditures | Monthly | ~4 weeks after month-end |
| `PCEPILFE` | Core PCE Price Index | Monthly | Same as PCE |
| `ICSA` | Initial Jobless Claims | Weekly | Thursday morning |
| `ADPMNUSNERSA` | ADP Nonfarm Employment | Monthly | 2 days before NFP release |

**Collection schedule:**
- Pull all series on startup to build historical baseline
- Daily delta pull (only updates since last pull) — FRED returns `NaN` for unreleased dates

**Critical: FRED revisions.** FRED revises historical data. For backtesting, we need the data as it appeared at the time, not the current revised version. FRED's "vintage" API (`/fred/vintage_dates`, `/fred/series/observations?vintage_dates=...`) provides point-in-time snapshots. **Use vintage dates for all backtest feature construction.** Store both `value` and `vintage_date` for every observation.

**Table: `fred_observations`**
```sql
series_id      TEXT
date           DATE        -- reference period
value          REAL
vintage_date   DATE        -- when this revision was published
collected_at   DATETIME    -- when we pulled it
```

---

### 5. Philadelphia Fed Survey of Professional Forecasters (SPF)

**URL:** `https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/survey-of-professional-forecasters`
**Format:** Excel/CSV downloads, released quarterly
**Contents:** Mean and distribution of professional economists' forecasts for CPI, real GDP, unemployment, and other indicators at various horizons.

**Why useful:** SPF gives us the consensus view of informed forecasters as of a specific date. Kalshi mispricing relative to SPF consensus is a signal, especially for quarterly economic events.

**Collection method:** Download the latest release file on each quarterly publish date (January, May, August, November). Parse Excel. Store in `spf_forecasts` table.

**Data structure:**
```
release_date: date          -- when this SPF edition was published
forecast_horizon: str       -- "Q1", "Q2", "current_year", etc.
variable: str               -- "CPI", "RGDP", "UNEMP"
mean_forecast: float
p10_forecast: float         -- 10th percentile of panelists
p25_forecast: float
p75_forecast: float
p90_forecast: float
collected_at: datetime
```

---

### 6. Cleveland Fed Inflation Nowcast

**URL:** `https://www.clevelandfed.org/indicators-and-data/inflation-nowcasting`
**Format:** JSON API (publicly accessible)
**Contents:** Real-time CPI and PCE nowcasts updated daily as new data comes in before the official BLS release.

**Why useful:** The Cleveland Fed model is a well-calibrated machine learning model trained on leading indicators. Its CPI nowcast as of any day is a strong baseline for our CPI models — we don't need to build the nowcast from scratch, we just compare the nowcast to the Kalshi market price.

**Collection schedule:** Daily, 9am ET (updated after overnight model run).

**Data structure:**
```
forecast_date: date             -- reference date of the CPI release being forecast
collected_at: datetime
cpi_nowcast: float              -- nowcast for upcoming CPI release (YoY %)
core_cpi_nowcast: float
days_to_release: int            -- how many days until official BLS release
```

---

### 7. BLS (Bureau of Labor Statistics)

**URL:** `https://api.bls.gov/publicAPI/v2/timeseries/data/`
**Auth:** Registration API key (free, higher rate limits than anonymous)

**Used for:** Historical CPI and unemployment actuals with official vintage dates — as the ground truth for model outcomes.

**Why not just use FRED?** FRED redistributes BLS data, but BLS sometimes releases corrections first. For live trading around release dates, pull directly from BLS within minutes of the scheduled release. For historical backtesting, FRED vintages are fine.

**Collection schedule:** On CPI, PPI, and Unemployment release days, poll BLS every 2 minutes starting 5 minutes before scheduled release time until actual data appears.

---

## SQLite Schema

All tables share the append-only, timestamped pattern. No `UPDATE` or `DELETE` statements.

### `market_snapshots`
```sql
CREATE TABLE market_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT NOT NULL,
    collected_at    DATETIME NOT NULL,
    source          TEXT NOT NULL,        -- "rest_poll" | "websocket_ticker"
    best_bid_cents  INTEGER,              -- YES bid in cents (0-100)
    best_ask_cents  INTEGER,              -- YES ask in cents (0-100)
    last_price_cents INTEGER,
    volume_24h      INTEGER,              -- contracts traded in last 24h
    open_interest   INTEGER
);
CREATE INDEX idx_snapshots_ticker_time ON market_snapshots(ticker, collected_at);
```

### `markets`
```sql
CREATE TABLE markets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT NOT NULL UNIQUE,
    series_ticker   TEXT,
    event_type      TEXT,                 -- "fed_rate_decision" | "cpi" | etc.
    title           TEXT,
    resolution_date DATE,
    outcome         TEXT,                 -- NULL until settled; "YES" | "NO"
    settled_at      DATETIME,
    discovered_at   DATETIME NOT NULL,
    raw_json        TEXT                  -- full API response JSON blob
);
```

### `fed_watch_snapshots`
```sql
CREATE TABLE fed_watch_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_date    DATE NOT NULL,
    collected_at    DATETIME NOT NULL,
    hike_25bp_prob  REAL,
    hold_prob       REAL,
    cut_25bp_prob   REAL,
    implied_rate    REAL
);
CREATE INDEX idx_fedwatch_meeting_time ON fed_watch_snapshots(meeting_date, collected_at);
```

### `fred_observations`
```sql
CREATE TABLE fred_observations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id       TEXT NOT NULL,
    date            DATE NOT NULL,        -- reference period
    value           REAL,
    vintage_date    DATE NOT NULL,        -- when this value was first published
    collected_at    DATETIME NOT NULL
);
CREATE UNIQUE INDEX idx_fred_series_date_vintage ON fred_observations(series_id, date, vintage_date);
```

### `cleveland_nowcasts`
```sql
CREATE TABLE cleveland_nowcasts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_date   DATE NOT NULL,        -- CPI release date being forecast
    collected_at    DATETIME NOT NULL,
    days_to_release INTEGER,
    cpi_nowcast     REAL,
    core_cpi_nowcast REAL
);
```

### `spf_forecasts`
```sql
CREATE TABLE spf_forecasts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    release_date    DATE NOT NULL,
    forecast_horizon TEXT NOT NULL,
    variable        TEXT NOT NULL,
    mean_forecast   REAL,
    p10_forecast    REAL,
    p25_forecast    REAL,
    p75_forecast    REAL,
    p90_forecast    REAL,
    collected_at    DATETIME NOT NULL
);
```

### `signals`
```sql
CREATE TABLE signals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    market_ticker       TEXT NOT NULL,
    generated_at        DATETIME NOT NULL,
    model_name          TEXT NOT NULL,
    model_probability   REAL NOT NULL,
    market_probability  REAL NOT NULL,   -- midpoint at signal time
    edge                REAL NOT NULL,
    edge_after_fees     REAL NOT NULL,
    direction           TEXT NOT NULL,   -- "YES" | "NO" | "PASS"
    as_of               DATETIME NOT NULL
);
```

### `orders`
```sql
CREATE TABLE orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kalshi_order_id TEXT,
    market_ticker   TEXT NOT NULL,
    signal_id       INTEGER REFERENCES signals(id),
    direction       TEXT NOT NULL,       -- "YES" | "NO"
    contracts       INTEGER NOT NULL,
    limit_price_cents INTEGER NOT NULL,
    status          TEXT NOT NULL,       -- "pending"|"submitted"|"resting"|"filled"|"cancelled"|"expired"
    fill_price_cents INTEGER,
    fill_contracts  INTEGER,
    fee_cents       INTEGER,
    submitted_at    DATETIME,
    filled_at       DATETIME,
    cancelled_at    DATETIME
);
```

### `market_outcomes`
```sql
CREATE TABLE market_outcomes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    market_ticker   TEXT NOT NULL,
    outcome         TEXT NOT NULL,       -- "YES" | "NO"
    resolved_at     DATETIME NOT NULL,
    actual_value    REAL,                -- underlying economic value (e.g., CPI reading)
    source          TEXT                 -- "kalshi_api" | "bls" | "fed"
);
```

---

## Point-in-Time (PIT) Query Pattern

**The most important rule in the entire data pipeline.**

To reconstruct "what did we know about X at time T?", always filter on `collected_at`:

```python
def get_fedwatch_at(conn, meeting_date: date, as_of: datetime) -> dict | None:
    """Get the most recent FedWatch snapshot for a meeting as of a given time."""
    row = conn.execute("""
        SELECT hike_25bp_prob, hold_prob, cut_25bp_prob
        FROM fed_watch_snapshots
        WHERE meeting_date = ?
          AND collected_at <= ?
        ORDER BY collected_at DESC
        LIMIT 1
    """, (meeting_date.isoformat(), as_of.isoformat())).fetchone()
    return dict(row) if row else None

def get_kalshi_midpoint_at(conn, ticker: str, as_of: datetime) -> float | None:
    """Get the most recent midpoint for a market as of a given time."""
    row = conn.execute("""
        SELECT (best_bid_cents + best_ask_cents) / 2.0 / 100.0
        FROM market_snapshots
        WHERE ticker = ?
          AND collected_at <= ?
          AND best_bid_cents IS NOT NULL
          AND best_ask_cents IS NOT NULL
        ORDER BY collected_at DESC
        LIMIT 1
    """, (ticker, as_of.isoformat())).fetchone()
    return row[0] if row else None
```

**Never join on event date — always join on `collected_at <= as_of_timestamp`.**
**Never use `MAX(collected_at)` without also filtering `collected_at <= as_of`.**

These patterns are enforced by putting all PIT queries in `data/processors/pit.py` and never writing ad-hoc SQL elsewhere.

---

## Cold Start Problem

Kalshi's economics markets are relatively new. Deep historical price archives are limited. Strategies to mitigate:

1. **Start collecting immediately.** Every day without collection is data that's gone forever. Set up the collector before writing a single model line.

2. **Lychee Data backfill.** lycheedata.com offers Kalshi historical data exports. Pull a full backfill for economics tickers on setup.

3. **Use futures benchmarks as proxy for historical fair value.** CME FedWatch data goes back years. Even without Kalshi price history, you can construct "what would the signal have been if the Kalshi price equaled the market consensus?" scenarios. These scenarios won't have real bid-ask data, but they validate the edge hypothesis.

4. **Accept thin early backtests.** Fed rate decisions happen ~8 times per year. After 2 years of Kalshi data, you have ~16 events. That's enough to validate calibration but not enough for complex model training. Use the fundamentals data (FRED, CME) for the heavy ML work; use Kalshi price data primarily for signal calibration.

---

## Data Collection Startup Sequence

On first run (`scripts/collect_history.py`):

1. Initialize SQLite database, create all tables
2. Pull Kalshi `GET /historical/cutoff` to find data partition date
3. Pull all target markets via `GET /markets` filtered to economics series tickers
4. For each market: pull full candlestick history (daily OHLCV) from Kalshi historical API
5. Pull Lychee Data CSV exports and import (if credentials available)
6. Pull full FRED history for all series (use vintage dates API)
7. Pull CME FedWatch history (limited availability — CME doesn't provide deep archives)
8. Pull SPF archive (published as Excel files for prior years)
9. Pull Cleveland Fed nowcast history (available on their site)
10. Log summary: records per table, date ranges, any gaps

On subsequent runs (normal `run_collector.py` daemon):
- Incremental: only pull since last `collected_at` for each source
- Always pull Kalshi markets discovery to catch newly opened markets

---

## Data Quality Rules

### On write:
- Prices must be in [0, 100] cents (Kalshi binary contracts)
- Probabilities must be in [0.0, 1.0]
- `collected_at` must be within 60 seconds of current time (stale data detection)
- No duplicate rows: before inserting a snapshot, check if an identical row exists within the last N minutes

### On read (validation before model use):
- Check that `collected_at` is not more than 2× the expected polling interval ago (staleness alert)
- Check that `best_bid_cents < best_ask_cents` (crossed orderbook = bad data)
- Check that bid-ask spread is reasonable: `ask - bid <= 10` cents for liquid markets
- For CME FedWatch: probabilities must sum to ~1.0

### Alerting:
- If any critical source has no new data for > 2 poll intervals: log WARNING
- If Kalshi market snapshot is >4 hours old when pre-resolution polling is active: log ERROR

---

## Collection Failure Handling

| Failure type | Response |
|---|---|
| HTTP 4xx (auth error) | Log ERROR, stop collecting from that source, alert |
| HTTP 429 (rate limit) | Exponential backoff: 1s → 2s → 4s → max 60s |
| HTTP 5xx (server error) | Retry 3×, then log WARNING and skip interval |
| Network timeout | Retry once after 10s, then skip interval |
| Parse error (bad JSON) | Log ERROR with raw response, skip write |
| WebSocket disconnect | Reconnect with backoff, reconcile via REST on reconnect |

All failures are logged with full context (source, endpoint, error type, raw response excerpt). Never crash the collector daemon on a single source failure — other sources continue normally.
