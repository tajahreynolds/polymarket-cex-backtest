# SPEC-REMED-002 — Remediation Backlog: Ordered Rollout

## §G Goal

Ship risk-safe remediation in ordered gates: unit correctness, mode safety, actionable analytics, 2-leg execution safety, replay-stable attribution, fill-quality visibility.

---

## §C Constraints

- C1. No added live capital before Hotfix Phase (items 1-3) pass.
- C2. Risk checks evaluate USD notional; execution submits shares only after price conversion + venue precision rules.
- C3. Runtime must require explicit mode: `EXECUTION_MODE=mock|live`; implicit defaults forbidden.
- C4. Non-actionable signals must be excluded from default capture/win-rate KPI paths.
- C5. Two-leg execution must bound residual exposure with timeout SLA + forced unwind policy.
- C6. Edge gate decision must use executable net edge (fees + slippage + timeout/cancel penalty), not raw spread.
- C7. Analytics must be replay-stable (idempotent/deduped risk decisions).
- C8. Rollout order fixed: Hotfix -> Shadow window -> Limited live -> Execution hardening -> Analytics hardening -> Scale checkpoint.

---

## §I Interfaces

| id  | surface | notes |
|-----|---------|-------|
| I.1 | Signal intent schema | add `target_notional_usd`, `order_size_shares`, 2-leg intent fields |
| I.2 | Executor submit path | notional->shares conversion, venue rounding, min/max lot guard |
| I.3 | Risk/config startup | `EXECUTION_MODE`, credential checks, startup banner/warnings |
| I.4 | Signal emission path | actionability enum tagging (`*_live`, `*_shadow`) |
| I.5 | Execution orchestrator | two-leg state machine + hedge/unwind + timeout handling |
| I.6 | Persistence/reporting layer | idempotency key or deduped analytics view |
| I.7 | Fill metrics persistence | intended/filled shares, completion ratio, skew/residual timing |
| I.8 | Analysis notebooks/queries | default KPI filters + completion-ratio bucket tables |

---

## §V Invariants

- V1. For each executable intent, `order_size_shares = round_venue(target_notional_usd / entry_price)` and persisted submitted size equals rounded value.
- V2. If computed shares < min lot or > max size, order is reject/clip per policy and event is auditable.
- V3. Risk checks use notional fields; execution path uses share fields; no unit mixing across checks/submission.
- V4. Process startup fails hard if `EXECUTION_MODE` missing/invalid.
- V5. `EXECUTION_MODE=live` without required API creds fails hard before serving traffic.
- V6. `EXECUTION_MODE=mock` emits mandatory startup `[MOCK MODE]` banner and periodic warning cadence.
- V7. Signal actionability enum exists and correctly marks non-shortable positive spread as `sell_both_shadow`.
- V8. Default funnel/capture/win-rate KPI excludes `*_shadow` (or other non-actionable) rows unless explicitly overridden.
- V9. Two-leg intent carries both legs (YES/NO), prices, sizes, and correlation/audit ids.
- V10. If leg B fails after leg A fill, hedge/unwind path must trigger and close residual within timeout SLA or escalate policy.
- V11. Timeout path always emits cancel, risk release, and audit events.
- V12. Executable edge gate = gross spread - fees - modeled 2-leg slippage - cancel/timeout penalty - conservative buffers.
- V13. Positive raw spread with insufficient depth/slippage must fail executable-edge gate.
- V14. Replay of same risk event cannot multiply effective decisions in analytics view.
- V15. Fill-quality fields persist per trade: `intended_shares`, `filled_shares`, `completion_ratio`, `leg_fill_skew_ms`, `residual_exposure_ms`.
- V16. Completion-ratio bucket KPIs (PnL + counts) are present in default analytics outputs.
- V17. Gate A exit requires V1-V8 pass; Gate B exit requires V9-V13 pass with zero unresolved residual past SLA; Gate C exit requires V14-V16 pass.

---

## §T Tasks

| id | status | description | cites |
|----|--------|-------------|-------|
| T1 | x | Hotfix: add `target_notional_usd` + `order_size_shares` to intent schema and persistence mappings | I.1,V1,V3 |
| T2 | x | Hotfix: implement notional->shares conversion at execution with venue precision rounding | I.2,V1 |
| T3 | x | Hotfix: enforce min-lot/max-size reject/clip policy on computed shares with audit events | I.2,V2 |
| T4 | x | Hotfix: split unit responsibilities (risk uses notional, execution uses shares) and block cross-use | I.2,I.3,V3 |
| T5 | x | Hotfix: replace `LIVE_TRADING_ENABLED` with required `EXECUTION_MODE=mock|live` and fatal validation | I.3,V4 |
| T6 | x | Hotfix: add live-cred fatal guard and mandatory mock startup banner + periodic warnings | I.3,V5,V6 |
| T7 | x | Hotfix: add actionability enum tagging in signal emission (`buy_both_live`, `sell_both_shadow`, etc.) | I.4,V7 |
| T8 | . | Hotfix: update analysis/notebooks default filters to exclude non-actionable rows from capture/win-rate | I.8,V8 |
| T9 | . | Safety: extend intent to explicit two-leg payload (legs, target prices/sizes, audit ids) | I.1,I.5,V9 |
| T10 | . | Safety: implement state machine `prepare -> legA_submit -> legB_submit -> done/cancel/hedge` | I.5,V10,V11 |
| T11 | . | Safety: implement residual timeout SLA + forced unwind policy + required audit emissions | I.5,V10,V11 |
| T12 | . | Safety: replace simplistic edge gate with executable-edge model (fees/slippage/timeout penalty/buffer) | I.4,V12,V13 |
| T13 | . | Data: add risk decision idempotency key and/or deduped analytics view for replay stability | I.6,V14 |
| T14 | . | Data: persist fill-quality fields and compute completion ratio at write/read boundary | I.7,V15 |
| T15 | . | Data: add KPI tables/notebooks stratified by completion-ratio buckets (counts + pnl) | I.8,V16 |
| T16 | . | Rollout Gate A: deploy after T1-T8 pass, then run 24-48h mock/shadow validation window | C1,C8,V17 |
| T17 | . | Rollout Gate B: limited live with capped capital after Gate A; complete T9-T12 before size increase | C8,V17 |
| T18 | . | Rollout Gate C: complete T13-T15 then run baseline performance review + scale checkpoint | C8,V17 |

---

## §B Bug Log

| id | date | cause | fix |
|----|------|-------|-----|
