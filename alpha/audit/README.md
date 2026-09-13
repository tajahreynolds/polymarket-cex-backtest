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

## Results

### 1. No look-ahead remains — corrupt-the-future, five cut points

Every bar after the cut replaced with an unrelated random walk spliced on
continuously, the whole pipeline rerun, and every trade entered before the cut
required to be bit-identical on `entry_ts`, `entry_idx`, `direction`,
`stop_pct`, `pd_pos`, `mfi` and `bars_to_fill` — so zone geometry, stop
placement and the money-flow gate are all covered, not just which trades fired.

```
cut    trades before cut   identical
30%           219             pass
45%           347             pass
60%           468             pass
75%           598             pass
90%           726             pass
```

The bug `lookahead_probe.py` documents appears to have been the only one in the
entry path.

### 2. The fairness invariant holds

`run_arms` specifies that `null_dir` — same fill, same price, same bar,
direction reversed — must midpoint with the signal at minus the modelled fee.
Pooling 18 independent random walks at 3% daily vol:

```
midpoint of gross   +0.0068   sd 0.0171   t = +1.69     (invariant: 0)
```

And it holds across every variant tested, so it is not an artefact of one
data-generating choice:

| variant | midpoint | t |
|---|---|---|
| base, 3% daily vol | +0.0107 | 1.96 |
| price-martingale (Itô term removed) | +0.0104 | 1.55 |
| low vol, 1.5% | +0.0020 | 1.02 |
| high vol, 6% | +0.0009 | 0.09 |

The exit model is direction-symmetric. That is a clean pass on exactly what the
control was built to detect.

### 3. But the per-arm null is not zero

On data containing nothing, pooled over 18 random walks:

```
fvg         -0.0495   sd 0.0493   t =  -4.26     negative in 15/18 runs
null_dir    +0.0631   sd 0.0459   t =  +5.83
null_flip   +0.1264   sd 0.0461   t = +11.63     positive in 18/18 runs
```

They cancel in the midpoint, so this is structural to the entry/exit
construction rather than an asymmetry bug. It survives removing the geometric
drift, and the flip arm's bias **scales with volatility** — +0.056R at 1.5%
daily vol, +0.127R at 3%, +0.207R at 6% — which is the signature of a
construction effect rather than anything in the data.

Two consequences:

1. `null_flip` is positive on pure noise, where there is nothing to invert. So
   *"the direction-flipping control is positive on all twelve"* is close to this
   harness's default behaviour and cannot on its own support the stronger claim
   that the edge was inverted. Anyone reading that line and trading the flip
   would be trading a construction artefact.
2. Zero is the wrong yardstick for this engine; `null_dir` is the right one, and
   the repo already builds it.

The retraction's actual conclusion — the strategy is not profitable, do not
build the engine — is untouched by either point.

## A data-labelling bug found on the way

`data/yf/*-1m-*.csv` are **hourly** bars, not 1-minute: median gap 60 minutes and
zero contiguous 1-minute intervals, spanning 2024-04 to 2026-09. `load_1m` reads
each row as a minute, so any run against that directory has every timeframe off
by a factor of 60 — a `--zone-hours 12` run is really building 30-day zones.
