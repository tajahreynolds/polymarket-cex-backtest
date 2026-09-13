import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import pandas as pd
from panel import load_panel, rf_daily
from engine import run, CostModel
import metrics as M

panel = load_panel()
cal = panel["close"].index
rf = rf_daily(cal)

def static(weights, start):
    first = cal[cal >= pd.Timestamp(start)][0]
    tg = pd.DataFrame(0.0, index=[first], columns=panel["close"].columns)
    for k, v in weights.items():
        tg.loc[first, k] = v
    return tg

def monthly_static(weights, start):
    idx = cal[cal >= pd.Timestamp(start)]
    me = pd.Series(idx, index=idx).groupby([idx.year, idx.month]).max().values
    tg = pd.DataFrame(0.0, index=pd.DatetimeIndex(me), columns=panel["close"].columns)
    for k, v in weights.items():
        tg[k] = v
    return tg

if __name__ == "__main__":
    START, END = "2005-03-01", "2017-11-10"
    cm = CostModel(spread_bps=5)
    rows = []
    spy = run(panel, static({"SPY": 1.0}, START), rf, cm, START, END)
    for label, w in [("SPY", {"SPY": 1.0}), ("QQQ", {"QQQ": 1.0}), ("IWM", {"IWM": 1.0}),
                     ("TLT", {"TLT": 1.0}), ("GLD", {"GLD": 1.0})]:
        rows.append(M.summary(run(panel, static(w, START), rf, cm, START, END), rf, spy.returns, label))
    rows.append(M.summary(run(panel, monthly_static({"SPY": .6, "AGG": .4}, START), rf, cm, START, END),
                          rf, spy.returns, "60/40 monthly"))
    rows.append(M.summary(run(panel, monthly_static(
        {"VTI": .2, "EFA": .2, "AGG": .2, "DBC": .2, "VNQ": .2}, START), rf, cm, START, END),
        rf, spy.returns, "Ivy-5 EW"))
    print(M.table(rows).to_string())
