---
date: 2026-07-18
description: Phase 4 guide (PLAN.md Revision 5). Ingestion with location-aware gap policy, dark Heritage Engine library, no-lookahead harness under Account Model v1, three-state evaluator, fenced job loop.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 04 — Backtester Worker (Phase 4)

Synced to PLAN.md Revision 5 (D8, D11, D12, D16; invariants 14-16). Supersedes the pre-review version.

**Preconditions**: Phase 3 gate green (schema + grants + audited seeds).
**Phase exit gate**: submitted job → claim → run → atomic finalization; identical manifest → identical hash; zombie-fencing test (SIGSTOP/reap/SIGCONT → exactly one result set); lookahead regression test green; premium gate respected.

Package layout:

```
backtester/
  backtester/
    config.py  db.py  log.py  health.py
    ingest/ccxt_source.py  ingest/scheduler.py  ingest/gaps.py
    engine/        # DARK LIBRARY (D11): triarb.py, bellmanford.py, fills.py, types.py — not in the Strategy registry
    strategies/    # USER-FACING: buyhold.py, sma_cross.py, registry.py
    harness/replay.py  harness/portfolio.py  harness/manifest.py
    rules/evaluator.py  rules/primitives.py
    worker.py      # job loop + scheduler + reaper + heartbeat
  tests/ (characterization/, invariants/, unit/, integration/)
```

## Sprint 4.1 — Ingestion

- Matrix: 10 symbols × 1 primary Venue per symbol × {1m(30d), 1h(3y), 1d(5y)} in `config.py` (R13-5). **Capacity gate**: after first full backfill, record `pg_total_relation_size('worker.ohlcv')` AND the Neon project's total storage in the PR; the budget is total-project-with-failback-headroom — primary + a fully-rewritten staging branch + recovery branch must fit the 0.5 GB free cap (target ≤160 MB logical primary); widening the matrix or breaching the cap requires explicit paid-tier approval (human-todo), never silent growth.
- CCXT public `fetch_ohlcv`, pagination, `enableRateLimit`, tenacity backoff+jitter. **Never ingest the still-open candle** (`ts + timeframe_ms <= now_utc`).
- `ingest/gaps.py`: continuity ledger per (venue,symbol,timeframe) — expected-vs-present ranges persisted with each `ingest_runs` row; revision detection: `ON CONFLICT DO UPDATE` returns changed-row count, logged as `revisions` metric; UTC ms normalization; delisting → matrix entry flagged inactive.
- **Gap policy (location-aware, PLAN Sprint 4.1)**: helper `gaps_in_window(window) -> [ranges]` used at submit (global bar: >0.5% missing → reject `insufficient_data`) and at evaluation (Sprint 4.4 downgrades).

### Acceptance
- Backfill idempotency; kill-and-rerun safety; open candle absent; seeded mutated row detected (content-validation test compares a re-fetched window hash); gap ranges recorded and queryable.
- Capacity (R14-7): after full backfill, the measured TOTAL Neon project storage × 3 (primary + rewritten staging + recovery during failback) fits the free cap with headroom, documented in the PR; breach = stop and obtain paid-tier approval.

## Sprint 4.2 — Heritage Engine extraction (dark library)

Unchanged in mechanics from Revision 2, with two amendments:
1. Characterization goldens (porting fidelity from `archive/legacy-bot/`) are PAIRED with **independent invariants + hand-computed fixtures**: consistent prices → zero opportunities; a constructed 3-pair cycle with known rates/fees → exact expected profit; Bellman-Ford on a graph with one negative cycle → that cycle exactly.
2. `engine/` is NOT wired into `strategies/registry.py` (D11, invariant 15). A unit test asserts the registry exposes exactly `{buyhold, sma_cross}`.

## Sprint 4.3 — Backtest harness (Account Model v1, no lookahead)

- **Execution chronology contract** (documented in `harness/replay.py` docstring, enforced by API shape): the Strategy receives `on_candle(history: CandleView)` where `CandleView` exposes only closed candles ≤ N; returned orders execute on candle N+1: market fills at `N+1.open` adjusted by ADVERSE `slippage_bps`, **used as-is (no clamping into N+1's range)**; window gaps fill at the first tradable candle's open; `fees_bps` per fill.
- **Account Model v1** (`spot-long-v1`, D16): USDT quote accounting, long-only, no leverage/margin/funding/liquidation; `initial_balance = config.account_size` (ONE per Backtest); equity marks open position at candle close. Model id recorded in the manifest.
- Strategies: `buyhold` (all-in at window start, exit at end), `sma_cross` (params: fast, slow; long on golden cross, flat on death cross).
- Ledger output: balance series, equity series, trade log, position events (open/close with ts), daily PnL (per ruleset's `daily_anchor` computed at evaluation time from raw series — the harness stores anchor-agnostic raw series).
- **Determinism manifest** (`harness/manifest.py`, D8): sha256 over canonical JSON of {config (incl. account_size, seed), candle-window content hash, gap ranges, ruleset row ids, engine git sha + semver, uv.lock hash, python version, tzdata version, decimal-context policy id} + canonicalized output bytes → `results_hash`.

### Acceptance
- Lookahead regression: a probe strategy attempting same-candle fill cannot compile/execute against the API (type-level + runtime assertion test).
- buyhold hand-computed month reproduced exactly; cross-process hash equality; mutated candle → different hash.

## Sprint 4.4 — Challenge Simulation evaluator

- Verdict domain **pass | fail | incomplete**. Primitives declare `required_inputs` AND `min_resolution`; evaluator re-checks compatibility (defense-in-depth behind submit-time rejection).
- Location-aware downgrades: any gap intersecting an open-position interval, a daily-anchor boundary, or an SL-deadline window converts would-be PASS → `incomplete` (details name the gap); FAIL stands when provable from present candles, with `first_violation_indeterminate=true` when an earlier rule-sensitive gap exists.
- DD semantics honored per ruleset: `drawdown_basis`, `daily_anchor`, `trailing`, `open_position_treatment`. Formulas in module docstring.
- Unknown primitive key → job error `unsupported_rule:<key>`.

### Acceptance
- Fixture suite: daily-DD breach at known candle → FAIL + timestamp; Breakout seed (no consistency) → PASS on same fixture; gap-inside-position fixture → `incomplete`; FAIL-after-gap fixture → `first_violation_indeterminate=true`; DD boundary suite (midnight, DST, trailing vs static, open positions) green; property test: verdict invariant under equity downsampling.

## Sprint 4.5 — Job loop hardening

- Claim bumps `attempt` (Sprint 3.3); complexity re-validation + entitlement snapshot re-check per claim (`premium AND NOT is_paid` → error `entitlement_required`).
- 10-minute runtime watchdog (SIGALRM-equivalent thread) → finalize as `error('timeout')` through the SAME finalization txn.
- Completion exclusively via the atomic finalization transaction (results + simulations + job_events + status CAS, rollback on rowcount≠1).
- Reaper + heartbeats as Sprint 3.3; queue depth + oldest-age logged per idle poll; structured logs carry `job_id`, `attempt`, `worker_id`.

### Acceptance
- End-to-end psql-submitted job → done with results + simulations + one `completed` job_event; kill -9 mid-run → reaped and re-run cleanly; SIGSTOP zombie test → exactly one result set, zombie finalization rolled back; identical config → identical `results_hash`; premium refusal for unpaid user.
