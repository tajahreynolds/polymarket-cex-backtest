# Iteration 4 — the bearish leg, and the idle cash

Two questions, both tested directly. Point-in-time universe (>$50M/day), inverse-vol
sizing, 2006-03 → 2012-12, 5bps one-way, 50bp annual stock-loan fee on shorts.

## 1. Why not take the bearish trade at premium?

Fair challenge — the earlier note tested only the long leg, which is half the
framework. The short leg is now implemented and charged a borrow fee. It is the
worst part of the concept:

| | CAGR | Vol | Sharpe | MaxDD | α (t) |
|---|---|---|---|---|---|
| SMC k=5 long | -1.70% | 11.1% | -0.23 | -23.0% | -3.0% (-0.72) |
| SMC k=5 short | -3.40% | 10.4% | -0.43 | -39.6% | -4.1% (-1.05) |
| SMC k=10 long | -1.26% | 11.5% | -0.18 | -23.2% | -2.5% (-0.57) |
| **SMC k=10 short** | -6.53% | 9.8% | **-0.79** | -40.2% | **-7.4% (-2.05)** |
| SMC k=20 long | 2.82% | 11.2% | 0.17 | -19.8% | 1.5% (0.37) |
| SMC k=20 short | -4.71% | 9.4% | -0.62 | -32.9% | -5.6% (-1.58) |

The short leg is negative at every swing length, and at k=10 its alpha is
**-7.4% a year with t = -2.05** — significantly negative, not merely absent.
Combining both legs is worse than the long leg alone at every k.

The raw conditional says why. In bearish structure, mean forward 21-day returns:

```
in premium  (the prescribed short entry):  +0.068%   -> a short earns -0.068%
in discount:                               -0.660%   -> a short earns +0.660%
```

In this panel the profitable short during a downtrend was in **discount** — that
is, selling breakdowns as they continue lower — not in premium. The premium zone
in a downtrend is where price bounces, and shorting into it paid nothing.

The framework's rule is backwards here, not just weak. This is the evidence that
an earlier draft of ITERATION-02 gestured at and then withdrew for lack of a
direct test. The direct test now exists and it points the same way.

## 2. Can the 55% idle cash be put to work to beat QQQ?

Directionally yes on return, no on risk-adjusted return. Routing whatever gross
the sleeves are not using into a core:

| | CAGR | Vol | Sharpe | MaxDD | Calmar | cost drag |
|---|---|---|---|---|---|---|
| QQQ | 7.48% | 24.1% | 0.36 | -53.4% | 0.14 | 0.01% |
| Sleeves only (55% cash) | 5.26% | 9.9% | **0.42** | **-12.8%** | **0.41** | 1.08% |
| Core-satellite, QQQ core | **7.40%** | 20.1% | 0.38 | -39.2% | 0.19 | 1.55% |
| Core-satellite, trend core | 6.33% | 16.0% | 0.37 | -27.3% | 0.23 | 1.56% |
| Sleeves levered 2.4x to QQQ vol | 5.96% | 24.1% | 0.30 | -30.5% | 0.20 | **2.63%** |

Filling the cash closes the CAGR gap almost exactly — 7.40% against QQQ's 7.48%,
with a drawdown of -39% instead of -53%. As a *product* that is defensible.
As *outperformance* it is not: Sharpe goes the wrong way, 0.42 → 0.38.

The reason is structural. A core is beta, not alpha. Adding beta to an alpha book
raises return and risk together, so it can improve absolute return but not
risk-adjusted return. To beat QQQ on a risk-adjusted basis the book needs more
alpha or less cost — not more exposure.

And the leverage route is shut by costs, which is the more important finding.
Levering the sleeves 2.4x to match QQQ's volatility *lowers* CAGR to 5.96% and
Sharpe to 0.30, because leverage scales the turnover drag with it: 1.08% becomes
**2.63% a year**. A 21x-turnover book cannot be levered into outperformance.

## What this implies for the next iteration

The binding constraint is turnover, not signal. The liquidity sleeve runs 37-50x
a year and carries most of the cost drag. Either:

1. find an edge of similar strength at a fraction of the turnover, so leverage
   becomes viable; or
2. accept this as a low-drawdown, QQQ-return book and stop calling it alpha.

Configurations tried to date: roughly 60. Nothing has yet earned a walk-forward
run, let alone the 2013-2017 holdout.
