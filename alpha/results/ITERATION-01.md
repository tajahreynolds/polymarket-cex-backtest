> **Superseded by ITERATION-03-SURVIVORSHIP.md.** The numbers below use a
> hand-picked universe and equal weighting. Correcting both cuts the ensemble
> Sharpe from 0.70 to 0.42. Kept for the cost-sensitivity work, which stands.

# Iteration 1 — backlog swept on the development window

Development window **2005-03 → 2012-12** (GFC included). Holdout 2013-01 → 2017-11
is untouched. Costs 5bps one-way unless stated. 52-ETF multi-asset universe.

## Benchmarks
| | CAGR | Vol | Sharpe | MaxDD |
|---|---|---|---|---|
| SPY | 2.68% | 22.3% | 0.15 | -56.5% |
| QQQ | 7.97% | 23.0% | 0.37 | -53.4% |
| 60/40 | 2.91% | 13.0% | 0.15 | -38.5% |

## Results
| Strategy | CAGR | Vol | Sharpe | MaxDD | Turn/yr | α vs SPY (t) |
|---|---|---|---|---|---|---|
| Faber TAA (10m SMA, 5 assets) | 4.67% | 9.3% | 0.35 | -15.8% | 1.4 | 2.5% (0.9) |
| Dual momentum | 5.57% | 15.8% | 0.31 | -27.5% | 1.9 | 3.7% (0.8) |
| **XS-momentum top8** | 11.09% | 18.2% | **0.57** | -24.1% | 7.4 | 9.2% (1.6) |
| TSMOM + YZ vol target 12% | 4.19% | 8.8% | 0.31 | -18.3% | 4.3 | 2.2% (0.8) |
| Vol-managed QQQ 15% | 8.47% | 15.6% | 0.49 | -31.8% | 1.4 | 5.8% (1.6) |
| **Liquidity provision (capitulation)** | 10.08% | 15.7% | **0.58** | -25.7% | 44.3 | 7.9% (1.6) |
| Reversal, no capitulation gate | 9.03% | 24.2% | 0.41 | -50.3% | 78.1 | 6.9% (1.3) |
| **50 XS-mom / 50 liquidity** | 11.08% | 13.9% | **0.70** | **-19.6%** | 26.2 | 8.5% (**2.10**) |

Sleeve correlations on the development window: XS-mom ↔ liquidity **0.35**, which is
where the ensemble's Sharpe gain comes from — neither sleeve alone exceeds 0.58.

## The finding that constrains everything else

Cost sensitivity, development Sharpe:

| sleeve | 2bps | 5bps | 10bps | 20bps | 40bps |
|---|---|---|---|---|---|
| XS-momentum | 0.59 | 0.57 | 0.55 | 0.51 | 0.43 |
| Vol-managed | 0.49 | 0.49 | 0.48 | 0.47 | 0.46 |
| TSMOM | 0.33 | 0.31 | 0.29 | 0.24 | 0.14 |
| **Liquidity provision** | 0.67 | 0.58 | **0.44** | **0.16** | -0.40 |

And the edge will not be held longer to pay for itself. Using Jegadeesh-Titman
overlapping tranches to cut turnover destroys it outright:

| hold periods | turnover/yr | Sharpe @10bps |
|---|---|---|
| 1 week | 44.3 | 0.44 |
| 2 weeks | 23.0 | 0.12 |
| 4 weeks | 12.0 | -0.18 |
| 8 weeks | 6.2 | 0.03 |

So the capitulation-reversal premium is real but decays inside a week: it is a
capacity-limited, execution-sensitive satellite, not a backbone. Any headline
number that leans on it at 5bps is quoting the friendliest assumption.

## Carried into iteration 2
1. Backbone = cross-sectional momentum (cost-robust: 0.55 at 10bps), not reversal.
2. Cut the liquidity sleeve's *trade count* rather than its horizon — fire only on
   extreme capitulation and only when index vol is elevated (Nagel 2012: the
   reversal payoff scales with volatility), so fewer, higher-conviction trades.
3. Walk-forward the momentum parameters instead of fixing top_k=8 by inspection.
4. Configurations tried so far: 22 — tracked for the deflated Sharpe at the end.
