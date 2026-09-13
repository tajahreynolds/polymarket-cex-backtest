# audit/ — testing the `trading` repo's SMC engine

`trading/README.md` states the lesson this directory acts on:

> Out-of-sample replication cannot detect look-ahead. The bias lived in the code,
> not the data, so it applied identically to every set.

Two tests that can, neither of which needs the original crypto data:

| script | what it does |
|---|---|
| `synth.py` | generates 1-minute OHLCV from a driftless random walk, bars built from a 12-step sub-minute path so highs and lows are genuine extremes of a traded path |
| `run_seeds.py` | runs the engine over many independent random walks at the locked config |
| `analyse.py` | checks the engine's own documented invariants on that noise |
| `robust.py` | varies geometric-walk drift and volatility, to separate structural results from artefacts of how the data was generated |
| `perturb.py` | replaces every bar after a cut timestamp with unrelated noise and requires that trades entered before the cut are unchanged, at five cut points |

## Why a random walk is the right instrument

A driftless random walk contains no edge by construction. Any arm that scores
significantly away from its modelled fee is reading something it should not, or
is measuring the harness rather than the market. Unlike a holdout, it has a known
right answer.

## Results so far (12 seeds x 1.2M minutes)

**The engine's fairness invariant passes.** `run_arms` documents that the
`null_dir` control — same fill, same price, same bar, direction reversed — must
midpoint with the signal at minus the modelled fee. It does:

```
midpoint of gross (should be 0):  +0.0049   sd 0.0189   t = +0.89
residual vs -fee:                 +0.0049   sd 0.0189   t = +0.89
```

The exit model is direction-symmetric. That is a clean pass on the thing the
control was built to detect.

**But the harness's null is not zero.** On data with nothing in it:

```
fvg        gross -0.0623   t =  -5.28
null_dir   gross +0.0720   t =  +6.49
null_flip  gross +0.1318   t = +11.37
```

The offsets cancel in the midpoint, so this is not an asymmetry bug — it is a
structural property of the entry and exit construction. Two consequences:

1. `null_flip` is positive on pure noise, where there is nothing to invert. So
   "the direction-flipping control is positive on all twelve" is not by itself
   evidence that the edge was inverted; it is close to what this harness does by
   default. The retraction's conclusion — the strategy is not profitable — is
   unaffected. The inference that the signal is backwards is not supported by
   that control alone.
2. Zero is the wrong baseline for this engine. `null_dir` is the right one, and
   the repo already builds it.
