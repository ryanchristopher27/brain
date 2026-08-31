# Architecture — Prediction Market Bot
Date: 2026-05-19
Status: Draft

---

## System Overview

The bot is a **signal-driven execution system** organized around a one-way data pipeline:

```
External Sources
  ├── Kalshi REST/WS API  ──────────────────────────────────┐
  ├── CME FedWatch                                          │
  ├── FRED (Federal Reserve Economic Data)                  ▼
  ├── Philadelphia Fed SPF                         ┌─────────────────┐
  ├── Cleveland Fed Nowcast                        │  Data Collector  │
  ├── BLS (Bureau of Labor Statistics)             │   (daemon)       │
  └── ADP Research Institute                       └────────┬────────┘
                                                            │ writes
                                                            ▼
                                                   ┌─────────────────┐
                                                   │  SQLite Archive  │
                                                   │  (local store)   │
                                                   └────────┬────────┘
                                                            │ reads
                                              ┌─────────────┴──────────────┐
                                              │                            │
                                              ▼                            ▼
                                   ┌────────────────┐            ┌─────────────────┐
                                   │  Signal Engine  │            │  Backtest Runner │
                                   │  (model layer) │            │  (offline)       │
                                   └───────┬────────┘            └─────────────────┘
                                           │ trade signals
                                           ▼
                                   ┌────────────────┐
                                   │  Risk Module   │
                                   │  (Kelly, caps) │
                                   └───────┬────────┘
                                           │ sized orders
                                           ▼
                                   ┌────────────────┐
                                   │  Order Manager  │
                                   │  (execution)   │
                                   └───────┬────────┘
                                           │
                              ┌────────────┴─────────────┐
                              │                           │
                              ▼                           ▼
                     Kalshi Demo API              Kalshi Live API
                     (dev/staging)               (production)
```

The **Backtest Runner** is an offline path that reads from the same archive and simulates execution against historical data. It shares the Signal Engine and Risk Module so the same code runs in both modes — no separate "backtest model" that diverges from production.

---

## Components

### 1. Data Collector (daemon)

**Responsibility:** Pull data from all external sources on schedule and write to SQLite.

**Runs as:** A persistent process with an internal scheduler (APScheduler or a simple `asyncio` loop with per-task sleep intervals). Not a cron job — needs WebSocket connections that stay alive.

**Key behaviors:**
- Polls Kalshi REST API for market prices at configured intervals (hourly normally, 15-min in last 48h before resolution)
- Maintains WebSocket subscription to `ticker` and `orderbook_delta` channels during active event windows
- Polls CME FedWatch on a schedule and extracts implied Fed hike probability
- Pulls FRED series on release schedules (not continuously — monthly/quarterly)
- Pulls SPF and Cleveland Fed nowcast when new editions are published
- Writes every snapshot with a `collected_at` timestamp (strict — never mutate historical records)
- Validates data before writing (schema checks, range sanity checks, duplicate guards)

**Failure mode:** If a collection run fails, log the error and skip that interval. Never write partial data. Alert (print / notify) if more than 2 consecutive intervals fail for a critical source.

---

### 2. SQLite Archive

**Responsibility:** Single source of truth for all historical data.

**Design principles:**
- **Immutable append-only writes.** Every row has a `collected_at` timestamp. Records are never updated.
- **Point-in-time (PIT) safe.** Queries filter by `collected_at <= as_of_timestamp` to reconstruct what was known at any past moment.
- **No foreign key enforcement** (SQLite makes this optional; keep it simple early).
- Separate tables per data type (see `docs/data.md` for full schema).

**Storage estimate:** Kalshi price snapshots at 15-min intervals across 10 active markets for a year ≈ ~5M rows ≈ well under 1GB. Local storage is not a concern at v1 scale.

**Migration path:** If data volume or concurrent access becomes a bottleneck, migrate to Postgres. The SQLite schema is designed to translate cleanly (no SQLite-specific types).

---

### 3. Signal Engine (model layer)

**Responsibility:** Consume data from the archive and output a trade signal for a specific market event.

**Signal interface — inputs:**
```python
@dataclass
class EventContext:
    market_ticker: str           # Kalshi market ID
    event_type: str              # "fed_rate_decision" | "cpi" | "unemployment"
    resolution_date: datetime    # When the market settles
    as_of: datetime              # Treat as "now" — enforced PIT cutoff
```

**Signal interface — output:**
```python
@dataclass
class TradeSignal:
    market_ticker: str
    direction: str               # "YES" | "NO" | "PASS"
    model_probability: float     # Model's estimated probability of YES
    market_probability: float    # Current Kalshi midpoint
    edge: float                  # model_probability - market_probability
    edge_after_fees: float       # Edge net of expected fee at this price
    confidence: str              # "high" | "medium" | "low" — for logging
    model_name: str              # Which model produced this signal
    as_of: datetime
```

**Signal generation flow:**
1. Fetch current Kalshi midpoint for the market
2. Run the appropriate model (baseline or nowcast) for the event type
3. Calculate raw edge and edge after fees
4. If `edge_after_fees >= MIN_EDGE_THRESHOLD` (config), set direction; otherwise `PASS`
5. Return the full signal object

**Models are stateless** — they don't hold internal state between calls. All state lives in the archive. This makes them safe to use identically in live and backtest contexts.

---

### 4. Risk Module

**Responsibility:** Take a trade signal and produce a sized order respecting all risk constraints.

**Inputs:** `TradeSignal` + current portfolio state (balance, open positions)

**Outputs:** `SizedOrder` (ticker, direction, contracts, limit_price) or `None` (rejected)

**Risk checks applied in order:**
1. **Edge floor:** `edge_after_fees >= MIN_EDGE_THRESHOLD` — hard gate, no override
2. **Direction sanity:** Signal direction must be consistent with edge sign
3. **Kelly sizing:** Compute 0.25× fractional Kelly → raw contract count
4. **Per-bet cap:** Contract count cannot exceed 5% of bankroll at current price — hard cap
5. **Position limit:** If already holding contracts in this market, reduce size or skip
6. **Daily loss limit:** If today's realized + unrealized loss exceeds `MAX_DAILY_LOSS`, reject all new trades for the day
7. **Minimum size:** If computed size < `MIN_CONTRACTS` (e.g., 5 contracts), skip (not worth the overhead)

All thresholds live in `config/settings.py` and can be tuned without touching execution logic.

---

### 5. Order Manager

**Responsibility:** Submit and manage orders on Kalshi (or Manifold for paper trading). Monitor fills via WebSocket. Handle partial fills and timeouts.

**Order lifecycle:**
```
PENDING → SUBMITTED → RESTING (maker) → FILLED | CANCELLED | EXPIRED
```

**Maker order strategy:**
- Post limit orders at `market_ask - 1¢` initially (just inside the spread)
- If not filled within `MAKER_TIMEOUT_SECONDS`, cancel and repost at `market_ask - 0¢` (join the ask)
- If still not filled within second timeout, cancel entirely and log as `MISSED`
- Never cross to taker unless `edge_after_fees >= TAKER_EDGE_THRESHOLD` (set high — ~8%)

**Fill monitoring:**
- Subscribe to `fill` WebSocket channel for real-time notifications
- Fallback: poll `GET /portfolio/orders/{id}` every 30 seconds if WebSocket connection drops

**Position tracking:**
- Maintain in-memory position map synchronized from WebSocket `market_positions` channel
- Reconcile against REST `GET /portfolio/positions` at startup and every hour

---

### 6. Backtest Runner

**Responsibility:** Replay historical signal generation and simulate execution against archived data.

Shares the Signal Engine and Risk Module directly — zero code duplication. The only difference is the execution layer (no real API calls) and the time axis (replays historical `as_of` timestamps).

See `docs/backtesting.md` for full design.

---

## Runtime Modes

| Mode | What runs | Entry point |
|---|---|---|
| **Collector** | Data Collector daemon only | `scripts/run_collector.py` |
| **Backtest** | Backtest Runner (offline) | `scripts/run_backtest.py` |
| **Signal check** | Signal Engine on current live data, no orders placed | `scripts/check_signals.py` |
| **Paper trade (Manifold)** | Full stack against Manifold API | `scripts/run_bot.py --env manifold` |
| **Demo** | Full stack against Kalshi demo | `scripts/run_bot.py --env demo` |
| **Live** | Full stack against Kalshi production | `scripts/run_bot.py --env live` |

The `--env` flag switches the API base URL and credential set. No other code changes between modes.

---

## Configuration Hierarchy

```
config/
├── settings.py          # All tunable parameters, loaded from env vars
└── markets.yaml         # Market universe definition
```

**`settings.py` structure:**
```python
# Risk parameters
MIN_EDGE_THRESHOLD = 0.05        # 5% minimum edge after fees to trade
TAKER_EDGE_THRESHOLD = 0.08     # 8% to cross to taker
MAX_POSITION_PCT = 0.05         # Max 5% of bankroll per position
KELLY_FRACTION = 0.25           # Fractional Kelly multiplier
MAX_DAILY_LOSS = 0.10           # 10% of bankroll max daily loss
MIN_CONTRACTS = 5                # Minimum position size in contracts

# Execution parameters
MAKER_TIMEOUT_SECONDS = 300     # Time before repricing maker order
MAKER_RETRY_TIMEOUT_SECONDS = 180  # Time before cancelling entirely

# Collection parameters
PRICE_POLL_INTERVAL_NORMAL = 3600    # 1 hour normal polling
PRICE_POLL_INTERVAL_PRERESOLUTION = 900  # 15 min in final 48h
PRERESOLUTION_WINDOW_HOURS = 48

# Environment (loaded from env vars, never hardcoded)
KALSHI_API_KEY = os.environ["KALSHI_API_KEY"]
KALSHI_PRIVATE_KEY_PATH = os.environ["KALSHI_PRIVATE_KEY_PATH"]
ENV = os.environ.get("BOT_ENV", "demo")  # "manifold" | "demo" | "live"
```

**`markets.yaml` structure:**
```yaml
markets:
  fed_rate_decisions:
    enabled: true
    platform: kalshi
    ticker_pattern: "FED-*"   # Kalshi ticker prefix
    model: baseline_futures
    cme_instrument: "SOFR"    # CME FedWatch instrument to compare
    min_days_to_resolution: 1
    max_days_to_resolution: 30
    
  cpi:
    enabled: false             # Enable when nowcast model is ready
    platform: kalshi
    ticker_pattern: "CPI-*"
    model: nowcast_cpi
    
  unemployment:
    enabled: false
    platform: kalshi
    ticker_pattern: "JOBS-*"
    model: nowcast_unemployment
```

---

## Secrets Management

**Never hardcode credentials.** All secrets flow through environment variables:

| Secret | Env var | Notes |
|---|---|---|
| Kalshi API Key ID | `KALSHI_API_KEY` | From Kalshi dashboard |
| RSA private key path | `KALSHI_PRIVATE_KEY_PATH` | Path to PEM file on disk |
| FRED API key | `FRED_API_KEY` | Free at api.stlouisfed.org |
| Bot environment | `BOT_ENV` | "demo" \| "live" \| "manifold" |

Use a `.env` file locally (gitignored). Production: set env vars directly in the shell.

**Private key file:** Store the RSA PEM file outside the repo directory. `KALSHI_PRIVATE_KEY_PATH` points to an absolute path.

---

## Logging & Observability

**Library:** `loguru` — structured JSON logs to file, human-readable to console.

**Log levels:**
- `DEBUG`: Every data collection poll result, every signal computation
- `INFO`: Signals generated, orders submitted, fills received, daily summary
- `WARNING`: Collection failures, missed fills, edge cases
- `ERROR`: Uncaught exceptions, authentication failures, risk module rejections

**Log files:**
```
logs/
├── collector.log     # Data collection events
├── signals.log       # Signal generation with full TradeSignal JSON
├── execution.log     # Order submission, fills, cancellations
└── pnl.log          # Daily PnL summary, position snapshots
```

**Daily summary (logged at midnight):**
- Positions opened today, average edge
- Realized PnL today
- Brier score update (if any markets resolved)
- Bankroll snapshot

---

## Testing Strategy

| Layer | Test type | Tool |
|---|---|---|
| Data collectors | Unit tests with mocked HTTP | `pytest` + `respx` |
| Signal Engine | Unit tests with fixture data | `pytest` |
| Risk Module | Property-based tests (Kelly invariants) | `pytest` + `hypothesis` |
| Backtest Runner | Integration test against fixture archive | `pytest` |
| Order Manager | Integration test against Kalshi demo | Manual + demo environment |
| End-to-end | Full pipeline smoke test on demo | `scripts/run_bot.py --env demo --dry-run` |

**Critical invariant tests for the Risk Module:**
- Kelly fraction always ≤ `KELLY_FRACTION`
- Position size never exceeds `MAX_POSITION_PCT × bankroll`
- No trade when `edge_after_fees < MIN_EDGE_THRESHOLD`
- Daily loss limit blocks all trades when breached

---

## Dependency Graph (Python packages)

```
Core runtime:
  pykalshi          → Kalshi API client
  fredapi           → FRED data
  httpx             → HTTP for CME FedWatch + other REST
  apscheduler       → Scheduler for collector daemon
  loguru            → Structured logging
  pyyaml            → markets.yaml config
  python-dotenv     → .env file loading

Data / modeling:
  pandas            → Time series manipulation
  polars            → Fast bulk historical loads
  scikit-learn      → Calibration, metrics
  statsmodels       → Econometric nowcast models
  lightgbm          → Gradient boosting (expansion models)
  scipy             → Statistical utilities

Dev / testing:
  pytest            → Test runner
  hypothesis        → Property-based testing
  respx             → Mock HTTP for collector tests
  black             → Formatting
  ruff              → Linting
```
