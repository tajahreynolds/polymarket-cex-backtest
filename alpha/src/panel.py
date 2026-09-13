"""Build an aligned daily OHLCV panel plus a cash/risk-free series."""
import pathlib
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "kaggle_etfs"

FIELDS = ["Open", "High", "Low", "Close", "Volume"]


def load_panel(min_rows: int = 500) -> dict[str, pd.DataFrame]:
    frames = {}
    for f in sorted(RAW.glob("*.csv")):
        df = pd.read_csv(f, parse_dates=["Date"]).set_index("Date").sort_index()
        if len(df) < min_rows:
            continue
        frames[f.stem] = df

    cal = frames["SPY"].index
    panel = {}
    for fld in FIELDS:
        wide = pd.DataFrame({t: d[fld] for t, d in frames.items()})
        panel[fld.lower()] = wide.reindex(cal)
    # A ticker is tradable only where it has a genuine print; forward-filling
    # prices would invent liquidity, so keep NaNs and mask them in the engine.
    panel["tradable"] = panel["close"].notna() & (panel["volume"].fillna(0) > 0)
    return panel


def load_rf() -> pd.Series:
    """Annualised short rate in percent, daily, forward-filled onto the calendar."""
    d = pd.read_csv(ROOT / "data" / "us_market_data.csv", parse_dates=["Date"])
    return d.set_index("Date")["Risk Free Rate"].sort_index() / 100.0


def rf_daily(cal: pd.DatetimeIndex) -> pd.Series:
    ann = load_rf().reindex(cal.union(load_rf().index)).ffill().reindex(cal)
    return (ann.fillna(0.0) / 252.0)


if __name__ == "__main__":
    p = load_panel()
    c = p["close"]
    print(f"tickers={c.shape[1]} dates={c.shape[0]} {c.index.min().date()}..{c.index.max().date()}")
    counts = p["tradable"].sum(axis=1)
    print("tradable breadth by year:")
    print(counts.groupby(counts.index.year).mean().round(1).to_string())
    r = rf_daily(c.index)
    print(f"rf daily mean {r.mean()*252:.4%} ann; missing={r.isna().sum()}")


# ------------------------------------------- full 1,320-ETF point-in-time panel
WIDE = ROOT / "data" / "wide"


def load_wide() -> dict[str, pd.DataFrame]:
    p = {f: pd.read_parquet(WIDE / f"{f}.parquet").astype("float64")
         for f in ("open", "high", "low", "close", "volume")}
    p["tradable"] = p["close"].notna() & (p["volume"].fillna(0) > 0)
    return p


def eligible(panel, min_dollar_vol=10e6, min_history=252, adv_window=60):
    """Point-in-time investability: enough history to compute a signal, and
    enough traded value to actually fill. Uses only data up to each date.

    Note dollar volume is computed on dividend-adjusted prices, so it understates
    true notional in early years by the cumulative dividend factor (~14% for SPY
    in 2005). The screen is therefore slightly stricter the further back you go.
    """
    dv = (panel["close"] * panel["volume"]).rolling(adv_window, min_periods=adv_window // 2).median()
    age = panel["tradable"].cumsum()
    return (dv >= min_dollar_vol) & (age >= min_history) & panel["tradable"]
