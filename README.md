# polymarket-cex-backtest

> ⚠️ **Analysis in progress.** This repo is a replay analysis consumer — not a trading engine. It reads event data produced by the live Go engine in `../market/micro-arb`.

## What this is

Jupyter notebooks that analyze signal quality, fill rates, and realized PnL from micro-arb's persisted event stream.

**Scope: single-condition identity arb only.** The engine detects when `YES price + NO price ≠ 1` on a single Polymarket binary condition. No CEX dependency. No momentum model. No cross-market dependency.

**This repo does not implement arb detection.** Detection is owned by `micro-arb/internal/signal/engine.go` (`sum_arb` strategy). This repo reads its output.

---

## The arb condition

```
long-both entry:  yes_ask + no_ask + total_cost < 1   → buy YES + buy NO
```

Signal detection, risk checks, execution, and fill recording all happen in the Go engine. This repo joins the results.

---

## Architecture

```
../market/micro-arb  (Go engine)
  ├── PmxtBookClient          — live L2 WebSocket from Polymarket CLOB
  ├── signal/engine.go        — sum_arb: YES+NO divergence detection
  ├── risk/, execution/       — risk gates, order submission
  └── persistence/            — writes to Railway Postgres (Supabase)
           │
           ▼ signal_snapshots, risk_decisions, fills
polymarket-cex-backtest  (this repo, Python)
  └── notebooks/              — load → join → compute → visualize
```

---

## Notebooks

| Notebook | What it does | Invariants |
|---|---|---|
| `01_load_signals.ipynb` | Load `signal_snapshots` for sum_arb; verify V1 (spread = YES+NO-1) | V1 |
| `02_join.ipynb` | Join signal→risk→fills on `correlation_id`; check V2 | V2 |
| `03_pnl.ipynb` | Net PnL = `fill_size × |spread| - fill_size × cost_rate` | V4, V7 |
| `04_funnel.ipynb` | Win rate (filled only), capture rate (emitted / all evals) | V3, V5 |
| `05_latency.ipynb` | p50/p95 submit and fill latency from attribution view | V6 |
| `06_drawdown.ipynb` | Equity curve, drawdown, daily PnL time series | V7 |
| `07_rejections.ipynb` | Breakdown by rejection reason; confirms C4 accounting | V5, C4 |

---

## Setup

Requires a `RAILWAY_DATABASE_URL` pointing at the micro-arb Railway Postgres instance.

```bash
# Option 1: env var
export RAILWAY_DATABASE_URL=postgresql://...

# Option 2: .env.railway file at repo root
echo "RAILWAY_DATABASE_URL=postgresql://..." > .env.railway
```

Config values (feeBPS, slippageBPS, spreadThreshold) are loaded from `../market/micro-arb/backtest.config.json` — do not hardcode them in notebooks.

```bash
python3 -m pip install psycopg2-binary pandas matplotlib python-dotenv nbformat
jupyter notebook notebooks/
```

---

## Repo structure

```
notebooks/
  01_load_signals.ipynb   — load + V1 spread check
  02_join.ipynb           — signal→risk→fills join
  03_pnl.ipynb            — net PnL per trade (V4)
  04_funnel.ipynb         — win rate + opportunity funnel
  05_latency.ipynb        — latency p50/p95
  06_drawdown.ipynb       — equity curve + drawdown
  07_rejections.ipynb     — rejection breakdown

src/
  config.py               — load feeBPS/slippageBPS/threshold from backtest.config.json
  db.py                   — Postgres connection via RAILWAY_DATABASE_URL

experimental/
  proxy.py                — old CEX momentum proxy (not in use)
  edge.py                 — old Binance-anchored edge model (not in use)

data/
  pull_polymarket.py      — historical CLOB snapshot pull script
  pull_binance.py         — historical Binance aggTrade pull
  export_signals.py       — CSV export of signals table
```

---

## What this analysis can and cannot prove

| Can prove | Cannot prove |
|---|---|
| Arb condition fired on historical engine data | Real fill at that exact price was available |
| Net PnL after fee+slippage is positive | Fill was not affected by market impact |
| Invariants V1–V9 hold in persisted records | L2 depth was sufficient at signal time (not persisted) |
| Latency is within SLO bounds | Future latency will be the same |

L2 depth is not persisted. Fill simulation against raw depth is not possible from stored events.

---

## License

MIT.
