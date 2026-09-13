"""Correctness tests for the backtest engine.

The decisive one is `test_future_data_cannot_change_the_past`: corrupt every bar
after a cut date and assert the equity curve before that date is bit-identical.
No amount of code reading proves absence of lookahead; that test does.
"""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import pytest

from panel import load_panel, rf_daily
from engine import run, CostModel
import strategies as ST
import signals as S

PANEL = load_panel()
CAL = PANEL["close"].index
RF = rf_daily(CAL)
SLEEVE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "LQD", "HYG",
          "GLD", "DBC", "VNQ", "XLU", "XLP", "XLV", "XLK", "XLE", "XLF"]
ZERO = CostModel(spread_bps=0.0, commission_bps=0.0, borrow_spread_bps=0.0)
NORF = pd.Series(0.0, index=CAL)      # isolates price P&L from cash accrual


def _corrupt(cut, seed):
    """Replace every bar after `cut` with noise, leaving earlier bars untouched."""
    rng = np.random.default_rng(seed)
    out = {}
    for k, df in PANEL.items():
        d = df.astype(bool) if k == "tradable" else df.astype(float)
        mask = d.index > cut
        if k == "tradable":
            d.loc[mask] = True
        else:
            d.loc[mask] = d.loc[mask].to_numpy() * rng.uniform(0.5, 2.0, d.loc[mask].shape)
        out[k] = d
    return out


def _oracle(p, horizon=21, rebal="M"):
    """Perfect foresight over `horizon` days - deliberately leaky, used as a control."""
    cal = p["close"].index
    idx = S.month_ends(cal) if rebal == "M" else S.week_ends(cal)
    fwd = (p["close"].shift(-horizon) / p["close"] - 1).reindex(idx)[SLEEVE].dropna(how="all")
    w = pd.DataFrame(0.0, index=idx, columns=p["close"].columns)
    for d, t in fwd.idxmax(axis=1).dropna().items():
        w.loc[d, t] = 1.0
    return w


def _single(ticker, date):
    tg = pd.DataFrame(0.0, index=[pd.Timestamp(date)], columns=PANEL["close"].columns)
    tg.loc[pd.Timestamp(date), ticker] = 1.0
    return tg


# ---------------------------------------------------------------- accounting
def test_buy_and_hold_matches_hand_computed_return():
    """Decide at the first close, fill at the next open, mark at the last close."""
    start, end = "2006-01-03", "2012-12-31"
    cal = CAL[(CAL >= start) & (CAL <= end)]
    d0 = cal[0]
    res = run(PANEL, _single("SPY", d0), NORF, ZERO, start, end)
    entry = PANEL["open"].loc[cal[1], "SPY"]
    exit_ = PANEL["close"].loc[cal[-1], "SPY"]
    assert res.equity.iloc[-1] == pytest.approx(exit_ / entry, rel=1e-9)


def test_all_cash_compounds_at_the_short_rate():
    start, end = "2006-01-03", "2012-12-31"
    empty = pd.DataFrame(0.0, index=[pd.Timestamp(start)], columns=PANEL["close"].columns)
    res = run(PANEL, empty, RF, ZERO, start, end)
    cal = res.equity.index
    expected = (1 + RF.reindex(cal).fillna(0.0).iloc[1:]).prod()
    assert res.equity.iloc[-1] == pytest.approx(expected, rel=1e-9)


def test_costs_scale_linearly_with_the_spread():
    w = ST.xsmom(PANEL, top_k=8)
    a = run(PANEL, w, RF, CostModel(spread_bps=10), "2006-01-03", "2012-12-31")
    b = run(PANEL, w, RF, CostModel(spread_bps=20), "2006-01-03", "2012-12-31")
    # not exactly 2x: the heavier drag lowers the equity path, which lowers the
    # dollar turnover it subsequently generates. Linear to within a percent.
    assert b.costs.sum() == pytest.approx(2 * a.costs.sum(), rel=1e-2)
    assert a.turnover.sum() == pytest.approx(b.turnover.sum(), rel=1e-3)


def test_gross_exposure_never_exceeds_the_cap():
    w = ST.tsmom_voltarget(PANEL, SLEEVE, vol_target=0.30, max_gross=1.0)
    res = run(PANEL, w, RF, ZERO, "2006-01-03", "2012-12-31", max_gross=1.0)
    assert res.weights.abs().sum(axis=1).max() <= 1.0 + 1e-6


def test_holdings_drift_instead_of_silently_rebalancing():
    """Two assets bought equal-weight and left alone must diverge in weight."""
    d0 = CAL[CAL >= "2006-01-03"][0]
    tg = pd.DataFrame(0.0, index=[d0], columns=PANEL["close"].columns)
    tg.loc[d0, ["SPY", "TLT"]] = 0.5
    res = run(PANEL, tg, RF, ZERO, "2006-01-03", "2012-12-31")
    spread = (res.weights["SPY"] - res.weights["TLT"]).abs()
    assert spread.iloc[-1] > 0.05, "weights did not drift — engine is re-balancing for free"
    assert res.turnover.iloc[2:].sum() == pytest.approx(0.0, abs=1e-9)


# ------------------------------------------------------------------ lookahead
# A leak of horizon h placed within h days of the cut is invisible to any single
# cut date, so the cut is swept. Mid-month cuts matter: a month-end-only sweep
# sits exactly one rebalance away from a one-month leak and sees nothing.
CUTS = [pd.Timestamp(d) for d in
        ("2008-03-14", "2009-07-09", "2010-06-30", "2010-11-17", "2011-09-06")]


@pytest.mark.parametrize("builder", [
    pytest.param(lambda p: ST.xsmom(p, top_k=8), id="xsmom"),
    pytest.param(lambda p: ST.liquidity_provision(p, SLEEVE), id="liquidity"),
    pytest.param(lambda p: ST.tsmom_voltarget(p, SLEEVE, vol_target=0.12), id="tsmom"),
    pytest.param(lambda p: ST.faber_taa(p), id="faber"),
    pytest.param(lambda p: ST.vol_managed(p, "QQQ", 0.15), id="volmanaged"),
    pytest.param(lambda p: ST.smc_premium_discount(p, SLEEVE), id="smc"),
    pytest.param(lambda p: ST.smc_single(p, "SPY"), id="smc_single"),
])
def test_future_data_cannot_change_the_past(builder):
    """Corrupt every bar after the cut; the equity curve up to it must not move."""
    for i, cut in enumerate(CUTS):
        corrupt = _corrupt(cut, i)
        a = run(PANEL, builder(PANEL), NORF, ZERO, "2006-01-03", "2012-12-31")
        b = run(corrupt, builder(corrupt), NORF, ZERO, "2006-01-03", "2012-12-31")
        ea, eb = a.equity[a.equity.index <= cut], b.equity[b.equity.index <= cut]
        pd.testing.assert_series_equal(ea, eb, check_exact=False, rtol=1e-12,
                                       obj=f"equity before {cut.date()}")


@pytest.mark.parametrize("horizon,rebal", [(21, "M"), (5, "W"), (252, "M")])
def test_a_signal_that_peeks_is_detected_by_that_same_test(horizon, rebal):
    """Control: leaky strategies at three different horizons must FAIL the
    perturbation test on at least one cut, otherwise it proves nothing."""
    caught = 0
    for i, cut in enumerate(CUTS):
        corrupt = _corrupt(cut, i)
        a = run(PANEL, _oracle(PANEL, horizon, rebal), NORF, ZERO, "2006-01-03", "2012-12-31")
        b = run(corrupt, _oracle(corrupt, horizon, rebal), NORF, ZERO, "2006-01-03", "2012-12-31")
        ea, eb = a.equity[a.equity.index <= cut], b.equity[b.equity.index <= cut]
        caught += not np.allclose(ea.values, eb.values)
    assert caught >= 1, (
        f"a strategy reading {horizon} days ahead went undetected at every cut - "
        "the perturbation test is not sensitive enough to trust")


def test_perfect_foresight_makes_money_and_random_signals_do_not():
    """Sanity bounds: an oracle should crush the benchmark; coin flips should
    land near cash minus costs."""
    o = run(PANEL, _oracle(PANEL), NORF, ZERO, "2006-01-03", "2012-12-31")
    assert o.equity.iloc[-1] > 20.0

    idx = S.month_ends(CAL)
    rng = np.random.default_rng(7)
    noise = pd.DataFrame(0.0, index=idx, columns=PANEL["close"].columns)
    for d in idx:
        noise.loc[d, rng.choice(SLEEVE, 5, replace=False)] = 0.2
    n = run(PANEL, noise, NORF, ZERO, "2006-01-03", "2012-12-31")
    ann = n.equity.iloc[-1] ** (252 / len(n.equity)) - 1
    assert -0.05 < ann < 0.20


def test_execution_is_at_the_next_open_not_the_signal_close():
    """Same-close execution would capture the signal day's open-to-close move;
    the engine must not."""
    d0 = CAL[CAL >= "2006-01-03"][0]
    res = run(PANEL, _single("SPY", d0), NORF, ZERO, "2006-01-03", "2012-12-31")
    cal = res.equity.index
    assert res.weights.loc[cal[0], "SPY"] == 0.0, "position existed on the decision day"
    assert res.weights.loc[cal[1], "SPY"] > 0.99
    same_close = PANEL["close"].loc[cal[-1], "SPY"] / PANEL["close"].loc[cal[0], "SPY"]
    assert abs(res.equity.iloc[-1] - same_close) > 1e-6


def test_swing_points_are_not_visible_before_they_are_confirmed():
    """A swing high at bar t needs k bars after it. Reading it at bar t is the
    classic SMC backtest error; assert the series cannot do that."""
    k = 5
    sh, sl = S.swing_points(PANEL, k)
    h, l = PANEL["high"]["SPY"], PANEL["low"]["SPY"]
    win = 2 * k + 1
    peaks = h.index[(h == h.rolling(win, center=True).max()) & h.notna()]
    checked = 0
    for t in peaks[50:250]:
        i = h.index.get_loc(t)
        if i + k >= len(h.index):
            continue
        if (h.iloc[max(0, i - k):i] == h.iloc[i]).any():
            continue          # an identical earlier high: the level was already on the chart
        before = sh["SPY"].iloc[i + k - 1]
        at_confirm = sh["SPY"].iloc[i + k]
        if pd.notna(at_confirm) and at_confirm == pytest.approx(h.iloc[i]):
            assert before != pytest.approx(h.iloc[i]), (
                f"swing high of {t.date()} was already readable {k} bars early")
            checked += 1
    assert checked > 10, "test did not actually exercise any confirmed swings"
