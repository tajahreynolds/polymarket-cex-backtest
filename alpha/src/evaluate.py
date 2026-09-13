import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import pandas as pd
from panel import load_panel, rf_daily
from engine import run, CostModel
import metrics as M, strategies as ST
from baselines import static, monthly_static

DEV = ("2005-03-01", "2012-12-31")
OOS = ("2013-01-01", "2017-11-10")

RISK_SLEEVE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "TLT", "IEF", "LQD", "HYG",
               "GLD", "DBC", "VNQ", "XLU", "XLP", "XLV", "XLK", "XLE", "XLF"]

panel = load_panel()
cal = panel["close"].index
rf = rf_daily(cal)
CM = CostModel(spread_bps=5)


def ev(w, label, window, max_gross=1.0, bench=None):
    r = run(panel, w, rf, CM, window[0], window[1], max_gross=max_gross)
    return M.summary(r, rf, bench, label), r


def bench_returns(window):
    return run(panel, static({"SPY": 1.0}, window[0]), rf, CM, *window).returns


def suite(window, tag):
    b = bench_returns(window)
    rows = []
    for lab, w in [("SPY", {"SPY": 1.0}), ("QQQ", {"QQQ": 1.0})]:
        rows.append(ev(static(w, window[0]), lab, window, bench=b)[0])
    rows.append(ev(monthly_static({"SPY": .6, "AGG": .4}, window[0]), "60/40", window, bench=b)[0])
    rows.append(ev(ST.faber_taa(panel), "Faber TAA", window, bench=b)[0])
    rows.append(ev(ST.dual_momentum(panel), "Dual momentum", window, bench=b)[0])
    for k in (5, 8, 12):
        rows.append(ev(ST.xsmom(panel, top_k=k), f"XS-mom top{k}", window, bench=b)[0])
    for vt in (0.08, 0.12):
        rows.append(ev(ST.tsmom_voltarget(panel, RISK_SLEEVE, vol_target=vt),
                       f"TSMOM volT {vt:.0%}", window, bench=b)[0])
    rows.append(ev(ST.vol_managed(panel, "QQQ", 0.15), "VolMgd QQQ 15%", window, bench=b)[0])
    rows.append(ev(ST.vol_managed(panel, "SPY", 0.12), "VolMgd SPY 12%", window, bench=b)[0])
    rows.append(ev(ST.liquidity_provision(panel, RISK_SLEEVE), "Liq-provision", window, bench=b)[0])
    rows.append(ev(ST.liquidity_provision(panel, RISK_SLEEVE, require_capitulation=False),
                   "Reversal (no cap)", window, bench=b)[0])
    print(f"\n===== {tag}: {window[0]} .. {window[1]} (5bps one-way) =====")
    print(M.table(rows).to_string())
    return rows


if __name__ == "__main__":
    suite(DEV, "DEVELOPMENT")
