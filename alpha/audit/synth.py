"""Synthetic 1-minute OHLCV with no predictable structure.

A driftless random walk contains no edge by construction. Any backtest that
reports significantly positive expectancy on it is reading information it should
not have. This is a stronger test than a holdout, because - as `trading`'s own
README puts it - out-of-sample replication cannot detect look-ahead: a bug in the
code applies identically to every sample.

Bars are built from a sub-minute path so that high and low are genuine extremes
of a traded path, not synthetic envelopes. Fill logic keys off high/low, so
getting that wrong would test the wrong thing.
"""
import numpy as np, pandas as pd, pathlib

SUBSTEPS = 12
MIN_PER_MONTH = 43_200


def make(n_minutes, seed=0, daily_vol=0.03, start_price=50_000.0,
         start_ms=1_600_000_000_000, drift_ann=0.0):
    rng = np.random.default_rng(seed)
    sig = daily_vol / np.sqrt(1440 * SUBSTEPS)
    mu = drift_ann / (365 * 1440 * SUBSTEPS)
    steps = rng.normal(mu, sig, n_minutes * SUBSTEPS)
    path = start_price * np.exp(np.cumsum(steps))
    p = path.reshape(n_minutes, SUBSTEPS)

    prev_close = np.empty(n_minutes)
    prev_close[0] = start_price
    prev_close[1:] = p[:-1, -1]

    df = pd.DataFrame({
        "open_time": start_ms + np.arange(n_minutes, dtype="int64") * 60_000,
        "open": prev_close,
        "high": np.maximum(p.max(axis=1), prev_close),
        "low": np.minimum(p.min(axis=1), prev_close),
        "close": p[:, -1],
        "volume": rng.lognormal(3.0, 1.0, n_minutes),
    })
    assert (df.high >= df[["open", "close"]].max(axis=1) - 1e-9).all()
    assert (df.low <= df[["open", "close"]].min(axis=1) + 1e-9).all()
    return df


def write(df, symbol, out_dir):
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    for f in out.glob(f"{symbol}-1m-*.csv"):
        f.unlink()
    for i in range(0, len(df), MIN_PER_MONTH):
        chunk = df.iloc[i:i + MIN_PER_MONTH]
        chunk.to_csv(out / f"{symbol}-1m-{2000 + i // MIN_PER_MONTH:04d}-01.csv",
                     index=False)
    return len(df)


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1_200_000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    sym = sys.argv[3] if len(sys.argv) > 3 else "SYNTH"
    d = sys.argv[4] if len(sys.argv) > 4 else "/tmp/synthdata"
    df = make(n, seed=seed)
    print(f"{sym}: {write(df, sym, d)} bars -> {d}  "
          f"realised daily vol {np.log(df.close).diff().std()*np.sqrt(1440):.2%}")
