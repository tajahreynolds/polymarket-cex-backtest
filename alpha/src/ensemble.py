import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from panel import load_panel, rf_daily
from engine import run, CostModel
import metrics as M, strategies as ST
from evaluate import DEV, OOS, RISK_SLEEVE, panel, rf, ev, bench_returns
from baselines import static

cal = panel["close"].index


def sleeves():
    return {
        "xsmom": ST.xsmom(panel, top_k=8),
        "liq":   ST.liquidity_provision(panel, RISK_SLEEVE),
        "trend": ST.tsmom_voltarget(panel, RISK_SLEEVE, vol_target=0.12),
        "volmgd": ST.vol_managed(panel, "QQQ", 0.15),
    }


def sleeve_returns(sl, window, cm):
    return {k: run(panel, w, rf, cm, window[0], window[1]).returns for k, w in sl.items()}


if __name__ == "__main__":
    sl = sleeves()
    cm = CostModel(spread_bps=5)
    rets = sleeve_returns(sl, DEV, cm)
    R = pd.DataFrame(rets)
    print("=== sleeve correlation, development window ===")
    print(R.corr().round(2).to_string())
    print("\n=== cost sensitivity (development, Sharpe) ===")
    hdr = f"{'sleeve':<8}" + "".join(f"{b:>8}bps" for b in (2, 5, 10, 20, 40))
    print(hdr)
    for k, w in sl.items():
        line = f"{k:<8}"
        for b in (2, 5, 10, 20, 40):
            r = run(panel, w, rf, CostModel(spread_bps=b), DEV[0], DEV[1])
            s = M.summary(r, rf, None, k)["Sharpe"]
            line += f"{s:>11.2f}"
        print(line)

    print("\n=== ensembles (development) ===")
    b = bench_returns(DEV)
    rows = []
    mixes = {
        "50 xsmom / 50 liq": {"xsmom": .5, "liq": .5},
        "40/40/20 +trend":   {"xsmom": .4, "liq": .4, "trend": .2},
        "1/3 each x3":       {"xsmom": 1/3, "liq": 1/3, "volmgd": 1/3},
        "equal x4":          {k: .25 for k in sl},
    }
    for name, alloc in mixes.items():
        w = ST.combine({k: (sl[k], v) for k, v in alloc.items()}, cal)
        rows.append(ev(w, name, DEV, bench=b)[0])
    rows.append(ev(sl["xsmom"], "xsmom alone", DEV, bench=b)[0])
    rows.append(ev(sl["liq"], "liq alone", DEV, bench=b)[0])
    print(M.table(rows).to_string())
