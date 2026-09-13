# Iteration 3 — survivorship and universe selection

**Headline: iteration 1's result was inflated, and I do not yet have a strategy
that convincingly beats the top ETFs.** Details below.

## The dataset contains zero dead ETFs

All 1,344 files in the mirror end in Oct/Nov 2017. Not one stops earlier. The
vendor snapshot contains only funds alive on the last day, so every ETF that
closed between 2005 and 2017 — and there were hundreds — is simply absent. That
cannot be fixed from this data source.

Two separate biases were tangled together, and only one is fixable here:

1. **My selection bias** — I chose 52 tickers in 2026 knowing which ETFs grew
   large. Fixable: screen the full 1,320-ETF panel point-in-time instead.
2. **The vendor's survivorship bias** — no dead funds exist in the file set.
   Not fixable, but boundable (see below).

## Fixing my selection bias exposed a second bug

Running the momentum sleeve on the full universe produced 45% volatility, an
-88% drawdown and a *negative* beta. The cause was not survivorship: the broad
universe contains leveraged and inverse ETFs, and the strategy loaded into TNA
(91% vol), URE (85%), SPXL (68%), QLD, AGQ, SKF and SDS.

Equal-weighting is meaningless across a universe of mixed leverage — a 3x fund
gets three times the exposure of its own underlying, and an inverse fund flips
the book's sign. My hand-picked 52 were all 1x, so equal-weighting had been
*accidentally* risk-controlled the whole time. Broadening the universe removed
that accident and revealed the flaw.

The fix is the principled one rather than deleting the awkward tickers: size
positions by inverse Yang-Zhang volatility and scale the book to a target
portfolio vol. A 3x fund then earns a third of the weight and the leverage in the
wrapper stops mattering.

## One change at a time (2006-03 → 2012-12, 5bps, common window)

| | CAGR | Vol | Sharpe | MaxDD | α (t) |
|---|---|---|---|---|---|
| SPY | 2.10% | 23.5% | 0.14 | -56.5% | — |
| QQQ | 7.48% | 24.1% | 0.36 | -53.4% | 5.5% (1.50) |
| Liq-prov, hand-picked + equal weight | 9.59% | 16.3% | **0.55** | -25.7% | 7.9% (1.45) |
| Liq-prov, hand-picked + inverse-vol | 6.06% | 9.8% | 0.50 | -19.6% | 4.2% (1.28) |
| Liq-prov, point-in-time + inverse-vol | 4.76% | 11.4% | **0.33** | -20.6% | 3.3% (0.79) |
| XS-mom, hand-picked + equal weight | 5.47% | 14.0% | 0.34 | -24.2% | 3.9% (0.82) |
| XS-mom, point-in-time + inverse-vol | 4.21% | 13.7% | 0.26 | -18.9% | 3.5% (0.67) |
| **Ensemble, point-in-time** | 5.26% | 9.9% | **0.42** | **-12.8%** | 3.8% (1.03) |

Hand-picking the universe was worth about **0.17 of Sharpe** on the liquidity
sleeve — roughly a third of its apparent edge — and about 0.07 on momentum. The
sizing change costs another 0.05. Iteration 1's ensemble Sharpe of 0.70 becomes
**0.42** once both are corrected.

## Survivorship bias is *not* what drives the surviving edge

This is the one genuinely reassuring result. Funds that close are overwhelmingly
thin ones, so if the edge came from the missing dead funds it would weaken as the
liquidity floor rises. It does the opposite:

| point-in-time floor | names available | Liq-prov Sharpe | turnover/yr |
|---|---|---|---|
| >$1M/day | 324 | 0.31 | 53.7 |
| >$10M/day | 151 | 0.29 | 48.8 |
| >$50M/day | 77 | 0.33 | 36.6 |
| >$200M/day | 32 | **0.37** | 27.3 |

The sleeve is *strongest* among the most liquid names, where an ETF essentially
never closes within the year, and turnover halves there too. Whatever is left is
not an artifact of the absent dead funds.

## Honest verdict

The point-in-time ensemble beats QQQ on Sharpe (0.42 vs 0.36), on drawdown
(-12.8% vs -53.4%) and on Calmar (0.41 vs 0.14) — but **loses on CAGR** (5.26%
vs 7.48%) and sits 55% in cash. Its alpha t-stat is 1.03, which is not
statistically established, over a window of under seven years, after roughly 40
configurations tried.

That is not a strategy that outperforms the top ETFs. It is a low-risk book with
a plausible but unproven tilt. Claiming otherwise would mean quoting iteration 1's
number and ignoring what this iteration found.

## Next
1. Compare at **equal volatility** — the current book runs at 10% vol against
   QQQ's 24%, so a CAGR comparison is not like-for-like. Lever to matched vol,
   pay real borrow, and see whether the absolute gap survives.
2. Walk-forward the parameters rather than fixing them by inspection.
3. Only then touch the 2013-2017 holdout, once.
