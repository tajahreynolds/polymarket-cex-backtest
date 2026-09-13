"""Run the trading repo's engine over many independent random walks.

The engine's own comment on the null_dir arm states the invariant being tested:
"This one must come out near zero. If it does not, the result is an artefact of
the exit model rather than a signal."
"""
import subprocess, sys, pathlib, shutil
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import synth

ENGINE = "/home/user/trading"
CFG = ["--zone-types", "level", "--zone-hours", "12", "--trigger-minutes", "1",
       "--swing-lens", "50", "--internal-lens", "5", "--thresholds", "1.0",
       "--rrs", "3.0", "--min-stop-pcts", "1.0", "--max-holds", "480",
       "--fill-through-bps", "5"]

N_BARS, N_SEEDS = 1_200_000, int(sys.argv[1]) if len(sys.argv) > 1 else 10
for s in range(1, N_SEEDS + 1):
    sym, d, out = f"NS{s}", f"/tmp/ns{s}", f"/tmp/ns_{s}.csv"
    synth.write(synth.make(N_BARS, seed=1000 + s), sym, d)
    r = subprocess.run(["python3", "smc_backtest.py", "--symbols", sym,
                        "--raw", d, "--out", out] + CFG,
                       cwd=ENGINE, capture_output=True, text=True)
    shutil.rmtree(d, ignore_errors=True)
    print(f"seed {s}: rc={r.returncode}", flush=True)
    if r.returncode:
        print(r.stderr[-500:])
