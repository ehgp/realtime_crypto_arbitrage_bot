# Plan: CloudAITrader — Prop-Firm-Aware Crypto Backtesting SaaS (Template Format B)

_Locked via grill-with-docs (autonomous mode: decisions resolved from docs/, AGENTS.md, AGENTS-TODO.md, README.md, and code; assumptions recorded) — by Claude for ehgp. Terms per CONTEXT.md. Revised after Codex review Rounds 1-4 (PLAN-REVIEW-LOG.md) and re-grilled 2026-07-18 against the updated Template Format B standard (new invariant 13: canonical env-var names)._

Mode: migration · Generated: 2026-07-17 · Revision: 8

## Goal

Revive this dormant repo as CloudAITrader: a hosted SaaS where a trader signs in, runs a Backtest of a Strategy over Venue Datasets, and gets a Challenge Simulation verdict against versioned Firm Rulesets (HyroTrader, Breakout, Crypto Fund Trader, FTMO) before paying for a real Challenge. Launch Strategies are candle-faithful (Buy & Hold baseline, SMA Crossover); the Heritage Engines (Triangular Arbitrage, Bellman-Ford) are extracted and tested as a library but are not user-facing until quote-level data exists (D11). Built per Template Format B: a Next.js 16 web tier and Node/Express App Worker, plus a Python 3.12 Backtester Worker owning Ingestion, Backtest Jobs, and Challenge Simulations, coordinating only through shared Neon Postgres.

## Branch & targets

- **Working branch**: `ai` (current; no new branch invented).
- **Frontend**: cloudaitrader.com on Vercel (Next.js 16, App Router, BFF proxy).
- **App Worker (API)**: Express 5 on the Pi fleet (eg-server-N) in Docker, fronted by Cloudflare named tunnel at backend.cloudaitrader.com.
- **Backtester Worker**: Python 3.12 on the Pi fleet, same compose stack. **No inbound ingress in MVP**; worker.cloudaitrader.com reserved, unprovisioned (D5).
- **Database**: Neon Postgres 17 free tier, governed by the capacity model in Sprint 4.1 (projection ~1.6M candle rows ≈ 240-320 MB; hard gate before widening).
- **Deploy policy**: self-hosted on Pi fleet until profitable; paid tiers only on explicit command.

## Summary

CloudAITrader is a dual-worker Format B app. The capability tier (Backtester Worker) owns OHLCV Ingestion via CCXT, deterministic Backtest execution producing a Simulation Ledger under an explicit no-lookahead execution chronology, and the Challenge Simulation evaluator over versioned Firm Rulesets whose payloads are immutable at the database level (ADR-0002). Optional layers IN: Stripe (server-created Checkout Sessions; subscription-object-authoritative entitlements), Resend email via leased outbox with provider idempotency keys, Turnstile, PWA, admin surface, MFA (local TOTP with encrypted, rotatable secrets). OUT for MVP: user-facing arbitrage Strategies (D11), user job cancellation, pay-first flow, chat delivery, worker inbound tunnel, live trading (ADR-0001), account export.

## Gap table (current → Format B target)

| Layer | Current (2023 repo) | Format B target | Scope |
|---|---|---|---|
| Frontend | None (CLI + Sphinx docs) | Next.js 16 + TS + AntD 5, next-intl, cloudaitrader.com on Vercel | In |
| Auth | None (exchange API keys in parameters.yaml) | Auth0 v4 server session + BFF Bearer proxy + jose JWKS verify | In |
| Database | SQLite per exchange + CSVs | Neon Postgres 17, RLS keyed to `sub`, numbered idempotent migrations via one-shot migrate job | In |
| App worker | None | Node 22 / Express 5 ESM: auth, users, jobs API, admin, Stripe, outbox notifier (service_role, no DDL) | In |
| Capability worker | Monolithic threaded bot | Python 3.12 + SQLAlchemy 2.0 job loop with lease fencing + atomic finalization | In |
| Exchange layer | kucoin-python real; cbpro (retired) + gemini stubs | CCXT public OHLCV, one primary Venue per symbol; no keys (ADR-0001) | In |
| Engines | triarb.py, bellmanford.py inside live loop | Pure `engine/` library, characterization + invariant tests; NOT user-facing (D11) | In (library) |
| Launch Strategies | None | Buy & Hold, SMA Crossover under the execution chronology contract | In |
| Prop-rule awareness | None | DB-immutable versioned Firm Rulesets + Simulation Ledger evaluator (ADR-0002) | In (core differentiator) |
| Payments | Donations paragraph in README | Stripe Checkout Sessions + event store + subscription-authoritative status | In |
| Storage/blob | None | None in MVP (equity curves are rows, not files); `R2_*` vars reserved without a consumer pending H-R2-1 | Out |
| Bot protection | None | Turnstile on contact form | In |
| Email | None | Resend via leased outbox with idempotency keys + admin alerts | In |
| Observability | log/ files | Sentry x4 runtimes + correlation IDs (request_id, job_id) | In |
| Deploy | Local docker-compose | compose-{dev,host}; Pi fleet + backend named tunnel; Vercel web | In |
| Legacy data | 2022 KuCoin SQLite/CSVs | Frozen in archive/; NOT migrated | Out (D9) |
| Live trading | trade.py execution | Removed (ADR-0001) | Out |

## Database roles (D14)

| Role | Used by | Privileges |
|---|---|---|
| owner (Neon default) | One-shot migrate job ONLY | DDL, everything; `DIRECT_URL` confined to the migrate job |
| service_role | App Worker ownerPool (webhooks, outbox, admin reads, provisioning) | BYPASSRLS + DML grants; NO DDL, no schema ownership |
| app_user | App Worker request pool (`withUser`) | RLS-governed DML on user-facing tables |
| worker_role | Backtester Worker | Verb-matrix grants per ownership split; no DDL |

## Table-ownership split

| Table | Owner | App Worker verbs | Backtester Worker verbs |
|---|---|---|---|
| app.users | App (RLS) | full via withUser | none |
| app.admins | App (service_role; bootstrap via one-time CLI, D12) | SELECT/INSERT/DELETE (guarded, audited) | none |
| app.user_mfa (encrypted secrets + key_version) | App (service_role) | full | none |
| app.entitlements (subscription status model, D13) | App; webhook writes | SELECT/UPDATE (service_role) | **SELECT only** (gate re-check per claim) |
| app.stripe_events (event dedupe + ordering; NO user FK, survives deletion, 2y retention) | App | INSERT/SELECT (service_role) | none |
| app.deleted_subs (tombstones: sub, incarnation, retired billing ids — D15) | App | INSERT/SELECT (service_role) | none |
| app.billing_actions (persisted cancel/reconcile work items, D13/D15) | App | full (service_role) | none |
| app.tier_limits (quota + complexity + concurrency bounds) | App (admin CRUD) | SELECT | none |
| app.quota_usage (transactional reservation) | App (service_role) | INSERT/UPDATE in submit txn | none |
| app.backtests (queue; `attempt` fencing token) | Shared | INSERT (submit txn), SELECT (RLS read) | **SELECT/UPDATE** (claim, finalization) + seq |
| app.backtest_results (Simulation Ledger; written only in finalization txn) | Shared | SELECT (RLS read) | **INSERT** (inside finalization txn) |
| app.simulations (verdicts; written only in finalization txn) | Shared | SELECT (RLS read) | **INSERT** (inside finalization txn) |
| app.job_events (outbox; leased claims) | Shared | SELECT/UPDATE (lease, stamp) | **INSERT** (inside finalization txn) |
| app.firm_rulesets (payload immutable via trigger; lifecycle columns mutable) | App (admin CRUD, no destructive delete) | full (service_role, admin-gated) | **SELECT** |
| app.notification_prefs | App (RLS) | full | none |
| worker.ohlcv / worker.ingest_runs / worker.heartbeats | Backtester | SELECT (admin observability, service_role) | full |

## Environment contract & canonical-name reconciliation (Format B invariant 13)

The updated Format B standard requires canonical portfolio-wide env-var names, `.env.example` as the single consolidation point, env read only through each worker's loader, and an old→canonical table for every deviating legacy var. Audit result (2026-07-18, code-verified):

**Conforming verbatim**: `AUTH0_DOMAIN/CLIENT_ID/CLIENT_SECRET/SECRET`, `APP_BASE_URL`, `AUTH0_AUDIENCE`, `AUTH0_M2M_CLIENT_ID/SECRET`, `DATABASE_URL`, `DIRECT_URL`, `TURNSTILE_SECRET`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, `RESEND_API_KEY`, `ADMIN_NOTIFICATION_EMAIL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `SENTRY_*`, `MAIN_PORT`, `API_BASE_URL`, `MFA_MAX_ATTEMPTS`, `MFA_LOCKOUT_MS`, `BACKEND_TUNNEL_*` (Phase 8). Loader discipline holds: backend reads env only in `src/config.js`, Backtester only in `backtester/config.py`; `migrations/run.js` reads `DIRECT_URL` directly and is itself the migrate job's entrypoint/loader.

**New-concern vars (documented additions, not synonyms)**:

| Var | Concern | Why the contract has no name for it |
|---|---|---|
| `SERVICE_DATABASE_URL` | BYPASSRLS DML **without DDL** for the App Worker runtime (D14) | The contract's two-URL model predates Codex R2-7; `DIRECT_URL` (owner/DDL) still exists, confined to the migrate job |
| `WORKER_DATABASE_URL` | Backtester Worker's `worker_role` credentials | Contract names no capability-worker DB var; distinct role, distinct name |
| `STRIPE_PRICE_ID` | Server-created Checkout Sessions (D13) | Replaces the contract's Payment Link (see deviations) |
| `MFA_ENC_KEYS`, `MFA_ENC_KEY_ACTIVE` | Versioned MFA secret encryption (R2-12) | Contract's MFA row predates the key-rotation hardening |
| `ENVIRONMENT` | Backtester mode flag (Python-side `NODE_ENV` analogue) | Contract names no Python mode var |

**Contract vars deliberately dropped (Codex-approved hardenings; recorded deviations from the Format B contract)**:

| Contract prescription | Our decision | Rationale |
|---|---|---|
| `ADMIN_EXTERNAL_IDS` seed-on-login | Removed; one-time bootstrap CLI (D12) | Codex R1-12: env seeding is a persistent privilege-escalation path |
| Stripe Payment Link + `client_reference_id` | Server-created Checkout Sessions + `metadata.user_id` (D13) | Codex R2-15: parameterized links are forgeable; aligns with the contract's own anti-hijack posture |
| Backend ownerPool on `DIRECT_URL` | `service_role` pool; `DIRECT_URL` migrate-job-only (D14) | Codex R2-7: runtime must not hold DDL credentials |

**Platform-standard vars (allowed per-language, never a third name)**: runtime mode is `NODE_ENV` on the Node platform and `ENVIRONMENT` on the Python worker — cross-language platform-standard names for one concern are permitted; inventing an additional synonym is not. `PORT` is the Node platform listener var (container-internal, defaulted).

**User-declared additions (2026-07-18 `.env.example` edit, classified here)**:

| Var | Class | Status |
|---|---|---|
| `RESEND_FROM_EMAIL` | New concern (sender identity for Resend) | Adopted; consumed by the email service from Sprint 6.1 |
| `ENABLE_EMAIL_NOTIFICATIONS` | New concern (global outbound-email kill switch) | Adopted; notifier checks it before any send (Sprint 6.2) |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`, `R2_PUBLIC_DOMAIN` | **Reserved — NO consumer in this plan** | Blob storage remains out of MVP scope (gap table); the vars stay declared but nothing may read them until a storage decision adds a sprint (human-todo H-R2-1). Adding a consumer without a plan revision violates invariant 17 |

**Dev-compose constants rule**: `docker-compose-dev.yml` intentionally sets container-internal literals (local-postgres URLs targeting the compose `postgres` service, `NODE_ENV`, `PORT`, worker `ENVIRONMENT`) rather than interpolating them from `.env` — per the Format B contract, dev compose "overrides Neon URLs — never for hosting", and interpolating `DATABASE_URL` from a developer's `.env` could silently point dev containers at production Neon. The host compose (Phase 8) interpolates everything from the consolidated environment.

**Legacy old→canonical table**: `KUCOIN_YOUR_API_KEY`, `KUCOIN_YOUR_SECRET`, `KUCOIN_YOUR_PASS` (in the `.env` tracked from 2023 until its removal landed in commit 7f32fcf on 2026-07-18, and in parameters.yaml) → **RETIRED, no successor** (ADR-0001: no Venue keys; rotation is human-todo H-SEC-1). No other legacy vars existed.

**Enforcement (invariant 17 gate)**: Sprint 9.3 ships an env-contract conformance test in CI — it extracts every `process.env.*` / `os.getenv` read outside the approved loader entrypoints (`app/backend/src/config.js`, `app/backend/migrations/run.js`, `backtester/backtester/config.py`, and `app/frontend/lib/env.ts` — the frontend's server-only env loader introduced in Sprint 2.1 for all non-public server reads), collects `.env.example` keys, and fails on any undeclared name, any synonym for a contract concern, any loader-bypass read, or any read of a Reserved var. **Exemptions**: build-time-inlined `NEXT_PUBLIC_*` reads are permitted anywhere in frontend code; Next.js/Node platform internals are out of scope. **Boolean vars parse strictly**: `ENABLE_EMAIL_NOTIFICATIONS` (and future flags) accept exactly `true`/`false`; any other value or absence FAILS CLOSED in production (emails off + startup warning) — never JS truthiness. **Atomic-entry rule**: `BACKEND_TUNNEL_HOSTNAME/NAME/TOKEN` enter `.env.example` and this inventory atomically in Sprint 8.3, the sprint that first consumes them; until then they are named here as scheduled, not declared.

These deviations are candidates for absorption into the Format B standard itself (human-todo H-STD-1).

## Key decisions & tradeoffs

- **D1 Revive-repurposed, not archive** — resolves AGENTS-TODO.md.
- **D2 Backtesting only, no live execution** — ADR-0001.
- **D3 Firm Rulesets as versioned data** — ADR-0002. Payload columns (`rules`, `firm_name`, `version`, `effective_date`, `source_url`, `verified_at`) are IMMUTABLE once `published`, enforced by a database trigger tested via direct owner-role SQL (R2 findings 5-6); lifecycle columns (`published`, `revoked_at`) are the only mutable fields; deletion is prohibited (revocation only); Simulations pin the exact ruleset row id.
- **D4 CCXT public OHLCV, one primary Venue per symbol** — capacity-bounded matrix.
- **D5 Worker has no inbound ingress in MVP** — worker.cloudaitrader.com reserved.
- **D6 Standard login-first checkout** — pay-first deferred.
- **D7 (amended R2 finding 2) Outbox with provider idempotency** — Backtester inserts `app.job_events` inside the finalization transaction. The App Worker notifier claims events with a lease (`claimed_at` + expiry, SKIP LOCKED), sends via Resend passing `job_event.id` as the provider idempotency key, then stamps `sent_at`. Delivery is at-least-once at the claim layer with provider-side dedupe making duplicates inert; retry state (`attempts`, `last_error`) lives on the event row.
- **D8 (amended R2 finding 15) Determinism manifest** — `results_hash` = sha256 over: config, candle-window content hash, recorded gap ranges, ruleset row ids, engine version (git sha + semver), `uv.lock` hash, Python version, tzdata version, decimal-context policy id, and canonicalized output bytes. Identical manifests → identical hashes; the CI gate mutates a candle to prove input-freeze.
- **D9 Legacy frozen in archive/ via git mv; third-party `comparison/` moves intact with licenses.**
- **D10 Monorepo on branch `ai`.**
- **D11 Candle-faithful MVP strategies** — `buyhold`, `sma_cross` only; Heritage Engines ship dark as a tested library until quote-level Datasets exist (post-MVP ADR).
- **D12 (amended R2 findings 8-9, 13) Concurrency + privilege contracts** — Claim increments the `attempt` fencing token. Completion is a single **atomic finalization transaction**: `INSERT INTO app.backtest_results/app.simulations/app.job_events ... SELECT ... WHERE EXISTS (SELECT 1 FROM app.backtests WHERE id=:id AND attempt=:att AND claimed_by=:wid AND status='running')`, then `UPDATE app.backtests SET status='done', ... WHERE id=:id AND attempt=:att AND claimed_by=:wid AND status='running'`; commit ONLY if that UPDATE reports rowcount=1, else rollback — a reaped zombie's partial writes vanish atomically, so `PK(backtest_id)` on results stays valid with no attempt column in unique keys. The reaper requeues by incrementing `attempt`. Admin bootstrap CLI has NO `--force`: in production it refuses whenever `app.admins` is non-empty; break-glass is direct SQL through the Neon console by the human (documented in human-todo, audited by Neon's own history). _Recorded Format B contract deviation (drops `ADMIN_EXTERNAL_IDS` seeding) — see env reconciliation._
- **D13 (amended R3 findings 6-7) Stripe entitlement policy with two input domains** — `checkout.session.completed` only binds customer/subscription ids (metadata.user_id from the server-created session). The policy: (a) PRIMARY input = subscription lifecycle events, mapped from the full embedded subscription object (`status`, `current_period_end`); activation = status in (active, trialing); `past_due` keeps access within grace. (b) PAYMENT-DOMAIN OVERRIDES, which do NOT assume Stripe cancels the subscription: `charge.refunded` covering the latest invoice → revoke access + a persisted `app.billing_actions` work item (subscription cancel with retries; admin alert after 3 failures — the same reconciliation sweep D15 uses); `charge.dispute.created` → immediate local `suspended` override + admin alert. **Overrides never auto-clear** (a later invoice does not lift them); only explicit admin action or confirmed resolution clears an override (R4 finding 5). Ordering: per-subscription `last_event_created` guard; on EQUAL timestamps or any ambiguity, fetch the CURRENT Subscription from the Stripe API and reconcile from that live object before committing. `app.stripe_events` UNIQUE(event_id) makes replays no-ops. Verification covers incomplete, async-payment-failure, trial, cancel-at-period-end, refund-without-cancel, and dispute permutations. _Recorded Format B contract deviation (Checkout Sessions replace Payment Link) — see env reconciliation._
- **D14 (new, R2 finding 7) Three-tier DB credentials** — migrations run in a one-shot `migrate` compose job (same backend image, `node migrations/run.js`, `pg_advisory_lock`) holding the only `DIRECT_URL` (owner). The App Worker runtime gets `SERVICE_DATABASE_URL` (`service_role`: BYPASSRLS DML, no DDL) + `DATABASE_URL` (`app_user`). An App Worker compromise cannot alter schema. _Recorded Format B contract deviation (backend ownerPool moves off `DIRECT_URL`) — see env reconciliation._
- **A1 (assumption) Shared Auth0 tenant** → deletion is LOCAL-ONLY, via the D15 state machine.
- **D15 (amended R3 findings 3-5) Account deletion is a persisted workflow, not a transaction** — `users.deletion_state`: active → deleting → billing_severed → (row deleted). Steps, each idempotent and resumable: (1) set `deleting` + record a tombstone (`app.deleted_subs`: sub, `incarnation`, deleted_at, **stripe_customer_id, stripe_subscription_id** — the retired billing identity, R4 finding 4) + destroy the web session; submit path rejects while ≠ active; provisioning refuses sessions issued BEFORE `deleted_at` (iat check) and assigns a fresh `app.users.incarnation` uuid on re-provision, so a recreated account is a NEW billing identity: webhook reconciliation matches by customer/subscription id first — ids found in a tombstone archive as no-ops; the new incarnation gets its own Stripe customer at next checkout. (2) queued jobs → `error('account_deleted')`; running jobs fenced by attempt bump (finalization rolls back). (3) Billing severance: Stripe subscription cancel via API; the mapping is RETAINED until Stripe confirms (2xx or subscription already canceled); on failure, enqueue in a reconciliation sweep (15-min drain + admin alert after 3 failures) — never delete the row while a subscription may still bill. (4) Only after billing_severed: DELETE `app.users` — FK cascades results, simulations, job_events, prefs, quota, mfa. `app.stripe_events` has NO user FK and is NEVER cascaded (immutable billing audit keyed by event/customer/subscription ids, 2-year retention); late webhooks for a deleted user reconcile against the tombstone and archive as no-ops.
- **D16 (amended R4 findings 1-2) Account Model v1 + resolution compatibility + one account size per Backtest** — every Backtest runs under a versioned account/execution model recorded in the manifest. `spot-long-v1`: quote-currency (USDT) accounting, long-only, no leverage, no margin, no funding fees, no liquidation, no position limits; equity marks open positions at candle close. **A Backtest pins exactly ONE account size** (config field, manifest-recorded, = initial balance); the ruleset picker groups by account size, and only Rulesets matching the Backtest's pinned size are selectable — different sizes mean separate Backtests (R4 finding 1). Rule evaluation is percent-based against that pinned balance. Only Firm Rulesets whose CHALLENGE RULES `spot-long-v1` faithfully evaluates are offered (the rules — profit target, drawdowns, min days, consistency, SL discipline — are account-value rules and evaluable regardless of the firm's live leverage mechanics; rules that reference leverage/liquidation states are incompatible and excluded per-primitive). Each primitive declares its MINIMUM DATA RESOLUTION; submission REJECTS combinations the timeframe cannot prove. **Representability audit gate (R4 finding 2): Sprint 3.4 acceptance requires all four seeded firms' rulesets to be fully representable by `spot-long-v1` primitives at declared resolutions; any shortfall forces a scope decision (drop the ruleset or extend the model) BEFORE Phase 4 starts — the catalog cannot launch empty or hollow.**
- **A2 (amended R2 finding 10) Tier limits: quota + complexity + concurrency as data** — free: 10 Backtests/mo, ≤50k candles/job, 1h/1d, 2 active jobs; paid $29/mo: 200/mo, ≤1M candles/job, all timeframes, 10 active. Monthly quota reserved transactionally at submission (consumed-on-submit). Concurrency: the submit transaction takes `pg_advisory_xact_lock(hashtext(sub))`, counts the user's rows in status queued/claimed/running, and rejects at the cap; slots free automatically on any terminal status (done/error, incl. watchdog timeout and reaper outcomes). **No user cancellation in MVP** (stated; post-MVP). Numbers are placeholder DATA (H-PRICE-1).
- **MFA (amended R2 finding 12)** — local TOTP retained (shared-tenant rationale stands, endorsed by Codex R2). Secrets encrypted AES-256-GCM with a **versioned key map**: `MFA_ENC_KEYS` (JSON version→key) + `MFA_ENC_KEY_ACTIVE`; each row stores `key_version`; decrypt by stored version, encrypt/lazily re-encrypt with the active version on successful verify; rotation = add key, flip active, let re-encryption drain, retire old key when no rows reference it (admin metric). Recovery codes are HASHED (bcrypt), not encrypted — key loss cannot lock users out (recovery-code reset path). Replay protection via `last_used_step`; ±1-step skew; durable lockout retained.

## Plan (Phases → Sprints)

### Phase 0 — Discovery & Scoping
**Goal:** scope locked, accounts exist. **Exit gate:** PLAN.md approved by Codex review; provisioning checklist handed to human.
- [x] Sprint 0.1 — Current-state audit (docs/modernization-plan.md).
- [x] Sprint 0.2 — Gap table + table-ownership split.
- [ ] Sprint 0.3 — Provision accounts (HUMAN: human-todo.md).

### Phase 1 — Foundation & Scaffold
**Goal:** runnable empty monorepo, both workers + db under one compose. **Exit gate:** `docker compose -f docker-compose-dev.yml up` boots migrate (runs to completion) then backend + backtester + postgres healthy (pgAdmin only under `--profile tools`); `npm run dev` serves frontend; legacy relocated with licenses intact.
- [ ] Sprint 1.1 — Legacy relocation (git mv; attribution preserved) + monorepo scaffold + `.env` untracked.
- [ ] Sprint 1.2 — docker-compose-dev.yml with one-shot `migrate` service (D14: sole holder of DIRECT_URL; backend `depends_on: migrate: condition: service_completed_successfully`), `.env.example`, fail-fast env loaders, structured JSON logs with `request_id`.
- [ ] Sprint 1.3 — next-intl + pickContent + AntD theme from DESIGN.md; brand rename.

### Phase 2 — Auth & Identity
**Goal:** end-to-end login, token off-client. **Exit gate:** authed request traverses BFF → JWKS verify → users upsert; baseline rate limits live.
- [ ] Sprint 2.1 — Auth0 v4 server session; middleware.ts.
- [ ] Sprint 2.2 — BFF proxy injecting Bearer + `request_id`.
- [ ] Sprint 2.3 — jose JWKS verify, users upsert, withUser (`SET LOCAL`) + service_role pool split (D14); baseline global rate limit.
- [ ] Sprint 2.4 — TOTP MFA per the amended MFA decision (versioned encryption keys, hashed recovery codes, replay protection, lockout); admin bootstrap CLI (no `--force` in production — D12); last-admin + concurrent-removal guards.

### Phase 3 — Data, Schema & Worker-Integration Contract
**Goal:** domain schema + RLS + DB-as-only-boundary with explicit idempotency and immutability enforced in the database. **Exit gate:** migrate job idempotent twice on fresh Neon; worker verb-matrix passes; cross-user RLS matrix (reads AND mutations) passes; ruleset payload UPDATE via direct owner SQL is rejected by trigger; seeds load.
- [ ] Sprint 3.1 — 000 roles (owner-bootstrap for app_user, service_role, worker_role) + RLS helpers; migrate job with `pg_advisory_lock` (D14).
- [ ] Sprint 3.2 — Domain tables per ownership split incl. `attempt`, `app.stripe_events` (**no user FK, never cascaded — immutable billing audit, 2y retention; per-subscription `last_event_created`**), `app.deleted_subs` tombstones (D15), `app.job_events` (lease columns: `claimed_at`, `lease_expires_at`, `attempts`, `last_error`, `sent_at`), `app.tier_limits`, `users.deletion_state`; uniqueness contract: ohlcv PK(venue,symbol,timeframe,ts); results PK(backtest_id); simulations UNIQUE(backtest_id, ruleset_id); stripe_events UNIQUE(event_id); job_events UNIQUE(backtest_id, type). Ruleset payload-immutability trigger; ruleset compatibility metadata (min resolution, account-model requirements — D16).
- [ ] Sprint 3.3 — Worker DB access: batched upserts, claim protocol, **atomic finalization transaction** (D12 — the exact SQL shape lives here), reaper (attempt increment), heartbeats, retention.
- [ ] Sprint 3.4 — Firm Ruleset seeds with full drawdown semantics (tz/anchor, basis, trailing-vs-static, open-position treatment); provenance + `estimate` flags. **Acceptance includes the D16 representability audit: every seeded ruleset's primitives map to `spot-long-v1` at a declared resolution, documented per firm; shortfalls escalate before Phase 4.**

### Phase 4 — Backtester Worker
**Goal:** Datasets + Jobs → Simulation Ledger + verdicts end-to-end. **Exit gate:** job → claim → run → finalization; identical manifest → identical hash; zombie-fencing test (SIGSTOP/reap/SIGCONT → exactly one result set, zombie rolled back); premium gate respected; lookahead test passes.
- [ ] Sprint 4.1 — Ingestion: 10 symbols × 1 primary Venue × {1m(90d), 1h(3y), 1d(5y)}; measured capacity gate before widening; correctness policies (open-candle exclusion, gap ledger, revision detection + changed-value counter, UTC normalization, delisting flags); mutated-row detection gate. **Gap policy (amended R3 finding 8, location-aware): >0.5% missing candles in the window → submission fails `insufficient_data`. Below threshold, gaps are recorded in the manifest AND evaluated by location: a gap that intersects an open-position interval, a daily-reset boundary, or a rule-sensitive window (e.g. an SL deadline) downgrades any PASS verdict to `incomplete` (never a definitive PASS); FAIL stands when the violation is provable from present candles.**
- [ ] Sprint 4.2 — Heritage Engine extraction as dark library: characterization goldens + independent invariants + hand-computed fixtures.
- [ ] Sprint 4.3 — Backtest harness with an **execution chronology contract (R2 finding 1, fill rule amended R3 finding 9)**: signals computed on candle N's close may execute no earlier than candle N+1; market fills price at N+1 open adjusted by ADVERSE slippage, used AS-IS with **no clamping into N+1's [low, high]** (clamping would manufacture favorable fills; the adverse-modeled price is conservative by construction); gaps fill at the first tradable candle's open; fees per fill. Contract documented in `harness/replay.py`, enforced by a lookahead regression test (strategies receive only closed candles ≤ N and emit orders for N+1 — same-candle fills impossible by API construction). Runs under Account Model v1 (D16). Ledger output + determinism manifest (D8).
- [ ] Sprint 4.4 — Challenge Simulation evaluator: **verdict domain is PASS | FAIL | INCOMPLETE** (schema CHECK, UI, DoD all three — R4 finding 6); primitives declare required Ledger inputs AND minimum data resolution (D16); incompatible combinations unreachable (submit-time rejection double-checked at evaluation); location-aware gap downgrades; **FAIL with a rule-sensitive gap earlier in the window keeps the verdict ("failure proven") but flags `first_violation_indeterminate=true` — the reported rule/timestamp is the first OBSERVABLE violation (R4 finding 3)**; DD boundary suite (midnight/DST/trailing/open positions).
- [ ] Sprint 4.5 — Job loop hardening: complexity re-validation + entitlement snapshot per claim, 10-min watchdog, fencing + finalization, outbox insert in the finalization txn, structured logs with job_id.

### Phase 5 — Core App Surface
**Goal:** trader and admin can do everything the product promises. **Exit gate:** sign in → submit → watch → Ledger charts + verdicts; profile edit; deletion state machine verified with a running job; admin manages Rulesets and sees worker health.
- [ ] Sprint 5.1 — Dashboard: new-Backtest form (single symbol; complexity preview against tier bounds; ruleset picker disables combinations incompatible with the chosen timeframe/account model, with the reason shown — D16), list with polling, detail (curves, metrics, verdict cards incl. `incomplete` state with gap explanation, trade log).
- [ ] Sprint 5.2 — Account: nickname-backed profile; **deletion via the D15 persisted workflow** (tombstone + session destroy + stale-session iat guard → job fencing → confirmed billing severance → cascade; stripe_events retained) — LOCAL-ONLY on the shared tenant (A1). No export in MVP.
- [ ] Sprint 5.3 — Admin: users + audited entitlement override, Ruleset version CRUD (immutable payloads, lifecycle-only edits), worker observability (heartbeats, queue depth, ingest runs, gap/revision counters, coverage, MFA key-rotation drain metric).

### Phase 6 — Edge Services & Monetization
**Goal:** contact, email, payments correct under retries, replays, and reordering. **Exit gate:** contact delivers behind Turnstile; full Stripe permutation suite green (see gates); outbox crash test shows no duplicate emails (provider idempotency); quota + concurrency survive concurrent submissions.
- [ ] Sprint 6.1 — Contact form (Turnstile verify + Resend from `RESEND_FROM_EMAIL`, dev fallback).
- [ ] Sprint 6.2 — Outbox notifier per D7 (leased claims, Resend idempotency key = job_event id, retry state) + prefs + admin signup alert; `ENABLE_EMAIL_NOTIFICATIONS` is the global kill switch checked before any send.
- [ ] Sprint 6.3 — Stripe per D13: server-created Checkout Sessions, webhook before express.json() → stripe_events insert (dedupe) → entitlement policy (subscription-object reconciliation with per-subscription ordering; live Subscription fetch on ambiguity; refund/dispute payment-domain overrides); billing portal; transactional quota reservation + advisory-lock concurrency check in submit (A2).
- [ ] Sprint 6.4 — Vercel Analytics.

### Phase 7 — Observability & PWA
**Goal:** every runtime reports, traceable end-to-end. **Exit gate:** forced error in each of 4 runtimes reaches Sentry with correlation IDs; a job traceable request_id → backtest_id → attempt → outbox → email; /serwist/sw.js + /offline work.
- [ ] Sprint 7.1 — Sentry x4 + correlation propagation + queue-latency/retry/failure metrics.
- [ ] Sprint 7.2 — Serwist PWA.
- [ ] Sprint 7.3 — Manifest + icons.

### Phase 8 — Deploy
**Goal:** production matches local. **Exit gate:** prod authed round-trip; worker completes a real Backtest on the Pi; Stripe live webhook verified; no open LAN ports; DIRECT_URL absent from runtime service env.
- [ ] Sprint 8.1 — docker-compose-host.yml (Neon; migrations via `docker compose run --rm migrate` in the deploy script so the completed container — and its DIRECT_URL env — is removed, R3 finding 10; runtime services get only their role URLs — D14); post-deploy check: `docker ps -a` shows no migrate container; arm64 images; Pi per eg-pi-ops.
- [ ] Sprint 8.2 — Vercel env + domains; Auth0 prod callbacks; Stripe live webhook.
- [ ] Sprint 8.3 — Backend named tunnel only (D5); CORS pinned; trust proxy.

### Phase 9 — Hardening & Verification
**Goal:** ship-ready audit sweep. **Exit gate:** security review no High/Critical; CI green incl. determinism, fencing, lookahead, RLS-matrix, Stripe-permutation gates; CSP verified in prod.
- [ ] Sprint 9.1 — Security review: RLS matrix in prod, role least-privilege (incl. service_role no-DDL check), CSP/Helmet, safe errors, secrets, gitleaks, dependency audit.
- [ ] Sprint 9.2 — Rate-limit tiering finalized, scheduler drift audit, reaper/fencing prod test, Neon capacity actuals, MFA key-rotation drill.
- [ ] Sprint 9.3 — Full suites + CI incl. the **env-contract conformance gate** (invariant 17: undeclared names, synonyms, loader-bypass reads, Reserved-var reads all fail CI); README/AGENTS.md rewrite.

## Non-negotiable invariants

1. RLS is the authorization spine; withUser (`SET LOCAL`, txn-scoped) for authed ops; RLS proof = full cross-user policy matrix incl. mutations; service_role confined to webhooks/outbox/admin/provisioning paths (grep-audited).
2. The browser never holds the access token.
3. Auth0 audience mandatory on both sides.
4. Identity = Auth0 `sub`; user_id columns are TEXT.
5. middleware.ts stays middleware.ts.
6. Migrations single-source, idempotent, applied ONLY by the one-shot migrate job under pg_advisory_lock (D14); runtime services never hold DDL credentials; 000 roles + admin bootstrap CLI are the manual steps.
7. Stripe webhook before express.json(); every event id stored and deduplicated; entitlement derives from the Subscription object with per-subscription ordering (D13).
8. Secrets enforced at startup in production.
9. The database is the ONLY boundary between workers; grants match real verbs.
10. Backtester Worker is restart-safe: declared unique keys everywhere; completion happens only inside the atomic finalization transaction gated by the `attempt` CAS (D12); entitlement snapshot re-checked per claim.
11. RLS is for user-owned tables only; worker never connects as app_user.
12. One compose file boots the whole system (migrate job included).
13. No code path places orders on any Venue (ADR-0001).
14. Determinism: identical manifests → identical `results_hash`; the manifest freezes data (incl. gaps), rulesets, engine + runtime versions, and canonical serialization (D8).
15. No user-facing arbitrage Strategy until quote-level Datasets exist (D11).
16. No lookahead: strategies see only closed candles ≤ N and their orders execute at N+1 under the execution chronology contract (Sprint 4.3).
17. Env-var names are canonical portfolio-wide (Format B invariant 13): `.env.example` is the single consolidation point; each worker reads env only through its env loader; the reconciliation section above is authoritative for every addition to or deviation from the contract, and no synonym for a contract-named concern may be introduced.

## Verification gates

- Compose: migrate job exits 0, then backend, backtester, postgres healthy (pgAdmin only with `--profile tools`).
- RLS matrix: cross-user SELECT/INSERT/UPDATE/DELETE denied per table; bare-pool zero rows; grep-audit of service_role usage.
- Worker verb matrix: claim/finalization succeed; users/mfa/admins/quota fail; ruleset SELECT succeeds; service_role DDL attempt fails.
- Fencing: claim, SIGSTOP worker, reaper requeues (attempt+1), second worker finalizes; SIGCONT original → its finalization rolls back; exactly one result set (results, simulations, job_events all consistent).
- Lookahead: regression test proves a same-candle signal-fill is impossible through the Strategy API.
- Determinism: same manifest twice → identical hash; mutated candle → different hash; manifest records lock/runtime/tzdata identifiers.
- Ingestion: idempotent re-run; mutated-row detection; open candle absent; >0.5%-gap window → `insufficient_data`; sub-threshold gaps recorded in manifest and UI.
- Simulation: DD-breach fixture → FAIL at known candle; DD boundary suite green; all three terminal verdicts (PASS, FAIL, INCOMPLETE) exercised, incl. a FAIL-with-earlier-gap fixture asserting `first_violation_indeterminate=true`.
- Quota/concurrency: 2 concurrent submissions at quota-1 → exactly one accepted; user at active-job cap → 402/409; slot frees on terminal status.
- Compatibility (D16): submitting a 1h Backtest against a ruleset carrying `stop_loss_required_within_minutes` → rejected at submit with the named incompatibility; leverage-dependent ruleset absent from the spot-long-v1 catalog.
- Gap location: fixture with a sub-threshold gap inside an open-position interval → verdict `incomplete`, not PASS; same gap outside positions/boundaries → PASS with gap disclosed.
- Stripe permutation suite: replayed event no-op; out-of-order subscription events converge to subscription-object truth; equal-timestamp ambiguity triggers a live Subscription fetch; checkout-completed alone does NOT activate; async-payment-failure, trial, cancel-at-period-end land documented statuses; refund WITHOUT subscription cancel revokes; dispute suspends immediately.
- Outbox: kill notifier between send and stamp → restart resends with same idempotency key → provider dedupes, exactly one visible email.
- Deletion (D15): run against an account with one running + one queued job and an active subscription → running job's finalization rolls back, queued job errored; simulated Stripe-cancel failure leaves the mapping intact and enqueues reconciliation (no row deletion); after confirmed cancel, cascade completes; stripe_events rows survive; a pre-deletion session token replays → 401 (iat guard); fresh login → new empty account with a NEW incarnation; a late webhook for the retired customer id archives as a tombstone no-op while a checkout by the new incarnation provisions a distinct Stripe customer.
- Observability: 4 Sentry runtime events; one job traceable end-to-end.
- Env contract: the invariant-17 conformance test passes (and a seeded violation — a `process.env` read outside a loader — fails it).
- Kill switch: with `ENABLE_EMAIL_NOTIFICATIONS=false`, neither the contact form nor the outbox notifier sends (both tested); an invalid value in production mode disables sends and logs the startup warning (fail-closed).
- Prod: authed round-trip; real Backtest on the Pi; `nmap` spot check; runtime env lacks DIRECT_URL and no completed migrate container remains (`docker ps -a`).

## Risks / open questions

- A1 shared-tenant assumption unconfirmed — human-todo.
- A2 pricing/quota/complexity numbers are placeholder data — H-PRICE-1.
- Neon capacity model is a projection until Sprint 4.1 measures actuals; widening gated on measurements.
- Ruleset accuracy liability: provenance + `estimate` flags; H-RULES-1 verification; marketing never promises outcomes.
- Heritage Engine extraction may reveal live-data dependencies candle fixtures cannot exercise — bounded by invariant tests; engines ship dark regardless (D11).
- Single Pi worker throughput unknown — concurrency caps + queue monitoring; scale by adding Pis.
- `R2_*` vars are declared but unscoped: if blob storage enters scope (H-R2-1), a storage decision + sprint + threat model must be added before any consumer code.

## Out of scope

- Live or paper trading, Venue API keys, order placement (ADR-0001).
- User-facing arbitrage Strategies and quote/orderbook ingestion (D11).
- User job cancellation (A2), account export, pay-first flow, chat delivery, worker inbound tunnel, multi-language beyond en.
- Full prop-firm operations; tick/orderbook replay; paid data vendors.
- Migrating 2022 SQLite market data.

## Definition of Done

Format B DoD: both workers boot under one compose file (with the one-shot migrate job) and coordinate only via Postgres; the Backtester produces end-to-end outputs (Ingestion → Backtest → Simulation Ledger → verdicts) respecting entitlement, quota, concurrency, fencing, and finalization contracts; Sentry reports from all runtimes with correlation IDs; security review confirms role least-privilege (incl. no runtime DDL) and the RLS matrix. CloudAITrader gates: determinism manifest, lookahead, fencing, Stripe-permutation, and outbox-idempotency tests green in CI; a signed-in user on cloudaitrader.com can run a candle-faithful Backtest against a seeded immutable Firm Ruleset and see a **PASS | FAIL | INCOMPLETE** verdict with provenance in production (all three terminal states tested).
