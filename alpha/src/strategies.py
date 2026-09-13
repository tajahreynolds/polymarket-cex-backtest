"""Strategy definitions. Each returns target weights indexed by decision date."""
import numpy as np
import pandas as pd
import signals as S

CASH_PROXY = ["SHY", "BIL", "SHV"]


def _rebal_index(cal, freq):
    return S.month_ends(cal) if freq == "M" else S.week_ends(cal)


def risk_size(panel, picks, vol_target=0.12, vol_window=60, vol_floor=0.05,
              max_gross=1.0, cov_window=126):
    """Turn a boolean selection into weights sized by inverse volatility, then
    scale the book to a target portfolio volatility.

    Equal-weighting only works when the candidates carry similar risk. Across a
    universe that contains 1x, 2x, 3x and inverse funds it is meaningless - a 3x
    fund simply gets three times the exposure of its own underlying. Inverse-vol
    sizing neutralises that automatically: the 3x fund earns a third of the
    weight, so the leverage in the wrapper stops mattering.
    """
    vol = S.yang_zhang(panel, vol_window).clip(lower=vol_floor)
    idx = picks.index
    inv = (1.0 / vol).reindex(idx)[picks.columns].where(picks).fillna(0.0)
    raw = inv.div(inv.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)

    rets = panel["close"].pct_change()
    out = []
    for d in idx:
        wd = raw.loc[d]
        live = wd[wd != 0].index
        if len(live) == 0:
            out.append(wd * 0.0)
            continue
        hist = rets.loc[:d, live].tail(cov_window)
        cov = hist.cov().fillna(0.0).to_numpy() * 252
        v = wd[live].to_numpy()
        pv = float(np.sqrt(max(v @ cov @ v, 1e-8)))
        out.append(wd * min(vol_target / pv, max_gross / max(wd.abs().sum(), 1e-9)))
    return _normalise(pd.DataFrame(out, index=idx), max_gross)


def _normalise(w, max_gross):
    g = w.abs().sum(axis=1).replace(0, np.nan)
    scale = (max_gross / g).clip(upper=1.0).fillna(0.0)
    return w.mul(scale, axis=0)


# --------------------------------------------------------------- benchmarks
def faber_taa(panel, assets=("SPY", "EFA", "AGG", "DBC", "VNQ"), window=200, freq="M"):
    """Faber's rule: hold the asset when its close is above the 10-month SMA,
    otherwise that fifth of the portfolio sits in cash."""
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    on = S.sma_trend(panel, window).reindex(idx)
    w = pd.DataFrame(0.0, index=idx, columns=panel["close"].columns)
    for a in assets:
        w[a] = on[a].astype(float) / len(assets)
    return w


def dual_momentum(panel, risky=("SPY", "EFA"), safe="AGG", lookback=252, freq="M"):
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    mom = S.tsmom(panel, lookback).reindex(idx)[list(risky)].dropna(how="all")
    idx = mom.index
    w = pd.DataFrame(0.0, index=idx, columns=panel["close"].columns)
    best = mom.idxmax(axis=1)
    absolute_ok = mom.max(axis=1) > 0
    for d in idx:
        if pd.isna(best.get(d)):
            continue
        w.loc[d, best[d] if absolute_ok[d] else safe] = 1.0
    return w


# ------------------------------------------------------------- core research
def xsmom(panel, top_k=8, lookbacks=(63, 126, 252), skip=5, freq="M",
          trend_filter=True, sma=200, universe=None, weighting="ew",
          vol_target=0.12, max_gross=1.0):
    """Cross-sectional momentum: hold the top-k ETFs by blended momentum,
    equally weighted, and only those also in an uptrend."""
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    score = S.blended_momentum(panel, lookbacks, skip)
    tradable = panel["tradable"]
    if universe is not None:
        score = score[universe]
    score = score.where(tradable.reindex(columns=score.columns))
    if trend_filter:
        score = score.where(S.sma_trend(panel, sma).reindex(columns=score.columns))
    score = score.reindex(idx)

    w = pd.DataFrame(0.0, index=idx, columns=panel["close"].columns)
    ranks = score.rank(axis=1, ascending=False)
    picks = (ranks <= top_k) & score.notna()
    if weighting == "invvol":
        sel = risk_size(panel, picks, vol_target=vol_target, max_gross=max_gross)
    else:
        n = picks.sum(axis=1).replace(0, np.nan)
        sel = picks.div(n, axis=0).fillna(0.0)
    w[sel.columns] = sel
    return w


def tsmom_voltarget(panel, universe, vol_target=0.10, vol_window=20, sma=200,
                    freq="M", max_gross=1.0, vol_floor=0.05, use_yz=True):
    """Hold each asset in the sleeve only while it trends, sized inversely to its
    Yang-Zhang volatility, then scale the book to a constant portfolio vol."""
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    vol = (S.yang_zhang(panel, vol_window) if use_yz else S.close_vol(panel, vol_window))
    vol = vol.clip(lower=vol_floor)
    on = S.sma_trend(panel, sma) & panel["tradable"]

    inv = (1.0 / vol)[universe].where(on[universe]).reindex(idx).fillna(0.0)
    raw = inv.div(inv.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)

    # ex-ante portfolio vol from the realised covariance of the sleeve
    rets = panel["close"][universe].pct_change()
    w = pd.DataFrame(0.0, index=idx, columns=panel["close"].columns)
    scaled = []
    for d in idx:
        wd = raw.loc[d]
        hist = rets.loc[:d].tail(126).dropna(axis=1, how="all")
        cols = [c for c in wd.index if c in hist.columns]
        if not cols or wd.abs().sum() == 0:
            scaled.append(wd * 0.0)
            continue
        cov = hist[cols].cov().fillna(0.0).to_numpy() * 252
        v = wd[cols].to_numpy()
        pv = float(np.sqrt(max(v @ cov @ v, 1e-8)))
        scaled.append(wd * min(vol_target / pv, max_gross / max(wd.abs().sum(), 1e-9)))
    sc = pd.DataFrame(scaled, index=idx)
    w[sc.columns] = sc
    return _normalise(w, max_gross)


def vol_managed(panel, ticker="QQQ", vol_target=0.15, vol_window=20, freq="M",
                max_gross=1.0, use_yz=True):
    """Moreira-Muir: scale a single risky holding by the inverse of its recent
    realised variance; the remainder earns the short rate."""
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    vol = (S.yang_zhang(panel, vol_window) if use_yz else S.close_vol(panel, vol_window))
    w = pd.DataFrame(0.0, index=idx, columns=panel["close"].columns)
    w[ticker] = (vol_target / vol[ticker].clip(lower=0.03)).reindex(idx).clip(upper=max_gross).fillna(0.0)
    return w


def liquidity_provision(panel, universe, top_k=5, window=5, freq="W",
                        require_capitulation=True, vol_gate=None, max_gross=1.0,
                        hold_periods=1, weighting="ew", vol_target=0.12):
    """Buy the ETFs that just sold off hardest on capitulation-shaped bars, hold
    one period. This is the cash-market version of fading a liquidation cascade."""
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    rev = S.reversal(panel, window)[universe]
    if require_capitulation:
        cap = S.capitulation(panel)[universe].rolling(window).max()
        rev = rev.where(cap > 0)
    rev = rev.where(panel["tradable"][universe]).reindex(idx)

    w = pd.DataFrame(0.0, index=idx, columns=panel["close"].columns)
    ranks = rev.rank(axis=1, ascending=False)
    picks = (ranks <= top_k) & rev.notna() & (rev > 0)
    if weighting == "invvol":
        sel = risk_size(panel, picks, vol_target=vol_target, max_gross=max_gross)
    else:
        n = picks.sum(axis=1).replace(0, np.nan)
        sel = picks.div(n, axis=0).fillna(0.0) * max_gross
    if vol_gate is not None:
        gate = (S.yang_zhang(panel, 20)["SPY"].reindex(idx) > vol_gate).astype(float)
        sel = sel.mul(gate, axis=0)
    if hold_periods > 1:
        # Jegadeesh-Titman overlapping tranches: each period commits 1/N of the
        # book and holds it N periods, so turnover falls ~N-fold while average
        # exposure to the signal is unchanged.
        sel = sel.rolling(hold_periods, min_periods=1).mean()
    w[sel.columns] = sel
    return w


def combine(parts: dict[str, tuple[pd.DataFrame, float]], cal) -> pd.DataFrame:
    """Blend sleeves on a shared decision calendar, carrying each sleeve's last
    decision forward between its own rebalances."""
    idx = pd.DatetimeIndex(sorted(set().union(*[p.index for p, _ in parts.values()])))
    total = None
    for name, (w, alloc) in parts.items():
        ww = w.reindex(idx).ffill().fillna(0.0) * alloc
        total = ww if total is None else total.add(ww, fill_value=0.0)
    return total


def smc_premium_discount(panel, universe, k=5, discount=0.382, freq="W",
                         top_k=5, require_bullish=True, max_gross=1.0):
    """Smart-money concepts, made testable.

    Hold assets whose structure is bullish (price has taken out the last
    CONFIRMED swing high) while price sits in the discount half of the current
    dealing range. Everything is lagged to the bar that confirms it, so no swing
    is used before it could have been drawn on a live chart.
    """
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    pos, _, _ = S.dealing_range(panel, k)
    st = S.market_structure(panel, k)

    ok = (pos[universe] <= discount)
    if require_bullish:
        ok &= (st[universe] > 0)
    ok &= panel["tradable"][universe]

    # deepest discount first when more names qualify than slots
    score = (-pos[universe]).where(ok).reindex(idx)
    ranks = score.rank(axis=1, ascending=False)
    picks = (ranks <= top_k) & score.notna()
    n = picks.sum(axis=1).replace(0, np.nan)
    sel = picks.div(n, axis=0).fillna(0.0) * max_gross

    w = pd.DataFrame(0.0, index=idx, columns=panel["close"].columns)
    w[sel.columns] = sel
    return w


def smc_single(panel, ticker="SPY", k=5, discount=0.5, freq="W", max_gross=1.0):
    """Single-asset version: long only while structure is bullish and price is in
    discount, otherwise cash."""
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    pos, _, _ = S.dealing_range(panel, k)
    st = S.market_structure(panel, k)
    on = ((pos[ticker] <= discount) & (st[ticker] > 0)).reindex(idx).astype(float)
    w = pd.DataFrame(0.0, index=idx, columns=panel["close"].columns)
    w[ticker] = on * max_gross
    return w


def smc_long_short(panel, universe, k=10, zone=0.382, freq="W", top_k=5,
                   side="both", max_gross=1.0, weighting="invvol", vol_target=0.12):
    """The symmetric version of the concept: long in discount while structure is
    bullish, short in premium while structure is bearish.

    The earlier note only tested the long leg, which is half the framework. If
    the premium/discount idea is real the short leg should carry its own weight.
    """
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    pos, _, _ = S.dealing_range(panel, k)
    st = S.market_structure(panel, k)
    ok = panel["tradable"][universe]

    longs = (pos[universe] <= zone) & (st[universe] > 0) & ok
    shorts = (pos[universe] >= 1 - zone) & (st[universe] < 0) & ok

    def side_weights(mask, sign):
        score = (-pos[universe] if sign > 0 else pos[universe]).where(mask).reindex(idx)
        ranks = score.rank(axis=1, ascending=False)
        picks = (ranks <= top_k) & score.notna()
        if weighting == "invvol":
            sized = risk_size(panel, picks, vol_target=vol_target, max_gross=max_gross)
        else:
            n = picks.sum(axis=1).replace(0, np.nan)
            sized = picks.div(n, axis=0).fillna(0.0) * max_gross
        return sized * sign

    w = pd.DataFrame(0.0, index=idx, columns=panel["close"].columns)
    total = None
    if side in ("both", "long"):
        total = side_weights(longs, +1)
    if side in ("both", "short"):
        sw = side_weights(shorts, -1)
        total = sw if total is None else total.add(sw, fill_value=0.0)
    if side == "both":
        total = total / 2.0          # half the book to each leg
    w[total.columns] = total
    return _normalise(w, max_gross)


def core_satellite(panel, core, sleeves, max_gross=1.0):
    """Put the satellites' unused capital to work in a core rather than cash.

    The selective sleeves are flat most of the time - that idle cash is a pure
    drag on absolute return even when it flatters Sharpe. This routes whatever
    gross the sleeves are not using into a core allocation, so the book stays
    fully invested without ever exceeding the gross cap.
    """
    idx = pd.DatetimeIndex(sorted(set().union(
        *[w.index for w in list(sleeves.values()) + [core]])))
    total = None
    for w in sleeves.values():
        ww = w.reindex(idx).ffill().fillna(0.0)
        total = ww if total is None else total.add(ww, fill_value=0.0)
    if total is None:
        total = pd.DataFrame(0.0, index=idx, columns=core.columns)

    used = total.abs().sum(axis=1)
    residual = (max_gross - used).clip(lower=0.0)
    c = core.reindex(idx).ffill().fillna(0.0)
    cg = c.abs().sum(axis=1).replace(0, np.nan)
    c = c.div(cg, axis=0).fillna(0.0).mul(residual, axis=0)
    return total.add(c, fill_value=0.0)


def trend_core(panel, assets=("QQQ", "SPY", "EFA", "TLT", "GLD"), sma=200,
               freq="M", vol_target=0.14, weighting="invvol"):
    """A core that stays invested while trends hold: hold each asset above its
    long moving average, sized by inverse volatility."""
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    on = (S.sma_trend(panel, sma) & panel["tradable"])[list(assets)].reindex(idx).fillna(False)
    if weighting == "invvol":
        return risk_size(panel, on, vol_target=vol_target, max_gross=1.0)
    n = on.sum(axis=1).replace(0, np.nan)
    return on.div(n, axis=0).fillna(0.0)


def diversified_trend(panel, universe, lookbacks=(21, 63, 126, 252), freq="M",
                      vol_target=0.12, vol_window=60, max_gross=1.0,
                      band=0.0, allow_short=False, cov_window=126):
    """Trend following in the institutional shape rather than the chart shape.

    Every asset carries its own weak signal - the average sign of returns over
    several lookbacks - and the portfolio is sized by inverse volatility and
    scaled to a constant target vol. The edge is meant to come from breadth and
    sizing, not from any one entry being good.

    `band` is a no-trade threshold: weights move only when the target has drifted
    further than this from the current book. Turnover is what decides whether a
    strategy can be levered, so it is a first-class parameter here, not an
    afterthought.
    """
    cal = panel["close"].index
    idx = _rebal_index(cal, freq)
    c = panel["close"]

    sig = sum(np.sign(c / c.shift(lb) - 1.0) for lb in lookbacks) / len(lookbacks)
    sig = sig[universe].where(panel["tradable"][universe])
    if not allow_short:
        sig = sig.clip(lower=0.0)

    vol = S.yang_zhang(panel, vol_window).clip(lower=0.05)[universe]
    raw = (sig / vol).reindex(idx).fillna(0.0)
    gross = raw.abs().sum(axis=1).replace(0, np.nan)
    raw = raw.div(gross, axis=0).fillna(0.0)

    rets = c.pct_change()
    out, prev = [], None
    for d in idx:
        wd = raw.loc[d]
        live = wd[wd != 0].index
        if len(live) == 0:
            wd = wd * 0.0
        else:
            hist = rets.loc[:d, live].tail(cov_window)
            cov = hist.cov().fillna(0.0).to_numpy() * 252
            v = wd[live].to_numpy()
            pv = float(np.sqrt(max(v @ cov @ v, 1e-8)))
            wd = wd * min(vol_target / pv, max_gross / max(wd.abs().sum(), 1e-9))
        if prev is not None and band > 0:
            drift = (wd - prev).abs()
            wd = wd.where(drift > band, prev)      # leave small deviations alone
        prev = wd
        out.append(wd)

    w = pd.DataFrame(0.0, index=idx, columns=c.columns)
    sel = pd.DataFrame(out, index=idx)
    w[sel.columns] = sel
    return _normalise(w, max_gross)
