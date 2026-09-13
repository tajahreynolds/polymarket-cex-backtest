# Iteration 7 — two effects neither repo had tried

Both pre-specified from the literature rather than mined, and both structurally
unlike the price-pattern ideas in either graveyard. Both fail.

## Overnight vs intraday

The statistic is real and survives into the present. Annualised, by era:

| | 1993-2007 | 2007-2012 | 2013-2017 | 2018-2026 |
|---|---|---|---|---|
| SPY overnight | 12.75% (t 5.7) | 4.78% | 6.92% (t 2.0) | 10.69% (t 2.6) |
| SPY intraday | -0.80% | -0.87% | 7.98% | 4.74% |
| QQQ overnight | 19.08% (t 3.3) | 8.30% | 13.01% (t 3.1) | 13.46% (t 2.7) |
| QQQ intraday | **-13.33%** | 1.35% | 6.89% | 7.56% |

QQQ from 1993-2007 is the striking one: buy-and-hold returned -0.69% while the
overnight session returned +19.08% and the day destroyed -13.33%. Holding QQQ
only overnight over that window beat holding it outright by twenty points a year.

As a strategy it is dead, because it needs a round trip every session — 252 a
year. Breakeven cost per round trip:

| | SPY | QQQ | IWM |
|---|---|---|---|
| 1993-2007 | 5.1bp | **7.6bp** | 6.6bp |
| 2013-2017 | 2.7bp | 5.2bp | 2.9bp |
| 2018-2026 | 4.2bp | 5.3bp | 6.6bp |

Even at a generous 1bp all-in through the closing and opening auctions, QQQ
overnight returns 10.37% at Sharpe 0.6 over 2018-2026 against buy-and-hold's
19.97% at Sharpe 0.77. The anomaly also decayed in the way that matters: pre-2007
the overnight session was *larger than the whole day's return*; since 2018 it is
smaller. Worse than buy-and-hold on both axes, now.

## Turn of the month

Chosen for turnover — 12 round trips a year against the overnight trade's 252,
which is the profile that could actually be levered. The effect is visible in the
raw data:

```
SPY, mean return by position in the trading month
  first day of month  +22bp        all-day average  +5bp
  fourth-last day     +14bp
```

But it never beats buy-and-hold, in any era, for any of the four ETFs tested:

| | TOM ann (t) | rest-of-month ann | strategy @2bp | B&H CAGR |
|---|---|---|---|---|
| SPY 2018-2026 | 20.20% (1.4) | 14.33% | 5.34% (Sh 0.36) | 14.61% (Sh 0.67) |
| QQQ 2018-2026 | 30.78% (1.7) | 18.74% | 7.27% (Sh 0.48) | 19.97% (Sh 0.77) |
| SPY 2013-2017 | 5.62% (0.5) | **17.10%** | 0.65% | 15.23% |
| IWM 2013-2017 | -5.30% | 18.52% | -1.55% | 13.57% |

It inverts entirely over 2013-2017 — the rest of the month beat the turn of the
month on every ETF. No t-statistic anywhere reaches 2.6 except SPY's in the
pre-2007 window. Levering QQQ's best case 3x to match QQQ's volatility still
lands under buy-and-hold, and at a lower Sharpe.

## The pattern across ~85 configurations

Every publicly documented effect tested in this repo and in `trading` — price
patterns, momentum, reversal, trend, zones, calendar, session microstructure —
is either absent or has decayed to nothing in liquid US ETFs since roughly 2010.
That is not bad luck. It is the expected outcome for effects that have been in
print for twenty to forty years in the most heavily arbitraged instruments in the
world.

The one thing that keeps half-working, in both repos independently, is combining
weakly-correlated sleeves — which raises Sharpe by cutting drawdown, not by
adding return, and therefore cannot close a CAGR gap to QQQ.
