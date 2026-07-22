---
date: 2026-07-21
description: Phase 3 guide (PLAN.md Revision 10). Four-role contract bootstrap with privilege boot-asserts, RLS, full domain schema with fencing/outbox/billing tables, immutability trigger, finalization transaction, and audited ruleset seeds.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 03 — Data, Schema & Worker-Integration Contract (Phase 3)

Synced to PLAN.md Revision 10 (decisions D12-D16, four-role contract, invariants 18-20). Supersedes prior versions.

**Preconditions**: Phase 2 gate green.
**Phase exit gate**: migrate job idempotent twice on fresh Neon under `pg_advisory_lock`; worker verb-matrix passes; cross-user RLS matrix (reads AND mutations) passes; ruleset payload UPDATE via direct owner SQL rejected by trigger; seeds load AND pass the D16 representability audit.

## Sprint 3.1 — Roles + migrate job

Four-role contract, canonical names (PLAN.md D14 / Format B inv 14). THREE manual `000_*` files (owner, once per environment); **the runner SKIPS `000_*` files** (implemented in run.js), so all GRANTs live in the next auto-applied migration. **Passwords are NEVER hardcoded (R9-4)**: each file takes a protected psql variable and idempotently converges attributes on re-run:

Secrets never travel through argv (R10-6): invoke each file with `psql -f 000_role.sql` and supply the password via `\prompt -s` inside the file (interactive), or `\i` a 0600 transient variable file that is securely deleted afterward; shell history/logging must not capture values.

```sql
-- migrations/000_role.sql — password via \prompt -s or a 0600 transient \i file (never -v on the command line)
DO $$ BEGIN CREATE ROLE app_user LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
ALTER ROLE app_user LOGIN PASSWORD :'app_user_password' NOSUPERUSER NOREPLICATION NOBYPASSRLS NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE cloudaitrader TO app_user;
-- migrations/000_worker_role.sql — password via \prompt -s or 0600 transient \i file (never argv)
DO $$ BEGIN CREATE ROLE worker_user LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
ALTER ROLE worker_user LOGIN PASSWORD :'worker_user_password' NOSUPERUSER NOREPLICATION NOBYPASSRLS NOCREATEDB NOCREATEROLE;
GRANT CONNECT ON DATABASE cloudaitrader TO worker_user;
-- migrations/000_service_role.sql — password via \prompt -s or 0600 transient \i file (never argv)
DO $$ BEGIN CREATE ROLE app_service LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
ALTER ROLE app_service LOGIN PASSWORD :'app_service_password' NOSUPERUSER NOREPLICATION BYPASSRLS NOCREATEDB NOCREATEROLE;
-- Every asserted attribute is converged here idempotently (R14-9); the bootstrap also
-- REVOKEs unexpected memberships and REASSIGN OWNED strays so boot-asserts cannot
-- deadlock against a pre-existing overprivileged role.
GRANT CONNECT ON DATABASE cloudaitrader TO app_service;
-- app_service: enumerated DML only, NO DDL, owns nothing. Owner runs migrations (migrate job only).
```

Dev compose provisions the same three roles with dev literals via `infra/db-init/dev-roles.sql` (mounted into `/docker-entrypoint-initdb.d/`; re-init requires `docker compose down -v`) — R9-5.

Boot-asserts (Format B inv 14-15, extended R9-8 + R10-5): backend refuses to start in production with `DIRECT_URL` present (implemented in `src/config.js`); each pool asserts `SELECT current_user` AND the full privilege contract at init, throwing on mismatch — `app_user`/`worker_user`: NOT rolbypassrls; `app_service`: rolbypassrls; ALL runtime roles additionally: NOT rolsuper, NOT rolreplication, NOT rolcreatedb, NOT rolcreaterole, no unexpected `pg_auth_members` memberships, zero owned objects via a COMPLETE audit — `pg_shdepend` plus local catalogs (`pg_class`, `pg_namespace`, `pg_proc`, `pg_type`) so owned SECURITY DEFINER functions, types, and schemas cannot slip the gate (R11-4). Provisioning revokes stray memberships and `REASSIGN OWNED` strays. Tests: swapped/overprivileged DSNs refuse naming the failed attribute; owner-created fixtures — a table, a function, AND a schema — each survive runtime-role `ALTER`/`DROP` attempts (denied).

Migrate job (`migrations/run.js`): acquires `SELECT pg_advisory_lock(7401)`, applies numbered files EXCLUDING `000_*`, records them in `schema_migrations`, releases, exits. Runs ONLY as the compose `migrate` service (DIRECT_URL).

`003_rls_helpers.sql`: `app.current_user_id()`, `app.is_admin()` as before; RLS enabled deny-by-default on every app_user-visible table; `app.user_mfa`, `app.admins` have NO app_user grants (app_service only).

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

Grants are SINGLE-SOURCE in their own idempotent, re-runnable migration `005_grants.sql` (R12-2 — the exact file the warm-sync and failback scripts re-apply after every restore; nothing else grants anything): app_service gets ENUMERATED DML on the app.* tables its runtime paths touch (BYPASSRLS covers RLS; no blanket schema grant, no DDL); worker_user: SELECT on entitlements/firm_rulesets/tier_limits, SELECT/UPDATE on backtests, INSERT on backtest_results/simulations/job_events (+ sequence usage), full on worker.* (its own schema); worker policies on RLS-on shared tables as before; NO worker grant on users/mfa/admins/quota/stripe_events/billing_actions/deleted_subs — explicit per-table grants only, never a blanket app-schema grant (Format B inv 11). A companion read-only assertion script `migrations/verify_roles.sql` encodes the full verb/RLS/ownership matrix and is the SHARED verifier used by boot-asserts (compact subset), the test suite, and the pre-swap/pre-promotion checks in Sprint 8.4.

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
- Verb matrix (worker_user + app_service, via `verify_roles.sql`): worker claim/finalize succeed; worker SELECT users fails; **app_service DDL attempt (`CREATE TABLE`) fails**; app_user bare-pool zero rows; **complete ownership audit passes — `pg_shdepend` + `pg_class`/`pg_namespace`/`pg_proc`/`pg_type` report ZERO objects owned by any runtime role (R11-4/R12-3)**; **all three denial fixtures pass — owner-created table, SECURITY DEFINER function, and schema each deny runtime-role `ALTER`/`DROP`**; boot-asserts: worker started as app_user or owner refuses; backend with DIRECT_URL in production env refuses.
- RLS matrix: scripted cross-user SELECT/INSERT/UPDATE/DELETE per app-owned table, all denied.
- Immutability: `UPDATE app.firm_rulesets SET rules='{}' WHERE published` as OWNER → trigger exception; `UPDATE ... SET published=false` succeeds; `DELETE` → exception.
- Finalization: stale-attempt txn rolls back completely (no orphan results/sims/events rows).
- `SELECT count(*) FROM app.firm_rulesets WHERE published` = 4; representability audit green.
