"""The overnight/intraday split, tested as a strategy rather than a statistic.

Close-to-open is a real and well-documented effect; the standard objection is
that it needs a round trip every single day and dies on costs. So the whole
question is the breakeven cost, which is what this computes. Trades are assumed
to go through the closing and opening auctions, which is where that flow
actually belongs - MOC/MOO in SPY or QQQ is among the deepest liquidity of the
day, so a 1-2bp all-in round trip is realistic there and nowhere near realistic
for a thin ETF.
"""
import sys, pathlib, warnings
sys.path.insert(0, str(pathlib.Path(__file__).parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import panel_trading as PT

P = PT.load(); cal = P["close"].index
o, c = P["open"], P["close"]
rf = PT.rf_from_irx(cal)
ERAS = {"1993-2007": ("1993-01-29", "2007-05-31"),
        "2007-2012": ("2007-06-01", "2012-12-31"),
        "2013-2017": ("2013-01-01", "2017-11-10"),
        "2018-2026": ("2018-01-01", "2026-09-11")}


def stats_of(r, rfd, label, extra=""):
    r = r.dropna()
    if len(r) < 100:
        return None
    yrs = len(r) / 252
    cagr = (1 + r).prod() ** (1 / yrs) - 1
    vol = r.std() * np.sqrt(252)
    ex = r - rfd.reindex(r.index).fillna(0.0)
    sh = ex.mean() / ex.std() * np.sqrt(252) if ex.std() > 0 else np.nan
    eq = (1 + r).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    return dict(name=label + extra, CAGR=cagr, vol=vol, Sharpe=sh, maxDD=dd)


print("=== overnight-only vs buy-and-hold, after a per-day round-trip cost ===")
print("(one round trip every session: 252 a year)\n")
for t in ("SPY", "QQQ", "IWM"):
    print(f"-- {t}")
    hdr = f"{'era':12s}{'B&H CAGR':>10s}{'B&H Sh':>8s}{'ON vol':>8s}"
    hdr += "".join(f"{'ON@'+str(b)+'bp':>11s}" for b in (0, 1, 2, 5))
    print(hdr + f"{'breakeven':>11s}")
    for ename, (s, e) in ERAS.items():
        m = (cal >= s) & (cal <= e)
        on_gross = (o[t] / c[t].shift(1) - 1)[m]
        bh = c[t].pct_change()[m]
        if on_gross.notna().sum() < 200:
            continue
        b_s = stats_of(bh, rf, "bh")
        line = f"{ename:12s}{b_s['CAGR']:>9.2%}{b_s['Sharpe']:>8.2f}" \
               f"{on_gross.std()*np.sqrt(252):>8.1%}"
        for bps in (0, 1, 2, 5):
            r = on_gross - bps / 1e4          # one round trip per session
            st = stats_of(r, rf, "on")
            line += f"{st['CAGR']:>7.2%}/{st['Sharpe']:>3.1f}"
        # cost per round trip that takes the gross edge to zero
        be = on_gross.mean() * 1e4
        line += f"{be:>10.1f}bp"
        print(line)
    print()

print("=== overnight on a diversified sleeve, equal weight across 6 liquid ETFs ===")
SL = ["SPY", "QQQ", "IWM", "EFA", "GLD", "TLT"]
for ename, (s, e) in ERAS.items():
    m = (cal >= s) & (cal <= e)
    on = (o[SL] / c[SL].shift(1) - 1)[m]
    live = on.notna().sum(axis=1) >= 3
    port = on[live].mean(axis=1)
    if len(port) < 200:
        continue
    for bps in (0, 2):
        st = stats_of(port - bps / 1e4, rf, f"{ename} @{bps}bp")
        print(f"  {st['name']:22s} CAGR {st['CAGR']:>7.2%}  vol {st['vol']:>6.1%}  "
              f"Sharpe {st['Sharpe']:>5.2f}  maxDD {st['maxDD']:>7.1%}")
