"""
Load analysis config from micro-arb's backtest.config.json (V9, C3, I.5).
Raises if file not found or required keys missing.
"""
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "market" / "micro-arb" / "backtest.config.json"


def load() -> dict:
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(f"backtest.config.json not found at {_CONFIG_PATH}")
    with _CONFIG_PATH.open() as f:
        raw = json.load(f)
    strat = raw.get("strategy", {})
    return {
        "fee_bps": float(strat["fee_bps"]),
        "slippage_bps": float(strat["slippage_bps"]),
        "spread_threshold": float(strat["spread_threshold"]),
        "window_start": raw["window"]["start"],
        "window_end": raw["window"]["end"],
    }
