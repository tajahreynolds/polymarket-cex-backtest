"""
Export the Railway Postgres signals table to a timestamped CSV.

Reads DATABASE_URL from:
  1. RAILWAY_DATABASE_URL env var
  2. .env.railway file in repo root (key=value format, no quotes needed)

Usage:
  python3 data/export_signals.py
  python3 data/export_signals.py --out data/raw/signals/

Cron (every 6 hours):
  0 */6 * * * cd /home/tajah/projects/polymarket-cex-backtest && python3 data/export_signals.py >> /tmp/export_signals.log 2>&1
"""
import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_database_url() -> str:
    url = os.environ.get("RAILWAY_DATABASE_URL", "")
    if url:
        return url

    env_file = REPO_ROOT / ".env.railway"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "RAILWAY_DATABASE_URL":
                return val.strip()

    return ""


def export(database_url: str, out_dir: Path) -> None:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("psycopg2 not installed — run: pip3 install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"signals_{ts}.csv"

    conn = psycopg2.connect(database_url)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT
                    id,
                    contract_id,
                    direction,
                    implied_prob_market,
                    implied_prob_real,
                    spread,
                    expected_edge,
                    decision,
                    rejection_reason,
                    decision_timestamp_ns,
                    created_at
                FROM signals
                ORDER BY decision_timestamp_ns ASC
            """)
            rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        print("No rows in signals table.")
        return

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    print(f"Exported {len(rows)} rows → {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/raw/signals", help="Output directory")
    args = parser.parse_args()

    database_url = load_database_url()
    if not database_url:
        print(
            "No DATABASE_URL found.\n"
            "Set RAILWAY_DATABASE_URL env var or create .env.railway with:\n"
            "  RAILWAY_DATABASE_URL=postgresql://...",
            file=sys.stderr,
        )
        sys.exit(1)

    export(database_url, Path(args.out))


if __name__ == "__main__":
    main()
