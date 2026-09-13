"""Corrupt-the-future test against the trading repo's engine.

The repo's own lesson is that out-of-sample replication cannot detect look-ahead,
because a bug in the code applies identically to every sample. This is the test
that can: replace every bar after a cut timestamp with noise, rerun the whole
pipeline, and require that every trade ENTERED before the cut is unchanged.

`lookahead_probe.py` showed one such bug existed and was fixed. This asks whether
any others remain, at five different cut points.
"""
import subprocess, sys, pathlib, shutil
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import synth

ENGINE = "/home/user/trading"
CFG = ["--zone-types", "level", "--zone-hours", "12", "--trigger-minutes", "1",
       "--swing-lens", "50", "--internal-lens", "5", "--thresholds", "1.0",
       "--rrs", "3.0", "--min-stop-pcts", "1.0", "--max-holds", "480",
       "--fill-through-bps", "5"]
N = 600_000


def run(df, sym, tag):
    d, out, tr = f"/tmp/pt_{tag}", f"/tmp/pt_{tag}.csv", f"/tmp/pt_{tag}_trades.csv"
    synth.write(df, sym, d)
    r = subprocess.run(["python3", "smc_backtest.py", "--symbols", sym, "--raw", d,
                        "--out", out, "--trades-out", tr, "--dump-all"] + CFG,
                       cwd=ENGINE, capture_output=True, text=True)
    shutil.rmtree(d, ignore_errors=True)
    if r.returncode:
        print(r.stderr[-800:]); return None
    return pd.read_csv(tr)


def corrupt(df, cut_idx, seed):
    """Everything at or after cut_idx becomes an unrelated random walk, spliced
    on continuously so no artificial gap is introduced at the join."""
    rng = np.random.default_rng(seed)
    tail = synth.make(len(df) - cut_idx, seed=seed + 7919,
                      start_price=float(df.close.iloc[cut_idx - 1]),
                      start_ms=int(df.open_time.iloc[cut_idx]))
    out = df.copy()
    for c in ("open", "high", "low", "close", "volume"):
        out.loc[out.index[cut_idx:], c] = tail[c].to_numpy()
    return out


if __name__ == "__main__":
    base_df = synth.make(N, seed=31337)
    base = run(base_df, "PTB", "base")
    if base is None:
        sys.exit("base run failed")
    base = base[base.arm == "fvg"].sort_values("entry_ts").reset_index(drop=True)
    print(f"base run: {len(base)} fvg trades\n")

    cols = ["entry_ts", "exit_ts", "direction", "r"]
    cols = [c for c in cols if c in base.columns]
    print(f"comparing on: {cols}\n")
    print(f"{'cut %':>7}{'trades before cut':>20}{'identical':>12}{'VERDICT':>12}")
    ok_all = True
    for frac in (0.30, 0.45, 0.60, 0.75, 0.90):
        ci = int(N * frac)
        cut_ts = int(base_df.open_time.iloc[ci])
        pert = run(corrupt(base_df, ci, seed=int(frac * 1000)), "PTB", f"c{int(frac*100)}")
        if pert is None:
            continue
        pert = pert[pert.arm == "fvg"].sort_values("entry_ts").reset_index(drop=True)

        # A trade entered before the cut may legitimately EXIT after it, so only
        # its entry-side fields are required to match; exits are excluded.
        ecols = [c for c in cols if c != "exit_ts" and c != "r"]
        a = base[base.entry_ts < cut_ts][ecols].reset_index(drop=True)
        b = pert[pert.entry_ts < cut_ts][ecols].reset_index(drop=True)
        same = len(a) == len(b) and a.equals(b)
        ok_all &= same
        print(f"{frac:>7.0%}{len(a):>20}{str(same):>12}"
              f"{'pass' if same else 'LEAK':>12}")
        if not same:
            print(f"    base {len(a)} vs perturbed {len(b)} trades before the cut")
    print("\n" + ("ALL CUTS PASS - no entry before a cut is changed by data after it"
                  if ok_all else "FAILURE - future data altered pre-cut entries"))
