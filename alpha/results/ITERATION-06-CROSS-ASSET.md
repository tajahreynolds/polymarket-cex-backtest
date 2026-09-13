# Iteration 6 — the candidate dies on the modern regime

The `trading` repo supplied what this environment could not fetch: 27 cross-asset
ETFs with history to **2026-09-11**, including FX and commodities. That fixes the
breadth problem *and* answers the holdout question at once.

## Breadth is genuinely fixed

| panel | mean pairwise corr | first eigenvalue | effective bets |
|---|---|---|---|
| my equity-heavy ETF panel | 0.621 | 75.1% | **1.7** |
| cross-asset panel (FX + commodities added) | 0.203 | 36.6% | **5.4** |

Adding currencies and commodities triples the effective breadth. This is what the
institutional trend book has and my panel did not.

## The pre-registered prediction was right, and understated

Recorded in ITERATION-05 before running: *"this book will underperform over
2013-2017."* Same locked configuration, no retuning, run across three eras:

| era | Trend Sharpe | Trend CAGR | QQQ Sharpe | QQQ CAGR | alpha (t) |
|---|---|---|---|---|---|
| 2007-2012 (development) | **0.67** | 6.11% | 0.35 | 6.71% | 5.98% (1.88) |
| 2013-2017 (predicted holdout) | 0.58 | 2.83% | 1.32 | 19.92% | 1.26% (0.64) |
| **2018-2026 (never seen)** | **0.03** | 2.65% | 0.76 | 19.66% | **0.37% (0.19)** |

Monotonic decay: 0.67 → 0.58 → 0.03. In the modern regime the edge is not
weakened, it is **gone** — alpha of 0.37% at t = 0.19.

The full-period 2007-2026 figures look respectable (Sharpe 0.41, alpha 3.28% at
t = 2.30) and that is exactly the trap: the whole result is the 2007-2012 block.
A backtest that starts before 2008 and ends today will always show trend working,
because one crisis carries it.

## This replicates the other repo independently

`trading/README.md` records, from a separate implementation on a separate
universe:

> Cross-asset trend on 11 ETFs, standalone — Sharpe 0.47 excess of cash, against
> a 0.8 bar. Matches AQR's published 0.45 for the same window.
>
> Restricting trend to its best asset class — No slice survived. All four classes
> degraded after 2007, worst in the last decade.

Two implementations, two universes, two authors: same number, same decay. That is
about as strong as a negative result gets. The iteration-5 candidate is dead, and
the 2008-dependence hypothesis is confirmed rather than merely suspected.

## Status

Nothing in this repository currently beats QQQ out of sample. Configurations
tried: roughly 80. The honest summary of six iterations:

| tested | verdict |
|---|---|
| SMC premium/discount, long | loses at the swing lengths it is taught with |
| SMC premium/discount, short | alpha -7.4%/yr, t = -2.05 |
| Cross-sectional momentum | 0.26 point-in-time, below QQQ |
| Liquidity provision / capitulation | real but 40x turnover, unleverable |
| Core-satellite to deploy idle cash | matches QQQ's return, worse Sharpe |
| Long/short cross-asset trend | 0.67 pre-2013, **0.03 after 2018** |
