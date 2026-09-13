"""Two effects neither repo has tested, both pre-specified from the literature
rather than mined, and both structurally unlike the price-pattern ideas already
rejected.

1. Overnight vs intraday decomposition. Lachance (2021), Bogousslavsky (2021):
   essentially the whole US equity premium accrues close-to-open, while
   open-to-close is flat to negative. If that holds for ETFs it is both a
   possible strategy and - more usefully - an execution fact that affects every
   other strategy in both repos, since we fill at the open.

2. Turn of the month. Ariel (1987), Lakonishok & Smidt (1988): the last day of
   the month plus the first three have historically carried the entire equity
   premium. ~12 round trips a year, which is leverage-viable, unlike everything
   that has worked so far.
"""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy import stats
import panel_trading as PT

P = PT.load(); cal = P["close"].index
o, c = P["open"], P["close"]
rf = PT.rf_from_irx(cal)

ERAS = {"1993-2007": ("1993-01-29", "2007-05-31"),
        "2007-2012": ("2007-06-01", "2012-12-31"),
        "2013-2017": ("2013-01-01", "2017-11-10"),
        "2018-2026": ("2018-01-01", "2026-09-11")}


def tstat(x):
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan


print("=== 1. overnight (close->open) vs intraday (open->close), annualised ===")
print(f"{'ticker':8s}{'era':12s}{'overnight':>11s}{'t':>7s}{'intraday':>11s}{'t':>7s}{'total':>10s}")
for t in ("SPY", "QQQ", "IWM", "EFA", "TLT", "GLD"):
    for ename, (s, e) in ERAS.items():
        m = (cal >= s) & (cal <= e)
        on = (o[t] / c[t].shift(1) - 1)[m]
        idy = (c[t] / o[t] - 1)[m]
        tot = (c[t].pct_change())[m]
        if on.notna().sum() < 200:
            continue
        print(f"{t:8s}{ename:12s}{on.mean()*252:>10.2%}{tstat(on):>7.1f}"
              f"{idy.mean()*252:>10.2%}{tstat(idy):>7.1f}{tot.mean()*252:>9.2%}")
    print()

print("=== 2. turn of the month: day-of-month-position vs return ===")
# position within the trading month: -1 is the last trading day, 0 the first
pos = pd.Series(index=cal, dtype=float)
grp = pd.Series(cal, index=cal).groupby([cal.year, cal.month])
for _, days in grp:
    idx = pd.DatetimeIndex(days.values)
    pos.loc[idx] = np.arange(len(idx))
    pos.loc[idx[-4:]] = np.arange(-4, 0)

for t in ("SPY", "QQQ", "EFA", "IWM"):
    r = c[t].pct_change()
    print(f"\n-- {t}")
    print(f"{'era':12s}{'TOM ann':>10s}{'t':>7s}{'rest ann':>10s}{'t':>7s}"
          f"{'TOM days/yr':>13s}{'buy-hold':>10s}")
    for ename, (s, e) in ERAS.items():
        m = (cal >= s) & (cal <= e)
        rr, pp = r[m], pos[m]
        # last 1 trading day + first 3: the classic window
        tom = rr[(pp >= -1) | (pp <= 2)]
        rest = rr[~((pp >= -1) | (pp <= 2))]
        if tom.notna().sum() < 50:
            continue
        yrs = m.sum() / 252
        print(f"{ename:12s}{tom.mean()*252:>9.2%}{tstat(tom):>7.1f}"
              f"{rest.mean()*252:>9.2%}{tstat(rest):>7.1f}"
              f"{tom.notna().sum()/yrs:>13.0f}{rr.mean()*252:>9.2%}")
