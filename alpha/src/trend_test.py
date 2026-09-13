"""Diversified low-turnover trend: is it leverage-viable where the sleeves were not?"""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from panel import load_wide, eligible, rf_daily
from engine import run, CostModel
import metrics as M, strategies as ST
from core_satellite import hold, lever_to

W = load_wide(); cal = W["close"].index; rf = rf_daily(cal)
CM = CostModel(spread_bps=5)
WIN = ("2006-03-01", "2012-12-31")
p = dict(W); p["tradable"] = eligible(W, min_dollar_vol=50e6)
uni = list(W["close"].columns)

b, q = hold("SPY"), hold("QQQ")
qvol = q.returns.std() * np.sqrt(252)
rows = [M.summary(b, rf, b.returns, "SPY"), M.summary(q, rf, b.returns, "QQQ")]

for band in (0.0, 0.02, 0.05):
    w = ST.diversified_trend(p, uni, band=band)
    res = run(p, w, rf, CM, *WIN)
    rows.append(M.summary(res, rf, b.returns, f"Div-trend band={band:.0%}"))

best = ST.diversified_trend(p, uni, band=0.02)
res = run(p, best, rf, CM, *WIN)
lv, k = lever_to(res, qvol, b)
rows.append(M.summary(lv, rf, b.returns, f"  ^ levered {k:.1f}x to QQQ vol"))

# blended with the two existing sleeves
sleeves = {"trend": (best, 0.5),
           "xsmom": (ST.xsmom(p, top_k=8, universe=uni, weighting="invvol"), 0.25),
           "liq": (ST.liquidity_provision(p, uni, top_k=5, weighting="invvol"), 0.25)}
mix = ST.combine(sleeves, cal)
res2 = run(p, mix, rf, CM, *WIN)
rows.append(M.summary(res2, rf, b.returns, "Trend 50 / xsmom 25 / liq 25"))
lv2, k2 = lever_to(res2, qvol, b)
rows.append(M.summary(lv2, rf, b.returns, f"  ^ levered {k2:.1f}x to QQQ vol"))

print(f"===== diversified trend, {WIN[0]}..{WIN[1]}, 5bps =====")
print(M.table(rows).to_string())
