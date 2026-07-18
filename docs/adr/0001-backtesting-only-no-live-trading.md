---
status: accepted
date: 2026-07-17
---

# Backtesting only; no live trading execution

This repo began as a live triangular-arbitrage bot with real order execution (trade.py, kucoinlive.py private sessions). CloudAITrader ships Backtests and Challenge Simulations only: no code path places orders on any Venue, and no Venue API keys are required for the product to function. We chose this because the validated market wedge is pre-Challenge strategy validation (docs/competitor-analysis.md), while live execution multiplies regulatory, custody, and key-management risk and forces per-exchange execution engineering that free OSS (Freqtrade, Hummingbot) already gives away.

## Consequences

- trade.py is retired; its fee and order-sizing math survives as the Backtest fill model.
- The 2022 live-detection profit claims (13-67%) are not carried into product marketing.
- Any future live or paper-trading mode requires a new ADR superseding this one.
