"""Check the engine's own documented invariants on pure noise.

From smc_backtest.run_arms:
  null_dir  - "must land at minus the modelled fee" when midpointed with the
              signal; same fill, same price, same bar, direction reversed.
  null_dir  - "This one must come out near zero. If it does not, the result is
              an artefact of the exit model rather than a signal."
"""
import glob
import numpy as np, pandas as pd

rows = []
for f in sorted(glob.glob("/tmp/ns_*.csv")):
    d = pd.read_csv(f)
    d["seed"] = int(f.split("_")[1].split(".")[0])
    rows.append(d)
d = pd.concat(rows)
n_seeds = d.seed.nunique()

piv = d.pivot_table(index="seed", columns="arm",
                    values=["gross_r", "expectancy_r", "fee_r", "trades"])
g, e, fee = piv["gross_r"], piv["expectancy_r"], piv["fee_r"]

print(f"=== {n_seeds} independent random walks, 1.2M minutes each ===")
print(f"{'arm':14s}{'mean gross':>12s}{'sd':>9s}{'t':>7s}{'mean net':>10s}{'trades':>9s}")
for a in ["fvg", "null_dir", "null_flip", "null_paired", "fvg_long", "fvg_short"]:
    if a not in g:
        continue
    x = g[a].dropna()
    t = x.mean() / (x.std() / np.sqrt(len(x)))
    print(f"{a:14s}{x.mean():>12.4f}{x.std():>9.4f}{t:>7.2f}"
          f"{e[a].mean():>10.4f}{piv['trades'][a].mean():>9.0f}")

print("\n=== the engine's own fairness identity ===")
mid_g = (g["fvg"] + g["null_dir"]) / 2
mid_n = (e["fvg"] + e["null_dir"]) / 2
mfee = fee[["fvg", "null_dir"]].mean(axis=1)
tg = mid_g.mean() / (mid_g.std() / np.sqrt(len(mid_g)))
resid = mid_n + mfee                      # should be 0: midpoint == -fee
tr = resid.mean() / (resid.std() / np.sqrt(len(resid)))
print(f"midpoint of gross  (should be 0.0000): {mid_g.mean():+.4f}  "
      f"sd {mid_g.std():.4f}  t = {tg:+.2f}")
print(f"midpoint of net    (should be -fee):   {mid_n.mean():+.4f}  "
      f"vs -fee = {-mfee.mean():+.4f}")
print(f"residual                               {resid.mean():+.4f}  "
      f"sd {resid.std():.4f}  t = {tr:+.2f}")
print(f"\nper-seed gross midpoint: "
      f"{' '.join(f'{v:+.3f}' for v in mid_g.values)}")
print(f"seeds with positive midpoint: {(mid_g > 0).sum()}/{len(mid_g)}")
