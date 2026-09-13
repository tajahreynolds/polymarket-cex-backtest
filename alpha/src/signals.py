"""Signal primitives computed from OHLCV bars only."""
import numpy as np
import pandas as pd


# ---------------------------------------------------------------- volatility
def yang_zhang(panel, window=20):
    """Yang-Zhang realised volatility: the minimum-variance, drift-independent
    range estimator. Uses all four prices, so for a given window it is several
    times more efficient than close-to-close - which is the main reason to run
    this research on OHLCV rather than closes."""
    o, h, l, c = (panel[k] for k in ("open", "high", "low", "close"))
    pc = c.shift(1)
    log_oc = np.log(o / pc)          # overnight jump
    log_co = np.log(c / o)           # intraday drift
    log_ho, log_lo, log_cc = np.log(h / o), np.log(l / o), np.log(c / o)

    sigma_o = log_oc.rolling(window).var()
    sigma_c = log_co.rolling(window).var()
    rs = (log_ho * (log_ho - log_cc) + log_lo * (log_lo - log_cc)).rolling(window).mean()

    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    return np.sqrt((sigma_o + k * sigma_c + (1 - k) * rs).clip(lower=0) * 252)


def close_vol(panel, window=20):
    return panel["close"].pct_change().rolling(window).std() * np.sqrt(252)


# -------------------------------------------------------------------- trend
def sma_trend(panel, window=200):
    c = panel["close"]
    return c > c.rolling(window).mean()


def tsmom(panel, lookback=252, skip=0):
    """Total return over the lookback, optionally skipping the most recent days
    to sidestep short-horizon reversal."""
    c = panel["close"]
    return c.shift(skip) / c.shift(lookback) - 1.0


def blended_momentum(panel, lookbacks=(63, 126, 252), skip=5):
    """Average of z-scored momentum over several horizons. Averaging horizons is
    the standard defence against picking one lucky lookback."""
    parts = []
    for lb in lookbacks:
        m = tsmom(panel, lb, skip)
        parts.append(m.sub(m.mean(axis=1), axis=0).div(m.std(axis=1).replace(0, np.nan), axis=0))
    return sum(parts) / len(parts)


# ------------------------------------------------------- liquidation / stress
def capitulation(panel, window=20):
    """OHLCV signature of forced selling: a wide-range down bar that closes near
    its low on volume far above normal. This is the cash-market analogue of a
    derivatives liquidation cascade - the print that a leveraged holder was made
    to sell rather than chose to."""
    o, h, l, c, v = (panel[k] for k in ("open", "high", "low", "close", "volume"))
    rng = (h - l).replace(0, np.nan)
    close_loc = (c - l) / rng                        # 0 = closed on the low
    range_z = (rng / c) / (rng / c).rolling(window).mean()
    vol_z = v / v.rolling(window).mean()
    down = (c / c.shift(1) - 1) < 0
    return (down & (close_loc < 0.35) & (range_z > 1.5) & (vol_z > 1.5)).astype(float)


def reversal(panel, window=5):
    """Short-horizon reversal: the return to supplying liquidity to whoever just
    had to get out. Nagel (2012) shows this payoff scales with volatility."""
    c = panel["close"]
    return -(c / c.shift(window) - 1.0)


# ------------------------------------------------------------------ plumbing
def month_ends(cal):
    s = pd.Series(cal, index=cal)
    return pd.DatetimeIndex(s.groupby([cal.year, cal.month]).max().values)


def week_ends(cal):
    s = pd.Series(cal, index=cal)
    iso = cal.isocalendar()
    return pd.DatetimeIndex(s.groupby([iso.year.values, iso.week.values]).max().values).sort_values()
