# Execution — Prediction Market Bot
Date: 2026-05-19
Status: Draft

---

## Overview

The execution layer converts a sized trade signal into real orders on Kalshi (or Manifold for paper trading). It is responsible for:

1. Authenticating and communicating with the Kalshi API
2. Implementing the maker-first order strategy
3. Monitoring fills via WebSocket
4. Tracking open positions and order status
5. Enforcing all pre-trade risk checks
6. Abstracting environment differences (demo vs. live vs. Manifold)

**Execution is the highest-stakes module.** A bug here can result in lost capital or unwanted positions. It must be tested exhaustively on the demo environment before touching live. Every action is logged with full context.

---

## Environment Abstraction

All API communication goes through a single client class that switches behavior based on `BOT_ENV`:

```python
class ExecutionEnvironment(Enum):
    MANIFOLD = "manifold"
    KALSHI_DEMO = "demo"
    KALSHI_LIVE = "live"

class ExecutionClient:
    def __init__(self, env: ExecutionEnvironment):
        self.env = env
        if env == ExecutionEnvironment.MANIFOLD:
            self._client = ManifoldClient()
        elif env == ExecutionEnvironment.KALSHI_DEMO:
            self._client = KalshiClient(base_url=KALSHI_DEMO_URL)
        elif env == ExecutionEnvironment.KALSHI_LIVE:
            self._client = KalshiClient(base_url=KALSHI_LIVE_URL)
```

The `ManifoldClient` and `KalshiClient` share the same method signatures. Swapping environments requires only the `BOT_ENV` env var — no code changes.

**A dry-run mode** (`--dry-run`) routes to a `NullClient` that logs every intended action but submits nothing. Use for signal validation without execution.

---

## Kalshi Authentication

Kalshi uses RSA-PSS (RSASSA-PSS with SHA-256) for authenticated requests. This is different from the API key + secret pattern used by most exchanges.

### Key Setup

Generate the RSA key pair locally:
```bash
openssl genrsa -out kalshi_private.pem 2048
openssl rsa -in kalshi_private.pem -pubout -out kalshi_public.pem
```

Register the public key in the Kalshi dashboard (Settings → API). Store the private key file outside the repository. Set `KALSHI_PRIVATE_KEY_PATH` to its absolute path.

### Signature Construction

For each authenticated request:
```python
import time
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

def build_auth_headers(method: str, path: str, private_key_pem: bytes) -> dict:
    timestamp_ms = str(int(time.time() * 1000))
    message = f"{timestamp_ms}{method.upper()}{path}".encode("utf-8")

    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )

    return {
        "KALSHI-ACCESS-KEY": API_KEY_ID,
        "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("utf-8"),
        "Content-Type": "application/json",
    }
```

**Path note:** Sign only the path (`/trade-api/v2/portfolio/balance`) — do not include query parameters or hostname in the signature string.

**Clock skew:** Kalshi rejects requests where the timestamp is >5 minutes from server time. Ensure system clock is accurate (NTP-synced). Log any auth failure mentioning timestamp.

---

## Order Submission

### Order Types

Kalshi supports two order types:
- **Limit orders:** Post at a specific price. Maker if it doesn't immediately cross; taker if it does.
- **Market orders:** Immediately fill at best available price. Always taker. **Avoid except for rare high-edge cases.**

**Policy: Maker-first always.** Only cross to taker if `edge_after_fees >= TAKER_EDGE_THRESHOLD` (8%+) — a level where the fee cost is justified.

### Order Submission Request

```python
order_body = {
    "ticker": "FOMC-25JUN25-HIKE",
    "side": "yes",                    # "yes" | "no"
    "action": "buy",
    "type": "limit",
    "count": 10,                      # number of contracts
    "yes_price": 67,                  # limit price in cents (for YES side)
    # "no_price": 33,                 # alternatively specify from NO side
    "expiration_ts": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),  # GTC-ish
    "client_order_id": str(uuid.uuid4()),   # idempotency key
}

response = kalshi_client.post("/portfolio/orders", json=order_body)
```

**Always set `client_order_id`** for idempotency. If the request times out but the order was accepted, resubmitting with the same ID is safe — Kalshi deduplicates.

### Price Setting for Maker Orders

```
Current market: YES bid = 63¢, YES ask = 67¢ (spread = 4¢)
Midpoint = 65¢

Strategy (buying YES):
  Post at 64¢ (one cent inside the spread from the bid side)
  → If the ask moves down to meet us, we fill as maker
  → If not filled in MAKER_TIMEOUT_SECONDS, reprice to 65¢ (midpoint)
  → If still not filled in second timeout, cancel
```

**For buying NO:** Post at `100 - (ask_cents - 1)` on the NO side, which is equivalent to one cent inside the spread from the YES ask.

**Spread constraint:** If `ask - bid > MAX_SPREAD_CENTS` (configurable, default 8¢), do not post — the market is too illiquid to execute efficiently. Log as `SKIP_ILLIQUID`.

---

## Order Lifecycle Management

```
State machine:

PENDING ──────────────────→ SUBMITTED
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
                RESTING               IMMEDIATELY_FILLED
                    │                (taker fill — rare)
        ┌───────────┼───────────┐
        ▼           ▼           ▼
    FILLED      REPRICED    CANCELLED
   (maker fill)  (repost)   (manual or
                             timeout)
```

**State transitions managed by `OrderManager`:**

```python
class OrderManager:
    def submit_order(self, signal: TradeSignal, sized_order: SizedOrder) -> Order:
        # 1. Submit to API
        # 2. Record in DB (orders table) with status = SUBMITTED
        # 3. Start fill monitor (WebSocket + poll fallback)
        # 4. Schedule repricing task

    def _on_fill(self, fill_event: dict):
        # Update order status, record fill price and fee
        # Update position tracking
        # Log to execution.log

    def _on_timeout(self, order_id: str):
        # Cancel current order
        # If still have remaining edge: repost at new price
        # If edge is gone (market moved): log MISSED, do not repost

    def _reconcile_positions(self):
        # Called on startup and every hour
        # Compare in-memory positions to REST API positions
        # Log any discrepancy > 0 contracts
```

### Fill Monitoring

**Primary: WebSocket `fill` channel.** Subscribe on startup. Fill events arrive within milliseconds of execution.

**Fallback: REST polling.** If WebSocket is down, poll `GET /portfolio/orders/{order_id}` every 30 seconds for all `RESTING` orders. Reconnect WebSocket in parallel with exponential backoff.

**Reconciliation on reconnect:** When WebSocket reconnects after a dropout, immediately call `GET /portfolio/orders` to catch fills that arrived during the dropout window.

---

## Position Tracking

Maintain an in-memory `PositionBook` synchronized from WebSocket:

```python
@dataclass
class Position:
    ticker: str
    direction: str        # "YES" | "NO"
    contracts: int
    avg_entry_price: float
    current_bid: float
    current_ask: float
    unrealized_pnl: float

class PositionBook:
    def __init__(self): self._positions: dict[str, Position] = {}

    def update_from_fill(self, fill: dict): ...
    def update_prices(self, ticker_event: dict): ...
    def get_open_value(self) -> float: ...    # total $ in open positions
    def net_exposure_to(self, ticker: str) -> int: ...
```

**Persist to DB on every change.** If the bot crashes, reconstruct `PositionBook` from `orders` table on restart:
```python
def restore_positions_from_db(conn) -> PositionBook:
    # Load all FILLED orders, net by ticker/direction
    # Subtract positions where the market has since resolved
```

---

## Risk Checks (Pre-Trade)

The Risk Module runs before order submission. All checks must pass or the order is rejected:

```python
def check_all(signal: TradeSignal, book: PositionBook, bankroll: float) -> RiskResult:
    checks = [
        check_edge_floor(signal),               # edge_after_fees >= MIN_EDGE_THRESHOLD
        check_kelly_size(signal, bankroll),      # kelly fraction <= KELLY_FRACTION
        check_position_cap(signal, book, bankroll),  # position <= MAX_POSITION_PCT
        check_existing_position(signal, book),   # no oversizing on existing positions
        check_daily_loss(bankroll),              # today's loss <= MAX_DAILY_LOSS
        check_data_freshness(signal),            # snapshots not stale
        check_market_liquidity(signal),          # spread <= MAX_SPREAD_CENTS
    ]
    failures = [r for r in checks if not r.passed]
    return RiskResult(passed=len(failures) == 0, failures=failures)
```

Any failure produces a detailed log entry. The order is not submitted.

### Kelly Sizing Calculation

For a binary market: buying YES at market price `p_market` with model estimate `p_model`:

```python
def kelly_fraction(p_model: float, p_market: float) -> float:
    """Full Kelly fraction for a binary prediction market."""
    if p_model <= p_market:
        return 0.0
    return (p_model - p_market) / (1 - p_market)

def position_size(p_model: float, p_market: float, bankroll: float, price_cents: int) -> int:
    """Number of contracts to buy."""
    full_kelly = kelly_fraction(p_model, p_market)
    fractional_kelly = full_kelly * KELLY_FRACTION        # e.g., 0.25×
    dollar_size = min(
        fractional_kelly * bankroll,
        MAX_POSITION_PCT * bankroll                       # hard cap
    )
    contracts = int(dollar_size / (price_cents / 100))    # 1 contract = $1 max payout
    return max(0, min(contracts, int(bankroll / (price_cents / 100))))
```

**Example:**
- Bankroll: $300
- `p_model` = 0.65, `p_market` = 0.55, `price_cents` = 55
- Full Kelly = (0.65 - 0.55) / (1 - 0.55) = 22.2%
- Fractional (0.25×) = 5.6%
- Dollar size = min(0.056 × $300, 0.05 × $300) = min($16.7, $15) → $15
- Contracts = $15 / $0.55 = 27 contracts → buy 27 YES at 55¢

---

## Manifold Paper Trading

Manifold Markets uses play-money (Mana, M$). Use it to validate the Signal Engine before deploying real capital on Kalshi.

**Manifold API:** REST API at `https://api.manifold.markets/v0/`. No auth for read; API key (free) for write.

**Key differences from Kalshi:**
- Play-money — no real financial risk
- Different market structure (AMM, not CLOB) — prices move with each trade
- Larger variety of markets — need to filter to economics/current events relevant to our models

**What to test on Manifold:**
- Signal generation end-to-end (does the pipeline run without errors?)
- Order submission and fill tracking
- Position book reconciliation
- Calibration of model outputs vs. actual Manifold market prices
- Brier score on resolved markets over 4–8 weeks

**Gate to advance to Kalshi demo:** At least 20 resolved predictions with Brier score better than the market baseline (market midpoint Brier score). Document the calibration curve.

---

## Kalshi Demo Environment

The Kalshi demo (`demo.kalshi.co`) is a fully-featured sandbox with simulated liquidity and fake money. It uses a completely separate account and credentials from production.

**What to test on demo:**
- Authentication and all REST endpoint calls
- WebSocket connection stability and reconnect behavior
- Maker order placement and repricing logic
- Fill monitoring (may need to manually accept the other side or wait for simulator)
- Position reconciliation after simulated fills
- Order cancellation flow

**Known limitation of demo:** Liquidity is simulated and may not match production behavior. Fills may happen differently. Use demo primarily for API integration testing, not market behavior testing — Manifold is better for the latter.

**Gate to advance to Kalshi live:** Zero unhandled exceptions in 2 weeks of demo operation. All order lifecycle states exercised. Positions reconcile correctly after restart.

---

## Live Deployment

### Startup Sequence

```python
# run_bot.py --env live
1. Load config and validate all env vars present
2. Load RSA private key from KALSHI_PRIVATE_KEY_PATH
3. Connect to SQLite, verify schema version
4. Restore PositionBook from orders table
5. Reconcile PositionBook against Kalshi REST /portfolio/positions
6. Start WebSocket connection: subscribe to fill, market_positions channels
7. Subscribe to ticker channels for all active target markets
8. Start data collector (or verify it's running as a separate process)
9. Start signal evaluation loop
10. Log startup summary: bankroll, open positions, next target events
```

### Signal Evaluation Loop

```python
async def signal_loop():
    while True:
        for market in active_markets:
            if market.is_within_trading_window():
                signal = signal_engine.predict(market, as_of=now())
                if signal.direction != "PASS":
                    risk_result = risk_module.check_all(signal, position_book, bankroll)
                    if risk_result.passed:
                        sized_order = risk_module.size(signal, bankroll)
                        await order_manager.submit(sized_order)
                    else:
                        logger.info("Signal rejected", extra={"risk_failures": risk_result.failures})
        await asyncio.sleep(SIGNAL_EVAL_INTERVAL_SECONDS)
```

**Trading window:** Only evaluate signals within the configured window before resolution. By default: open trading 30 days before resolution, close 2 hours before resolution (to avoid illiquid market-close conditions).

### Shutdown Sequence

On SIGTERM or SIGINT:
1. Cancel all `RESTING` orders (do not leave unmonitored limit orders)
2. Log final position snapshot
3. Close WebSocket connection
4. Flush all pending DB writes
5. Write shutdown log entry with open positions and unrealized PnL

**Never hard-kill the process** while orders are resting. Always use graceful shutdown. Set up a systemd service (or Windows Task Scheduler) with `KillMode=mixed` and a 30-second timeout.

---

## Error Handling Patterns

| Error | Action |
|---|---|
| Auth failure (401) | Log ERROR, stop trading, alert. Do not retry — likely key issue. |
| Rate limit (429) | Exponential backoff: 1s → 2s → 4s → max 60s |
| Server error (5xx) | Retry 3× with 5s delay, then log WARNING and skip |
| Network timeout | Retry once after 10s, then skip |
| Order rejected by risk module | Log INFO with rejection reasons, do not retry |
| Order submission fails after all retries | Log ERROR, do not open position, alert |
| WebSocket disconnect | Reconnect with backoff, reconcile positions on reconnect |
| Partial fill | Track remaining contracts, decide whether to repost remainder |
| Position mismatch (in-memory vs. API) | Log ERROR with diff, pause new orders until resolved |
| Bankroll read fails | Log ERROR, pause all trading until resolved (no blind bets) |

**Circuit breaker:** If 3 consecutive order submissions fail for any reason, pause all trading for 30 minutes and log an alert. Something systemic may be wrong.

---

## Logging Specification

All execution events are logged to `logs/execution.log` as structured JSON lines (via `loguru`):

```json
// Order submitted
{"ts": "2026-05-19T14:23:01Z", "event": "order_submitted", "ticker": "FOMC-25JUN25-HIKE", "direction": "YES", "contracts": 27, "limit_cents": 64, "order_id": "abc123", "signal_edge": 0.07}

// Order filled
{"ts": "2026-05-19T14:26:33Z", "event": "order_filled", "ticker": "FOMC-25JUN25-HIKE", "order_id": "abc123", "fill_cents": 64, "fill_contracts": 27, "fee_cents": 75}

// Order cancelled (timeout)
{"ts": "2026-05-19T14:38:01Z", "event": "order_cancelled", "reason": "maker_timeout", "ticker": "FOMC-25JUN25-HIKE", "order_id": "abc123", "rested_seconds": 300}

// Risk rejection
{"ts": "2026-05-19T14:23:01Z", "event": "risk_rejected", "ticker": "FOMC-25JUN25-HIKE", "failures": ["edge_floor: 0.03 < 0.05", "data_freshness: snapshot 95min old"]}
```

These logs are the audit trail for every decision the bot makes. Preserve them indefinitely (they're small).
