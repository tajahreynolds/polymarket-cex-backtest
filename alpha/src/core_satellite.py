"""Does routing the sleeves' idle cash into a core close the gap to QQQ?"""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from panel import load_wide, eligible, rf_daily
from engine import run, CostModel
import metrics as M, strategies as ST

W = load_wide(); cal = W["close"].index; rf = rf_daily(cal)
CM = CostModel(spread_bps=5)
WIN = ("2006-03-01", "2012-12-31")
p = dict(W); p["tradable"] = eligible(W, min_dollar_vol=50e6)
uni = list(W["close"].columns)


def hold(t):
    tg = pd.DataFrame(0.0, index=[cal[cal >= WIN[0]][0]], columns=W["close"].columns)
    tg.loc[tg.index[0], t] = 1.0
    return run(W, tg, rf, CM, *WIN)


def lever_to(res, target_vol, b):
    """Scale the strategy's excess return to a target vol and re-report, paying
    the short rate plus a 50bp financing spread on the borrowed part."""
    r = res.returns
    rfr = rf.reindex(r.index).fillna(0.0)
    ex = r - rfr
    k = target_vol / (r.std() * np.sqrt(252))
    fin = max(k - 1.0, 0.0) * (rfr + 50 / 1e4 / 252)
    lev = rfr + k * ex - fin
    eq = (1 + lev).cumprod()

    class R: pass
    o = R(); o.equity = eq; o.returns = lev
    o.turnover = res.turnover * k; o.costs = res.costs * k; o.cash = res.cash
    return o, k


if __name__ == "__main__":
    b = hold("SPY")
    qqq = hold("QQQ")
    qvol = qqq.returns.std() * np.sqrt(252)
    rows = [M.summary(b, rf, b.returns, "SPY"), M.summary(qqq, rf, b.returns, "QQQ")]

    sleeves = {
        "xsmom": ST.xsmom(p, top_k=8, universe=uni, weighting="invvol"),
        "liq": ST.liquidity_provision(p, uni, top_k=5, weighting="invvol"),
    }
    ens = ST.combine({k: (v, 0.5) for k, v in sleeves.items()}, cal)
    rows.append(M.summary(run(p, ens, rf, CM, *WIN), rf, b.returns, "Sleeves only (55% cash)"))

    cores = {
        "QQQ buy-hold": (lambda: pd.DataFrame({"QQQ": 1.0}, index=[cal[0]])
                         .reindex(columns=W["close"].columns).fillna(0.0)),
        "trend core": (lambda: ST.trend_core(p)),
    }
    for cname, cf in cores.items():
        core = cf()
        cs = ST.core_satellite(p, core, {k: v * 0.5 for k, v in sleeves.items()})
        res = run(p, cs, rf, CM, *WIN)
        rows.append(M.summary(res, rf, b.returns, f"Core-sat: {cname}"))
        lv, k = lever_to(res, qvol, b)
        rows.append(M.summary(lv, rf, b.returns, f"  ^ levered {k:.1f}x to QQQ vol"))

    # and the sleeves-only book levered to QQQ vol, for contrast
    res = run(p, ens, rf, CM, *WIN)
    lv, k = lever_to(res, qvol, b)
    rows.append(M.summary(lv, rf, b.returns, f"Sleeves levered {k:.1f}x to QQQ vol"))

    print(f"===== core-satellite, {WIN[0]}..{WIN[1]}, 5bps =====")
    print(M.table(rows).to_string())
