"""The L/S trend book posts Sharpe 0.52 from a universe with 1.7 effective bets.
That is more than the breadth budget allows, so it is probably one big bet rather
than a diversified premium. Check where the return actually came from."""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from panel import load_wide, eligible, rf_daily
from engine import run, CostModel
import metrics as M, strategies as ST
from core_satellite import hold

W = load_wide(); cal = W["close"].index; rf = rf_daily(cal)
CM = CostModel(spread_bps=5, short_borrow_bps=50)
WIN = ("2006-03-01", "2012-12-31")
p = dict(W); p["tradable"] = eligible(W, min_dollar_vol=50e6)
uni = list(W["close"].columns)

res = run(p, ST.diversified_trend(p, uni, band=0.0, allow_short=True), rf, CM, *WIN)
r = res.returns
print("=== L/S diversified trend: return by calendar year ===")
yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
spy = hold("SPY").returns
syr = spy.groupby(spy.index.year).apply(lambda x: (1 + x).prod() - 1)
for y in yr.index:
    print(f"  {y}  strategy {yr[y]:+7.2%}   SPY {syr.get(y, float('nan')):+7.2%}")

ex_08 = r[r.index.year != 2008]
print(f"\nfull period Sharpe:        {(r-rf.reindex(r.index)).mean()/(r-rf.reindex(r.index)).std()*np.sqrt(252):.2f}")
e = ex_08 - rf.reindex(ex_08.index).fillna(0)
print(f"Sharpe excluding 2008:     {e.mean()/e.std()*np.sqrt(252):.2f}")
print(f"2008 contribution to total growth: "
      f"{(1+r[r.index.year==2008]).prod()-1:+.2%} of a {(1+r).prod()-1:+.2%} total")

print("\n=== robustness: small changes to the rule ===")
for label, kw in [("baseline", {}),
                  ("band 2%", dict(band=0.02)),
                  ("band 5%", dict(band=0.05)),
                  ("lookbacks 63/126/252", dict(lookbacks=(63, 126, 252))),
                  ("lookbacks 21/63", dict(lookbacks=(21, 63))),
                  ("weekly rebalance", dict(freq="W")),
                  ("vol window 20", dict(vol_window=20)),
                  ("vol target 8%", dict(vol_target=0.08))]:
    w = ST.diversified_trend(p, uni, allow_short=True, **kw)
    rr = run(p, w, rf, CM, *WIN)
    s = M.summary(rr, rf, None, label)
    print(f"  {label:24s} Sharpe {s['Sharpe']:>5.2f}  CAGR {s['CAGR']:>7.2%}  turn {s['turnover_ann']:>5.1f}")
