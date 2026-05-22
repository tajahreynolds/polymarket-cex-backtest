"""
Pull Polymarket BTC-related market data via the Gamma API.

Step 1: discover BTC markets active in the target period
Step 2: for each market, pull price history via the CLOB prices-history endpoint
Step 3: write one CSV per market to data/raw/polymarket/

Usage:
    python3 data/pull_polymarket.py --out data/raw/polymarket/

Gamma API base: https://gamma-api.polymarket.com
CLOB API base:  https://clob.polymarket.com
"""
import argparse
import csv
import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE  = "https://clob.polymarket.com"

# Unix timestamps for Dec 2025 – Apr 2026
START_TS = int(datetime(2025, 12, 1, tzinfo=timezone.utc).timestamp())
END_TS   = int(datetime(2026,  4, 30, 23, 59, 59, tzinfo=timezone.utc).timestamp())


def get_json(url: str, retries: int = 3) -> dict | list | None:
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            print(f"    attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    return None


def find_btc_markets() -> list[dict]:
    print("Fetching BTC markets from Gamma API...")
    markets = []
    offset = 0
    limit  = 100

    while True:
        url = f"{GAMMA_BASE}/markets?limit={limit}&offset={offset}&active=false"
        data = get_json(url)
        if not data:
            break
        if isinstance(data, dict):
            items = data.get("markets", data.get("data", []))
        else:
            items = data

        if not items:
            break

        for m in items:
            question = (m.get("question") or m.get("title") or "").lower()
            slug = (m.get("slug") or "").lower()
            # Filter: BTC price contracts
            if ("btc" in question or "bitcoin" in question) and \
               ("above" in question or "below" in question or "price" in question or "btc" in slug):
                markets.append(m)
                print(f"  found: {m.get('question') or m.get('slug')}")

        offset += limit
        if len(items) < limit:
            break
        time.sleep(0.15)  # respect rate limit

    print(f"  {len(markets)} BTC markets found")
    return markets


def pull_price_history(condition_id: str, out_dir: str, slug: str) -> str | None:
    safe_slug = slug.replace("/", "_").replace(" ", "-")[:60]
    dest = os.path.join(out_dir, f"{safe_slug}.csv")

    if os.path.exists(dest):
        print(f"  {slug}: exists, skipping")
        return dest

    url = (
        f"{CLOB_BASE}/prices-history"
        f"?market={urllib.parse.quote(condition_id)}"
        f"&startTs={START_TS}&endTs={END_TS}&fidelity=60"
    )
    print(f"  pulling prices: {slug} ...")
    data = get_json(url)
    if not data:
        print(f"  {slug}: no data")
        return None

    if isinstance(data, list):
        history = data
    else:
        history = data.get("history", [])
    if not history:
        print(f"  {slug}: empty history")
        return None

    with open(dest, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["t", "p"])
        w.writeheader()
        for row in history:
            w.writerow({"t": row.get("t") or row.get("ts"), "p": row.get("p") or row.get("price")})

    print(f"  {slug}: {len(history)} rows → {dest}")
    return dest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/raw/polymarket")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    markets = find_btc_markets()
    if not markets:
        print("No markets found. Check API availability.")
        return

    print(f"\nPulling price history for {len(markets)} markets...")
    success = 0
    for m in markets:
        condition_id = m.get("conditionId") or m.get("condition_id") or m.get("clob_token_ids", [None])[0]
        slug = m.get("slug") or m.get("question") or condition_id
        if not condition_id:
            print(f"  skipping {slug}: no condition_id")
            continue
        path = pull_price_history(condition_id, args.out, slug)
        if path:
            success += 1
        time.sleep(0.1)

    print(f"\nDone. {success}/{len(markets)} markets saved to {args.out}/")


if __name__ == "__main__":
    main()
