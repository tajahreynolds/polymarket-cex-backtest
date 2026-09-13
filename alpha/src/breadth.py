"""Why does diversified trend fail here? Two candidate causes, both measurable:
the book is long-only, and the 'diversification' may be an illusion."""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from panel import load_wide, eligible, rf_daily
from engine import run, CostModel
import metrics as M, strategies as ST
from core_satellite import hold, lever_to

W = load_wide(); cal = W["close"].index; rf = rf_daily(cal)
CM = CostModel(spread_bps=5, short_borrow_bps=50)
WIN = ("2006-03-01", "2012-12-31")
el = eligible(W, min_dollar_vol=50e6)
p = dict(W); p["tradable"] = el
uni = list(W["close"].columns)

b, q = hold("SPY"), hold("QQQ")
rows = [M.summary(b, rf, b.returns, "SPY"), M.summary(q, rf, b.returns, "QQQ")]
for short in (False, True):
    for band in (0.0, 0.05):
        w = ST.diversified_trend(p, uni, band=band, allow_short=short)
        res = run(p, w, rf, CM, *WIN)
        rows.append(M.summary(res, rf, b.returns,
                              f"Div-trend {'L/S' if short else 'long-only'} band={band:.0%}"))
print(f"===== long-only vs long/short, {WIN[0]}..{WIN[1]} =====")
print(M.table(rows).to_string())

m = (cal >= WIN[0]) & (cal <= WIN[1])
r = W["close"].pct_change()[m]
live = el[m].all()
cols = [c for c in r.columns if live.get(c, False)]
R = r[cols].dropna(axis=1, how="any")
C = R.corr()
ev = np.linalg.eigvalsh(C.to_numpy())[::-1]
ev = ev[ev > 0]
pr = ev.sum() ** 2 / (ev ** 2).sum()
print(f"\n=== breadth of the ETF universe, {len(R.columns)} names always eligible ===")
print(f"mean pairwise correlation:               {C.to_numpy()[np.triu_indices(len(C), 1)].mean():.3f}")
print(f"first eigenvalue as share of variance:   {ev[0]/ev.sum():.1%}")
print(f"top-5 eigenvalues as share of variance:  {ev[:5].sum()/ev.sum():.1%}")
print(f"effective independent bets (part. ratio):{pr:.1f}")
for ic in (0.03, 0.05):
    print(f"  Grinold IR at IC={ic:.2f}, {pr:.0f} bets x 12 rebalances: {ic*np.sqrt(pr*12):.2f}")
