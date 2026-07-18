---
date: 2026-07-18
description: Phase 3 guide (PLAN.md Revision 5). Three-role bootstrap, RLS, full domain schema with fencing/outbox/billing tables, immutability trigger, finalization transaction, and audited ruleset seeds.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 03 — Data, Schema & Worker-Integration Contract (Phase 3)

Synced to PLAN.md Revision 5 (decisions D12-D16). Supersedes the pre-review version.

**Preconditions**: Phase 2 gate green.
**Phase exit gate**: migrate job idempotent twice on fresh Neon under `pg_advisory_lock`; worker verb-matrix passes; cross-user RLS matrix (reads AND mutations) passes; ruleset payload UPDATE via direct owner SQL rejected by trigger; seeds load AND pass the D16 representability audit.

## Sprint 3.1 — Roles + migrate job

Three-tier credentials (PLAN.md D14):

`migrations/000_role.sql` (manual, owner, once per environment; passwords set by human — H-NEON):

```sql
DO $$ BEGIN CREATE ROLE app_user LOGIN PASSWORD 'app_user'; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE service_role LOGIN PASSWORD 'service_role' BYPASSRLS; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE worker_role LOGIN PASSWORD 'worker_role'; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
GRANT CONNECT ON DATABASE cloudaitrader TO app_user, service_role, worker_role;
-- service_role: DML only, NO DDL, no schema ownership. Owner runs migrations (migrate job only).
```

Migrate job (`migrations/run.js`): acquires `SELECT pg_advisory_lock(7401)`, applies numbered files recorded in `schema_migrations`, releases, exits. Runs ONLY as the compose `migrate` service (DIRECT_URL); backend/backtester never migrate and never see DIRECT_URL.

`003_rls_helpers.sql`: `app.current_user_id()`, `app.is_admin()` as before; RLS enabled deny-by-default on every app_user-visible table; `app.user_mfa`, `app.admins` have NO app_user grants (service_role only).

## Sprint 3.2 — Domain schema (`004_domain.sql`)

Beyond the Revision-2 tables, this migration MUST include:

```sql
-- users additions
ALTER TABLE app.users ADD COLUMN IF NOT EXISTS incarnation uuid NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE app.users ADD COLUMN IF NOT EXISTS deletion_state TEXT NOT NULL DEFAULT 'active'
  CHECK (deletion_state IN ('active','deleting','billing_severed'));

CREATE TABLE IF NOT EXISTS app.deleted_subs (          -- D15 tombstones
  sub TEXT NOT NULL, incarnation uuid NOT NULL, deleted_at timestamptz NOT NULL DEFAULT now(),
  stripe_customer_id TEXT, stripe_subscription_id TEXT,
  PRIMARY KEY (sub, incarnation));

CREATE TABLE IF NOT EXISTS app.stripe_events (         -- NO user FK; never cascaded; 2y retention
  event_id TEXT PRIMARY KEY, type TEXT NOT NULL, created timestamptz NOT NULL,
  subscription_id TEXT, customer_id TEXT, payload jsonb NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now());

CREATE TABLE IF NOT EXISTS app.billing_actions (       -- persisted cancel/reconcile work (D13/D15)
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kind TEXT NOT NULL CHECK (kind IN ('cancel_subscription')),
  stripe_subscription_id TEXT NOT NULL, reason TEXT NOT NULL,
  attempts int NOT NULL DEFAULT 0, last_error TEXT,
  resolved_at timestamptz, created_at timestamptz NOT NULL DEFAULT now());

CREATE TABLE IF NOT EXISTS app.job_events (            -- outbox (D7)
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  backtest_id uuid NOT NULL, type TEXT NOT NULL,
  claimed_at timestamptz, lease_expires_at timestamptz,
  attempts int NOT NULL DEFAULT 0, last_error TEXT, sent_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (backtest_id, type));

CREATE TABLE IF NOT EXISTS app.tier_limits (
  tier TEXT PRIMARY KEY,                                -- 'free' | 'paid'
  limits jsonb NOT NULL);                               -- {backtests_per_month, max_candles_per_job, timeframes, max_active_jobs, premium_rulesets}
```

`app.backtests` gains `attempt int NOT NULL DEFAULT 0` and `account_size numeric NOT NULL` (D16, pinned per Backtest). `app.entitlements` becomes the status model (D13): `status TEXT NOT NULL DEFAULT 'none' CHECK (status IN ('none','active','trialing','past_due','canceled','suspended'))`, `current_period_end timestamptz`, `override_reason TEXT`, per-subscription `last_event_created timestamptz`; `is_paid` is a VIEW-level derivation (or generated column) = status IN ('active','trialing') OR (status='past_due' AND now() < current_period_end + grace). `app.simulations.verdict` CHECK becomes `('pass','fail','incomplete')` with `first_violation_indeterminate boolean NOT NULL DEFAULT false`.

Firm rulesets: payload-immutability trigger — reject UPDATE of (`rules`, `firm_name`, `version`, `effective_date`, `source_url`, `verified_at`) whenever OLD.published; lifecycle columns (`published`, `revoked_at`) remain mutable; DELETE always rejected. Compatibility metadata columns: `account_models TEXT[] NOT NULL DEFAULT '{spot-long-v1}'`, `min_timeframe TEXT NOT NULL` (derived from the strictest primitive, e.g. '1m' when SL-timing present), `account_size numeric NOT NULL`.

Uniqueness contract (PLAN.md Sprint 3.2): ohlcv PK(venue,symbol,timeframe,ts) · results PK(backtest_id) · simulations UNIQUE(backtest_id, ruleset_id) · stripe_events PK(event_id) · job_events UNIQUE(backtest_id, type).

### Grants

As Revision 2, adjusted: service_role gets DML on all app.* tables (BYPASSRLS covers RLS); worker_role: SELECT on entitlements/firm_rulesets/tier_limits, SELECT/UPDATE on backtests, INSERT on backtest_results/simulations/job_events (+ sequence usage), full on worker.*; worker policies on RLS-on shared tables as before; NO worker grant on users/mfa/admins/quota/stripe_events/billing_actions/deleted_subs.

## Sprint 3.3 — Worker DB access + finalization transaction

- Claim (single statement): as before (`FOR UPDATE SKIP LOCKED`) PLUS `attempt = attempt + 1` in the claiming UPDATE; the claimed attempt value travels with the job.
- **Atomic finalization transaction (D12) — the exact shape, in one txn:**

```sql
BEGIN;
INSERT INTO app.backtest_results (backtest_id, equity_curve, trades, metrics)
SELECT :id, :curve, :trades, :metrics
WHERE EXISTS (SELECT 1 FROM app.backtests
              WHERE id=:id AND attempt=:att AND claimed_by=:wid AND status='running');
INSERT INTO app.simulations (backtest_id, ruleset_id, verdict, violated_rule, violated_at, first_violation_indeterminate, details)
SELECT :id, r.ruleset_id, r.verdict, r.rule, r.at, r.indet, r.details FROM jsonb_to_recordset(:sims) AS r(...)
WHERE EXISTS (SELECT 1 FROM app.backtests
              WHERE id=:id AND attempt=:att AND claimed_by=:wid AND status='running');
INSERT INTO app.job_events (backtest_id, type)
SELECT :id, 'completed'
WHERE EXISTS (SELECT 1 FROM app.backtests
              WHERE id=:id AND attempt=:att AND claimed_by=:wid AND status='running');
UPDATE app.backtests SET status=:final, results_hash=:hash, error=:err, finished_at=now()
WHERE id=:id AND attempt=:att AND claimed_by=:wid AND status='running';
-- application code: if UPDATE rowcount != 1 -> ROLLBACK (zombie: all inserts vanish); else COMMIT.
COMMIT;
```

- Reaper requeues stale leases with `attempt = attempt + 1, status='queued', claimed_by=NULL` — permanent zombie fence.
- Heartbeats, retention, batched upserts unchanged from Revision 2.

## Sprint 3.4 — Firm Ruleset seeds + representability audit

- `rules` jsonb vocabulary extended with explicit semantics per PLAN.md: `drawdown_basis`, `daily_anchor`, `trailing` (bool, max-DD high-water), `open_position_treatment` (`mark_to_close`), plus the Revision-1 primitives.
- Seed four firms (HyroTrader, Breakout, Crypto Fund Trader, FTMO-crypto), version 1, `published=true`, provenance + `estimate` flags (H-RULES-1), each with `account_size`, `min_timeframe`, `account_models`.
- **Representability audit (D16, blocks Phase 4)**: an automated test walks every seeded ruleset and asserts each primitive (a) exists in the evaluator vocabulary, (b) is satisfiable under `spot-long-v1`, (c) declares a resolution ≤ an offered timeframe. Output: a per-firm compatibility table committed as `docs/ruleset-representability.md`. Any failure = scope escalation before Phase 4.

## Acceptance (phase)

- Migrate job twice on fresh DB → second run no-op; concurrent double-invocation serialized by advisory lock (test with two parallel runs).
- Verb matrix (worker + service_role): worker claim/finalize succeed; worker SELECT users fails; **service_role DDL attempt (`CREATE TABLE`) fails**; app_user bare-pool zero rows.
- RLS matrix: scripted cross-user SELECT/INSERT/UPDATE/DELETE per app-owned table, all denied.
- Immutability: `UPDATE app.firm_rulesets SET rules='{}' WHERE published` as OWNER → trigger exception; `UPDATE ... SET published=false` succeeds; `DELETE` → exception.
- Finalization: stale-attempt txn rolls back completely (no orphan results/sims/events rows).
- `SELECT count(*) FROM app.firm_rulesets WHERE published` = 4; representability audit green.
