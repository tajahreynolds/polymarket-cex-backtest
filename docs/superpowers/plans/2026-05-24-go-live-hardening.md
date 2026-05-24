# Go-Live Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix three bugs blocking sum-arb signal emission, harden trades dedup, add startup safety, and add Python capture efficiency baseline.

**Architecture:** Two repos touched independently. Go engine (`../market/micro-arb`) owns signal logic and execution hardening. Python analysis (`polymarket-cex-backtest`) owns replay validation and metrics. Tasks 1–2 are ordered (BestAsk before engine changes). Tasks 3–8 are independent.

**Tech Stack:** Go 1.25 (signal engine, execution, persistence), Python 3 + psycopg2 + pandas (analysis), Polymarket CLOB WS, Redis, PostgreSQL (pgx/v5).

---

## Spec Corrections (recorded before implementation)

The design doc `2026-05-24-go-live-hardening-design.md` had two incorrect findings based on a stale structural analysis. These are corrected here:

- **Section 1.1 (spread formula)** — `engine.go` already computes `YES + NO - 1` at line 464. No change needed.
- **Section 1.2 (OutcomePairEvent via getPrices REST)** — WS already subscribes both legs via `complementID`. Pairing already happens in engine state via `lastNoPrice`. REST polling not needed.

Actual bugs found by reading source are documented in each task below.

---

## File Map

| File | Change |
|------|--------|
| `internal/ingestion/ws_common.go` | Add `BestAsk float64` to `PriceEvent`; zero it in `PutPriceEvent` |
| `internal/ingestion/polymarket.go` | Emit `BestAsk` from parsed WS ask price |
| `internal/signal/engine.go` | Remove Binance hard gates; use `BestAsk` for YES/NO prices; fix `EntryPrice` |
| `internal/persistence/repo.go` | Add `ON CONFLICT (correlation_id) DO NOTHING` to `TradeRepo.Insert()` + `InsertLive()` |
| `internal/config/config.go` | Add startup risk param logging; add MockExecutor warning config |
| `cmd/agent/main.go` | Log effective risk params at startup |
| `internal/execution/mock.go` | Log warning every 100 mock trades |
| `internal/execution/polymarket.go` | Add WS fill listener; FILL_TIMEOUT_MS cancel path |
| `src/validate.py` (Python repo) | V1–V7 assertion functions |
| `src/config.py` (Python repo) | MICRO_ARB_CONFIG_PATH env var with fatal on missing |
| `notebooks/03_pnl.ipynb` (Python repo) | Add `fill_completeness_rate` metric |
| `notebooks/04_funnel.ipynb` (Python repo) | Add `capture_efficiency` baseline |

---

## Task 1: Add BestAsk to PriceEvent

**Goal:** Expose the raw ask price from the Polymarket WS frame so the signal engine can compute arb cost using actual entry price instead of midpoint.

**Files:**
- Modify: `internal/ingestion/ws_common.go` (PriceEvent struct + PutPriceEvent)
- Modify: `internal/ingestion/polymarket.go` (set BestAsk when ask parses cleanly)
- Test: `internal/ingestion/polymarket_test.go` (assert BestAsk populated)

**Acceptance Criteria:**
- [ ] `PriceEvent.BestAsk` is set to the WS frame's `best_ask` value for Polymarket events
- [ ] `BestAsk` is zero-valued when `best_ask` is missing or unparseable
- [ ] `PutPriceEvent` zeroes `BestAsk` on return to pool
- [ ] Existing tests pass unchanged

**Verify:** `cd ../market/micro-arb && go test ./internal/ingestion/... -v -run TestPolymarket` → PASS

**Steps:**

- [ ] **Step 1: Add BestAsk to PriceEvent**

In `internal/ingestion/ws_common.go`, update the struct:

```go
// PriceEvent is a normalized price update from any data source.
type PriceEvent struct {
	Source           string
	ContractOrSymbol string
	Price            float64
	// BestAsk is the raw best-ask price from the venue (0 if unavailable).
	// Used for arb cost computation — ask is the actual entry price for a buy.
	BestAsk    float64
	ReceivedAt time.Time
}
```

Update `PutPriceEvent` to zero the new field:
```go
func PutPriceEvent(e *PriceEvent) {
	*e = PriceEvent{}
	priceEventPool.Put(e)
}
```
(The struct zero already handles this since `*e = PriceEvent{}` zeroes all fields — verify this is the current impl and no change is needed beyond the struct definition.)

- [ ] **Step 2: Set BestAsk in PolymarketClient**

In `internal/ingestion/polymarket.go`, in the `for _, pc := range frame.PriceChanges` loop, the `ask` variable is already parsed at line 333. Wire it through:

```go
// Existing code already parses: ask, askErr := strconv.ParseFloat(pc.BestAsk, 64)
// ... (midpoint computation stays as Price for backward compat)

evtp := GetPriceEvent()
*evtp = PriceEvent{
    Source:           "polymarket",
    ContractOrSymbol: pc.AssetID,
    Price:            price, // midpoint — unchanged
    BestAsk:          func() float64 {
        if askErr == nil {
            return ask
        }
        return 0
    }(),
    ReceivedAt: time.Now(),
}
```

Simplify the anonymous func to a local var before the event:
```go
var bestAsk float64
if askErr == nil {
    bestAsk = ask
}

evtp := GetPriceEvent()
*evtp = PriceEvent{
    Source:           "polymarket",
    ContractOrSymbol: pc.AssetID,
    Price:            price,
    BestAsk:          bestAsk,
    ReceivedAt:       time.Now(),
}
```

- [ ] **Step 3: Write a test asserting BestAsk is populated**

In `internal/ingestion/polymarket_test.go`, find the existing test that sends a synthetic WS frame and add an assertion:

```go
// After receiving a PriceEvent from the test WS server:
evt := <-out
require.Greater(t, evt.BestAsk, 0.0, "BestAsk must be set from best_ask field")
require.Equal(t, evt.BestAsk, parsedAsk) // parsedAsk = value from test frame
```

(If no such test exists, add a minimal one that sends `{"price_changes":[{"asset_id":"abc","price":"0.55","best_bid":"0.54","best_ask":"0.56"}]}` and checks `BestAsk == 0.56`.)

- [ ] **Step 4: Run tests**

```bash
cd /home/tajah/projects/market/micro-arb
go test ./internal/ingestion/... -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add internal/ingestion/ws_common.go internal/ingestion/polymarket.go internal/ingestion/polymarket_test.go
git commit -m "feat(ingestion): expose BestAsk on PriceEvent for arb cost computation"
```

---

## Task 2: Decouple Binance from Sum-Arb Signal Gate

**Goal:** Remove three Binance-dependent guards that block sum-arb signal emission when Binance is absent or stale. Use `BestAsk` for correct arb cost. Fix `EntryPrice`.

**Files:**
- Modify: `internal/signal/engine.go`

**Acceptance Criteria:**
- [ ] Engine emits sum-arb signals with no Binance data present (`lastBinanceSpot == 0`)
- [ ] Engine emits sum-arb signals when Binance feed is stale > 10s
- [ ] `TradeIntent.Spread` = `yesAsk + noAsk - 1` when BestAsk available
- [ ] `TradeIntent.EntryPrice` = YES ask price, not Binance spot
- [ ] MomentumScore factor computation still uses Binance `priceWindow` when available
- [ ] Existing tests pass

**Verify:** `cd ../market/micro-arb && go test ./internal/signal/... -v` → PASS

**Steps:**

- [ ] **Step 1: Remove the `lastBinanceSpot == 0` hard gate**

In `engine.go`, find lines 420–422:
```go
if e.lastBinanceSpot == 0 {
    return nil
}
```

Delete these lines entirely. Sum-arb does not need Binance spot. The NO price staleness check above already handles the case where complementary data is missing.

- [ ] **Step 2: Remove Binance staleness check from sum-arb path**

Lines 403–410 suppress signals when Binance feed age > 10s:
```go
binanceAge := time.Duration(now - e.lastBinanceAt.Load())
polymarketAge := time.Duration(now - e.lastPolymarketAt.Load())
if e.lastBinanceAt.Load() > 0 && binanceAge > stalePriceThreshold {
    e.logger.Warn().Dur("age", binanceAge).Msg("engine: stale binance price; suppressing signal")
    if e.metrics != nil {
        e.metrics.IncSignalsSkipped()
    }
    return nil
}
```

Replace with: keep the Polymarket staleness check, remove the Binance staleness block. The Binance age can remain as a logged warning (non-suppressing) for debugging momentum score quality.

```go
polymarketAge := time.Duration(now - e.lastPolymarketAt.Load())
// Log stale Binance feed as a warning but do not suppress sum-arb signals —
// sum-arb spread computation is independent of CEX price.
if e.lastBinanceAt.Load() > 0 {
    binanceAge := time.Duration(now - e.lastBinanceAt.Load())
    if binanceAge > stalePriceThreshold {
        e.logger.Warn().Dur("age", binanceAge).Msg("engine: stale binance price (momentum score degraded)")
    }
}
if e.lastPolymarketAt.Load() > 0 && polymarketAge > stalePriceThreshold {
    e.logger.Warn().Dur("age", polymarketAge).Msg("engine: stale polymarket price; suppressing signal")
    if e.metrics != nil {
        e.metrics.IncSignalsSkipped()
    }
    return nil
}
```

- [ ] **Step 3: Add lastNoBestAsk field to Engine**

In the `Engine` struct, alongside `lastNoPrice`, add:
```go
lastNoPrice   float64 // guarded by mu; 0.0 = not yet received
lastNoBestAsk float64 // guarded by mu; raw ask for NO leg; 0.0 = not yet received
```

- [ ] **Step 4: Update complement handler to store BestAsk**

In `evaluate()`, the complement event handler (lines 370–374):
```go
if e.isComplementContract(event.ContractOrSymbol) {
    e.lastNoPrice = event.Price
    e.lastNoPriceAt.Store(time.Now().UnixNano())
    return nil
}
```

Update to also store `BestAsk`:
```go
if e.isComplementContract(event.ContractOrSymbol) {
    e.lastNoPrice = event.Price
    if event.BestAsk > 0 {
        e.lastNoBestAsk = event.BestAsk
    }
    e.lastNoPriceAt.Store(time.Now().UnixNano())
    return nil
}
```

- [ ] **Step 5: Use BestAsk for spread computation**

Find the sum-arb computation block (lines 464–472). Currently:
```go
sum := event.Price + noPrice
```

Replace with ask-based computation when available:
```go
yesAsk := event.Price // fall back to midpoint if BestAsk unavailable
if event.BestAsk > 0 {
    yesAsk = event.BestAsk
}
noAsk := noPrice // fall back to midpoint
if e.lastNoBestAsk > 0 {
    noAsk = e.lastNoBestAsk
}
sum := yesAsk + noAsk
```

Keep existing `sum == 1` check and `spread := sum - 1` unchanged.

- [ ] **Step 6: Fix EntryPrice**

Line 544: `EntryPrice: e.lastBinanceSpot` — this is Binance spot, meaningless for a binary outcome arb.

Replace with YES ask price:
```go
EntryPrice: yesAsk, // cost to buy YES leg
```

Also update the verbose log at line 582:
```go
Float64("entry_price", yesAsk).
```

- [ ] **Step 7: Write a signal emission test without Binance**

Add to `internal/signal/engine_test.go`:

```go
func TestSumArbEmitsWithoutBinance(t *testing.T) {
    writer := newTestWriter(t) // use existing test helper or mock
    eng := NewEngine(0.01, 0, 10, 5, false, writer)
    eng.SetPrimaryContract("yes-token")
    eng.SetComplementContract("no-token")
    eng.PreloadMarketState("yes-token")

    // Feed NO price first
    noEvt := ingestion.PriceEvent{
        Source: "polymarket", ContractOrSymbol: "no-token",
        Price: 0.40, BestAsk: 0.41, ReceivedAt: time.Now(),
    }
    require.Nil(t, eng.Evaluate(noEvt))

    // Feed YES price — sum = 0.60 + 0.41 = 1.01 → overpriced → "sell"
    // With spread threshold 0.01: |0.01| >= 0.01, edge = 0.01 - (10+5)/10000 = 0.0085 > 0
    yesEvt := ingestion.PriceEvent{
        Source: "polymarket", ContractOrSymbol: "yes-token",
        Price: 0.60, BestAsk: 0.60, ReceivedAt: time.Now(),
    }
    intent := eng.Evaluate(yesEvt)
    // Binance never called — engine MUST still emit
    require.NotNil(t, intent, "expected signal emission without Binance data")
    require.Equal(t, "sell", intent.Direction)
    require.InDelta(t, 0.01, intent.Spread, 0.0001)
}
```

- [ ] **Step 8: Run tests**

```bash
cd /home/tajah/projects/market/micro-arb
go test ./internal/signal/... -v
```

Expected: PASS (including new test)

- [ ] **Step 9: Commit**

```bash
git add internal/signal/engine.go internal/signal/engine_test.go
git commit -m "fix(signal): decouple Binance from sum-arb gate; use BestAsk for arb cost"
```

---

## Task 3: Trades Table ON CONFLICT Dedup

**Goal:** Prevent duplicate trade rows on WAL replay by adding `ON CONFLICT (correlation_id) DO NOTHING` to both trade insert paths.

**Files:**
- Modify: `internal/persistence/repo.go` (two INSERT statements)

**Acceptance Criteria:**
- [ ] `TradeRepo.Insert()` silently ignores duplicate `correlation_id` rows
- [ ] `TradeRepo.InsertLive()` silently ignores duplicate `correlation_id` rows
- [ ] Returns `(0, nil)` on conflict (no error surfaced to caller)
- [ ] Existing persistence tests pass

**Verify:** `cd ../market/micro-arb && go test ./internal/persistence/... -v -run TestTrade` → PASS

**Steps:**

- [ ] **Step 1: Verify unique index exists**

```bash
cat /home/tajah/projects/market/micro-arb/internal/persistence/migrations/0012_correlation_id.up.sql | grep "idx_trades_correlation"
```

Expected: `CREATE UNIQUE INDEX idx_trades_correlation ON trades(correlation_id);`

Migration already exists — no new migration needed.

- [ ] **Step 2: Update TradeRepo.Insert()**

In `internal/persistence/repo.go`, find `TradeRepo.Insert()` (~line 132):

```go
// BEFORE
const q = `INSERT INTO trades (correlation_id, signal_id, direction, status, entry_price, size, pnl)
    VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id`
```

Replace with:
```go
const q = `INSERT INTO trades (correlation_id, signal_id, direction, status, entry_price, size, pnl)
    VALUES ($1,$2,$3,$4,$5,$6,$7)
    ON CONFLICT (correlation_id) DO NOTHING
    RETURNING id`
```

After this change, `row.Scan(&id)` will return `pgx.ErrNoRows` on conflict. Handle it:
```go
var id int64
row := r.db.QueryRow(ctx, q, ...)
if err := row.Scan(&id); err != nil {
    if errors.Is(err, pgx.ErrNoRows) {
        return 0, nil // duplicate — idempotent
    }
    return 0, fmt.Errorf("trade insert: %w", err)
}
return id, nil
```

Add `"github.com/jackc/pgx/v5"` import if not already present.

- [ ] **Step 3: Update TradeRepo.InsertLive()**

Find `TradeRepo.InsertLive()` (~line 187):

```go
// BEFORE
const q = `INSERT INTO trades (external_id, contract_id, direction, status, entry_price, size, correlation_id, signal_id)
    VALUES ($1,$2,$3,'open',$4,$5,$6,(SELECT id FROM signals WHERE correlation_id = $6 LIMIT 1)) RETURNING id`
```

Replace with:
```go
const q = `INSERT INTO trades (external_id, contract_id, direction, status, entry_price, size, correlation_id, signal_id)
    VALUES ($1,$2,$3,'open',$4,$5,$6,(SELECT id FROM signals WHERE correlation_id = $6 LIMIT 1))
    ON CONFLICT (correlation_id) DO NOTHING
    RETURNING id`
```

Apply the same `pgx.ErrNoRows` guard as in Step 2.

- [ ] **Step 4: Run tests**

```bash
cd /home/tajah/projects/market/micro-arb
go test ./internal/persistence/... -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add internal/persistence/repo.go
git commit -m "fix(persistence): add ON CONFLICT DO NOTHING to trade inserts for WAL replay dedup"
```

---

## Task 4: Startup Safety — Risk Param Log + MockExecutor Warning

**Goal:** Make misconfigured live/mock state immediately visible. Log effective risk params at boot. Warn loudly in mock mode.

**Files:**
- Modify: `cmd/agent/main.go`
- Modify: `internal/execution/mock.go`

**Acceptance Criteria:**
- [ ] First structured log after config load prints: capital, daily loss limit, max position size, spread threshold, execution mode
- [ ] MockExecutor logs `[MOCK MODE] trade #N discarded` every 100 trades
- [ ] Existing tests pass

**Verify:** `cd ../market/micro-arb && go build ./cmd/agent/... && go test ./internal/execution/... -v` → no errors

**Steps:**

- [ ] **Step 1: Log risk params at startup**

In `cmd/agent/main.go`, after the config load block (~line 356), add immediately after `cfg` is validated:

```go
log.Info().
    Float64("total_capital_usd", cfg.TotalCapitalUSD).
    Float64("daily_loss_limit_pct", cfg.DailyLossLimitPct).
    Float64("max_position_size_usd", cfg.MaxPositionSizeUSD).
    Float64("spread_threshold", cfg.SignalSpreadThreshold).
    Bool("live_trading", cfg.LiveTradingEnabled).
    Str("wal_dir", cfg.WALDir).
    Msg("startup: effective config")
```

Check `config.Config` field names (`TotalCapitalUSD`, `DailyLossLimitPct`, etc.) by reading `internal/config/config.go` — match exact field names.

- [ ] **Step 2: Add mock trade counter to MockExecutor**

In `internal/execution/mock.go`, add an atomic counter:

```go
type MockExecutor struct {
    // existing fields...
    tradeCount atomic.Int64
}
```

In the `Execute()` method, after recording the mock trade:

```go
n := e.tradeCount.Add(1)
if n%100 == 0 {
    log.Warn().Int64("trade_n", n).Msg("[MOCK MODE] trade discarded — not submitted to venue")
}
```

- [ ] **Step 3: Run tests and build**

```bash
cd /home/tajah/projects/market/micro-arb
go build ./cmd/agent/...
go test ./internal/execution/... -v
```

Expected: build succeeds, tests PASS

- [ ] **Step 4: Commit**

```bash
git add cmd/agent/main.go internal/execution/mock.go
git commit -m "feat(agent): log effective risk config at startup; warn on mock mode trades"
```

---

## Task 5: WS-Based Fill Listener

**Goal:** Replace polling as the primary fill confirmation path with a WS user-channel subscription. Add 500ms fill timeout with order cancel + WAL event on expiry. Keep OrderPoller as fallback.

**Files:**
- Modify: `internal/execution/polymarket.go`
- Modify: `internal/config/config.go` (add `FILL_TIMEOUT_MS`)

**Acceptance Criteria:**
- [ ] Fill confirmed via WS within `FILL_TIMEOUT_MS` (default 500ms) or order cancelled
- [ ] Cancel emits `order_cancelled` WAL event
- [ ] Risk manager `NotifyClose()` called on fill or cancel so capital is released
- [ ] OrderPoller remains and runs as a reconciliation pass (catches WS-missed fills)
- [ ] Integration test: mock WS fill arrives → trade marked filled within 600ms

**Verify:** `cd ../market/micro-arb && go test ./internal/execution/... -v -run TestFill` → PASS

**Steps:**

- [ ] **Step 1: Add FILL_TIMEOUT_MS to config**

In `internal/config/config.go`:
```go
FillTimeoutMs int `envconfig:"FILL_TIMEOUT_MS" default:"500"`
```

- [ ] **Step 2: Add WS fill listener to PolymarketExecutor**

Polymarket authenticated WS supports a `user` channel subscription:
```json
{"type": "user", "auth": {"apiKey": "...", "secret": "...", "passphrase": "..."}}
```

Order events arrive as:
```json
{"event_type": "order", "order": {"id": "...", "status": "filled", "size_matched": "100"}}
```

In `internal/execution/polymarket.go`, add a method:

```go
// runFillListener subscribes to the Polymarket user WS channel and routes
// fill/cancel events to the fillCh channel. Reconnects on disconnect.
func (e *PolymarketExecutor) runFillListener(ctx context.Context, fillCh chan<- fillEvent) {
    backoff := ingestion.NewExponentialBackoff()
    for {
        if err := e.connectFillWS(ctx, fillCh); err != nil {
            if ctx.Err() != nil {
                return
            }
            delay := backoff.Next()
            log.Warn().Err(err).Dur("backoff", delay).Msg("fill ws: reconnecting")
            select {
            case <-ctx.Done():
                return
            case <-time.After(delay):
            }
            continue
        }
        backoff.Reset()
    }
}
```

Define `fillEvent`:
```go
type fillEvent struct {
    OrderID    string
    Status     string // "filled", "canceled", "partially_filled"
    SizeMatched float64
}
```

- [ ] **Step 3: Implement fill timeout in Execute()**

After submitting an order, instead of returning immediately and relying solely on OrderPoller, wait for WS confirmation with timeout:

```go
func (e *PolymarketExecutor) awaitFill(ctx context.Context, orderID string, fillCh <-chan fillEvent, timeoutMs int) (fillEvent, bool) {
    deadline := time.Duration(timeoutMs) * time.Millisecond
    timer := time.NewTimer(deadline)
    defer timer.Stop()
    for {
        select {
        case evt := <-fillCh:
            if evt.OrderID == orderID {
                return evt, true
            }
        case <-timer.C:
            return fillEvent{}, false
        case <-ctx.Done():
            return fillEvent{}, false
        }
    }
}
```

On timeout: submit `DELETE /order/{orderID}` cancel request, write WAL `order_cancelled` event, call `riskMgr.NotifyClose()`.

- [ ] **Step 4: Run tests**

```bash
cd /home/tajah/projects/market/micro-arb
go test ./internal/execution/... -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add internal/execution/polymarket.go internal/config/config.go
git commit -m "feat(execution): add WS fill listener with FILL_TIMEOUT_MS cancel path"
```

---

## Task 6: Python — Invariant Assertions, Config Hardening, Capture Metrics

**Goal:** Programmatic V1–V7 assertions, config path env var, fill completeness rate, and capture efficiency baseline.

**Files:**
- Create: `src/validate.py` (Python repo)
- Modify: `src/config.py`
- Modify: `notebooks/03_pnl.ipynb`
- Modify: `notebooks/04_funnel.ipynb`

**Acceptance Criteria:**
- [ ] `python -m src.validate` runs against live DB and raises `AssertionError` with message on any violation
- [ ] `src/config.py` raises `FileNotFoundError` with path and env var hint when config not found
- [ ] `03_pnl.ipynb` computes `fill_completeness_rate` per trade
- [ ] `04_funnel.ipynb` computes `capture_efficiency` and displays value

**Verify:**
```bash
cd /home/tajah/projects/polymarket-cex-backtest
python -m src.validate  # should pass or raise clear error
```

**Steps:**

- [ ] **Step 1: Create src/validate.py**

```python
# src/validate.py
"""Programmatic invariant checks for the sum-arb analysis pipeline.

Run standalone: python -m src.validate
Called from notebooks at the top of each analysis cell.
"""
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src import db, config


def assert_v1(df: pd.DataFrame) -> None:
    """V1: spread = YES + NO - 1; must be in [-1.0, 1.0]."""
    if df.empty:
        return
    out_of_range = df[(df["spread"] < -1.0) | (df["spread"] > 1.0)]
    if not out_of_range.empty:
        raise AssertionError(
            f"V1 FAIL: {len(out_of_range)} rows have spread outside [-1, 1]. "
            f"Sample correlation_ids: {out_of_range['correlation_id'].head(3).tolist()}"
        )


def assert_v2(df_signals: pd.DataFrame, df_risk: pd.DataFrame) -> None:
    """V2: every emitted signal has a risk_decision (correlation_id join)."""
    emitted = df_signals[df_signals["decision"] == "emitted"]["correlation_id"]
    matched = emitted.isin(df_risk["correlation_id"])
    missing = emitted[~matched]
    if not missing.empty:
        raise AssertionError(
            f"V2 FAIL: {len(missing)} emitted signals have no risk_decision. "
            f"Sample: {missing.head(3).tolist()}"
        )


def assert_v4(df: pd.DataFrame, fee_bps: float, slippage_bps: float) -> None:
    """V4: net_pnl = fill_size * |spread| - fill_size * (fee_bps + slippage_bps) / 10000."""
    if df.empty:
        return
    cost_rate = (fee_bps + slippage_bps) / 10000
    expected = df["fill_size"] * df["spread"].abs() - df["fill_size"] * cost_rate
    delta = (df["net_pnl"] - expected).abs()
    violations = df[delta > 1e-6]
    if not violations.empty:
        raise AssertionError(
            f"V4 FAIL: {len(violations)} rows have net_pnl inconsistent with fee model. "
            f"Max delta: {delta.max():.8f}"
        )


def assert_v6(df: pd.DataFrame) -> None:
    """V6: submit_latency_us and fill_latency_us are present and non-null on filled trades."""
    filled = df[df["status"] == "filled"]
    if filled.empty:
        return
    for col in ("submit_latency_us", "fill_latency_us"):
        if col not in filled.columns:
            raise AssertionError(f"V6 FAIL: column '{col}' missing from execution_results")
        null_count = filled[col].isna().sum()
        if null_count > 0:
            raise AssertionError(
                f"V6 FAIL: {null_count} filled trades have NULL {col}"
            )


def assert_v7(df: pd.DataFrame) -> None:
    """V7: no positive net_pnl without net_edge > 0."""
    if df.empty:
        return
    false_positives = df[(df["net_pnl"] > 0) & (df["expected_edge"] <= 0)]
    if not false_positives.empty:
        raise AssertionError(
            f"V7 FAIL: {len(false_positives)} trades show positive PnL but expected_edge <= 0. "
            f"Sample: {false_positives['correlation_id'].head(3).tolist()}"
        )


def run_all() -> None:
    """Run all invariant checks against the live database."""
    cfg = config.load()
    conn = db.connect()

    df_signals = pd.DataFrame(db.query("SELECT correlation_id, decision, spread FROM signal_decisions WHERE strategy = 'sum_arb'"))
    df_risk = pd.DataFrame(db.query("SELECT correlation_id FROM risk_decisions"))
    df_exec = pd.DataFrame(db.query(
        "SELECT correlation_id, status, fill_size, net_pnl, expected_edge, "
        "submit_latency_us, fill_latency_us FROM execution_results"
    ))

    assert_v1(df_signals)
    print("V1 PASS")

    assert_v2(df_signals, df_risk)
    print("V2 PASS")

    filled_exec = df_exec[df_exec["status"] == "filled"].copy()
    if not filled_exec.empty:
        # V4 requires spread on execution rows — join if needed
        if "spread" not in filled_exec.columns:
            spread_map = df_signals.set_index("correlation_id")["spread"]
            filled_exec["spread"] = filled_exec["correlation_id"].map(spread_map)
        assert_v4(filled_exec, cfg["fee_bps"], cfg["slippage_bps"])
        print("V4 PASS")

        assert_v6(df_exec)
        print("V6 PASS")

        assert_v7(filled_exec)
        print("V7 PASS")
    else:
        print("V4/V6/V7: no filled trades to check")

    conn.close()
    print("All invariants PASS")


if __name__ == "__main__":
    run_all()
```

- [ ] **Step 2: Harden src/config.py**

Find `config.py`'s path resolution. Replace hardcoded path:

```python
import os

def load() -> dict:
    config_path = os.environ.get(
        "MICRO_ARB_CONFIG_PATH",
        os.path.join(os.path.dirname(__file__), "../../market/micro-arb/backtest.config.json"),
    )
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Config not found: {config_path!r}. "
            "Set MICRO_ARB_CONFIG_PATH to the absolute path of backtest.config.json."
        )
    with open(config_path) as f:
        return json.load(f)
```

- [ ] **Step 3: Add fill_completeness_rate to 03_pnl.ipynb**

Open `notebooks/03_pnl.ipynb`. After the cell that loads `execution_results`, add a new cell:

```python
# Fill completeness: actual vs intended size
# fill_completeness_rate < 0.8 → partial fill; inflates win rate
if "intended_size" in df_exec.columns and "fill_size" in df_exec.columns:
    df_exec["fill_completeness_rate"] = df_exec["fill_size"] / df_exec["intended_size"]
    partial_fills = df_exec[df_exec["fill_completeness_rate"] < 0.8]
    print(f"Partial fills (<80% complete): {len(partial_fills)} of {len(df_exec)} trades")
    print(f"Avg fill completeness: {df_exec['fill_completeness_rate'].mean():.2%}")
else:
    print("NOTE: intended_size not in schema — add fill_size to ExecutionResult in Go executor")
```

- [ ] **Step 4: Add capture_efficiency to 04_funnel.ipynb**

Open `notebooks/04_funnel.ipynb`. After the funnel metrics cell, add:

```python
# Capture efficiency: what fraction of theoretical max PnL was actually captured
# < 50% → fill quality or latency is eating the edge
# ~0 → arb edge is not real or fees exceed spread

cost_rate = (cfg["fee_bps"] + cfg["slippage_bps"]) / 10000

# Theoretical: sum of net edges across all signals (emitted + above threshold)
if "spread" in df_signals.columns and "expected_edge" in df_signals.columns:
    emitted = df_signals[df_signals["decision"] == "emitted"]
    avg_fill_size = df_exec["fill_size"].mean() if not df_exec.empty else 0
    theoretical_max_pnl = (emitted["spread"].abs() - cost_rate).clip(lower=0).sum() * avg_fill_size

    actual_net_pnl = df_exec[df_exec["status"] == "filled"]["net_pnl"].sum() if not df_exec.empty else 0

    if theoretical_max_pnl > 0:
        capture_efficiency = actual_net_pnl / theoretical_max_pnl
        print(f"Theoretical max PnL: ${theoretical_max_pnl:.4f}")
        print(f"Actual net PnL:      ${actual_net_pnl:.4f}")
        print(f"Capture efficiency:  {capture_efficiency:.1%}")
        if capture_efficiency < 0.5:
            print("WARNING: <50% capture — fill quality or latency is eating the edge")
    else:
        print("No positive-edge signals emitted yet")
```

- [ ] **Step 5: Run validate**

```bash
cd /home/tajah/projects/polymarket-cex-backtest
python -m src.validate
```

Expected: each invariant prints PASS (or clear AssertionError if data violates it).

- [ ] **Step 6: Commit**

```bash
git add src/validate.py src/config.py notebooks/03_pnl.ipynb notebooks/04_funnel.ipynb
git commit -m "feat(analysis): programmatic invariant checks, capture efficiency, config hardening"
```

---

## Dependency Order

```
Task 1 (BestAsk) → Task 2 (engine uses BestAsk)
Task 3, 4, 5, 6 independent of each other and of Tasks 1–2
```

---

## Go-Live Checklist (after all tasks complete)

1. Run `python -m src.validate` — all PASS
2. Start engine with `LIVE_TRADING_ENABLED=false` — verify startup log prints risk params
3. Observe 10 mock fills — confirm `[MOCK MODE] trade discarded` logs every 100
4. Run `go test ./...` in micro-arb — all PASS
5. Set `LIVE_TRADING_ENABLED=true`, confirm fatal error if API keys absent
6. Run 20 live fills — check `capture_efficiency` in `04_funnel.ipynb`
7. Verify daily loss circuit breaker fires at `TOTAL_CAPITAL_USD * DAILY_LOSS_LIMIT_PCT`
