# SPEC-CORE-001 — Single-Condition Identity Arb: Backtest Analysis Layer

## §G Goal

Analyze signal quality, fill rates, and realized PnL from micro-arb's persisted event stream.
Python repo is the **replay analysis consumer** — not an arb engine.
Engine lives in `../market/micro-arb` (Go); this repo reads its output.

---

## §C Constraints

- C1. No arb detection logic in Python. Signal detection owned by `micro-arb/internal/signal/engine.go` (`sum_arb` strategy).
- C2. All analysis joins on `correlation_id` across signal→risk→execution event records.
- C3. PnL deduction must match micro-arb's `feeBPS` + `slippageBPS` config values, not hardcoded constants.
- C4. Stale-suppressed and threshold-rejected signals excluded from win-rate numerator; included in opportunity-count denominator.
- C5. Remove `proxy.py` / `edge.py` from main strategy path (broken import; wrong scope). Move to `experimental/` or delete.
- C6. L2 depth is not persisted — fill simulation against raw depth is not possible from stored events. Analysis bounded by what Supabase holds: signal decisions, risk decisions, execution results.

---

## §I Interfaces

| id  | surface                                          | notes                                                              |
|-----|--------------------------------------------------|--------------------------------------------------------------------|
| I.1 | Supabase — `signal_decisions` table              | `SignalEventPayload`: spread, edge, direction, decision, rejection |
| I.2 | Supabase — `risk_decisions` table                | `RiskDecisionEventPayload`: risk level, gate latency, rejection    |
| I.3 | Supabase — `execution_results` table             | `ExecutionResultPayload`: fill price, fill size, latency fields    |
| I.4 | `micro-arb/internal/signal/engine.go`            | upstream engine — read-only reference; do not reimplement          |
| I.5 | `micro-arb/backtest.config.json`                 | source of `feeBPS`, `slippageBPS`, `spreadThreshold` for analysis  |
| I.6 | `notebooks/` (this repo)                         | analysis consumer: load → join → compute → visualize              |
| I.7 | `micro-arb/internal/replay/` (Go replay runner)  | authoritative replay harness; Python analysis supplements, not replaces |

---

## §V Invariants

- V1. `yes_price + no_price - 1 = spread` in persisted events must match engine log within floating-point tolerance.
- V2. Every emitted signal must have a corresponding risk decision joinable by `correlation_id`.
- V3. Win rate = fills with positive net PnL / total filled signals. Rejections excluded from numerator AND denominator.
- V4. Net PnL per trade = `fill_size × |spread| - fill_size × (feeBPS + slippageBPS) / 10000`.
- V5. Opportunity count = all signal evaluations (emitted + rejected). Capture rate = emitted / opportunity count.
- V6. Latency analysis uses `submit_latency_us` and `fill_latency_us` from execution records; p50/p95 reported.
- V7. Any analysis claiming "guaranteed profit" must cite `net_edge > 0` after V4 deduction, not gross spread.
- V8. `proxy.py` / `edge.py` must not appear in any notebook import chain.
- V9. Analysis config (feeBPS, slippageBPS, threshold) loaded from `backtest.config.json`, not hardcoded.

---

## §T Tasks

| id  | status | description                                                          | cites          |
|-----|--------|----------------------------------------------------------------------|----------------|
| T1  | x      | Move `proxy.py` + `edge.py` to `experimental/` or delete            | C5, V8         |
| T2  | x      | Notebook: load signal_decisions from Supabase, filter by strategy=sum_arb | I.1, C1   |
| T3  | x      | Notebook: join signal→risk→execution on correlation_id               | I.1,I.2,I.3,V2 |
| T4  | x      | Notebook: compute net PnL per trade using V4 formula                 | V4, C3, I.5    |
| T5  | x      | Notebook: win rate, capture rate, opportunity funnel                 | V3, V5         |
| T6  | x      | Notebook: latency distribution (p50/p95 detect-to-submit, fill)      | V6, I.3        |
| T7  | x      | Notebook: drawdown curve and daily PnL time series                   | V7             |
| T8  | x      | Notebook: rejection breakdown by reason (below_threshold, stale, negative_edge) | I.1, C4 |
| T9  | x      | Load feeBPS/slippageBPS/spreadThreshold from backtest.config.json    | C3, V9, I.5    |
| T10 | x      | Update README: scope = analysis consumer of micro-arb events; engine is Go | C1, C5    |

---

## §B Bug Log

| id | date | cause | fix |
|----|------|-------|-----|
