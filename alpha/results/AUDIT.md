# Backtest audit

Verdict: **the engine is sound.** 18 tests pass, including a lookahead probe that
is demonstrably able to catch a leak. The remaining weaknesses are in the *data*,
not the mechanics, and are listed at the bottom.

## The test that carries the weight

`test_future_data_cannot_change_the_past` corrupts every bar after a cut date —
multiplying OHLC and volume by uniform noise in [0.5, 2.0] — reruns the whole
pipeline, and asserts the equity curve *before* the cut is identical to 1e-12.
Reading code cannot prove the absence of lookahead; this can.

Two things make it trustworthy rather than decorative:

**It is swept across five cut dates.** The first version used one cut, placed on
a month-end. A strategy peeking 21 days ahead passed it — because the last
rebalance before that cut was exactly 21 trading days earlier, so the leak
reached only clean bars. A single cut has a blind spot one leak-horizon wide.

**It has controls.** `test_a_signal_that_peeks_is_detected_by_that_same_test`
runs deliberately leaky oracles at 5-, 21- and 252-day horizons and asserts each
one **fails**. A perturbation test that nothing fails proves nothing.

All seven strategies pass: cross-sectional momentum, liquidity provision, TSMOM,
Faber, vol-managed, and both SMC variants.

## Other checks

| Test | What it pins down |
|---|---|
| `buy_and_hold_matches_hand_computed_return` | fill is next open, mark is last close, to 1e-9 |
| `all_cash_compounds_at_the_short_rate` | cash accrual exact |
| `costs_scale_linearly_with_the_spread` | doubling the spread doubles the drag (to 1%; not exact because heavier drag lowers the equity path and so the dollar turnover it generates) |
| `gross_exposure_never_exceeds_the_cap` | no accidental leverage |
| `holdings_drift_instead_of_silently_rebalancing` | no free continuous rebalancing — SPY/TLT weights diverge, turnover after entry is 0 |
| `execution_is_at_the_next_open_not_the_signal_close` | no position exists on the decision day |
| `perfect_foresight_makes_money_and_random_signals_do_not` | sanity bounds at both ends |
| `swing_points_are_not_visible_before_they_are_confirmed` | SMC-specific, see below |

## Two real defects found and fixed

**Same-day volume peek.** The engine gated execution on `tradable[i]`, which
needs day *i*'s volume — not knowable when placing an order at day *i*'s open. It
now gates on `tradable[i-1]`. Only 2 bars in the whole panel were affected and no
reported number changed, but it was a genuine peek.

**Swing points readable before confirmation.** A fractal swing high needs *k*
bars on each side, so it cannot be drawn until *k* bars later. A centred rolling
window read at the pivot bar is the standard way an SMC backtest lies to itself.
`swing_points` stamps each swing at its confirming bar via `.shift(k)`, and there
is a test that walks 200 actual SPY pivots to prove the level is not readable
early. (One caveat the test itself surfaced: when two adjacent bars share an
identical high, the level genuinely was on the chart a bar earlier — those are
skipped rather than counted as leaks.)

## What the tests do NOT cover — the honest caveats

1. **Universe selection bias — the biggest one.** The 52 tickers were chosen in
   2026 knowing which ETFs survived and grew large. No ETF that delisted before
   2017 is in the panel. This flatters cross-sectional momentum most of all. No
   test catches this; only a wider, point-in-time universe fixes it, which is the
   next piece of work.
2. **Data ends 2017-11.** No evidence from the 2018-2026 regime, which is exactly
   where this strategy family struggled.
3. **Month-end inference.** Rebalance dates are inferred from the realised
   calendar. Exchange holidays are published years ahead so a live trader does
   know them, and only 1 of 154 month-ends falls more than 3 days before the
   calendar month end. Negligible, but it is an assumption.
4. **Dividend back-adjustment.** Signals run on adjusted prices, so a moving
   average computed today differs slightly from the one a trader saw live when a
   dividend falls inside the window. Standard practice, small, not zero.
