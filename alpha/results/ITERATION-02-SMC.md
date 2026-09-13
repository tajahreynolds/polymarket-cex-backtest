# Iteration 2 — smart-money premium/discount

Tested as specified: swing highs and lows confirmed *k* bars after the pivot, a
dealing range drawn between the last confirmed swing high and low, equilibrium at
50%, long only in the discount half while structure is bullish (price has taken
out the last confirmed swing high). Development window, 5bps, same 18-ETF sleeve.

## It does not work

| Variant | CAGR | Sharpe | MaxDD | Turn/yr | α vs SPY (t) |
|---|---|---|---|---|---|
| SPY | 2.68% | 0.15 | -56.5% | 0.1 | — |
| QQQ | 7.97% | 0.37 | -53.4% | 0.1 | 5.4% (1.6) |
| SMC k=5, discount ≤0.382 | -5.26% | **-0.41** | -52.2% | 48.9 | -6.8% (-1.4) |
| SMC k=5, discount ≤0.5 | -3.60% | -0.26 | -44.2% | 57.1 | -5.1% (-1.0) |
| SMC k=10, discount ≤0.382 | -0.05% | -0.05 | -40.7% | 39.6 | -1.7% (-0.4) |
| SMC k=20, discount ≤0.5 | 7.05% | 0.41 | -44.1% | 31.8 | 5.4% (1.1) |
| SMC single SPY | 4.35% | 0.49 | -10.3% | 5.9 | 2.5% (1.3) |
| XS-momentum (incumbent) | 11.09% | 0.57 | -24.1% | 7.4 | 9.2% (1.6) |

At the swing lengths the concept is actually taught with (k=5, k=10) it loses
money outright. It turns positive only at k=20, and that variant correlates
**0.72** with its own structure filter run alone — it is a slow trend filter
wearing SMC clothes, and it still loses to the momentum sleeve on every metric
while turning over 4x as hard.

The single-asset versions post a respectable-looking Sharpe of 0.49, but they sit
**92% in cash**. That is a T-bill portfolio with an equity sliver attached; a
static 25% SPY / 75% bills would do the same thing without 6x annual turnover.

## Why the conditional table is a trap

Pooling all 18 ETFs by dealing-range bucket makes the concept look right — in
bullish structure, forward 21-day returns are 1.07% in deep discount versus 0.55%
in deep premium. That table is what a chart-based writeup would stop at.

It does not survive the correlation. The 18 ETFs move together, so pooled
observations are nowhere near independent. Averaging the discount-minus-premium
spread **per date** first, then applying Newey-West with 21 lags for the
overlapping windows:

```
mean 21d spread:            -0.098%      (negative, not positive)
naive t-stat:                -0.64
Newey-West t-stat:           -0.27
dates: 1000, distinct months: 88
```

The spread flips sign and the t-stat is nowhere. The pooled result was an
artifact of wildly unequal cell counts — bullish+premium has 21,990 observations,
bullish+discount has 1,078 — combined with cross-sectional correlation.

**Correction to an earlier draft of this note.** It claimed the bearish row was a
sign problem, on the grounds that returns are higher in premium (1.23%) than in
discount (0.61%). That was a misreading of the framework. In a downtrend,
"discount" means catching a falling knife, so premium outperforming discount on
the bearish side is the expected shape, not a contradiction. The critique is
withdrawn; it was never load-bearing.

What the result rests on is the bullish+discount cell alone — the one the concept
actually says to trade — and that is where the clustering test above kills it.

## Conclusion

Dropped. The mechanism is not indefensible — "buy pullbacks in an uptrend" is
momentum with a worse entry rule — but the premium/discount overlay adds turnover
and subtracts return, and the effect it claims is not statistically present in
this panel. No configuration of it beats the incumbent momentum sleeve.
