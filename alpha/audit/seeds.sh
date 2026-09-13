#!/bin/bash
# Same engine, same locked config, independent random walks. On noise every arm
# should land near zero gross; anything that is consistently signed across seeds
# is the engine, not the data.
set -u
for s in 1 2 3 4 5; do
  python3 /home/user/polymarket-cex-backtest/alpha/audit/synth.py 1200000 $s SY$s /tmp/synth$s >/dev/null
  ( cd /home/user/trading && python3 smc_backtest.py --symbols SY$s --raw /tmp/synth$s \
      --zone-types level --zone-hours 12 --trigger-minutes 1 --swing-lens 50 \
      --internal-lens 5 --thresholds 1.0 --rrs 3.0 --min-stop-pcts 1.0 \
      --max-holds 480 --fill-through-bps 5 --out /tmp/synth_s$s.csv >/dev/null 2>&1 )
  echo "seed $s done"
done
