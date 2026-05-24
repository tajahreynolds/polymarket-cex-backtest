"""
Edge computation: spread in basis points after fees and slippage.
"""
from .proxy import binance_implied_prob

FEE_BPS = 200    # Polymarket taker 2%
SLIPPAGE_BPS = 0  # caller adds their own slippage estimate


def compute_edge(
    polymarket_prob: float,
    btc_spot: float,
    anchor: float,
    scale: float = 10_000.0,
    fee_bps: int = FEE_BPS,
    slippage_bps: int = SLIPPAGE_BPS,
) -> dict:
    bip = binance_implied_prob(btc_spot, anchor, scale)
    spread_bps = (polymarket_prob - bip) * 10_000
    edge_bps = spread_bps - fee_bps - slippage_bps
    return {
        "polymarket_prob": polymarket_prob,
        "binance_implied_prob": bip,
        "spread_bps": spread_bps,
        "edge_bps": edge_bps,
        "direction": "LONG" if edge_bps > 0 else "SHORT",
    }
