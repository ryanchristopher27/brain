# Brainstorm — Trading Dashboard & Control Plane
Date: 2026-06-03
Status: Captured — pending /plan

---

## Problem / Opportunity

The prediction market bot has a working data pipeline (Kalshi snapshots, FedWatch, FRED) and a
baseline signal model (M3). As the framework scales toward live trading, there are two growing
needs:

1. **Data visibility** — understanding what data has been collected, where the gaps are, and
   whether the signals make intuitive sense before committing capital.
2. **Operational control** — deploying models, managing risk limits, and interacting with the
   live trading framework without dropping into the terminal for every action.

These are distinct in urgency but unified in architecture. A read-only dashboard built on the
wrong foundation will need to be rewritten when operational control is added. The goal is to
design the right system from day one and build into it in phases.

---

## Goals

- Provide a visual interface for monitoring data quality, FedWatch probabilities, Kalshi prices,
  and active trade signals.
- Surface model performance metrics (calibration, Brier score, simulated P&L) as resolved
  markets accumulate.
- Serve as the operational interface for deploying/disabling models, adjusting risk limits,
  and managing live trades — without requiring terminal access.
- Be local-first but structured so it can be shared with collaborators without a rewrite.

---

## Audience

**Primary:** Solo operator (current). Local use only, full trust.

**Future:** Potential collaborators. Requires auth enforcement and a presentable UI before
sharing. Architecture must anticipate this without implementing it prematurely.

---

## Constraints

- Python-only codebase — no context switch to JS unless the operational complexity demands it.
- Local-first: runs on localhost, no cloud dependency in Phase 1.
- Share-ready: auth and deployment path must be designable in Phase 1, even if not activated.
- The dashboard must never be the source of truth for trading decisions — it surfaces signals
  and executes confirmed actions, but the models and risk engine remain in the Python modules.
- Operational actions touching live capital (place order, cancel order, kill switch) require
  confirmation flows — a misclick must not fire a trade.

---

## Ideas & Directions

### Direction A — Pure Streamlit (read-only dashboard only)

Streamlit pages import Python modules directly. Fast, no API layer.

**Pros:** Fastest path to useful monitoring. No new dependencies.

**Cons:** Dead-end architecture for operational control. Streamlit reruns the full script on
every widget interaction — risky for consequential actions. Auth retrofitting is painful.
Ruled out as the final architecture; acceptable only if scope stays read-only forever.

---

### Direction B — FastAPI backend + Streamlit frontend ✓ RECOMMENDED

A lightweight FastAPI service wraps all data access and operational actions. Streamlit pages
call `http://localhost:8000/api/...` rather than importing modules directly.

**Pros:**
- Auth lives in one place (API middleware) — no-op locally, enforced when sharing.
- Every operational action is an auditable, idempotent HTTP call. Confirmation flows,
  audit logging, and retry safety are natural at the API layer.
- Streamlit can be replaced by React or anything else later without touching the backend.
- Pure Python — no JS context switch.
- FastAPI is already a natural fit alongside the existing `httpx`/async patterns in the project.

**Cons:**
- More upfront scaffolding than Direction A.
- Two processes to run locally (uvicorn + streamlit). Mitigated with a single launcher script.

---

### Direction C — FastAPI backend + React frontend

Full stack from day one. Best UX for operational controls; real-time WebSocket updates;
modal confirmation dialogs are native.

**Pros:** Most polished end state; best for eventual collaboration UX.

**Cons:** 3-4x effort multiplier; introduces a JS context switch; no advantage over Direction B
until the operational complexity genuinely outgrows Streamlit's widget model.

**Verdict:** Valid upgrade path from Direction B. Build to B now; swap Streamlit for React
if/when warranted.

---

## Recommended Architecture

```
dashboard/
├── api/
│   ├── main.py              # FastAPI app (uvicorn on :8000)
│   ├── routers/
│   │   ├── data.py          # GET: collection status, fred, fedwatch snapshots
│   │   ├── markets.py       # GET: market inventory, snapshot history
│   │   ├── signals.py       # GET: live signals, edge distribution
│   │   ├── models.py        # GET/POST: model status, enable/disable, trigger backtest
│   │   └── control.py       # POST: risk limits, kill switch, order cancellation
│   └── auth.py              # API key middleware (no-op in Phase 1, enforced in Phase 2)
├── app.py                   # Streamlit entry point (`streamlit run dashboard/app.py`)
├── pages/
│   ├── 1_Overview.py        # Health badges, last-updated per source, active signal count
│   ├── 2_Data.py            # FedWatch probability curves, FRED history, snapshot heatmap
│   ├── 3_Markets.py         # Market inventory table, price history chart per market
│   ├── 4_Signals.py         # Live signal table, edge histogram, FedWatch vs Kalshi overlay
│   ├── 5_Model.py           # Calibration curve, Brier score, simulated P&L
│   └── 6_Control.py         # Risk limits, model deployment panel, kill switch
└── client.py                # Thin Python client Streamlit uses to call the FastAPI backend
```

---

## Phase Plan

### Phase 1 — Monitoring (build now)
Implement read endpoints in `api/routers/data.py`, `markets.py`, `signals.py`.
Build pages 1–5. Control page exists but is limited to editing config-file thresholds
(no live order actions yet). Auth middleware is a no-op stub.

**Deliverable:** A running dashboard that answers "what data do I have, and what does the
model think right now?"

### Phase 2 — Operational Control (before live capital)
Add write endpoints: risk limit updates, model enable/disable, order cancellation, kill switch.
Wire them to page 6. Enforce confirmation flows at the API layer (two-step commit pattern).
Add auth middleware (API key) for sharing.

**Deliverable:** Full control plane. Can deploy models and manage positions without terminal.

---

## Page Inventory

| Page | Purpose | Phase |
|---|---|---|
| Overview | Health badges, last-updated per data source, active signal count, bankroll | 1 |
| Data Explorer | FedWatch probability curves per meeting, FRED series history, snapshot coverage heatmap | 1 |
| Markets | Market inventory, active vs. settled, price history chart for any selected market | 1 |
| Signals | Live signal table (replaces run_signals.py), edge distribution histogram, FedWatch vs Kalshi overlay per meeting | 1 |
| Model Analysis | Calibration reliability diagram, Brier score over time, simulated P&L curve | 1 |
| Control | Risk limit editor, model deployment toggles, kill switch, open order management | 2 |

---

## Recommendations

1. **Architecture:** FastAPI backend + Streamlit frontend (Direction B). This is the right
   long-term structure and the right amount of work for Phase 1.

2. **Chart library:** Plotly Express. Interactive, renders natively in Streamlit, handles
   time-series, histograms, and calibration scatter plots cleanly.

3. **Data access pattern:** All pages go through `dashboard/client.py` → FastAPI → Python
   modules. No page imports trading engine modules directly. This enforces the seam that
   makes Phase 2 (auth, sharing) a config change, not a refactor.

4. **Launcher:** A single `scripts/run_dashboard.sh` that starts both uvicorn and streamlit
   in parallel. One command to run the full dashboard locally.

5. **Auto-refresh:** The Signals page should poll the API every 60 seconds while open.
   Streamlit's `st.rerun()` with a sleep makes this straightforward.

---

## Suggested Decisions (confirm before /plan)

| Decision | Recommendation |
|---|---|
| Architecture | FastAPI + Streamlit (Direction B) |
| Chart library | Plotly Express |
| Phase 1 scope | Pages 1–5, read-only; Control page stub only |
| Launcher | Single shell script starting both services |
| Auto-refresh interval | 60 seconds on Signals page |

---

## Open Questions (resolve during /plan or Phase 2)

1. **Auto-refresh:** Should the Signals page poll automatically every 60s while the collector
   is running, or should refresh be manual (button-triggered)? Automatic is more useful for
   live monitoring but adds background requests to the API.

2. **Kill switch scope:** When triggered, does the kill switch (a) pause the collector daemon,
   (b) cancel all open Kalshi orders, or (c) both? Scope needs to be defined before the
   Control page endpoint is implemented.

3. **Config mutability:** Risk limits today live in `config/markets.yaml`. Should the dashboard
   write back to that file (simple, but ties runtime state to a tracked file), or maintain a
   separate runtime config table in SQLite that overrides the YAML at startup? The SQLite
   approach is cleaner for auditability and avoids git-tracked config churn.

4. **Auth mechanism for sharing:** API key (simple, sufficient for collaborator access) vs.
   OAuth / Streamlit's native `st.login()` (better UX, supports multiple users). Decision
   needed in Phase 2 before any deployment outside localhost.

---

## Next Steps for /plan

- Define the FastAPI app structure and the minimal set of endpoints needed for Phase 1.
- Decide Streamlit page-by-page what data each page needs and which API call serves it.
- Resolve auto-refresh question (open question 1) — it affects Signals page design.
- Identify any DB queries that don't yet exist and need to be added to `database.py`.
- Scope the launcher script.
