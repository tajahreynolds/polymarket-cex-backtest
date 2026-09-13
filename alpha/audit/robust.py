"""Is the -0.062R noise baseline structural, or an artefact of how I generated
the data? Vary the two things that could plausibly cause it: the price-space
drift of a geometric walk, and the volatility level."""
import subprocess, sys, pathlib, shutil, glob
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import synth

ENGINE = "/home/user/trading"
CFG = ["--zone-types", "level", "--zone-hours", "12", "--trigger-minutes", "1",
       "--swing-lens", "50", "--internal-lens", "5", "--thresholds", "1.0",
       "--rrs", "3.0", "--min-stop-pcts", "1.0", "--max-holds", "480",
       "--fill-through-bps", "5"]

# martingale_in_price sets the log drift to -sigma^2/2 so E[P_t] = P_0 exactly,
# removing the Ito term as a candidate explanation.
VARIANTS = {
    "base vol 3%":        dict(daily_vol=0.03, martingale=False),
    "price-martingale":   dict(daily_vol=0.03, martingale=True),
    "low vol 1.5%":       dict(daily_vol=0.015, martingale=False),
    "high vol 6%":        dict(daily_vol=0.06, martingale=False),
}


def one(tag, seed, daily_vol, martingale):
    sub = synth.SUBSTEPS
    drift = 0.0
    if martingale:
        sig = daily_vol / np.sqrt(1440 * sub)
        drift = -0.5 * sig ** 2 * (365 * 1440 * sub)   # annualised log drift
    df = synth.make(1_200_000, seed=seed, daily_vol=daily_vol, drift_ann=drift)
    sym, d, out = f"{tag}{seed}", f"/tmp/rb_{tag}{seed}", f"/tmp/rb_{tag}{seed}.csv"
    synth.write(df, sym, d)
    r = subprocess.run(["python3", "smc_backtest.py", "--symbols", sym,
                        "--raw", d, "--out", out] + CFG,
                       cwd=ENGINE, capture_output=True, text=True)
    shutil.rmtree(d, ignore_errors=True)
    return out if r.returncode == 0 else None


if __name__ == "__main__":
    print(f"{'variant':20s}{'fvg gross':>11s}{'t':>7s}{'null_dir':>10s}"
          f"{'null_flip':>11s}{'midpoint':>10s}{'t_mid':>7s}")
    for i, (name, kw) in enumerate(VARIANTS.items()):
        tag = f"V{i}"
        outs = [one(tag, 2000 + i * 100 + s, kw["daily_vol"], kw["martingale"])
                for s in range(1, 7)]
        d = pd.concat([pd.read_csv(o).assign(seed=j) for j, o in enumerate(outs) if o])
        p = d.pivot_table(index="seed", columns="arm", values="gross_r")
        mid = (p["fvg"] + p["null_dir"]) / 2
        t = lambda x: x.mean() / (x.std() / np.sqrt(len(x)))
        print(f"{name:20s}{p['fvg'].mean():>11.4f}{t(p['fvg']):>7.2f}"
              f"{p['null_dir'].mean():>10.4f}{p['null_flip'].mean():>11.4f}"
              f"{mid.mean():>10.4f}{t(mid):>7.2f}")
