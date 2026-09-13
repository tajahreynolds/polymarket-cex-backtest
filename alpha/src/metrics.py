import numpy as np, pandas as pd
from scipy import stats

TRADING_DAYS = 252


def _ann_ret(eq):
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    return eq.iloc[-1] ** (1 / yrs) - 1


def max_dd(eq):
    return (eq / eq.cummax() - 1).min()


def summary(res, rf_daily, bench_ret: pd.Series | None = None, name="strategy"):
    r = res.returns
    eq = res.equity
    rf = rf_daily.reindex(r.index).fillna(0.0)
    ex = r - rf
    vol = r.std() * np.sqrt(TRADING_DAYS)
    sharpe = ex.mean() / ex.std() * np.sqrt(TRADING_DAYS) if ex.std() > 0 else np.nan
    down = ex[ex < 0].std()
    sortino = ex.mean() / down * np.sqrt(TRADING_DAYS) if down > 0 else np.nan
    dd = max_dd(eq)
    cagr = _ann_ret(eq)
    out = {
        "name": name, "CAGR": cagr, "vol": vol, "Sharpe": sharpe, "Sortino": sortino,
        "maxDD": dd, "Calmar": cagr / abs(dd) if dd < 0 else np.nan,
        "turnover_ann": res.turnover.sum() / ((eq.index[-1] - eq.index[0]).days / 365.25),
        "cost_drag_ann": res.costs.sum() / ((eq.index[-1] - eq.index[0]).days / 365.25),
        "worst12m": eq.pct_change(TRADING_DAYS).min(),
        "avg_cash": res.cash.mean(),
    }
    if bench_ret is not None:
        b = bench_ret.reindex(r.index).fillna(0.0) - rf
        beta, alpha, rv, pv, _ = stats.linregress(b.values, ex.values)
        out["beta"] = beta
        out["alpha_ann"] = alpha * TRADING_DAYS
        out["t_alpha"] = alpha / (ex - beta * b).std() * np.sqrt(len(ex))
    return out


def table(rows) -> pd.DataFrame:
    df = pd.DataFrame(rows).set_index("name")
    pct = ["CAGR", "vol", "maxDD", "worst12m", "cost_drag_ann", "avg_cash", "alpha_ann"]
    for c in df.columns:
        df[c] = df[c].map(lambda x: f"{x:>7.2%}" if c in pct and pd.notna(x)
                          else (f"{x:>7.2f}" if pd.notna(x) else "     na"))
    return df


def deflated_sharpe(sr, n_obs, n_trials, skew=0.0, kurt=3.0):
    """Bailey & Lopez de Prado: probability the observed Sharpe survives the
    number of configurations that were tried."""
    if n_trials < 2:
        return np.nan
    e = 0.5772156649
    sr0 = np.sqrt(1 / TRADING_DAYS) * (
        (1 - e) * stats.norm.ppf(1 - 1 / n_trials) + e * stats.norm.ppf(1 - 1 / (n_trials * np.e)))
    srd = sr / np.sqrt(TRADING_DAYS)
    num = (srd - sr0) * np.sqrt(n_obs - 1)
    den = np.sqrt(1 - skew * srd + (kurt - 1) / 4 * srd ** 2)
    return stats.norm.cdf(num / den)
