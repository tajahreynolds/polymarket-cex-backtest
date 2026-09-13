"""Fetch daily OHLCV for a multi-asset ETF universe from a GitHub mirror of the
Stooq-derived "Huge Stock Market Dataset" (split/dividend adjusted, ends 2017-11).
Only GitHub is reachable from this environment, so raw.githubusercontent is the transport.
"""
import concurrent.futures as cf, io, pathlib, sys
import pandas as pd, urllib.request

BASE = "https://raw.githubusercontent.com/neo-zhao/CMSC320_Final_Tutorial_Huge_Stock_Market_Dataset/main/ETFs/{t}.us.txt"
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "kaggle_etfs"
OUT.mkdir(parents=True, exist_ok=True)

UNIVERSE = """
SPY QQQ IWM MDY EFA EEM VGK EWJ VTI VEU
TLT IEF SHY LQD HYG AGG TIP BND SHV BIL
GLD SLV DBC GSG VNQ IYR RWX
XLK XLF XLE XLV XLI XLP XLU XLY XLB
DIA EWZ EWG EWU EWA EWC EWH EWS EWT EWY FXI
PFF EMB BWX IGOV MUB
""".split()

def grab(t):
    try:
        with urllib.request.urlopen(BASE.format(t=t.lower()), timeout=60) as r:
            raw = r.read().decode()
    except Exception as e:
        return t, f"ERR {e}"
    df = pd.read_csv(io.StringIO(raw), parse_dates=["Date"])
    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].sort_values("Date")
    df.to_csv(OUT / f"{t}.csv", index=False)
    return t, f"{len(df)} rows {df.Date.min().date()}..{df.Date.max().date()}"

if __name__ == "__main__":
    with cf.ThreadPoolExecutor(12) as ex:
        for t, msg in ex.map(grab, UNIVERSE):
            print(f"{t:6s} {msg}")
