---
date: 2026-07-17
description: Plan to revive the dormant 2023 arbitrage bot as the backtesting module of the CloudAITrader prop firm app, with tracked modernization workstreams M1-M8.
tags:
  - modernization
  - cloudaitrader
---

# Modernization Plan: realtime_crypto_arbitrage_bot to CloudAITrader Backtesting Module

**Date**: 2026-07-17
**Companion docs**: [competitor-analysis.md](competitor-analysis.md) (why), AGENTS.md (current architecture), AGENTS-TODO.md (open decision), README.md (original scope).

## Decision (resolves AGENTS-TODO.md)

AGENTS-TODO.md asks: revive or archive. **Decision: revive, repurposed.** The bot does not return as a live-trading arbitrage bot. Its engines (triangular arbitrage, Bellman-Ford negative-cycle detection, forecasting models) become strategy templates inside a new product: the backtesting module of CloudAITrader (cloudaitrader.com), a prop-firm-aware crypto backtesting SaaS. Live execution against real funds is out of scope indefinitely (see Non-Goals).

Rationale is in [competitor-analysis.md](competitor-analysis.md): no crypto prop firm offers integrated backtesting, OSS engines are unhosted and rule-agnostic, and the closest product (TradeZella) is manual and not crypto-algorithmic.

## Current State Audit (verified against code 2026-07-17)

| Area | State | Evidence |
|---|---|---|
| Runtime | Python 3.7, last commit 2023-05-09 | README requirements; git log |
| Core engines | triarb.py (260 LOC), bellmanford.py (536 LOC), analysis.py (115 LOC, LSTM/ARIMA/SARIMAX per docs), trade.py (428 LOC), history.py (160 LOC) | wc -l |
| Exchange layer | kucoinlive.py (189 LOC) is the only real connector; coinbaselive.py (8 LOC) and geminilive.py (7 LOC) are stubs; cbpro 1.1.4 targets the retired Coinbase Pro API; ccxt commented out in both dep files | requirements.txt, Pipfile |
| Data layer | SQLAlchemy 1.4.3 + aiosqlite; SQLite dbs per exchange in db/ plus CSV logs (market.csv, tri_arb_ops.csv) | AGENTS.md, db/ |
| Dependencies | Dual Pipfile + requirements.txt, already out of sync (networkx 2.6.3 vs 2.7.1); pandas 1.3.3, numpy 1.22.0 | both files |
| Concurrency | Multi-threaded with documented race-condition risk in trade paths | AGENTS.md gotcha 3 |
| Third-party | comparison/ contains Arbitrage-Bot and peregrine reference implementations, not original code | AGENTS.md gotcha 5 |
| Config | parameters.yaml (API keys risk documented), log_config.yaml | AGENTS.md gotcha 2 |
| Docs | Sphinx to GitHub Pages, capstone report with model results from 2022 data | docs/source/ |

## Target Role in CloudAITrader

Per the Template Format B build plan (produced separately as PLAN.md): CloudAITrader is a dual-tier app. A Next.js 16 web tier (cloudaitrader.com on Vercel, API routes at backend.cloudaitrader.com) handles auth, billing, dashboards, and backtest job submission. A separate always-on Python worker (worker.cloudaitrader.com, self-hosted on the Pi fleet) runs data ingestion and backtest execution. The two tiers coordinate only through shared Neon Postgres; no HTTP between them. **This repo's code becomes the core of that worker.**

## Modernization Tracks

### M1. Runtime and tooling baseline
- Python 3.7 to 3.12+. Type hints on all public functions.
- Kill the dual-dependency-file gotcha: single `pyproject.toml` with uv lockfile; delete Pipfile and requirements.txt.
- ruff (lint + format) replaces black 22.3/flake8 3.9/pydocstyle 6.0; pytest with a real suite (repo currently has none).
- Keep Docker; compose file shrinks to worker + local Postgres.

### M2. Exchange/data layer replacement
- Delete cbpro (API retired), gemini-python, and the stub connectors. Replace with CCXT (already contemplated; it sits commented out in requirements.txt since 2022).
- Backtesting-first means public REST OHLCV ingestion, no API keys required for MVP. KuCoin, Bybit, Kraken, Binance klines via CCXT unified `fetch_ohlcv`.
- kucoinlive.py websocket logic survives only if a later live-paper-trading phase needs it; not on the MVP path.

### M3. Engine extraction (the crown jewels)
- Extract triarb.py and bellmanford.py into a pure `engine/` package: deterministic functions over in-memory market snapshots, no I/O, no threads, seeded RNG where sampling exists. This unlocks unit testing and identical behavior in backtest and (future) live modes, the LEAN principle from the competitor analysis.
- analysis.py forecasting models (LSTM/ARIMA/SARIMAX) become optional strategy signals, ported only after the arb engines are green.
- trade.py live-execution logic is retired; its fee math and order-sizing survive as the backtest fill model.

### M4. Backtest harness (core new build)
- Event-driven replay over stored OHLCV: candle iterator, strategy callback interface, portfolio/equity tracker, fee + slippage model (taker fee already parameterized in parameters.yaml; extend with spread/slippage assumptions).
- Determinism contract: same inputs, same results, always (required for user trust and for caching).
- Honest-results rule from the competitor analysis: no marketing of the 2022 13-67% margin claims; backtests must model realistic fills.

### M5. Prop-firm rule engine (the differentiator)
- Config-driven, versioned rulesets per firm per date (rulebook churn risk): profit target, daily drawdown, max drawdown, minimum trading days, stop-loss discipline (e.g., HyroTrader's SL-within-5-minutes), consistency rules.
- Evaluated as a pass/fail overlay on any backtest equity curve, with the violated rule and timestamp reported.
- Ruleset definitions live in Postgres, not code.

### M6. Persistence migration
- SQLite to Neon Postgres 17 (Format B standard): `ohlcv` (partitioned by symbol/timeframe), `backtests`, `backtest_results`, `firm_rulesets`, plus job-queue tables for web-to-worker coordination.
- Existing db/*.db and CSVs are frozen as historical artifacts; a one-off import is optional, not required (2022 KuCoin data has little product value).
- Neon free tier is 0.5 GB: candle retention policy from day one (top N symbols, bounded timeframes, rollups).

### M7. Worker-ization (Format B integration)
- main.py becomes a long-running worker loop: poll Postgres job queue, claim job (SELECT FOR UPDATE SKIP LOCKED), run ingestion or backtest, write results, heartbeat.
- Deployed via Docker on the Pi fleet as worker.cloudaitrader.com (Cloudflare Tunnel), per portfolio policy: free/self-hosted until profitable.
- Replaces the multi-threaded design; race-condition gotcha dies with it. Single-process, sequential jobs per worker, scale by adding workers.

### M8. Repo hygiene
- comparison/ (third-party code), presentation/, eda/, indicators/, sql/, execute_comparison scripts: move to an `archive/` directory or a git tag, out of the runtime tree.
- AGENTS.md rewritten for the new architecture; AGENTS-TODO.md decision checked off; README repositioned (bot history preserved in a "Heritage" section).
- Secrets only via environment variables; parameters.yaml keys pattern retired.

## What Gets Dropped

| Item | Reason |
|---|---|
| cbpro + Coinbase Pro connector | API retired by Coinbase; connector was a stub anyway |
| gemini-python + Gemini connector | Stub; not on MVP data path |
| Live order execution (trade.py) | Product is backtesting; regulatory and risk surface we do not want |
| Multi-threading model | Replaced by single-process job worker |
| Pipfile/requirements.txt duality | Single pyproject.toml + uv lock |
| GitHub Pages Sphinx pipeline | Docs move to product docs; Sphinx retired with the capstone framing |

## Non-Goals

1. Live trading with real funds. Nothing in this plan places orders.
2. Building a full prop firm (challenges, funded accounts, payouts). See competitor analysis Lane 2: if that day comes, buy white-label.
3. HFT-grade latency or tick-level orderbook replay in MVP. OHLCV-grade fidelity first; tick data is a paid-data-vendor decision later.
4. More than ~4 exchanges of data coverage in MVP. Depth over breadth.

## Sequencing

M1 to M2 to M3+M4 (parallel) to M5 to M6+M7 (parallel) to M8. Detailed phase/sprint breakdown with exit gates lives in PLAN.md (Template Format B) and docs/sprints/.

## Risks

| Risk | Mitigation |
|---|---|
| Engine code quality unknown after 3 years dormant | M3 extraction includes characterization tests before refactor; treat current outputs as the spec |
| Free OHLCV depth insufficient for credible backtests | Start with 1m/5m/1h candles, 2+ years where available; document data provenance per backtest |
| Rulebook churn (firm rules change monthly) | M5 versioned config; per-firm ruleset dated snapshots; community-sourced corrections later |
| Pi fleet worker reliability for a paid SaaS | Job queue with retries and heartbeats; stateless worker; Postgres is the source of truth (Neon, not the Pi) |
| Scope creep back toward live trading | Non-Goal 1 is a hard gate; any live-mode work requires a new decision document |
