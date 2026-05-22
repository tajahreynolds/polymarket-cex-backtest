"""
Pull Binance BTCUSDT 1-minute OHLCV from data.binance.vision for a date range.
Downloads monthly zip files, extracts CSVs, merges into one file per month.

Usage:
    python3 data/pull_binance.py --start 2025-12 --end 2026-04 --out data/raw/binance/

Output columns (Binance klines format):
    open_time, open, high, low, close, volume, close_time, ...
"""
import argparse
import io
import os
import urllib.request
import zipfile

BASE_URL = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m"


def month_range(start: str, end: str):
    y0, m0 = int(start[:4]), int(start[5:7])
    y1, m1 = int(end[:4]), int(end[5:7])
    while (y0, m0) <= (y1, m1):
        yield f"{y0:04d}-{m0:02d}"
        m0 += 1
        if m0 > 12:
            m0 = 1
            y0 += 1


def download_month(ym: str, out_dir: str) -> str | None:
    fname = f"BTCUSDT-1m-{ym}.zip"
    url = f"{BASE_URL}/{fname}"
    dest_csv = os.path.join(out_dir, f"BTCUSDT-1m-{ym}.csv")

    if os.path.exists(dest_csv):
        print(f"  {ym}: already exists, skipping")
        return dest_csv

    print(f"  {ym}: downloading {url} ...")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
    except Exception as e:
        print(f"  {ym}: FAILED — {e}")
        return None

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        inner = [n for n in zf.namelist() if n.endswith(".csv")]
        if not inner:
            print(f"  {ym}: no CSV inside zip")
            return None
        with zf.open(inner[0]) as f:
            with open(dest_csv, "wb") as out:
                out.write(f.read())

    print(f"  {ym}: saved → {dest_csv}")
    return dest_csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-12", help="YYYY-MM")
    parser.add_argument("--end",   default="2026-04", help="YYYY-MM")
    parser.add_argument("--out",   default="data/raw/binance")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    print(f"Downloading Binance BTCUSDT 1m klines: {args.start} → {args.end}")

    downloaded = []
    for ym in month_range(args.start, args.end):
        path = download_month(ym, args.out)
        if path:
            downloaded.append(path)

    print(f"\nDone. {len(downloaded)} months downloaded to {args.out}/")
    print("Columns: open_time_ms, open, high, low, close, volume, close_time_ms, ...")


if __name__ == "__main__":
    main()
