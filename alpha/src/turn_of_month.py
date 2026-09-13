"""Turn of the month (Ariel 1987, Lakonishok & Smidt 1988).

The reason to care is turnover, not novelty: ~12 round trips a year against the
overnight trade's 252. If it carries a real share of the equity premium at ~40%
exposure, it is the first thing in either repo that could actually be levered.
"""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import panel_trading as PT

P = PT.load(); cal = P["close"].index
c = P["close"]
rf = PT.rf_from_irx(cal)
ERAS = {"1993-2007": ("1993-01-29", "2007-05-31"),
        "2007-2012": ("2007-06-01", "2012-12-31"),
        "2013-2017": ("2013-01-01", "2017-11-10"),
        "2018-2026": ("2018-01-01", "2026-09-11")}

# position within the trading month: 0,1,2.. from the start; -1 is the last day.
# Both are knowable in advance from an exchange calendar, so neither peeks.
frm = pd.Series(index=cal, dtype=float)
to = pd.Series(index=cal, dtype=float)
for _, days in pd.Series(cal, index=cal).groupby([cal.year, cal.month]):
    idx = pd.DatetimeIndex(days.values)
    frm.loc[idx] = np.arange(len(idx))
    to.loc[idx] = np.arange(-len(idx), 0)


def tstat(x):
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan


def summarise(r, rfd):
    r = r.dropna()
    yrs = len(r) / 252
    cagr = (1 + r).prod() ** (1 / yrs) - 1
    ex = r - rfd.reindex(r.index).fillna(0.0)
    eq = (1 + r).cumprod()
    return cagr, r.std() * np.sqrt(252), ex.mean() / ex.std() * np.sqrt(252), \
        (eq / eq.cummax() - 1).min()


print("=== mean return by day-of-month position, SPY, all history ===")
r = c["SPY"].pct_change()
tab = pd.DataFrame({"r": r, "frm": frm, "to": to}).dropna()
print("  first days of month:", "  ".join(
    f"d{int(k)}:{v*1e4:+.0f}bp" for k, v in tab[tab.frm <= 4].groupby("frm").r.mean().items()))
print("  last days of month: ", "  ".join(
    f"d{int(k)}:{v*1e4:+.0f}bp" for k, v in tab[tab.to >= -4].groupby("to").r.mean().items()))
print(f"  all-day average:     {tab.r.mean()*1e4:+.0f}bp")

print("\n=== TOM window = last 1 day + first 3 days, in-market vs out ===")
IN = (to >= -1) | (frm <= 2)
for t in ("SPY", "QQQ", "IWM", "EFA"):
    r = c[t].pct_change()
    print(f"\n-- {t}")
    print(f"{'era':12s}{'TOM ann':>10s}{'t':>6s}{'rest ann':>10s}{'t':>6s}"
          f"{'days/yr':>9s}{'B&H CAGR':>10s}{'TOM@2bp':>10s}{'Sharpe':>8s}{'maxDD':>8s}")
    for ename, (s, e) in ERAS.items():
        m = (cal >= s) & (cal <= e)
        rr, inn = r[m], IN[m]
        tom, rest = rr[inn], rr[~inn]
        if tom.notna().sum() < 50:
            continue
        yrs = m.sum() / 252
        # in the market only on TOM days, cash otherwise; ~12 round trips a year
        strat = rr.where(inn, 0.0) + rf.reindex(rr.index).fillna(0) * (~inn)
        entries = (inn.astype(int).diff() == 1).sum()
        strat = strat - pd.Series(np.where(inn.astype(int).diff() != 0, 2 / 1e4, 0.0),
                                  index=rr.index)
        cagr, vol, sh, dd = summarise(strat, rf)
        print(f"{ename:12s}{tom.mean()*252:>9.2%}{tstat(tom):>6.1f}"
              f"{rest.mean()*252:>9.2%}{tstat(rest):>6.1f}"
              f"{tom.notna().sum()/yrs:>9.0f}{(1+rr).prod()**(1/yrs)-1:>9.2%}"
              f"{cagr:>9.2%}{sh:>8.2f}{dd:>8.1%}")
