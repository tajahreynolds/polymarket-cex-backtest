"""Does the short leg of premium/discount work? Long-only was only half the test."""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import pandas as pd
from panel import load_wide, eligible, rf_daily
from engine import run, CostModel
import metrics as M, strategies as ST, signals as S

W = load_wide(); cal = W["close"].index; rf = rf_daily(cal)
CM = CostModel(spread_bps=5, short_borrow_bps=50)
WIN = ("2006-03-01", "2012-12-31")
p = dict(W); p["tradable"] = eligible(W, min_dollar_vol=50e6)
uni = list(W["close"].columns)

tg = pd.DataFrame(0.0, index=[cal[cal >= WIN[0]][0]], columns=W["close"].columns)
tg.loc[tg.index[0], "SPY"] = 1.0
b = run(W, tg, rf, CM, *WIN)
rows = [M.summary(b, rf, b.returns, "SPY")]
tg2 = tg * 0.0; tg2.loc[tg2.index[0], "QQQ"] = 1.0
rows.append(M.summary(run(W, tg2, rf, CM, *WIN), rf, b.returns, "QQQ"))

for k in (5, 10, 20):
    for side in ("long", "short", "both"):
        w = ST.smc_long_short(p, uni, k=k, side=side)
        rows.append(M.summary(run(p, w, rf, CM, *WIN, max_gross=1.0), rf, b.returns,
                              f"SMC k={k} {side}"))
print("===== SMC both legs, point-in-time universe, inverse-vol, 5bps + 50bp borrow =====")
print(M.table(rows).to_string())

# direct look at the short leg's raw edge, clustered by date
pos, _, _ = S.dealing_range(p, 10); st = S.market_structure(p, 10)
fwd = W["close"].pct_change(21).shift(-21)
m = (cal >= WIN[0]) & (cal <= WIN[1])
el = eligible(W, min_dollar_vol=50e6)
P, F, T, E = (x[m] for x in (pos, fwd, st, el))
bear_prem = F.where((P >= 0.618) & (T < 0) & E).mean(axis=1)
bear_disc = F.where((P <= 0.382) & (T < 0) & E).mean(axis=1)
print("\n=== bearish structure, mean forward 21d LONG return ===")
print(f"  in premium  (short entry zone): {bear_prem.mean():+.4%}  n_dates={bear_prem.notna().sum()}")
print(f"  in discount:                    {bear_disc.mean():+.4%}  n_dates={bear_disc.notna().sum()}")
print(f"  -> a short taken in premium earns {-bear_prem.mean():+.4%} per 21d before costs")
