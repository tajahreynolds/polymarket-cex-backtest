# alpha/ — OHLCV strategy research

Self-contained research track: build a rules-based strategy on daily OHLCV bars
that beats the top ETFs (SPY, QQQ) after costs on risk-adjusted terms.

## Data
Outbound network in this environment reaches GitHub and package registries only
(Yahoo, Stooq, Tiingo, Polygon, FRED, Binance are all blocked at the egress
proxy). The panel is therefore built from GitHub-hosted mirrors:

* `data/kaggle_etfs/` — 52 ETFs, daily OHLCV, 2005-02-25 → 2017-11-10, sourced
  from a mirror of the Stooq-derived "Huge Stock Market Dataset". Prices are
  back-adjusted for splits **and** dividends, so a buy-and-hold benchmark on
  these series is a total-return benchmark.
* `data/us_market_data.csv` — daily short rate used as the cash yield.

The universe spans US equity, developed and emerging equity, Treasuries across
the curve, credit, TIPS, munis, gold, silver, broad commodities, REITs and the
nine GICS sector ETFs, so the cross-section is genuinely multi-asset.

## Method
* `src/panel.py` — aligned OHLCV panel; prices are never forward-filled, so an
  ETF is untradable on days it has no print.
* `src/engine.py` — dollar-accounted engine. Signals use bars up to the close of
  day *t*; the resulting weights execute at the **open of day t+1**. Holdings
  drift between rebalances, cash accrues the short rate, and traded notional
  pays a configurable spread.
* `src/metrics.py` — CAGR, vol, Sharpe/Sortino, max drawdown, Calmar, turnover,
  cost drag, alpha/beta vs SPY, and the Bailey–López de Prado deflated Sharpe to
  discount the number of configurations tried.

## Benchmarks to beat (2005-03 → 2017-11, 5bps one-way)

| | CAGR | Vol | Sharpe | MaxDD |
|---|---|---|---|---|
| SPY | 7.32% | 18.99% | 0.41 | -56.50% |
| QQQ | 12.67% | 20.14% | 0.64 | -53.42% |
| 60/40 | 5.52% | 11.12% | 0.43 | -38.48% |
