# Backtesting — Prediction Market Bot
Date: 2026-05-19
Status: Draft

---

## Overview

The backtesting framework answers one question: **does the model beat the market on historical data in a way that would have produced real profit?** A backtest is only credible if it avoids the standard pitfalls (lookahead bias, survivorship bias, spread illusion) and uses a simulation environment that reflects real execution constraints.

**Design principle:** The backtest runner shares the Signal Engine and Risk Module directly with the live system. There is no separate "backtest model" — the same code that generates live signals is replayed on historical data with a `as_of` timestamp set to the past. This means a bug caught in backtesting is a bug caught in live trading, and vice versa.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Backtest Runner                 │
│                                              │
│  for each event in historical_event_list:    │
│    for as_of in time_steps_before_event:     │
│      1. signal = signal_engine.predict(      │
│              market, as_of=as_of, db=db)     │
│      2. risk = risk_module.check_all(...)    │
│      3. fill = simulator.simulate_fill(...)  │
│      4. record(signal, fill, as_of)          │
│                                              │
│  metrics = MetricsCalculator(all_records)    │
│  report = BacktestReport(metrics)            │
└─────────────────────────────────────────────┘
           │                    │
           ▼                    ▼
    Signal Engine         SQLite Archive
   (same as live)        (same database)
```

**Key invariant:** The `as_of` timestamp is the wall of knowledge. Every database query inside `signal_engine.predict()` filters `collected_at <= as_of`. The simulator also only uses data from `<= as_of`. No exceptions.

---

## Walk-Forward Validation

The backtest uses **expanding window walk-forward validation**, not a single train/test split.

```
Timeline:
  ──────────────────────────────────────────────────────►

  [───── Training Window ─────][──── Validation ────]
  Jan 2023 → Jun 2024          Jul 2024 → Dec 2024

  Then slide forward:
  [──── Training Window ────────][── Validation ──]
  Jan 2023 → Sep 2024            Oct 2024 → Dec 2024

  At each step:
  - Retrain model on all data up to the cutoff
  - Generate signals for events in the next period
  - Record signals and compare to outcomes
  - Slide cutoff forward
```

**Why expanding window (not rolling):** Prediction markets benefit from more historical data. The macro regime can shift, but early data is still informative about long-run calibration. Use a rolling window only if you detect regime drift (e.g., post-COVID inflation regime vs. pre-COVID).

**Step size:** One event per step — retrain before each new Fed meeting prediction (not each calendar month). This is the natural granularity given the event-driven structure of the strategy.

---

## Event List Construction

Before running the backtest, define the universe of historical events:

```python
@dataclass
class HistoricalEvent:
    market_ticker: str
    event_type: str               # "fed_rate_decision" | "cpi" | "unemployment"
    resolution_date: datetime
    outcome: str                  # "YES" | "NO"
    actual_value: float | None    # the economic reading itself (e.g., CPI = 3.2%)
```

**Event universe filter (must be defined before any analysis):**
- Only markets matching `markets.yaml` ticker patterns
- Only markets that have resolved (outcome known)
- Only markets with at least N price snapshots in the pre-resolution window (N = configurable, default 5)
- Only markets where we have at least one FedWatch/nowcast data point before resolution

**Write this filter before looking at outcomes.** Post-hoc selection of markets that "had good data" is a form of survivorship bias.

---

## Lookahead Bias Prevention

The most common and damaging backtest error. Three specific attack surfaces in this system:

### 1. Data timestamps

All data has a `collected_at` timestamp. Every query inside `signal_engine.predict()` must filter `collected_at <= as_of`. This is enforced by routing all reads through `data/processors/pit.py`.

```python
# CORRECT — PIT safe
price = get_kalshi_midpoint_at(conn, ticker, as_of=as_of)
fedwatch = get_fedwatch_at(conn, meeting_date, as_of=as_of)

# WRONG — lookahead
price = conn.execute("SELECT best_bid_cents FROM market_snapshots WHERE ticker=? ORDER BY collected_at DESC LIMIT 1", (ticker,)).fetchone()
```

**Enforcement:** Unit tests for `pit.py` helpers that inject future data into the test database and verify it's not returned when `as_of` is set to the past.

### 2. FRED vintage dates

FRED revises historical data. CPI for January 2024 looked different in February 2024 than it does today after revisions. **Always use vintage dates when constructing features for backtesting.**

```python
# CORRECT
value = get_fred_vintage(conn, series_id="CPIAUCSL", date="2024-01-01", as_of=as_of)

# WRONG — uses current revised value, not what was known at the time
value = fred.get_series("CPIAUCSL", observation_start="2024-01-01").iloc[0]
```

The `fred_observations` table stores `(series_id, date, value, vintage_date)` tuples. To get the vintage-correct value: filter `vintage_date <= as_of` and take the most recent.

### 3. Economic release timing

Economic data releases happen at specific times (typically 8:30am ET). Do not use release data in a signal constructed before 8:30am ET on release day.

```python
# Economic release times (ET) — hard-coded per event type
RELEASE_TIMES = {
    "cpi": time(8, 30),
    "unemployment": time(8, 30),
    "adp": time(8, 15),
    "fed_fomc_statement": time(14, 0),
}

def is_data_available(series: str, reference_date: date, as_of: datetime) -> bool:
    release_time = RELEASE_TIMES.get(series)
    release_datetime = datetime.combine(reference_date, release_time, tzinfo=ET)
    return as_of >= release_datetime
```

---

## Survivorship Bias Prevention

Kalshi's live API only returns currently active markets. Settled markets disappear. **The archive must capture markets as they are discovered, regardless of whether they later settle.**

```python
# On discovery: archive the market
conn.execute("INSERT OR IGNORE INTO markets (ticker, ...) VALUES (?, ...)", ...)

# When resolved: update outcome
conn.execute("UPDATE markets SET outcome=?, settled_at=? WHERE ticker=?", ...)
```

Backtests always read from `markets` table — never from a live API query. Settled markets with recorded outcomes are the training and validation data.

**Periodic audit:** Monthly, run a check that counts discovered markets vs. markets with outcomes. If the ratio of unresolved old markets is growing, something is wrong with outcome collection.

---

## Fill Simulation

The simulator translates a trade signal into a simulated fill, accounting for bid-ask spread and fees.

### Execution Price

```
Signal: BUY YES on ticker X

Simulate fill at:
  - Maker order: best_ask_cents at the time of the signal (pessimistic — we're buying at the ask)
  - Actually: we're posting inside the spread, so the real fill is between bid and ask
  - Conservative simulation default: fill at ask (full spread cost) — this is the upper bound on cost

For selling YES (i.e., closing a position):
  - Simulate fill at: best_bid_cents (we receive the bid)
```

**Never simulate fills at midpoint.** The midpoint is the theoretical fair value, not an executable price. This is one of the most common backtest optimism errors.

### Fee Calculation

```python
def kalshi_taker_fee(price_cents: int, contracts: int) -> float:
    """Taker fee in dollars."""
    p = price_cents / 100
    return 0.07 * p * (1 - p) * contracts

def kalshi_maker_fee(price_cents: int, contracts: int) -> float:
    """Maker fee in dollars."""
    p = price_cents / 100
    return 0.0175 * p * (1 - p) * contracts
```

Use **taker fee** in the conservative simulation (fills at ask). This is safe — it overestimates costs, which is the right direction for a prudent backtest.

### Market Impact

At small scale (< $100 per position), market impact on Kalshi economics markets is negligible — the contracts are not that liquid anyway. **Do not model market impact in v1.** Add it if position sizes grow to the point where our orders are moving prices.

### Simulated Position Close

When a market resolves YES, contracts pay $1.00 each. When it resolves NO, contracts pay $0.

```python
def simulate_pnl(order: SimulatedOrder, outcome: str) -> float:
    """PnL for a single resolved trade."""
    entry_cost = order.fill_price_cents / 100 * order.contracts
    exit_value = 1.0 * order.contracts if outcome == order.direction else 0.0
    fee = kalshi_taker_fee(order.fill_price_cents, order.contracts)
    return exit_value - entry_cost - fee
```

---

## Metrics

### Prediction Metrics

```python
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.calibration import calibration_curve

signals = [...]      # list of (model_probability, market_probability, actual_outcome)

# Brier scores
model_brier = brier_score_loss(outcomes, model_probs)
market_brier = brier_score_loss(outcomes, market_probs)    # market midpoint as baseline

# Brier Skill Score
bss = 1 - (model_brier / market_brier)

# Log loss
model_log_loss = log_loss(outcomes, model_probs)

# ECE
def ece(y_true, y_prob, n_bins=10):
    fraction_of_positives, mean_predicted = calibration_curve(y_true, y_prob, n_bins=n_bins)
    counts = np.histogram(y_prob, bins=n_bins, range=(0, 1))[0]
    return np.sum(np.abs(fraction_of_positives - mean_predicted) * counts) / len(y_true)

# Calibration curve
fraction_pos, mean_pred = calibration_curve(outcomes, model_probs, n_bins=10)
# Plot: fraction_pos vs. mean_pred (45° diagonal = perfect calibration)
```

### Financial Metrics

```python
# Per-trade metrics
avg_edge = np.mean([s.edge_after_fees for s in signals if s.direction != "PASS"])
avg_pnl_per_trade = total_pnl / n_trades
win_rate = sum(1 for t in trades if t.pnl > 0) / len(trades)
edge_realization_rate = avg_pnl_per_trade / avg_edge   # should be near 1.0

# Portfolio metrics
total_pnl = sum(t.pnl for t in trades)
roi = total_pnl / initial_bankroll
sharpe = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252)
max_drawdown = compute_max_drawdown(cumulative_pnl_series)

# Kelly metrics
avg_kelly_fraction = np.mean([t.kelly_fraction for t in trades])
theoretical_kelly_growth = np.mean([np.log(1 + t.kelly_fraction * t.edge) for t in trades])
```

### Signal Efficiency

How often does the signal fire, and how often does it translate to a trade?

```python
signal_stats = {
    "total_events_evaluated": N,
    "signals_generated": sum(1 for s in signals if s.direction != "PASS"),
    "signals_blocked_by_risk": ...,
    "orders_submitted": ...,
    "orders_filled_maker": ...,
    "orders_cancelled_timeout": ...,
    "signal_rate": signals_generated / total_events_evaluated,
    "fill_rate": orders_filled / orders_submitted,
}
```

---

## Backtest Output Report

The backtest generates a structured report saved to `backtest_results/run_{timestamp}/`:

```
backtest_results/run_20260519_143000/
├── summary.json          # All metrics in one JSON file
├── signals.csv           # Every signal with model_prob, market_prob, outcome
├── trades.csv            # Every simulated trade with fill price, fee, PnL
├── calibration.png       # Reliability diagram (predicted prob vs. observed freq)
├── pnl_curve.png         # Cumulative PnL over time
└── params.json           # Config used for this run (reproducibility)
```

**`summary.json` structure:**
```json
{
  "run_date": "2026-05-19",
  "model_name": "baseline_fedwatch",
  "event_type": "fed_rate_decision",
  "date_range": {"from": "2023-01-01", "to": "2026-05-01"},
  "n_events": 26,
  "n_signals": 18,
  "n_trades": 15,
  "prediction_metrics": {
    "model_brier": 0.142,
    "market_brier": 0.187,
    "brier_skill_score": 0.241,
    "model_log_loss": 0.412,
    "ece": 0.028
  },
  "financial_metrics": {
    "total_pnl": 47.23,
    "roi_pct": 15.7,
    "avg_edge_after_fees": 0.047,
    "avg_pnl_per_trade": 3.15,
    "win_rate": 0.67,
    "sharpe": 1.42,
    "max_drawdown": -22.40,
    "max_drawdown_pct": -7.5
  }
}
```

---

## Pitfall Checklist

Run through this before accepting any backtest result as valid:

- [ ] All data reads filter `collected_at <= as_of` — no exceptions
- [ ] FRED data uses vintage dates, not current revised values
- [ ] Economic release data is not used before the scheduled release time on release day
- [ ] Fills are simulated at ask (buying) and bid (selling) — never at midpoint
- [ ] Fees are applied to every trade (taker fee formula)
- [ ] Market universe was defined before looking at outcomes
- [ ] Markets with outcome = NULL are excluded (not included as NO outcomes)
- [ ] Position sizing uses the same Kelly logic as the live bot
- [ ] No parameter tuning was done on the validation period
- [ ] Walk-forward retraining is sequential — no look-forward in training data selection
- [ ] Calibration is fit on a held-out period, not the same data used for signal evaluation
- [ ] The calibration curve is plotted and reviewed (not just a single ECE number)

---

## Gate Criteria for Advancing to Live

The backtest must clear these thresholds before deploying to Kalshi live with real capital. These are minimums, not targets:

| Metric | Gate | Rationale |
|---|---|---|
| Brier Skill Score (vs. market baseline) | > 0.05 | Meaningful model edge over the crowd |
| ECE | < 0.05 | Reasonably well-calibrated probabilities |
| Number of out-of-sample events | ≥ 15 | Minimum for statistical confidence |
| Walk-forward net PnL (after fees) | > 0 | Must be profitable in simulation |
| No individual event loss > 20% of bankroll | Required | Risk sizing is working |
| Max drawdown | < 30% | Strategy survives realistic losing streaks |
| BSS stable over last 3 walk-forward steps | Required | Not just lucky early; model is consistently good |

**If the backtest passes all gates on paper but Manifold results don't match:** Trust the live results. Real data has properties (timing, fill uncertainty, regime shifts) that even a careful backtest misses. Resolve the discrepancy before going live.

---

## Computational Notes

**Event count:** Fed rate decisions happen ~8× per year. A 3-year historical backtest has ~24 events — thin but sufficient for the baseline model. CPI and NFP have ~36 events over the same period.

**Runtime:** The baseline model's backtest runs in seconds (pure SQL + arithmetic). A full LightGBM nowcast backtest may take minutes. No distributed computing is needed locally.

**Reproducibility:** Save `params.json` alongside every backtest output. When comparing two runs, diff the params files first to understand what changed. Random seeds must be set for any stochastic components (`numpy.random.seed(42)`, LightGBM `seed` parameter).

**Baseline comparison:** Always run the "dumb baseline" in the same backtest: a model that always predicts the market midpoint (edge = 0). Its Brier score is what you're trying to beat. If your model's BSS is negative, you are worse than just following the market.
