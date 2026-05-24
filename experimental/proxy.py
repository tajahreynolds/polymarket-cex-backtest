"""
CEX-implied probability proxies for BTC Up/Down contracts.

Two models:
  momentum_implied_prob  — short-term return sigmoid; used by live engine and backtest
  level_implied_prob     — legacy absolute-price sigmoid; kept for reference only
"""
import math

MOMENTUM_SIGMA = 0.005  # normalises ~0.5% (1 std dev of 15m BTC return) to sigmoid(1) ≈ 0.73


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def momentum_implied_prob(return_frac: float) -> float:
    """
    Convert a short-term price return to a direction probability.

    return_frac = (spot_now - spot_lookback) / spot_lookback

    Returns 0.5 for zero return (neutral), approaching 1.0 for strong upward
    momentum and 0.0 for strong downward momentum.
    """
    if not math.isfinite(return_frac):
        return 0.5
    return sigmoid(return_frac / MOMENTUM_SIGMA)


def level_implied_prob(btc_spot: float, anchor: float, scale: float = 10_000.0) -> float:
    """
    Legacy level-based proxy. Not suitable for Up/Down contracts.

    anchor: BTC price that maps to 0.5 probability
    scale:  price range over which probability moves from ~0.27 to ~0.73
    """
    return sigmoid((btc_spot - anchor) / scale)
