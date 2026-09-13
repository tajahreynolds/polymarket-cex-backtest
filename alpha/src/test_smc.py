import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import pandas as pd
from engine import run, CostModel
import metrics as M, strategies as ST, signals as S
from evaluate import DEV, RISK_SLEEVE, panel, rf, ev, bench_returns
from baselines import static

b = bench_returns(DEV)
rows = [ev(static({"SPY": 1.0}, DEV[0]), "SPY", DEV, bench=b)[0],
        ev(static({"QQQ": 1.0}, DEV[0]), "QQQ", DEV, bench=b)[0]]

for k in (5, 10, 20):
    for disc in (0.382, 0.5):
        rows.append(ev(ST.smc_premium_discount(panel, RISK_SLEEVE, k=k, discount=disc),
                       f"SMC xs k={k} d={disc}", DEV, bench=b)[0])
# structure filter off, to see which half of the rule is doing the work
rows.append(ev(ST.smc_premium_discount(panel, RISK_SLEEVE, k=10, discount=0.382,
                                       require_bullish=False), "SMC xs no-structure", DEV, bench=b)[0])
# premium side: the mirror trade the concept implies
rows.append(ev(ST.smc_premium_discount(panel, RISK_SLEEVE, k=10, discount=1.01,
                                       require_bullish=True), "Bullish structure only", DEV, bench=b)[0])
for tk in ("SPY", "QQQ"):
    rows.append(ev(ST.smc_single(panel, tk, k=10), f"SMC single {tk}", DEV, bench=b)[0])
rows.append(ev(ST.xsmom(panel, top_k=8), "XS-mom top8 (incumbent)", DEV, bench=b)[0])

print("===== SMC premium/discount, development window, 5bps =====")
print(M.table(rows).to_string())

# is the discount zone actually predictive? a direct look at the conditional edge
pos, _, _ = S.dealing_range(panel, 10)
st = S.market_structure(panel, 10)
fwd = panel["close"].pct_change(21).shift(-21)
print("\n=== forward 21d return by dealing-range bucket (sleeve pooled) ===")
P, F, ST_ = pos[RISK_SLEEVE].stack(), fwd[RISK_SLEEVE].stack(), st[RISK_SLEEVE].stack()
df = pd.DataFrame({"pos": P, "fwd": F, "st": ST_}).dropna()
buckets = pd.cut(df.pos, [0, .2, .4, .6, .8, 1.0])
print(df.groupby([buckets, df.st > 0], observed=True).fwd.agg(["mean", "count"]).unstack()
        .rename(columns={False: "bearish", True: "bullish"}).round(4).to_string())
