"""Adapter for the `trading` repo's ETF panel: 28 cross-asset ETFs, 1993-2026.

Format is date,open,close,adj,volume - there is no high or low, so the
Yang-Zhang estimator degrades to its overnight+intraday variance terms (the
Rogers-Satchell part goes to zero when high=low=close). That is a less efficient
volatility estimate than the full-OHLC version but an unbiased one.

The adjustment factor adj/close is applied to the open so that open and close
live on the same adjusted scale; mixing a raw open with an adjusted close would
manufacture a return every ex-dividend date.
"""
import pathlib
import numpy as np, pandas as pd

SRC = pathlib.Path("/home/user/trading/data/etf")

# Deliberately cross-asset: equities, rates, credit, FX, commodities, property.
# FX and commodities are what my own panel lacked, and the reason its effective
# breadth was 1.7 bets.
UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "EWJ", "VGK",
            "SHY", "IEF", "TLT", "TIP", "LQD", "HYG",
            "FXA", "FXB", "FXE", "FXF", "FXY", "UUP",
            "GLD", "SLV", "DBC", "DBA", "USO", "UNG",
            "VNQ", "RWX"]


def load(tickers=None):
    tickers = tickers or UNIVERSE
    frames = {}
    for t in tickers:
        f = SRC / f"{t}.csv"
        if not f.exists():
            continue
        d = pd.read_csv(f, parse_dates=["date"]).set_index("date").sort_index()
        factor = d["adj"] / d["close"]
        frames[t] = pd.DataFrame({
            "open": d["open"] * factor,
            "close": d["adj"],
            "volume": d["volume"],
        })

    cal = frames["SPY"].index
    panel = {}
    for fld in ("open", "close"):
        panel[fld] = pd.DataFrame({t: d[fld] for t, d in frames.items()}).reindex(cal)
    panel["volume"] = pd.DataFrame({t: d["volume"] for t, d in frames.items()}).reindex(cal)
    # no intrabar range in this source
    panel["high"] = panel["close"]
    panel["low"] = panel["close"]
    panel["tradable"] = panel["close"].notna() & (panel["volume"].fillna(0) > 0)
    return panel


def rf_from_irx(cal):
    """13-week T-bill yield from the repo's IRX file (date,rate; already a
    decimal fraction, not percent), converted to a daily rate."""
    d = pd.read_csv(SRC / "IRX.csv", parse_dates=["date"]).set_index("date").sort_index()
    ann = d["rate"].reindex(cal.union(d.index)).ffill().reindex(cal)
    return (ann.fillna(0.0) / 252.0)


if __name__ == "__main__":
    p = load()
    c = p["close"]
    print(f"{c.shape[1]} tickers, {c.shape[0]} bars, {c.index.min().date()}..{c.index.max().date()}")
    n = p["tradable"].sum(axis=1)
    print(n.groupby(n.index.year).mean().round(0).astype(int).to_string())
