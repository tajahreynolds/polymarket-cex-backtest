"""Does the edge depend on me having hand-picked 52 tickers that survived?

Two different biases are in play and only one of them is fixable here:
  (1) MY selection bias - I chose the universe in 2026 knowing the winners.
      Fixed by screening the full 1,320-ETF panel point-in-time instead.
  (2) The VENDOR's survivorship bias - every file in the mirror ends in Nov-2017,
      so not one delisted ETF exists in it. Unfixable without other data, but it
      can be bounded: funds that close are overwhelmingly thin ones, so if the
      edge holds at a high liquidity floor it cannot be an artifact of the
      missing dead funds.
"""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from panel import load_wide, eligible, rf_daily
from engine import run, CostModel
import metrics as M, strategies as ST
import signals as S

DEV = ("2006-03-01", "2012-12-31")     # +1yr vs before: the screen needs history
CM = CostModel(spread_bps=5)
HANDPICKED = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "LQD", "HYG",
              "GLD", "DBC", "VNQ", "XLU", "XLP", "XLV", "XLK", "XLE", "XLF"]

W = load_wide()
cal = W["close"].index
rf = rf_daily(cal)
print(f"panel: {W['close'].shape[1]} ETFs, {len(cal)} bars\n")


def bench(t):
    tg = pd.DataFrame(0.0, index=[cal[cal >= DEV[0]][0]], columns=W["close"].columns)
    tg.loc[tg.index[0], t] = 1.0
    return run(W, tg, rf, CM, *DEV)


def masked(floor):
    """A copy of the panel whose `tradable` flag is the point-in-time screen, so
    every strategy inherits the universe without knowing about it."""
    el = eligible(W, min_dollar_vol=floor)
    p = dict(W); p["tradable"] = el
    return p, el


if __name__ == "__main__":
    spy = bench("SPY")
    rows = [M.summary(spy, rf, spy.returns, "SPY"),
            M.summary(bench("QQQ"), rf, spy.returns, "QQQ")]

    print(f"{'floor':>10} {'names avg':>10} {'names min':>10}")
    for floor in (1e6, 10e6, 50e6, 200e6):
        p, el = masked(floor)
        n = el.sum(axis=1)
        n = n[(n.index >= DEV[0]) & (n.index <= DEV[1])]
        print(f"{floor/1e6:>8.0f}M {n.mean():>10.0f} {n.min():>10.0f}")

        cols = list(W["close"].columns)
        rows.append(M.summary(run(p, ST.xsmom(p, top_k=8, universe=cols,
                                              weighting="invvol"), rf, CM, *DEV),
                              rf, spy.returns, f"XS-mom PIT >{floor/1e6:.0f}M"))
        rows.append(M.summary(run(p, ST.liquidity_provision(p, cols, top_k=5,
                                                            weighting="invvol"), rf, CM, *DEV),
                              rf, spy.returns, f"Liq-prov PIT >{floor/1e6:.0f}M"))

    # the original hand-picked sleeve, same window, for a like-for-like read
    p = dict(W); p["tradable"] = W["tradable"]
    rows.append(M.summary(run(p, ST.xsmom(p, top_k=8, universe=HANDPICKED,
                                          weighting="invvol"), rf, CM, *DEV),
                          rf, spy.returns, "XS-mom hand-picked 18"))
    rows.append(M.summary(run(p, ST.liquidity_provision(p, HANDPICKED, top_k=5,
                                                        weighting="invvol"), rf, CM, *DEV),
                          rf, spy.returns, "Liq-prov hand-picked 18"))

    print(f"\n===== point-in-time universe vs hand-picked, {DEV[0]}..{DEV[1]} =====")
    print(M.table(rows).to_string())
