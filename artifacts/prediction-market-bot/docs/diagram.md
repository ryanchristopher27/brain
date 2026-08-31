# Architecture Diagram — Prediction Market Bot
Date: 2026-05-19

---

```mermaid
flowchart TD
    subgraph SOURCES["External Data Sources"]
        direction LR
        KREST["Kalshi REST API"]
        KWS["Kalshi WebSocket"]
        CMEF["CME FedWatch"]
        FRED["FRED API"]
        SPF["Philly Fed SPF"]
        CLEV["Cleveland Fed Nowcast"]
        BLS["BLS API"]
        ADP["ADP Research"]
    end

    subgraph COLLECTOR["Data Collector — daemon"]
        RPOLL["Scheduled REST Poller\nhourly / 15-min pre-resolution"]
        WSLIST["WebSocket Listener\nticker + orderbook_delta"]
        DVAL["Validator & Writer\nschema checks · dedup · timestamps"]
        RPOLL --> DVAL
        WSLIST --> DVAL
    end

    DB[("SQLite Archive\nmarket_snapshots · fred_observations\nfed_watch_snapshots · signals · orders")]

    subgraph SIGNAL["Signal Engine — shared by live and backtest"]
        PIT["PIT Query Layer\ncollected_at ≤ as_of"]
        T1["Tier 1 — FedWatch Baseline\nCME implied prob vs. Kalshi price"]
        T2["Tier 2 — CPI Nowcast\nCleveland Fed · BLS · SPF features"]
        T3["Tier 3 — NFP Nowcast\nADP · Initial Claims · ISM features"]
        PIT --> T1 & T2 & T3
    end

    subgraph RISKMOD["Risk Module — shared by live and backtest"]
        EDGECHK["Edge Floor\n≥ 5% after fees"]
        KELLY["Kelly Sizing\n0.25× fractional Kelly"]
        POSCAP["Position & Loss Caps\n5% bankroll per bet · daily loss limit"]
        EDGECHK --> KELLY --> POSCAP
    end

    subgraph LIVE["Live Execution Path"]
        OM["Order Manager\nmaker-first limit orders · repricing · cancellation"]
        POSBOOK["Position Book\nin-memory · DB-persisted"]
        OM <-.->|"fills via WebSocket fill channel"| POSBOOK
    end

    subgraph ENVS["Execution Environments  —  switched by BOT_ENV"]
        MANIFOLD["Manifold Markets\nplay-money paper trade"]
        KDEMO["Kalshi Demo\nfull sandbox · fake capital"]
        KLIVE["Kalshi Live\nproduction · real USDC"]
    end

    subgraph BACKTEST["Backtest Runner — offline"]
        WFENG["Walk-Forward Engine\nreplays events with historical as_of"]
        FILLSIM["Fill Simulator\nbid/ask fills · fee formula · no midpoint"]
        BTMETS["Metrics & Report\nBrier · BSS · Log Loss · ECE · PnL · Sharpe"]
        WFENG --> FILLSIM --> BTMETS
    end

    %% ── Collection flow ──────────────────────────────────────────
    KREST & CMEF & FRED & SPF & CLEV & BLS & ADP --> RPOLL
    KWS --> WSLIST
    DVAL --> DB

    %% ── Signal Engine reads archive (both paths share this) ──────
    DB --> PIT

    %% ── Live path ────────────────────────────────────────────────
    T1 & T2 & T3 --> EDGECHK
    POSCAP -->|"sized order"| OM
    OM --> MANIFOLD & KDEMO & KLIVE

    %% ── Backtest path ────────────────────────────────────────────
    DB --> WFENG
    WFENG -->|"as_of = historical timestamp"| PIT
    POSCAP -->|"sized signal"| FILLSIM

    %% ── Styling ──────────────────────────────────────────────────
    classDef source    fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef collector fill:#fef9c3,stroke:#ca8a04,color:#713f12
    classDef storage   fill:#fde68a,stroke:#d97706,color:#451a03
    classDef shared    fill:#d1fae5,stroke:#059669,color:#064e3b
    classDef live      fill:#dbeafe,stroke:#2563eb,color:#1e3a8a
    classDef backtest  fill:#ede9fe,stroke:#7c3aed,color:#2e1065
    classDef env       fill:#f1f5f9,stroke:#64748b,color:#1e293b

    class KREST,KWS,CMEF,FRED,SPF,CLEV,BLS,ADP source
    class RPOLL,WSLIST,DVAL collector
    class DB storage
    class PIT,T1,T2,T3,EDGECHK,KELLY,POSCAP shared
    class OM,POSBOOK live
    class WFENG,FILLSIM,BTMETS backtest
    class MANIFOLD,KDEMO,KLIVE env
```

---

## Reading the Diagram

| Color | Meaning |
|---|---|
| Light blue | External data sources |
| Yellow | Data Collector (daemon process) |
| Amber | SQLite Archive (single source of truth) |
| Green | Shared components — Signal Engine + Risk Module run identically in both live and backtest modes |
| Blue | Live execution path — Order Manager and Position Book |
| Purple | Backtest path — Walk-Forward Engine, Fill Simulator, Metrics |
| Gray | Execution environments — switched via `BOT_ENV` |

## Key Architectural Observations

**Shared Signal Engine and Risk Module.** The green components are the most important design decision: the same code that generates live trade signals is replayed with a historical `as_of` timestamp in the backtest. There is no separate "backtest model." A bug in the signal engine is a bug in both modes simultaneously — and a backtest that passes is testing real production code.

**Point-in-time (PIT) Query Layer.** Every database read inside the Signal Engine goes through the PIT layer, which enforces `collected_at ≤ as_of`. In live mode `as_of = now()`. In backtest mode `as_of = historical timestamp`. This is the primary defense against lookahead bias.

**Two edges from Risk Module.** `POSCAP` has two outgoing edges: one to the Order Manager (live mode) and one to the Fill Simulator (backtest mode). At runtime, only one of these paths is active based on `BOT_ENV`. The diagram shows both to illustrate the shared nature of the risk logic.

**Environment switching.** The three execution environments (Manifold, Kalshi Demo, Kalshi Live) share the same Order Manager code. The client underneath (`ManifoldClient` vs. `KalshiClient`) is swapped by `BOT_ENV`. No other code changes between environments.

**Data Collector is always separate.** The collector daemon runs continuously regardless of which execution environment is active. It is not part of the signal evaluation loop — it just keeps the archive fresh.
