import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import pandas as pd
from engine import run, CostModel
import metrics as M, strategies as ST
from evaluate import DEV, RISK_SLEEVE, panel, rf

print("liquidity-provision sleeve: turnover control (development window)")
print(f"{'hold':>5}{'topk':>6}{'cap':>6} | " + " ".join(f"Sh@{b}bps" for b in (5,10,20)) +
      f"{'CAGR':>8}{'maxDD':>9}{'turn/yr':>9}")
for hold in (1, 2, 4, 8):
    for topk in (5,):
        for cap in (True, False):
            w = ST.liquidity_provision(panel, RISK_SLEEVE, top_k=topk,
                                       require_capitulation=cap, hold_periods=hold)
            line = f"{hold:>5}{topk:>6}{str(cap):>6} | "
            base = None
            for b in (5, 10, 20):
                r = run(panel, w, rf, CostModel(spread_bps=b), DEV[0], DEV[1])
                s = M.summary(r, rf, None, "x")
                if b == 10:
                    base = s
                line += f"{s['Sharpe']:>8.2f}"
            line += f"{base['CAGR']:>8.2%}{base['maxDD']:>9.2%}{base['turnover_ann']:>9.1f}"
            print(line)
