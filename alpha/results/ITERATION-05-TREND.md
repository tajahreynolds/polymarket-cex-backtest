# Iteration 5 — trend following in the institutional shape

Prompted by the question of how institutions actually make money on breakouts.
The honest answer is breadth, risk sizing and low turnover rather than good
entries — so that is what got built and tested.

## Long-only trend fails; long/short works

| | CAGR | Vol | Sharpe | MaxDD | Turn/yr | α (t) |
|---|---|---|---|---|---|---|
| SPY | 2.10% | 23.5% | 0.14 | -56.5% | 0.2 | — |
| QQQ | 7.48% | 24.1% | 0.36 | -53.4% | 0.2 | 5.5% (1.50) |
| Div-trend long-only | 2.79% | 11.9% | 0.17 | -19.1% | 7.4 | 2.0% (0.43) |
| **Div-trend long/short** | **6.98%** | 11.4% | **0.52** | **-17.3%** | **7.6** | 6.2% (1.45) |
| Sleeves ensemble (iteration 3) | 5.26% | 9.9% | 0.42 | -12.8% | 21.5 | 3.8% (1.03) |

The short leg is not optional — it triples the Sharpe. A long-only trend book on
a correlated equity universe is a market-timing overlay on beta, nothing more.

This is the best risk-adjusted result in the project so far, and unlike the
liquidity sleeve it runs at **7.6x turnover instead of 40x**, which is what makes
a strategy financeable.

## The universe cannot support this approach, and that is measurable

At the >$50M/day floor only 20 ETFs are continuously eligible across the window:

```
mean pairwise correlation:                0.621
first eigenvalue as share of variance:    75.1%
top-5 eigenvalues:                         91.1%
effective independent bets:                 1.7
```

One factor explains three quarters of the variance. Seventy-odd ETFs with 0.62
average correlation are not seventy bets, they are **1.7**. Grinold's law
(IR ≈ IC·√breadth) puts the ceiling at roughly 0.2 even with a good IC.

Getting 0.52 out of a 1.7-bet universe is *above* the breadth budget. That is
either genuine crisis alpha — trend's payoff is non-linear and Grinold does not
describe it well — or it is overfitting. The next section is the attempt to tell
which.

## Where the return came from

| year | strategy | SPY |
|---|---|---|
| 2006 | +5.02% | +9.83% |
| 2007 | +12.73% | +3.24% |
| **2008** | **+20.83%** | **-38.30%** |
| 2009 | +6.06% | +23.49% |
| 2010 | -5.82% | +12.89% |
| 2011 | +9.87% | +1.87% |
| 2012 | +0.99% | +16.01% |

2008 contributed +20.8% of a +58.6% total. Sharpe excluding 2008 falls from
**0.52 to 0.37** — so it is not only 2008, but a third of the growth is one year.
This is the documented crisis-alpha signature of trend following, not an anomaly.

## Robustness: passes what should not matter, fails what should not either

| variant | Sharpe | CAGR | turn/yr |
|---|---|---|---|
| baseline (21/63/126/252, monthly, 12% target) | 0.52 | 6.98% | 7.6 |
| lookbacks 63/126/252 | 0.49 | 6.57% | 5.7 |
| lookbacks 21/63 | 0.50 | 6.99% | 10.8 |
| vol window 20 instead of 60 | 0.52 | 7.00% | 7.8 |
| vol target 8% | 0.53 | 5.66% | 6.4 |
| no-trade band 2% | 0.45 | 5.21% | 4.0 |
| **no-trade band 5%** | **0.11** | 1.91% | 2.1 |
| **weekly rebalance** | **0.17** | 2.80% | 19.4 |

Good news: it is insensitive to lookback choice, vol window and vol target —
exactly what the literature predicts, since Moskowitz-Ooi-Pedersen found 1- to
12-month lookbacks all work about equally.

Bad news: weekly rebalancing collapses it to 0.17, and a 5% no-trade band to
0.11. Costs do not explain either — 19.4x turnover at 5bps is about 1% of drag,
nowhere near the 0.35 of Sharpe that goes missing. A trend premium should not
care this much about *when* you look. That fragility is unexplained and is the
main reason not to believe this yet.

## Status and the pre-registered test

Candidate: long/short diversified trend, monthly, inverse-vol sized to a 12%
target, no band. Sharpe 0.52 vs QQQ's 0.36, CAGR 6.98% vs 7.48%, drawdown -17%
vs -53%, at a turnover low enough to lever.

The 2013-2017 holdout is still untouched. **Prediction, recorded before running
it: this book will underperform over 2013-2017.** That window is a grinding bull
market with no sustained bear leg, which is where trend following has nothing to
short and gets whipsawed. If it holds up there anyway, the 2008 dependence was
not the whole story. If it collapses, the honest read is that this strategy is a
crisis hedge that happens to look like alpha when the sample contains a crisis.

Either outcome is worth knowing, which is what makes it worth spending the
holdout on. Configurations tried to date: roughly 75.
