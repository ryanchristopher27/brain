# Models — Prediction Market Bot
Date: 2026-05-19
Status: Draft

---

## Overview

The model layer converts raw data into a probability estimate for each target market event. The system is designed around **three model tiers**, deployed in sequence as validation gates are passed:

| Tier | Model | Event types | Status |
|---|---|---|---|
| 1 | Baseline: Futures Benchmarking | Fed rate decisions | Start here |
| 2 | Nowcast: CPI | CPI releases | After Tier 1 is validated |
| 3 | Nowcast: Unemployment (NFP) | Non-farm payrolls | After Tier 2 is validated |

Each tier can run independently. A `PASS` from a higher-tier model falls back to the lower tier if one is available. Tier 1 requires zero ML — it's a pure statistical arbitrage based on futures market prices.

---

## Model Interface

All models implement the same interface so the Signal Engine treats them identically:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ModelInput:
    market_ticker: str
    event_type: str
    resolution_date: datetime
    as_of: datetime              # strict PIT cutoff — model may only use data collected_at <= as_of

@dataclass
class ModelOutput:
    probability: float           # P(YES) in [0, 1]
    confidence: str              # "high" | "medium" | "low"
    features: dict               # key features used (for logging/debugging)
    model_version: str           # for tracking which model version produced this

class BaseModel(ABC):
    @abstractmethod
    def predict(self, input: ModelInput, db_conn) -> ModelOutput | None:
        """Return None if insufficient data to make a prediction."""
        ...
```

All database reads inside `predict()` go through `data/processors/pit.py` helpers that enforce the `as_of` cutoff. This ensures the model is safe to use in both live and backtest contexts.

---

## Tier 1: Baseline Futures Benchmarking Model

### Concept

For Fed rate decision markets, CME FedWatch provides a free, highly sophisticated probability estimate derived from 30-Day Federal Funds futures contracts. These futures are traded by institutional participants with large capital at stake — they are well-calibrated.

When Kalshi's price diverges from CME's implied probability, we trade toward the CME estimate. We are not competing against CME; we are asking whether Kalshi's retail crowd has repriced as efficiently as the futures market.

**The brainstorm notes:** Kalshi has a perfect modal forecast record for Fed rate decisions 2022–present. This means the market is already highly efficient at picking the correct *direction*. Our edge comes from exploiting short-term divergences in the *magnitude*, particularly around FOMC meeting windows when markets reprice as data arrives.

### Signal Logic

```
P_model  = FedWatch_implied_probability (for the event matching the Kalshi contract)
P_kalshi = Kalshi midpoint price (as of our data snapshot)
Edge     = P_model - P_kalshi

If Edge > 0: BUY YES (Kalshi is underpriced relative to futures)
If Edge < 0: BUY NO  (Kalshi is overpriced — equivalent to buying YES at implied price)
|Edge| < threshold: PASS (not worth trading after fees)
```

### FedWatch Mapping

Kalshi lists Fed rate decision contracts in several forms:
- Binary: "Will the Fed raise rates at the [date] meeting?" (YES/NO)
- Multi-outcome: contracts for each possible outcome (hold, +25bp, +50bp, etc.)

For binary contracts: the Kalshi YES contract corresponds to one specific FedWatch bucket (e.g., "hike 25bp or more"). The mapping must be explicitly defined per contract in `markets.yaml`:

```yaml
fed_rate_decisions:
  FOMC-25JUN25-HIKE:
    kalshi_ticker: "FOMC-25JUN25-HIKE"
    fedwatch_bucket: "hike_25bp_prob"   # which FedWatch probability this contract corresponds to
    meeting_date: "2025-06-25"
```

For multi-outcome markets (if Kalshi lists them): sum the relevant FedWatch buckets.

### Data Requirements

```python
# Minimum data required for a Tier 1 prediction:
required_data = [
    "fed_watch_snapshots WHERE meeting_date = resolution_date AND collected_at <= as_of",  # must exist
    "market_snapshots WHERE ticker = kalshi_ticker AND collected_at <= as_of",             # must exist
]
# If either is missing: return None (PASS)
```

### Feature Logging (for diagnostics)

```python
features = {
    "fedwatch_hike_prob": 0.72,
    "kalshi_midpoint": 0.65,
    "raw_edge": 0.07,
    "bid_ask_spread": 0.04,
    "days_to_resolution": 12,
    "fedwatch_snapshot_age_hours": 1.5,
    "kalshi_snapshot_age_hours": 0.25,
}
```

### Known Limitations

- **Fed efficiency:** Per the 2026 Federal Reserve study, Kalshi is already highly efficient on Fed direction. The model's edge may be small and concentrated in the days immediately following major macro data releases (CPI, NFP) when the market is repricing.
- **No directional alpha:** If FedWatch and Kalshi agree, there's no signal. This model is purely an arbitrage against the futures market — it generates signals only when divergence exists.
- **Liquidity:** Economics markets are 1.7% of Kalshi volume. In thin markets, even a small position can move the price. Model the impact.

---

## Tier 2: CPI Nowcast Model

### Concept

Forecast the outcome of the upcoming CPI release and compare to Kalshi's market price. The model produces a probability that CPI will resolve YES on a given Kalshi contract (e.g., "Will CPI be above 3.0% YoY?").

### Baseline: Cleveland Fed Nowcast

The Cleveland Fed's inflation nowcasting model is publicly available, well-maintained, and updated daily. **Use it as-is before building anything custom.** The Tier 2 baseline is simply:

```
P_model = P(CPI outcome matches contract) given Cleveland Fed nowcast + uncertainty
P_kalshi = Kalshi midpoint
Edge = P_model - P_kalshi
```

Converting a point forecast to a probability requires a distributional assumption:
- Historical CPI forecast errors have approximately normal distribution
- Estimate the standard deviation of forecast errors using FRED historical actuals vs. SPF consensus
- P(CPI > threshold) = 1 - Φ((threshold - nowcast) / σ_forecast_error)

This gives a calibrated probability from a single number (the nowcast) plus a historical error model.

### Custom Nowcast Model (expansion)

After validating the baseline, build a custom nowcast using leading indicators:

**Feature candidates:**

| Feature | Source | Lead time | Notes |
|---|---|---|---|
| Cleveland Fed CPI nowcast | Cleveland Fed | Real-time | Baseline — use as a feature, not just the output |
| Core PCE (prior month) | FRED (vintage) | 1 month lag | Core PCE is the Fed's preferred measure; CPI and PCE co-move |
| PPI Final Demand | FRED (vintage) | ~1 week before CPI | Input prices → output prices |
| Import price index | FRED (vintage) | ~1 week before CPI | External cost-push signal |
| SPF consensus forecast | Philly Fed | Quarterly | Expert consensus baseline |
| Commodity prices (oil, food) | FRED | Daily | Energy and food are large CPI components |
| Shelter proxy (Zillow rent index) | FRED | Monthly lag | OER (Owner's Equivalent Rent) is slow-moving but predictable |
| University of Michigan inflation expectations | FRED | Monthly | 1-year and 5-year consumer expectations |
| Prior month CPI actuals | FRED (vintage) | 1 month | Autoregressive baseline |

**Model architecture (v1):**
- Ridge regression or LightGBM on the above feature set
- Target: CPI YoY % reading
- Walk-forward training (see `docs/backtesting.md`)
- Calibrate output probabilities with isotonic regression on a held-out validation set

**Feature engineering rules:**
- All features must use vintage dates — never the latest revised values
- Features with monthly releases need a `months_since_last_release` indicator for staleness
- Normalize features relative to trailing 24-month mean and std (prevent distribution shift issues)

### Kalshi CPI Contract Mapping

Kalshi CPI contracts are typically:
- "Will CPI (YoY) be above X%?" — requires P(CPI > X)
- "Will Core CPI be above X%?" — requires separate core CPI model

Map Kalshi contract thresholds to probability queries:
```python
def cpi_probability(nowcast_mean: float, sigma: float, threshold: float, direction: str = "above") -> float:
    from scipy.stats import norm
    if direction == "above":
        return 1 - norm.cdf(threshold, loc=nowcast_mean, scale=sigma)
    else:
        return norm.cdf(threshold, loc=nowcast_mean, scale=sigma)
```

---

## Tier 3: Unemployment / NFP Nowcast Model

### Concept

Same structure as CPI: produce a point forecast for Non-Farm Payrolls (and optionally unemployment rate), convert to a probability over the Kalshi contract threshold, compare to market price.

### Leading Indicators for NFP

| Feature | Source | Lead time | Notes |
|---|---|---|---|
| ADP National Employment Report | FRED / ADP | 2 days before NFP | Most predictive single leading indicator |
| Initial Jobless Claims (4-week avg) | FRED | Weekly | Weekly signal, strong predictor |
| Continuing Claims | FRED | Weekly | Slower-moving but confirms trend |
| ISM Manufacturing Employment component | ISM | ~1 week before NFP | Soft data but useful |
| ISM Non-Manufacturing Employment | ISM | ~1 week before NFP | Services sector signal |
| Conference Board Help Wanted Online | FRED | Monthly | Job posting demand signal |
| JOLTS Job Openings | FRED | Monthly lag | Lagged but structural |
| SPF consensus NFP forecast | Philly Fed | Quarterly | Expert baseline |

**ADP is the single most important feature.** It is the best publicly available leading indicator for NFP, released 2 days before the official BLS number. Build the model architecture around ADP as the anchor feature.

**Model architecture:** Same as CPI — Ridge/LightGBM, walk-forward, calibrated with isotonic regression.

**Known challenge:** NFP is notoriously noisy. Monthly revisions are often large. The model's Brier score will be worse than CPI because the signal-to-noise ratio is lower. Accept this and set a higher edge threshold for NFP trades.

---

## Probability Calibration

Raw classifier outputs are often poorly calibrated (e.g., a model that says 80% is right only 65% of the time). **All models must be calibrated before their probabilities are used for trading.**

### Calibration Methods

**Platt Scaling:**
- Fit a logistic regression on `(raw_probability, actual_outcome)` pairs from held-out validation data
- Simple, works well when training data is limited (which it will be early on)
- Implemented in `sklearn.calibration.CalibratedClassifierCV(method='sigmoid')`

**Isotonic Regression:**
- Non-parametric, more flexible than Platt
- Requires more calibration data (>200 samples recommended)
- Better when the miscalibration pattern is non-monotonic
- Implemented in `sklearn.calibration.CalibratedClassifierCV(method='isotonic')`

**Which to use:**
- Start with Platt scaling (less data needed)
- Switch to isotonic once you have >200 resolved predictions
- Compare ECE (Expected Calibration Error) on a held-out period — use whichever is lower

### Calibration Monitoring

Track calibration over time using a rolling window. A model that was well-calibrated 6 months ago may have drifted if the macro regime changed. Recalibrate monthly at minimum, or after any significant macro event.

```python
from sklearn.calibration import calibration_curve
import numpy as np

def expected_calibration_error(y_true, y_prob, n_bins=10):
    fraction_of_positives, mean_predicted = calibration_curve(y_true, y_prob, n_bins=n_bins)
    bin_sizes = np.histogram(y_prob, bins=n_bins, range=(0, 1))[0]
    ece = np.sum(np.abs(fraction_of_positives - mean_predicted) * bin_sizes) / len(y_true)
    return ece
```

---

## Evaluation Metrics

### Primary: Brier Score

```
BS = (1/N) × Σ(p_i - o_i)²
```
- `p_i`: model probability for event i
- `o_i`: actual outcome (1 = YES, 0 = NO)
- Range: 0 (perfect) to 1 (worst)
- **Benchmark:** Kalshi market midpoint Brier score. Model must beat the market.

**Brier Skill Score (BSS):**
```
BSS = 1 - (BS_model / BS_baseline)
```
BSS > 0 means the model beats baseline. BSS > 0.05 is meaningful. BSS > 0.10 is strong edge.

### Secondary: Log Loss

```
LogLoss = -(1/N) × Σ[o_i × log(p_i) + (1 - o_i) × log(1 - p_i)]
```
- Penalizes confident wrong predictions more heavily than Brier
- Log loss ∞ when `p_i = 1.0` and event doesn't happen — never assign 0 or 1 probability

### Calibration Metrics

- **ECE (Expected Calibration Error):** Weighted average gap between predicted probability and observed frequency across bins. Lower is better. Target < 0.03.
- **Reliability diagram:** Plot predicted probability (x) vs. observed frequency (y). Perfect calibration = 45° diagonal. Generate before any live deployment.

### Financial Metrics

- **Net PnL:** Realized gain/loss after all fees. Primary profitability metric.
- **Edge realization rate:** `(avg_net_PnL_per_trade) / (avg_predicted_edge_after_fees)`. Should be close to 1.0 if model is well-calibrated.
- **Kelly growth rate:** Theoretical growth rate of bankroll under fractional Kelly sizing.
- **Win rate:** Less important than PnL (prediction markets are not binary P&L per se), but useful for pattern diagnostics.

---

## Edge Threshold Requirements

Before any live trade is placed, the signal must pass these gates:

| Gate | Threshold | Notes |
|---|---|---|
| Minimum raw edge | ≥ 5% | `|P_model - P_kalshi|` |
| Minimum edge after fees | ≥ 3% | After probability-weighted fee calculation |
| Model confidence | Not "low" | Low-confidence signals are logged but not traded |
| Calibration recency | ≤ 30 days | Don't trade from a model that hasn't been recalibrated in a month |
| Data freshness | < 2× poll interval | Don't trade from stale market snapshots |

**At 50¢ contracts (the hardest case for fees):**
- Taker break-even edge: ~4.5%
- Our minimum after-fee threshold of 3% means we require ~7.5% raw edge for taker orders
- Maker break-even edge: ~1.0%
- Our minimum after-fee threshold of 3% means ~4% raw edge for maker orders

The strong preference for maker orders is largely about these thresholds.

---

## Model Versioning

Track model versions to enable rollback and performance attribution:

```python
@dataclass
class ModelVersion:
    model_name: str                 # "baseline_fedwatch" | "nowcast_cpi_v1"
    version: str                    # semantic version: "1.0.0"
    trained_through: date           # walk-forward training cutoff date
    calibration_method: str         # "platt" | "isotonic" | "none"
    calibrated_through: date
    brier_score_oos: float          # out-of-sample Brier score on validation period
    ece: float                      # ECE on validation period
    n_validation_events: int        # number of events in validation set
    deployed_at: datetime
    retired_at: datetime | None
```

Store in `models/registry.json`. On each retrain, write a new version entry without modifying prior entries. The Signal Engine always uses the most recently deployed non-retired version.

---

## Model Update Cadence

| Model | Retrain schedule | Recalibrate schedule | Trigger to retrain early |
|---|---|---|---|
| Baseline FedWatch | No training | Monthly calibration check | ECE > 0.05 on trailing 20 events |
| CPI Nowcast | Quarterly | Monthly | Brier score degrades > 0.05 vs. prior quarter |
| NFP Nowcast | Quarterly | Monthly | Same as CPI |

**Monthly recalibration:** Refit the calibration layer (Platt or isotonic) on the most recent 24 months of resolved predictions. Do not retrain the full model — only the calibration wrapper.

**Quarterly retrain:** Run the full walk-forward training cycle on data through the current month. Compare out-of-sample Brier score against the current deployed model. Deploy the new version only if it improves BSS by > 0.01.

---

## Election / Correlated Market Model (deferred)

This is the v2 secondary strategy — Bayesian joint probability modeling across correlated election markets. Not implemented in v1.

**The core insight:** Prediction markets price elections as independent events. Senate seat A and Senate seat B are correlated (same national environment) but often priced inconsistently. Model the joint distribution and find contracts where the marginal pricing is wrong.

**What's needed:**
- Polling data (538-style) by state
- Historical correlation structure between election outcomes
- A joint probability model (Bayesian network or factor model)
- Simultaneous positions in multiple correlated markets

**Defer until:** v1 economics strategy is profitable and running consistently. The election approach is seasonal (concentrated around November) and requires a separate modeling framework. Plan to activate this during the 2026 midterm cycle.
