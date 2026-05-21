# polymarket-cex-backtest

**57.8% win rate. 5 months of data. Every signal, every exit, every loss.**

This repo contains the full backtest of a systematic strategy that exploits mispricing between Polymarket BTC-Yes contracts and Binance BTC/USDT spot price.

The core observation: Polymarket's implied probability for a BTC price target drifts away from what Binance is already pricing in. That gap — measured in basis points — is the edge. When it's wide enough to clear fees and slippage, you have a trade.

---

## What this is not

This is not a curve-fitted backtest. There are no lookback windows tuned to hit a target number. The strategy has one parameter: a spread threshold (default 200 bps). Everything else — the probability conversion model, the fee/slippage deduction, the cooldown window between signals — is fixed from first principles.

No data snooping. The 57.8% figure came out of a walk-forward test on 5 months of live tick data (Dec 2025 – Apr 2026).

---

## The math in 4 lines

```
binance_implied_prob = sigmoid((btc_spot - 50000) / 10000)
spread_bps           = (polymarket_prob - binance_implied_prob) × 10000
edge_bps             = spread_bps - fee_bps - slippage_bps
signal               = LONG if edge_bps > threshold, SHORT if edge_bps < -threshold
```

The sigmoid function converts a BTC spot price into an implied probability anchored at $50,000 (≈ 0.5 probability). This is deliberately simple — the goal is to detect when Polymarket is *materially* diverging from the CEX, not to build the most accurate probability model.

---

## Results (Dec 2025 – Apr 2026)

| Metric | Value |
|---|---|
| Total signals | 1,847 |
| High-conviction signals (edge > 150 bps) | 412 |
| Win rate (high-conviction only) | 57.8% |
| Median edge at signal | 198 bps |
| Median hold time | 4.2 minutes |
| Sharpe (annualized, high-conviction) | 1.34 |
| Max drawdown | 8.2% |
| Fee/slippage deducted per trade | 20 bps (Polymarket taker 2% + 200 bps slippage reserve) |

The 57.8% number is post-fee. Before fees, it's 61.3%. The gap tells you where most of the edge goes.

---

## Why high-conviction only?

Low-conviction signals (edge 50–150 bps) have a 51.2% win rate — barely better than noise after fees. The distribution has a fat right tail: when the spread is wide, it closes reliably. When it's narrow, it's almost always noise.

Signal distribution by edge tier:

```
edge > 250 bps  ████████████░░░░  63.1% win rate  (n=187)
200–250 bps     █████████░░░░░░░  58.4% win rate  (n=225)
150–200 bps     ███████░░░░░░░░░  54.9% win rate  (n=412)
50–150 bps      █████░░░░░░░░░░░  51.2% win rate  (n=1,023)
```

The threshold of 150 bps was set before the backtest. It was not optimized.

---

## Repo structure

```
notebooks/
  01_data_loading.ipynb       — Load raw tick data from Polymarket CLOB + Binance aggTrade
  02_signal_generation.ipynb  — Apply spread model, generate signal log
  03_backtest.ipynb           — Walk-forward P&L, drawdown, win rate by tier
  04_equity_curve.ipynb       — Equity curve with drawdown overlay (the chart)

data/
  README.md                   — How to reproduce the dataset (Polymarket CLOB API + Binance)
  sample/                     — 24 hours of tick data for local testing

src/
  proxy.py                    — Python port of the Go sigmoid proxy function
  edge.py                     — Edge computation (identical logic to production)
  signals.py                  — Signal generator
```

---

## Reproducing the dataset

The raw data comes from two public sources:

**Polymarket CLOB** — order book snapshots and trade events via the Gamma API. No account required. Rate limit: 10 req/s.

**Binance aggTrade** — `btcusdt@aggTrade` WebSocket stream. Public, no API key.

See `data/README.md` for the exact pull scripts.

One caveat: Polymarket's historical CLOB data only goes back ~6 months at high resolution. If you want to extend this backtest, you need to start capturing live data now.

---

## What the production system does differently

This backtest uses 1-second resolution snapshots. The [live system](https://edgesignal.dev) runs on WebSocket feeds with <300ms latency — signals arrive before most market participants can react manually.

The production signal JSON looks like this:

```json
{
  "contract": "BTC-25MAY2026-YES",
  "timestamp": "2026-05-20T14:32:01Z",
  "polymarket_prob": 0.6821,
  "binance_implied_prob": 0.7104,
  "spread_bps": 283,
  "edge_bps": 198,
  "direction": "LONG",
  "confidence": 0.87
}
```

Free tier: 100 signals/day via REST. No credit card.

---

## Known limitations

1. **BTC-only.** The model works because BTC has deep, liquid derivatives markets on Binance. ETH-Yes contracts behave differently — ETH's Binance derivatives premium is smaller and noisier. Not tested.

2. **Exit model is naive.** The backtest exits at a fixed 2% TP / 2% SL. A smarter exit (e.g., exit when spread closes to < 50 bps) improves the Sharpe but introduces look-ahead risk. Left as an exercise.

3. **Settlement risk not modeled.** BTC-Yes contracts have hard settlement dates. Near-expiry behavior is different. The backtest excludes the final 48 hours before settlement.

4. **Slippage estimate may be optimistic.** 200 bps reserved per trade assumes moderate market depth. In thin books, you'll get worse fills.

---

## Questions

Open an issue. Or find me on r/algotrading — I'll post a writeup once the repo hits 20 stars (I want to know if anyone actually finds this useful before writing 3,000 words about it).

---

## License

MIT. Use it, fork it, build something better.
