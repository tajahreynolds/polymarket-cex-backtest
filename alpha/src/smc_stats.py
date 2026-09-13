"""Does the bullish+discount cell survive once cross-sectional correlation is
handled? Pooled t-stats across 18 ETFs on the same 21 days are badly overstated,
so the spread is averaged per date first (Fama-MacBeth style)."""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
import signals as S
from evaluate import RISK_SLEEVE, panel, DEV

pos, _, _ = S.dealing_range(panel, 10)
st = S.market_structure(panel, 10)
fwd = panel["close"].pct_change(21).shift(-21)

m = (panel["close"].index >= DEV[0]) & (panel["close"].index <= DEV[1])
P, F, T = (x[RISK_SLEEVE][m] for x in (pos, fwd, st))

bull_disc = F.where((P <= 0.382) & (T > 0))
bull_prem = F.where((P >= 0.618) & (T > 0))
spread = bull_disc.mean(axis=1) - bull_prem.mean(axis=1)   # one number per date
s = spread.dropna()

# overlapping 21-day windows -> Newey-West with 21 lags
x = s.values
mean = x.mean()
T_ = len(x)
g = x - mean
gamma0 = (g @ g) / T_
nw = gamma0 + 2 * sum((1 - k / 22) * (g[k:] @ g[:-k]) / T_ for k in range(1, 22))
t_nw = mean / np.sqrt(nw / T_)

print(f"bullish-discount minus bullish-premium, mean 21d spread: {mean:+.4%}")
print(f"dates with both cells populated: {T_}")
print(f"naive t-stat (ignores overlap):      {mean/ (x.std()/np.sqrt(T_)):+.2f}")
print(f"Newey-West t-stat (21 lags):         {t_nw:+.2f}")
print(f"distinct months represented:         {s.index.to_period('M').nunique()}")

# is the only profitable SMC variant just a slow trend filter in disguise?
import strategies as ST
from engine import run, CostModel
from evaluate import rf, ev, bench_returns
import metrics as M
b = bench_returns(DEV)
a = run(panel, ST.smc_premium_discount(panel, RISK_SLEEVE, k=20, discount=0.5),
        rf, CostModel(spread_bps=5), *DEV)
c = run(panel, ST.smc_premium_discount(panel, RISK_SLEEVE, k=20, discount=1.01),
        rf, CostModel(spread_bps=5), *DEV)
print(f"\ncorrelation of SMC k=20 with its own structure filter alone: "
      f"{a.returns.corr(c.returns):.3f}")
