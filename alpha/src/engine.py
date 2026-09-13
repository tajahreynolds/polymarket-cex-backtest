"""Event-ordered backtest engine.

Convention that keeps the test leak-free:
  * every signal is computed from bars up to and including the close of day t;
  * the resulting target weights are executed at the OPEN of day t+1;
  * between rebalances, holdings drift with prices (no free rebalancing).

Accounting is done in dollars so that drift, cash accrual and turnover costs are
exact rather than approximated with weight algebra.
"""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


@dataclass
class CostModel:
    # One-way cost applied to traded notional: half-spread + market impact.
    spread_bps: float = 5.0
    commission_bps: float = 0.0

    @property
    def rate(self) -> float:
        return (self.spread_bps + self.commission_bps) / 1e4


@dataclass
class BacktestResult:
    equity: pd.Series
    returns: pd.Series
    weights: pd.DataFrame
    turnover: pd.Series
    cash: pd.Series
    costs: pd.Series


def run(panel: dict[str, pd.DataFrame],
        targets: pd.DataFrame,
        rf_daily: pd.Series,
        costs: CostModel = CostModel(),
        start: str | None = None,
        end: str | None = None) -> BacktestResult:
    """`targets` holds weights decided at each row's close; rows may be sparse
    (only rebalance dates need to appear). Any weight not allocated is cash."""
    close = panel["close"]
    open_ = panel["open"]
    tradable = panel["tradable"]

    cal = close.index
    if start:
        cal = cal[cal >= pd.Timestamp(start)]
    if end:
        cal = cal[cal <= pd.Timestamp(end)]
    cols = close.columns

    targets = targets.reindex(columns=cols).reindex(cal.union(targets.index)).loc[cal]
    rebal_days = targets.dropna(how="all").index

    c = close.loc[cal].to_numpy(float)
    o = open_.loc[cal].to_numpy(float)
    tr = tradable.loc[cal].to_numpy(bool)
    tg = targets.to_numpy(float)
    rfd = rf_daily.reindex(cal).fillna(0.0).to_numpy(float)
    n, m = c.shape

    h = np.zeros(m)          # dollar holdings per asset
    cash = 1.0
    pending = None           # target decided yesterday, executed at today's open

    eq = np.zeros(n)
    w_hist = np.zeros((n, m))
    to_hist = np.zeros(n)
    cost_hist = np.zeros(n)
    cash_hist = np.zeros(n)
    eq[0] = 1.0

    rebal_set = set(np.where(targets.index.isin(rebal_days))[0])
    if 0 in rebal_set and np.isfinite(tg[0]).any():
        pending = tg[0]          # a target set on the first close trades next open

    for i in range(1, n):
        # ---- overnight leg: yesterday's holdings carried to today's open
        prev_c = c[i - 1]
        with np.errstate(divide="ignore", invalid="ignore"):
            on = np.where(np.isfinite(o[i]) & np.isfinite(prev_c) & (prev_c > 0),
                          o[i] / prev_c, 1.0)
        h = h * np.nan_to_num(on, nan=1.0)
        cash *= (1.0 + rfd[i])

        v = h.sum() + cash

        # ---- execute yesterday's decision at today's open
        traded = 0.0
        if pending is not None:
            w = np.nan_to_num(pending, nan=0.0)
            w = np.where(tr[i] & np.isfinite(o[i]), w, 0.0)
            gross = np.abs(w).sum()
            if gross > 1.0 + 1e-9:      # never lever beyond the declared cap
                w = w / gross
            tgt_h = w * v
            trades = tgt_h - h
            traded = np.abs(trades).sum()
            fee = traded * costs.rate
            h = tgt_h
            cash = v - h.sum() - fee
            pending = None

        # ---- intraday leg: open to close
        with np.errstate(divide="ignore", invalid="ignore"):
            idr = np.where(np.isfinite(c[i]) & np.isfinite(o[i]) & (o[i] > 0),
                           c[i] / o[i], 1.0)
        h = h * np.nan_to_num(idr, nan=1.0)

        v_end = h.sum() + cash
        eq[i] = v_end
        w_hist[i] = h / v_end if v_end > 0 else 0.0
        to_hist[i] = traded / v if v > 0 else 0.0
        cost_hist[i] = traded * costs.rate / v if v > 0 else 0.0
        cash_hist[i] = cash / v_end if v_end > 0 else 0.0

        # ---- decide tonight, trade tomorrow
        if i in rebal_set and np.isfinite(tg[i]).any():
            pending = tg[i]

    equity = pd.Series(eq, index=cal)
    return BacktestResult(
        equity=equity,
        returns=equity.pct_change().fillna(0.0),
        weights=pd.DataFrame(w_hist, index=cal, columns=cols),
        turnover=pd.Series(to_hist, index=cal),
        cash=pd.Series(cash_hist, index=cal),
        costs=pd.Series(cost_hist, index=cal),
    )


def buy_hold(panel, ticker, rf_daily, costs=CostModel(), start=None, end=None):
    close = panel["close"]
    tg = pd.DataFrame(index=close.index[:1], columns=close.columns, dtype=float)
    first = close.index[close.index >= pd.Timestamp(start)][0] if start else close.index[0]
    tg = pd.DataFrame(0.0, index=[first], columns=close.columns)
    tg.loc[first, ticker] = 1.0
    return run(panel, tg, rf_daily, costs, start=start, end=end)
