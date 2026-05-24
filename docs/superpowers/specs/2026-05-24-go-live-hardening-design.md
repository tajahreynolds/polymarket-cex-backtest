# Go-Live Hardening Design
**Date:** 2026-05-24  
**Scope:** micro-arb (Go engine) + polymarket-cex-backtest (Python analysis)  
**Goal:** Correct core signal logic drift, harden for live trading at $1–5k capital  
**Deferred:** Cross-venue sum-arb (Kalshi) — pending pipeline validation on Polymarket alone

---

## Problem Statement

Two independent issues block go-live:

1. **Signal logic drift** — Go engine computes `(polyMid - binanceMid) / polyMid` (directional bet vs. Binance spot). Spec V1 and intended strategy require `YES_price + NO_price - 1` (sum-arb, risk-free up to fees). These are different alphas. Current implementation does not capture the intended edge.

2. **Go-live hardening gaps** — Four operational blockers: MockExecutor misconfiguration risk, polling-based fill tracking, missing dedup on WAL replay, and unvalidated risk parameter calibration for target capital.

---

## Section 1: Signal Engine — Logic Fix

**Repo:** `micro-arb`  
**File:** `internal/signal/engine.go` (primary), `internal/ingestion/` (event model)

### 1.1 Spread Formula

Replace in `EvaluateCtx()`:
```go
// BEFORE (wrong — directional bet vs Binance spot)
spread := (polyMid - binanceMid) / polyMid

// AFTER (correct — sum-arb identity)
spread := yesPrice + noPrice - 1.0
```

`spread < 0` → both legs underpriced → `BUY_BOTH` (buy YES + buy NO, collect ~|spread| on resolution)  
`spread > 0` → both legs overpriced → `SELL_BOTH` (sell YES + sell NO)

For $1–5k retail on Polymarket: only `BUY_BOTH` is actionable without margin. Emit and log `SELL_BOTH` signals but do not route to executor until margin/short support confirmed.

### 1.2 PriceEvent Model

Current `PriceEvent` carries a single price. Sum-arb requires both YES and NO prices atomically from the same tick.

Extend `PriceEvent` (or introduce `OutcomePairEvent`):
```go
type OutcomePairEvent struct {
    ContractID          string
    YesPrice            float64  // best ask on YES leg (BUY side)
    NoPrice             float64  // best ask on NO leg (BUY side)
    ReceivedAt          time.Time
}
```

**API flow (Polymarket CLOB):**

1. **Startup** — call `getClobMarketInfo(conditionID)` once per market. Extract YES token ID (`t` field where `o == "Yes"`) and NO token ID (`t` field where `o == "No"`). Store both in `BookRegistry`.

2. **Per tick** — call `getPrices([{tokenId: yesTokenId}, {tokenId: noTokenId}])`. Single response returns both `BUY` prices atomically. Emit one `OutcomePairEvent`. Use `BUY` price (best ask) for both legs — arb entry requires buying both.

This eliminates the race condition where YES and NO prices come from different WS timestamps. Both legs fetched in single HTTP round-trip.

### 1.3 Binance Feed — Demote from Hot Path

Binance spot has no role in sum-arb spread computation. Changes:

- Remove `lastBinanceSpot` from `EvaluateCtx()` signal gate entirely
- Binance feed remains active for `MomentumScore` factor (optional confidence signal, not a gate)
- `MomentumScore` may use Binance to assess directional drift as a confidence weight on signal strength, but must not block or modify the spread gate
- Document clearly in config: `BINANCE_WS_URL` is optional when `MOMENTUM_SCORE_ENABLED=false`

### 1.4 Input Validation

Add in `EvaluateCtx()` before spread computation:
```go
if yesPrice <= 0 || noPrice <= 0 || yesPrice >= 1 || noPrice >= 1 {
    // malformed tick — log and skip, do not panic
    return
}
```

### 1.5 TradeIntent Semantics

Update `TradeIntent`:
- `Direction` enum: add `BUY_BOTH`, `SELL_BOTH` (in addition to or replacing `BUY`/`SELL`)
- `Spread` field: now `YES + NO - 1` (signed; negative = opportunity)
- `ExpectedEdge` field: `|spread| - (FEE_BPS + SLIPPAGE_BPS) / 10000`
- `ComplementContractID` already present — used for NO leg order routing

### 1.6 Spec Invariant V1 in Go

Assert V1 at the persistence layer: signal records with `spread` outside `[-1.0, 1.0]` must be rejected with logged error before `AsyncWriter` enqueue.

---

## Section 2: Go-Live Hardening

### 2.1 MockExecutor Misconfiguration Guard

**Problem:** `LIVE_TRADING_ENABLED=false` silently runs MockExecutor. No runtime distinction between intentional mock and misconfigured live.

**Fix:**
- Require `EXECUTION_MODE=mock|live` env var. Missing → fatal startup error with message:  
  `"EXECUTION_MODE must be set to 'mock' or 'live'"`
- MockExecutor logs warning every 100 trades:  
  `"[MOCK MODE] Trade #N discarded — not submitted to venue"`
- Live mode requires `POLYMARKET_API_KEY` and `POLYMARKET_API_SECRET` present at startup. Missing in live mode → fatal error.
- Remove `LIVE_TRADING_ENABLED` env var (replaced by `EXECUTION_MODE`).

### 2.2 Fill Tracking — Polling Replacement

**Problem:** `OrderPoller` polls `GET /orders` for fill status. Adds 100ms–2s fill latency. Missed fills cause open position reconciliation failures.

**Fix:**
- Replace primary fill path with WS-based fill listener on Polymarket authenticated feed.
- `OrderPoller` retained as fallback: activates only if WS drops (WS reconnect triggers polling catch-up for open orders).
- Add `FILL_TIMEOUT_MS` config (default: `500`). On expiry without fill confirmation:
  1. Emit cancel order request to CLOB
  2. Write `order_cancelled` WAL event
  3. Notify risk manager to release reserved capital
- Metric: `fill_latency_ms` histogram (WS-confirmed fills only, not polled fills).

### 2.3 AsyncWriter Dedup on WAL Replay

**Problem:** WAL replay on startup re-inserts rows. Without a `UNIQUE` constraint + upsert, duplicate signals/trades corrupt analysis.

**Fix:**
- Verify migrations include `UNIQUE(correlation_id)` on `signals`, `trades`, `risk_decisions`.
- Change all `AsyncWriter` inserts to:
  ```sql
  INSERT INTO signals (...) VALUES (...)
  ON CONFLICT (correlation_id) DO NOTHING
  ```
  Same for `trades` and `risk_decisions`.
- Add metric: `async_writer_conflicts_total` — nonzero value surfaces replay duplicates in Prometheus.
- Add integration test: write signal → crash simulate → replay WAL → assert single row in DB.

### 2.4 Risk Parameter Calibration ($1–5k)

**Validated configuration for initial live run:**

| Parameter | Value | Rationale |
|---|---|---|
| `TOTAL_CAPITAL_USD` | 2000 | Start at midpoint of range; expand after 50 fills |
| `DAILY_LOSS_LIMIT_PCT` | 0.05 | $100 max daily loss at $2k capital |
| `MAX_POSITION_SIZE_USD` | 100 | Bounded by Polymarket book depth ($50–500 typical) |
| `SIGNAL_SPREAD_THRESHOLD` | 0.005 | 50 bps minimum — below this, fees eat the edge |
| `SIGNAL_COOLDOWN_SECONDS` | 30 | Keep; prevents signal storm on single contract |

**Additional fixes:**
- Print effective risk params to structured log at startup (not buried — first log line after config load).
- Verify Redis TTL on `risk:daily_loss_usd` resets at UTC midnight, not on process restart. If key has no TTL set, startup must set it to seconds-until-midnight.
- Add `/ready` check to include Redis reachability (current check only verifies WS connected).

---

## Section 3: Python Analysis — Programmatic Validation

**Repo:** `polymarket-cex-backtest`

### 3.1 Invariant Assertions — `src/validate.py`

Extract V1–V7 from notebooks into standalone assertion functions:

```python
# src/validate.py

def assert_v1(df):
    """spread = YES + NO - 1; must be in [-1, 1]"""

def assert_v2(df_signals, df_risk):
    """every emitted signal has a risk_decision (correlation_id join)"""

def assert_v4(df, fee_bps, slippage_bps):
    """net_pnl = fill_size * |spread| - fill_size * (fee_bps + slippage_bps) / 10000"""

def assert_v6(df):
    """submit_latency_us and fill_latency_us are present and non-null"""

def assert_v7(df):
    """no positive PnL claim without net_edge > 0"""
```

Each raises `AssertionError` with descriptive message on failure.

Notebooks call these at the top of the analysis cell — no re-implementation inline. Running `python -m src.validate` executes all assertions against live DB as a smoke test.

### 3.2 Fill Quality Metric

Add to `03_pnl.ipynb`:
```python
df['fill_completeness_rate'] = df['actual_fill_size'] / df['intended_size']
```

Flag trades where `fill_completeness_rate < 0.8` — partial fills inflate apparent win rate. Report as separate `partial_fill_count` metric. If `actual_fill_size` not in `execution_results` schema, add it (Go executor must persist `FillSize` per `ExecutionResult`).

### 3.3 Config Path Hardening

`src/config.py` currently reads from hardcoded relative path `../market/micro-arb/backtest.config.json`.

Fix:
```python
config_path = os.environ.get(
    'MICRO_ARB_CONFIG_PATH',
    '../market/micro-arb/backtest.config.json'
)
if not os.path.exists(config_path):
    raise FileNotFoundError(f"Config not found: {config_path}. Set MICRO_ARB_CONFIG_PATH.")
```

### 3.4 Capture Efficiency Baseline

Add to `04_funnel.ipynb`:
```python
theoretical_max_pnl = opportunity_df['spread_bps'].abs().sum() * avg_fill_size / 10000
capture_efficiency = actual_net_pnl / theoretical_max_pnl
```

`capture_efficiency < 0.5` → fill quality or latency is eating edge. Primary alpha validation signal: if efficiency is consistently low, the arb is real but execution is the bottleneck. If `spread_bps` is consistently near zero after fees, the edge is not there.

---

## Invariants (Updated)

| ID | Invariant | Owner |
|---|---|---|
| V1 | `spread = YES + NO - 1` in `[-1, 1]` | Go engine (assert at emit) + Python (assert_v1) |
| V2 | Every emitted signal has a risk_decision | Python (assert_v2) |
| V3 | Win rate = positive PnL fills / total filled | Python notebooks |
| V4 | `net_pnl = fill_size * \|spread\| - fill_size * costs` | Python (assert_v4) |
| V5 | Opportunity count = emitted + rejected | Python notebooks |
| V6 | Latency fields non-null on filled trades | Python (assert_v6) |
| V7 | No positive PnL claim without net_edge > 0 | Python (assert_v7) |
| V8 | `proxy.py` / `edge.py` not imported by notebooks | Python (import check) |
| V9 | Config loaded from file, not hardcoded | Both repos |
| V10 | `EXECUTION_MODE` explicitly set; missing = fatal | Go engine startup |
| V11 | `correlation_id` unique in signals, trades, risk_decisions | Postgres migrations |

---

## Deferred

- **Kalshi ingestion** — new `KalshiClient`, cross-venue event correlation, unified `OutcomePairEvent` across venues. Deferred until Polymarket-only pipeline produces ≥50 validated live fills.
- **SELL_BOTH execution** — requires margin account or short support. Deferred.
- **Kelly/vol-adjusted position sizing** — deferred until capture efficiency baseline established.
- **Prometheus alertmanager rules** — deferred; not blocking for $1–5k capital run.

---

## Success Criteria for Go-Live

1. Signal engine emits `TradeIntent` with `spread = YES + NO - 1` (verified by assert_v1 on first 10 mock fills)
2. `EXECUTION_MODE=live` set; startup logs print effective risk params
3. Fill confirmed via WS within 500ms or order cancelled
4. WAL replay integration test passes (single row per correlation_id)
5. `capture_efficiency` computable from first 20 live fills
6. `DAILY_LOSS_LIMIT_PCT=0.05` circuit breaker tested in mock before live switch
