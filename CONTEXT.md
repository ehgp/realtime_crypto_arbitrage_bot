# CloudAITrader

Prop-firm-aware crypto backtesting SaaS: traders validate algorithmic strategies against the exact rulesets of prop firm challenges before paying for one. This repo's heritage arbitrage engines become its strategy library.

## Language

### Product & domain

**Strategy**:
A parameterized trading algorithm available for backtesting. Launch Strategies are candle-faithful (Buy & Hold, SMA Crossover); arbitrage Strategies wait for quote-level data (PLAN.md D11).
_Avoid_: bot, model, algo

**Heritage Engine**:
The 2022-2023 arbitrage detection code (triarb, Bellman-Ford) extracted as a pure, tested library. Library-only in MVP; not a user-facing Strategy.
_Avoid_: legacy code, the bot

**Venue**:
An exchange used as a market-data source (Bybit, Kraken, Binance, KuCoin). CloudAITrader never executes trades on a Venue.
_Avoid_: exchange (ambiguous), broker

**Challenge**:
A prop firm's real, paid evaluation program. CloudAITrader never runs Challenges; it simulates them.
_Avoid_: evaluation (overloaded)

### Backtesting

**Dataset**:
Stored OHLCV candles for one symbol, timeframe, and Venue.
_Avoid_: feed, market data

**Backtest**:
A single run of a Strategy over one Dataset window with a fee and slippage configuration, producing a Simulation Ledger.
_Avoid_: simulation, test run

**Simulation Ledger**:
The complete evidence a Backtest produces for rule evaluation: balance and equity series, trade log, position events, and daily PnL.
_Avoid_: results blob, equity curve (when the full ledger is meant)

**Equity Curve**:
The equity time series within a Simulation Ledger.

**Backtest Job**:
A queued unit of Backtester Worker work: run one Backtest and, optionally, its Challenge Simulations.
_Avoid_: task, run request

**Ingestion**:
The Backtester Worker's scheduled pull of candles from Venues into Datasets.
_Avoid_: scraping, sync

### Prop-firm rules

**Firm Ruleset**:
A dated, versioned configuration of one prop firm's Challenge rules (profit target, daily drawdown, max drawdown, minimum trading days, stop-loss discipline, consistency). Data, not code (ADR-0002).
_Avoid_: rules engine, challenge config

**Challenge Simulation**:
The overlay of one Firm Ruleset on a Backtest's Simulation Ledger, yielding PASS, FAIL, or INCOMPLETE and reporting the first observable violated rule and when (flagged indeterminate when a data gap could hide an earlier violation).
_Avoid_: evaluation, challenge test

### System tiers (Template Format B)

**App Worker**:
The Node/Express API tier serving the web app (auth, users, billing, job submission, read APIs).

**Backtester Worker**:
The Python capability tier that owns Ingestion, Backtest Jobs, and Challenge Simulations; the future home of AI features.
_Avoid_: bot, capability worker (generic)

**Entitlement**:
A user's paid status gating premium Backtests and the full Firm Ruleset library.
_Avoid_: subscription flag, premium bit
