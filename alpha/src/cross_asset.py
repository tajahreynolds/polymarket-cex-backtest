"""My iteration-5 candidate, run on the trading repo's cross-asset panel.

Two things change at once, both improvements: genuine breadth (FX and
commodities, not just correlated equity ETFs) and the modern regime through
2026. The 2008-dependence question and the 2013-2017 prediction both get
answered here, on data my own panel never had.
"""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import panel_trading as PT
from engine import run, CostModel
import metrics as M, strategies as ST

P = PT.load(); cal = P["close"].index
rf = PT.rf_from_irx(cal)
CM = CostModel(spread_bps=5, short_borrow_bps=50)
UNI = [t for t in PT.UNIVERSE if t in P["close"].columns]

# 2007 is when the panel first carries all four asset classes
FULL = ("2007-06-01", "2026-09-11")
ERAS = {"2007-2012 (my dev window)": ("2007-06-01", "2012-12-31"),
        "2013-2017 (my holdout)":    ("2013-01-01", "2017-11-10"),
        "2018-2026 (never seen)":    ("2018-01-01", "2026-09-11")}


def hold(t, win):
    tg = pd.DataFrame(0.0, index=[cal[cal >= win[0]][0]], columns=P["close"].columns)
    tg.loc[tg.index[0], t] = 1.0
    return run(P, tg, rf, CM, *win)


def breadth(win):
    m = (cal >= win[0]) & (cal <= win[1])
    R = P["close"].pct_change()[m][UNI].dropna(axis=1, how="any")
    C = R.corr().to_numpy()
    ev = np.linalg.eigvalsh(C)[::-1]; ev = ev[ev > 0]
    return (C[np.triu_indices(len(C), 1)].mean(), ev[0] / ev.sum(),
            ev.sum() ** 2 / (ev ** 2).sum())


if __name__ == "__main__":
    mc, e1, pr = breadth(FULL)
    print(f"=== cross-asset breadth, {len(UNI)} ETFs, {FULL[0]}..{FULL[1]} ===")
    print(f"mean pairwise correlation: {mc:.3f}   first eigenvalue: {e1:.1%}   "
          f"effective bets: {pr:.1f}")
    print("(my own equity-heavy panel: 0.621 / 75.1% / 1.7)\n")

    w = ST.diversified_trend(P, UNI, band=0.0, allow_short=True, vol_target=0.12)
    for label, win in [("FULL " + FULL[0][:4] + "-2026", FULL)] + list(ERAS.items()):
        b = hold("SPY", win); q = hold("QQQ", win)
        res = run(P, w, rf, CM, *win)
        rows = [M.summary(b, rf, b.returns, "SPY"),
                M.summary(q, rf, b.returns, "QQQ"),
                M.summary(res, rf, b.returns, "L/S cross-asset trend")]
        print(f"----- {label} -----")
        print(M.table(rows).to_string())
        print()
