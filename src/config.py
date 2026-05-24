"""
Load analysis config from micro-arb's backtest.config.json (V9, C3, I.5).
Raises if file not found or required keys missing.
"""
import json
import os
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "market" / "micro-arb" / "backtest.config.json"


def load() -> dict:
    config_path = os.environ.get(
        "MICRO_ARB_CONFIG_PATH",
        str(_CONFIG_PATH),  # keep existing default as fallback
    )
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Config not found: {config_path!r}. "
            "Set MICRO_ARB_CONFIG_PATH to the absolute path of backtest.config.json."
        )
    with open(config_path) as f:
        raw = json.load(f)
    strat = raw.get("strategy", {})
    return {
        "fee_bps": float(strat["fee_bps"]),
        "slippage_bps": float(strat["slippage_bps"]),
        "spread_threshold": float(strat["spread_threshold"]),
        "window_start": raw["window"]["start"],
        "window_end": raw["window"]["end"],
    }
