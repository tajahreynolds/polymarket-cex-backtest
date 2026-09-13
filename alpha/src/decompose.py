"""Where did iteration 1's Sharpe 0.70 actually come from?

Three things changed at once: the universe (hand-picked vs point-in-time), the
sizing rule (equal weight vs inverse-vol at a 12% target), and the start date.
Changing them one at a time says which one was carrying the result.
"""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import pandas as pd
from panel import load_wide, eligible, rf_daily
from engine import run, CostModel
import metrics as M, strategies as ST

W = load_wide(); cal = W["close"].index; rf = rf_daily(cal)
CM = CostModel(spread_bps=5)
HP = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "LQD", "HYG",
      "GLD", "DBC", "VNQ", "XLU", "XLP", "XLV", "XLK", "XLE", "XLF"]
WIN = ("2006-03-01", "2012-12-31")      # common window for every row


def spy_bench():
    tg = pd.DataFrame(0.0, index=[cal[cal >= WIN[0]][0]], columns=W["close"].columns)
    tg.loc[tg.index[0], "SPY"] = 1.0
    return run(W, tg, rf, CM, *WIN)


def pit(floor=50e6):
    p = dict(W); p["tradable"] = eligible(W, min_dollar_vol=floor); return p


if __name__ == "__main__":
    b = spy_bench()
    rows = [M.summary(b, rf, b.returns, "SPY"),
            M.summary(run(W, pd.DataFrame({"QQQ": [1.0]},
                      index=[cal[cal >= WIN[0]][0]]).reindex(columns=W["close"].columns)
                      .fillna(0.0), rf, CM, *WIN), rf, b.returns, "QQQ")]

    cases = [
        ("hand-picked + equal weight", dict(W), HP, "ew"),
        ("hand-picked + inverse-vol",  dict(W), HP, "invvol"),
        ("point-in-time + equal weight", pit(), list(W["close"].columns), "ew"),
        ("point-in-time + inverse-vol",  pit(), list(W["close"].columns), "invvol"),
    ]
    for label, p, uni, wt in cases:
        p = dict(p)
        if "hand-picked" in label:
            p["tradable"] = W["tradable"]
        rows.append(M.summary(run(p, ST.xsmom(p, top_k=8, universe=uni, weighting=wt),
                                  rf, CM, *WIN), rf, b.returns, f"XS-mom {label}"))
        rows.append(M.summary(run(p, ST.liquidity_provision(p, uni, top_k=5, weighting=wt),
                                  rf, CM, *WIN), rf, b.returns, f"Liq-prov {label}"))

    # the honest ensemble, built only from point-in-time components
    p = pit(); uni = list(W["close"].columns)
    parts = {"x": (ST.xsmom(p, top_k=8, universe=uni, weighting="invvol"), 0.5),
             "l": (ST.liquidity_provision(p, uni, top_k=5, weighting="invvol"), 0.5)}
    rows.append(M.summary(run(p, ST.combine(parts, cal), rf, CM, *WIN), rf, b.returns,
                          "ENSEMBLE point-in-time"))

    print(f"===== one change at a time, {WIN[0]}..{WIN[1]}, 5bps =====")
    print(M.table(rows).to_string())
