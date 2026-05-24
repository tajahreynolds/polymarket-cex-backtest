"""Programmatic invariant checks for the sum-arb analysis pipeline.
Run standalone: python -m src.validate
"""
import os
import pandas as pd

from . import db, config


def assert_v1(df: pd.DataFrame) -> None:
    """V1: spread in [-1.0, 1.0]."""
    if df.empty:
        return
    out = df[(df["spread"] < -1.0) | (df["spread"] > 1.0)]
    if not out.empty:
        raise AssertionError(
            f"V1 FAIL: {len(out)} rows have spread outside [-1, 1]. "
            f"Sample: {out['correlation_id'].head(3).tolist()}"
        )


def assert_v2(df_signals: pd.DataFrame, df_risk: pd.DataFrame) -> None:
    """V2: every emitted signal has a risk_decision."""
    emitted = df_signals[df_signals["decision"] == "emitted"]["correlation_id"]
    missing = emitted[~emitted.isin(df_risk["correlation_id"])]
    if not missing.empty:
        raise AssertionError(
            f"V2 FAIL: {len(missing)} emitted signals have no risk_decision. "
            f"Sample: {missing.head(3).tolist()}"
        )


def assert_v4(df: pd.DataFrame, fee_bps: float, slippage_bps: float) -> None:
    """V4: net_pnl = fill_size * |spread| - fill_size * (fee_bps + slippage_bps) / 10000."""
    if df.empty:
        return
    cost_rate = (fee_bps + slippage_bps) / 10000
    expected = df["fill_size"] * df["spread"].abs() - df["fill_size"] * cost_rate
    violations = df[(df["net_pnl"] - expected).abs() > 1e-6]
    if not violations.empty:
        raise AssertionError(
            f"V4 FAIL: {len(violations)} rows have inconsistent net_pnl. "
            f"Max delta: {(df['net_pnl'] - expected).abs().max():.8f}"
        )


def assert_v6(df: pd.DataFrame) -> None:
    """V6: submit_latency_us and fill_latency_us present and non-null on filled trades."""
    filled = df[df["status"] == "filled"]
    if filled.empty:
        return
    for col in ("submit_latency_us", "fill_latency_us"):
        if col not in filled.columns:
            raise AssertionError(f"V6 FAIL: column '{col}' missing from execution_results")
        null_count = filled[col].isna().sum()
        if null_count > 0:
            raise AssertionError(f"V6 FAIL: {null_count} filled trades have NULL {col}")


def assert_v7(df: pd.DataFrame) -> None:
    """V7: no positive net_pnl without net_edge > 0."""
    if df.empty:
        return
    false_pos = df[(df["net_pnl"] > 0) & (df["expected_edge"] <= 0)]
    if not false_pos.empty:
        raise AssertionError(
            f"V7 FAIL: {len(false_pos)} trades show positive PnL but expected_edge <= 0. "
            f"Sample: {false_pos['correlation_id'].head(3).tolist()}"
        )


def run_all() -> None:
    """Run all invariant checks against the live database."""
    cfg = config.load()

    df_signals = pd.DataFrame(db.query(
        "SELECT correlation_id, decision, spread FROM signal_decisions WHERE strategy = 'sum_arb'"
    ))
    df_risk = pd.DataFrame(db.query("SELECT correlation_id FROM risk_decisions"))
    df_exec = pd.DataFrame(db.query(
        "SELECT correlation_id, status, fill_size, net_pnl, expected_edge, "
        "submit_latency_us, fill_latency_us FROM execution_results"
    ))

    assert_v1(df_signals)
    print("V1 PASS")

    assert_v2(df_signals, df_risk)
    print("V2 PASS")

    filled = df_exec[df_exec["status"] == "filled"].copy() if not df_exec.empty else df_exec
    if not filled.empty:
        if "spread" not in filled.columns:
            spread_map = df_signals.set_index("correlation_id")["spread"]
            filled["spread"] = filled["correlation_id"].map(spread_map)
        assert_v4(filled, cfg["fee_bps"], cfg["slippage_bps"])
        print("V4 PASS")
        assert_v6(df_exec)
        print("V6 PASS")
        assert_v7(filled)
        print("V7 PASS")
    else:
        print("V4/V6/V7: no filled trades to check")

    print("All invariants PASS")


if __name__ == "__main__":
    run_all()
