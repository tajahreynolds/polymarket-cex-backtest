"""Build the full 1,344-ETF panel as parquet, keyed off SPY's trading calendar."""
import pathlib, sys
import numpy as np, pandas as pd

SRC = pathlib.Path("/tmp/etfs/ETFs")
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "wide"
OUT.mkdir(parents=True, exist_ok=True)
COLS = ["Open", "High", "Low", "Close", "Volume"]

frames = {}
for f in sorted(SRC.glob("*.txt")):
    t = f.stem.replace(".us", "").upper()
    try:
        df = pd.read_csv(f, parse_dates=["Date"], usecols=["Date"] + COLS)
    except Exception:
        continue
    if len(df) < 60:
        continue
    frames[t] = df.set_index("Date").sort_index()

cal = frames["SPY"].index
print(f"loaded {len(frames)} tickers; calendar {len(cal)} bars")
for c in COLS:
    wide = pd.DataFrame({t: d[c] for t, d in frames.items()}).reindex(cal).astype("float32")
    wide.to_parquet(OUT / f"{c.lower()}.parquet")
    print(f"  {c}: {wide.shape}")
