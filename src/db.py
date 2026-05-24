"""
Database connection for backtest analysis (I.1, I.2, I.3).
Reads RAILWAY_DATABASE_URL from env or .env.railway at repo root.
"""
import os
from pathlib import Path

import psycopg2
import psycopg2.extras

_REPO_ROOT = Path(__file__).resolve().parents[1]


def get_url() -> str:
    url = os.environ.get("RAILWAY_DATABASE_URL", "")
    if url:
        return url
    env_file = _REPO_ROOT / ".env.railway"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "RAILWAY_DATABASE_URL":
                return val.strip()
    raise EnvironmentError(
        "RAILWAY_DATABASE_URL not set. Add to env or .env.railway:\n"
        "  RAILWAY_DATABASE_URL=postgresql://..."
    )


def connect():
    return psycopg2.connect(get_url())


def query(sql: str, params=None) -> list[dict]:
    conn = connect()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()
