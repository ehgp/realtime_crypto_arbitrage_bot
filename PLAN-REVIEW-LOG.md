# Plan Review Log: CloudAITrader (Template Format B)

Act 1 (grill-with-docs) complete — plan locked, CONTEXT.md created, ADR-0001/ADR-0002 recorded. MAX_ROUNDS=5.

## Act 1 record (autonomous mode)

User away; grill questions resolved from docs/, AGENTS.md, AGENTS-TODO.md, README.md, DESIGN.md, and code. Mandatory three: **scope** = full Format B plan + sprint guides (implementation later by Codex); **branch** = `ai` (current, none invented); **host target** = Vercel (cloudaitrader.com) + Pi fleet behind backend.cloudaitrader.com tunnel; worker.cloudaitrader.com reserved, unprovisioned (D5).

Decisions D1-D10 and assumptions A1-A2 recorded in PLAN.md. Docs-vs-code conflicts surfaced during the grill:

1. AGENTS.md architecture lists three exchange connectors; code shows coinbaselive.py (8 LOC) and geminilive.py (7 LOC) are stubs — README's "Kucoin currently" is correct. Resolved: D4 (CCXT, no per-exchange SDKs).
2. AGENTS-TODO.md open decision "revive or archive" — resolved: D1 revive-repurposed.
3. README profit claims (13-67%, 2022) conflict with 2026 market reality per competitor analysis — resolved: ADR-0001 consequence, claims not carried forward.
4. requirements.txt vs Pipfile drift (networkx 2.6.3 vs 2.7.1) confirms AGENTS.md gotcha 6 — resolved: single pyproject.toml + uv (Sprint 1.1).
5. DESIGN.md is alpha placeholder branded "Realtime Crypto Arbitrage Bot" — resolved: Sprint 1.3 renames and applies tokens.

Codex config echo: codex-cli 0.144.5, model `gpt-5.6-sol` (from ~/.codex/config.toml), reasoning effort `ultra`, sandbox read-only per skill.

## Round 1 — Codex: FAILED (environment), Act 2 BLOCKED 2026-07-17

Four attempts, all `-s read-only`:

1. Foreground: crashed, `memory allocation of 536870912 bytes failed`, exit 127 (stderr initially swallowed).
2. Foreground diagnostic rerun: same 512MB OOM abort after ~3 min of healthy review activity.
3. Foreground with `-c mcp_servers={}` (override did NOT disable MCP): ran healthily for 10 minutes (88 events, deep repo inspection incl. git-history secret sniffing) then hit the Bash tool's 10-minute ceiling (SIGTERM 143).
4. Background (no ceiling) with `-c model_context_window=200000 -c model_auto_compact_token_limit=150000`: 512MB OOM abort again after 13 events (thread 019f724f-1dda-7870-a1e0-24c52b746eeb).

Root cause (measured): Windows commit charge 58.2/61.2 GB (95%), free physical 0.3 GB at failure time. codex-cli aborts on a 512MB allocation under this pressure. Not fixable from this session (would require killing user processes or changing system pagefile settings).

**Verdict: none. Act 2 must be re-run by the human after freeing memory** (close heavy apps, or reboot), with, from the repo root:

```bash
codex exec -s read-only "$(cat 'C:/Users/erick/AppData/Local/Temp/claude/C--Users-erick-projects-personal-realtime-crypto-arbitrage-bot/5056bbc0-c89f-44bc-a96b-fc0f8276292f/scratchpad/codex_review_prompt.txt')"
```

or by asking Claude to "resume Act 2 of the plan review" in a fresh session (prompt file may be gone; the canonical review prompt is reproduced in the grill-with-docs-codex skill). Claude remains final arbiter on findings; the loop then proceeds per MAX_ROUNDS=5.

Partial signal salvaged from the healthy 10-minute run before the tool-timeout kill: Codex was inspecting `git log` for the committed `.env` (221 bytes, tracked since 2023) — treated as a likely [MAJOR] secrets finding and already folded into Sprint 1.1 (untrack + gitignore) and human-todo H-SEC-1 (rotate keys, decide on history purge) without waiting for the formal verdict.

## Round 1 — Codex (thread 019f735a-fc1b-76c3-a0b7-65510ee5ac33, 2026-07-17)

The plan is not implementation-ready. Its core backtesting data model cannot faithfully execute the Heritage Engines, and several security and concurrency contracts remain underspecified.

1. [BLOCKER] The core Strategies require synchronized bid/ask prices and available depth across multiple pairs, but the proposed Datasets contain only per-symbol OHLCV candles. Candle closes cannot establish executable arbitrage, spreads, path liquidity, or simultaneous availability (`PLAN.md:108-110`; `triarb.py:12-22`; `bellmanford.py:254-330`). Fix: either ingest synchronized quote/order-book snapshots or remove arbitrage Strategies from the OHLCV MVP and launch with candle-compatible Strategies.

2. [BLOCKER] A Backtest is defined over one Dataset and the UI accepts one Venue/symbol/timeframe, while triangular arbitrage needs exactly three compatible markets and Bellman-Ford needs a multi-market graph (`CONTEXT.md:27-32`; `PLAN.md:116`; `bellmanford.py:404-433`). Fix: define a versioned multi-Dataset snapshot/bundle with symbol topology, alignment rules, and completeness constraints.

3. [BLOCKER] Challenge Simulations are specified as evaluating only an Equity Curve, but stop-loss discipline, minimum trading days, consistency rules, and five-minute SL timing require order/trade events, positions, session boundaries, and sometimes unrealized equity (`CONTEXT.md:48-53`; ADR-0002:8; `PLAN.md:111`). Fix: define a canonical simulation event ledger and make each rule primitive declare its required inputs.

4. [BLOCKER] The 0.5 GB Neon estimate is untenable. Twenty symbols at one-minute resolution for two years already produce roughly 21 million rows before indexes, higher timeframes, multiple Venues, results, or metadata (`PLAN.md:17,177`). Fix: produce a measured byte-per-row capacity model and substantially reduce retention, symbols, or raw storage before schema design.

5. [BLOCKER] `FOR UPDATE SKIP LOCKED` plus a stale-claim reaper does not prevent a slow original worker from writing after its lease is reaped, causing duplicate or conflicting results (`PLAN.md:53,103,112`). Fix: use atomic claim transitions with lease expiry, attempt number/fencing token, compare-and-set completion, and unique result keys tied to the active attempt.

6. [MAJOR] “Idempotent writes” is asserted but no uniqueness contract identifies a Backtest result, Simulation, candle, Stripe event, or notification (`PLAN.md:103,155-156`). Fix: specify natural/compound unique keys and exact `ON CONFLICT` behavior for every retryable write.

7. [MAJOR] The determinism gate compares two result hashes without freezing the exact input data, ruleset version, engine version, timezone database, dependency lock, or serialization format (`PLAN.md:72,166`). Equal configs can read different candles, while semantically identical outputs can hash differently. Fix: hash a canonical manifest containing immutable Dataset snapshot IDs, Ruleset version, engine artifact, parameters, and canonicalized output bytes.

8. [MAJOR] Characterization tests would preserve demonstrably questionable legacy behavior rather than establish financial correctness. The current engine consumes latest ticker rows, mutable global configuration, wall-clock timestamps, and bid/ask depth, none of which matches the proposed harness (`triarb.py:40-70,73-97`; `bellmanford.py:289-330`). Fix: pair characterization tests with independent arbitrage invariants and hand-calculated quote/depth fixtures before treating behavior as specification.

9. [MAJOR] Daily drawdown semantics are absent: timezone, reset boundary, balance-versus-equity basis, trailing-versus-static high-water mark, open-position treatment, and DST can change verdicts. The single known-candle fixture would not detect these errors (`PLAN.md:111,168`). Fix: encode these semantics in each Ruleset version and add boundary tests across midnight, DST, open positions, and trailing drawdown.

10. [MAJOR] Published Firm Rulesets have no stated immutability, effective interval, approval state, or referential pinning from Backtests. An admin edit or deletion could silently change historical verdicts despite ADR-0002 (`PLAN.md:58,104,118`; ADR-0002:16-18). Fix: make published versions immutable, prohibit destructive deletion, store effective dates and provenance, and persist the exact Ruleset version ID on each Simulation.

11. [MAJOR] RLS validation is too weak. A bare-pool count of zero does not detect leaked `SET` state, missing policies on another table, owner-role bypass, or accidental owner-pool use in an authenticated route (`PLAN.md:93,147,164`). Fix: use transaction-scoped `SET LOCAL`, separate credentials/pools, reset-on-release safeguards, and a complete cross-user/cross-table policy matrix including mutation tests.

12. [MAJOR] `ADMIN_EXTERNAL_IDS` runtime seeding creates a persistent privilege-escalation path if deployment configuration is compromised or mistyped, and “last-admin guard” does not mitigate bootstrap injection (`PLAN.md:97`). Fix: make bootstrap a one-time audited migration/CLI operation, disable it after initialization, and test concurrent last-admin removal.

13. [MAJOR] Local TOTP duplicates Auth0’s identity/MFA responsibility without specifying secret encryption, key rotation, recovery codes, replay protection, clock skew, factor reset, or session revocation (`PLAN.md:97`). It also delays the core product. Fix: use Auth0 MFA/step-up claims or explicitly design and threat-model the entire local authenticator lifecycle.

14. [MAJOR] Stripe entitlement state is reduced to `is_paid`, which cannot correctly model active, past-due, canceled-at-period-end, refunded, disputed, or replayed/out-of-order webhook states (`PLAN.md:52,124,169`). Fix: persist Stripe customer/subscription/event IDs, verify signatures, deduplicate events, apply monotonic state transitions, and derive access from authoritative subscription status.

15. [MAJOR] Using `client_reference_id` as the entitlement binding is unsafe unless it is server-generated and verified against authenticated ownership; the plan does not state this (`PLAN.md:124`). Fix: create checkout sessions server-side with immutable internal user metadata and reject webhook mappings that do not match the stored customer-user association.

16. [MAJOR] Free-tier quota enforcement is deferred to Phase 6 and has no atomicity model. Concurrent submissions can exceed quota, and jobs submitted before cancellation may bypass the intended policy (`PLAN.md:76,120-124`). Fix: perform transactional quota reservation at submission, define refund/release behavior, and separately revalidate execution entitlement using the reserved policy snapshot.

17. [MAJOR] Completion email depends on an App Worker “observing” a status transition through polling, which can miss transitions or send duplicates across replicas and restarts (`PLAN.md:71,123`). Fix: write a transactional outbox event with job completion and let the App Worker claim/deduplicate delivery records.

18. [MAJOR] Security and observability arrive after core implementation and deployment preparation (`PLAN.md:127-143`). This makes queue failures, data leakage, and webhook flaws expensive to unwind. Fix: introduce structured telemetry, authorization tests, rate limits, CSP/CORS, and secret enforcement in the phase that creates each surface.

19. [MAJOR] User-controlled Backtest windows, Strategy parameters, symbol sets, and Ruleset selections have no resource bounds. A free user can submit CPU-heavy graph workloads or enormous windows and exhaust the single Pi worker (`PLAN.md:108-116,178`). Fix: validate normalized job complexity at submission and enforce per-tier row, duration, graph-size, runtime, memory, and concurrency limits.

20. [MAJOR] Candle ingestion lacks correctness policies for incomplete current candles, exchange revisions, gaps, duplicates with changed values, delistings, clock skew, and cross-symbol alignment. “Row count unchanged” would pass while values were corrupted (`PLAN.md:108,167`). Fix: add content-validation gates for candle closure, continuity, revision detection, timestamp normalization, and aligned snapshot completeness.

21. [MAJOR] The plan archives `comparison/`, despite using characterization tests to establish engine behavior and identifying third-party implementations as useful references. Moving all evidence before correctness work increases regression risk (`PLAN.md:73,88,109`). Fix: extract and preserve legally usable oracle fixtures and attribution before archive relocation.

22. [MINOR] The development compose exit gate says App Worker, Backtester Worker, Postgres, and pgAdmin, but the verification gate expects three healthy services (`PLAN.md:87-89,163`). Fix: state whether pgAdmin is optional/profile-gated and make the expected service count consistent.

23. [MINOR] “Migrations are idempotent, run on startup” conflicts with two workers sharing the database and with role migrations being manual bootstrap (`PLAN.md:89,101,152`). Concurrent migrators can race or apply privileged SQL from application containers. Fix: designate one migration job with an advisory lock and keep privileged role bootstrap outside ordinary service startup.

24. [MINOR] Account export is explicitly a stub even though account deletion, financial-style results, and user-owned data are product surfaces (`PLAN.md:117`). Fix: either deliver a functional export or remove it from the MVP UI and acceptance language.

25. [MINOR] Sentry event arrival alone does not prove useful observability; the plan lacks correlation IDs across BFF, API, Backtest Job, worker attempt, and webhook/outbox processing (`PLAN.md:128-130,170`). Fix: define propagated correlation identifiers and verify searchable job-level traces, structured logs, queue latency, retries, and failure reason metrics.

Confidence: 96/100

VERDICT: REVISE

### Claude's response (Round 1, 2026-07-18)

Revised PLAN.md to Revision 2 and updated CONTEXT.md. Disposition of the 25 findings:

- **Accepted 1-2 (blockers) via scope change D11**: candle closes cannot establish executable arbitrage. Launch Strategies become candle-faithful (`buyhold`, `sma_cross`, single symbol/Venue/timeframe); Heritage Engines remain an extracted, invariant-tested LIBRARY, not user-facing, until quote-level Datasets exist (post-MVP, own ADR). This also aligns with docs/competitor-analysis.md ("arbitrage bots are not the product").
- **Accepted 3**: new canonical term Simulation Ledger (balance+equity series, trade log, position events, daily PnL); rule primitives declare required inputs; CONTEXT.md updated.
- **Accepted 4**: matrix shrunk to 10 symbols x 1 primary Venue x {1m/90d, 1h/3y, 1d/5y} (~1.6M rows, 240-320 MB projected); measured capacity gate before widening.
- **Accepted 5 via D12**: `attempt` fencing token; claims increment it; completions CAS-guarded; reaper requeues by incrementing; zombie-fencing verification gate added (SIGSTOP test).
- **Accepted 6**: explicit uniqueness contract enumerated per retryable write in Sprint 3.2.
- **Accepted 7 via amended D8**: determinism manifest freezes candle-window content hash, ruleset row ids, engine version, canonical serialization; gate proves input-freeze by mutating a candle.
- **Accepted 8**: characterization goldens (porting fidelity) paired with independent invariants + hand-computed fixtures; severity reduced by D11 (engines dark).
- **Accepted 9**: DD semantics (tz/anchor, basis, trailing-vs-static, open positions) encoded per Ruleset version; boundary test suite (midnight/DST/trailing/open-positions).
- **Accepted 10**: published Ruleset versions immutable, deletion = revocation, Simulations pin ruleset row id (D3 amended).
- **Accepted 11**: RLS proof upgraded to full cross-user policy matrix incl. mutations + ownerPool grep-audit (invariant 1).
- **Accepted 12 via D12**: runtime env seeding removed; one-time audited bootstrap CLI; concurrent last-admin-removal test.
- **Hybrid 13**: REJECT switching to Auth0 MFA — the tenant is shared (A1); tenant-wide MFA policies would affect sibling apps, which is exactly why Format B standardizes local TOTP. ACCEPT the lifecycle spec: AES-256-GCM secret encryption (`MFA_ENC_KEY`), 10 one-time recovery codes, +/-1-step skew, replay protection (`last_used_step`), factor reset + session revocation, durable lockout retained.
- **Accepted 14-15 via D13**: subscription status model (none|active|past_due|canceled) + `current_period_end`, `is_paid` derived; `app.stripe_events` UNIQUE(event_id) dedupe + out-of-order protection; server-created Checkout Sessions with metadata.user_id replace parameterized Payment Links; unmatched webhook mappings rejected + alerted.
- **Accepted 16 via amended A2**: transactional quota reservation at submission (consumed-on-submit policy stated); complexity bounds (candles/job, concurrency, runtime watchdog) per tier as data.
- **Accepted 17 via amended D7**: transactional outbox `app.job_events` written in the completion txn; App Worker claims/stamps; polling design dropped.
- **Accepted 18 (targeted, not a reshuffle)**: structured logs + request_id from Phase 1, baseline rate limits at Phase 2, per-surface security acceptance in each phase; Phase 9 remains the audit sweep. Foundation order preserved per Format B.
- **Accepted 19**: per-tier complexity bounds + 10-min runtime watchdog + per-user concurrency caps; single-symbol Backtests shrink the bound surface.
- **Accepted 20**: ingestion correctness policies (open-candle exclusion, gap ledger, revision detection with changed-value counter, UTC normalization, delisting flags) + mutated-row detection gate.
- **Partially rejected 21**: relocation uses `git mv` within the repo — nothing is lost and Sprint 4.2 explicitly reads fixtures from `archive/legacy-bot/`; ordering unchanged. Accepted the attribution point: `comparison/` moves intact with licenses (D9 amended).
- **Accepted 22**: pgAdmin profile-gated; gate wording fixed to 3 services.
- **Accepted 23**: App Worker is the only migrator, under pg_advisory_lock (invariant 6).
- **Accepted 24**: export stub removed from MVP UI/acceptance.
- **Accepted 25**: correlation IDs (request_id, job_id) propagated end-to-end; traceability is a Phase 7 gate.

Sprint guides in docs/sprints/ will be synced to Revision 2 in one pass after the review converges (avoids churn per round; noted so Codex reviews PLAN.md as authoritative).

## Round 2 — Codex (same thread, 2026-07-18)

Revision 2 resolves the original five blockers and most prior major findings. The following issues remain implementation-significant.

1. [BLOCKER] The candle replay contract still does not define signal/fill chronology, so SMA Crossover can accidentally observe a candle’s close and fill at that same close, introducing lookahead bias and invalidating Challenge verdicts (`PLAN.md:117-118`). Fix: define an event timeline where close-derived signals execute no earlier than the next tradable event, with explicit gap, fee, slippage, and OHLC price-bound rules.

2. [MAJOR] The outbox claims duplicate-free delivery after a notifier crash, but `send` followed by `sent_at` cannot be atomic with an external email provider; a crash between them necessarily permits duplicates (`PLAN.md:74,130,181`). Fix: use a stable provider idempotency key derived from `job_event.id`, plus leased claims and retry state, or explicitly promise at-least-once delivery.

3. [MAJOR] Stripe ordering based on “Stripe object timestamps” is not a safe monotonic state machine: events from different object types can arrive out of order, share timestamps, or describe different lifecycle transitions (`PLAN.md:80,160,180`). Fix: reconcile entitlement from the authoritative Subscription object/version and test permutations across checkout, invoice, subscription, refund, and dispute events.

4. [MAJOR] The verification gate says `checkout.session.completed` flips entitlement status, but checkout completion alone does not prove that a subscription is active or its payment succeeded (`PLAN.md:180`). Fix: make subscription/invoice state authoritative and test incomplete, async-payment, failed-payment, trial, cancellation, refund, and dispute flows.

5. [MAJOR] Firm Ruleset immutability conflicts with revocation: D3 says revocation changes `published=false`, while Sprint 3.4 says updates to published rows are rejected (`PLAN.md:70,111`). Fix: keep version payloads immutable and store revocation in separate mutable lifecycle metadata or an append-only superseding record.

6. [MAJOR] “Trigger or service layer” leaves Ruleset immutability optional even though the App Worker uses an owner pool that can bypass ordinary RLS protections (`PLAN.md:60,111`). Fix: enforce payload immutability and protected deletion in database constraints/triggers, then test direct SQL through the owner role.

7. [MAJOR] Running migrations from the App Worker requires production runtime access to schema-owner/DDL credentials, expanding the impact of an App Worker compromise (`PLAN.md:108,142,159`). Fix: use a one-shot migration container/job with advisory locking and separate credentials, then start the App Worker with only runtime privileges.

8. [MAJOR] The queue schema is internally ambiguous: results are described as “keyed by attempt,” but the uniqueness contract declares `PK(backtest_id)`, and “attempt CAS” does not specify how an INSERT is conditionally fenced (`PLAN.md:57,79,109`). Fix: define one transactional SQL operation or stored procedure using `INSERT … SELECT` from the currently leased Backtest followed by guarded completion, with stale-attempt tests for every result table.

9. [MAJOR] Simulation uniqueness omits the Backtest attempt even though a reaped attempt may have partially inserted Simulations before losing its completion CAS (`PLAN.md:58,109,175`). Fix: fence every Simulation insert against the active attempt and either include attempt in staging keys or publish results only through an atomic finalization transaction.

10. [MAJOR] Monthly quota reservation does not implement the stated concurrent-job limits. Two and ten “concurrent jobs” require an atomic queued/running slot lifecycle, including release after failure, cancellation, timeout, and reaping (`PLAN.md:82,109,119,179`). Fix: separately specify and test transactional concurrency-slot acquisition and idempotent release.

11. [MAJOR] Account deletion has no coordination contract for queued/running Backtests, results, quota reservations, outbox events, Stripe associations, or worker writes racing deletion (`PLAN.md:122-124`). Fix: define a deletion state machine that blocks submissions, cancels or fences active jobs, revokes billing mappings, handles dependent records, and only then deletes/anonymizes the account.

12. [MAJOR] The local TOTP design still omits encryption-key rotation despite accepting the original lifecycle finding; a single `MFA_ENC_KEY` creates an all-record compromise and rotation dead end (`PLAN.md:83,104`). Fix: store a key version with each encrypted secret and define dual-key rotation, re-encryption, retirement, and failure-recovery procedures.

13. [MINOR] Admin bootstrap is described as one-time but supports `--force` after initialization, retaining a privileged bypass whose authorization and audit protection are unspecified (`PLAN.md:104`). Fix: remove `--force` in production or require an explicit break-glass credential and immutable security audit event.

14. [MINOR] The ingestion gate verifies mutation detection but not missing-candle behavior: recording a gap does not define whether affected Backtests fail, warn, or silently replay discontinuous data (`PLAN.md:115,177`). Fix: define Dataset completeness thresholds and make the manifest record gaps, with deterministic reject/warn policies tested at window boundaries.

15. [MINOR] The determinism manifest identifies the engine by git SHA and semver but does not freeze dependency lock hash, Python/runtime version, timezone database, or numeric precision policy (`PLAN.md:75,167,176`). Fix: include runtime/lockfile/tzdata identifiers and canonical decimal/float normalization in the manifest contract.

The partial rejection of finding 21 is reasonable: an in-repository `git mv` preserves the reference material and attribution. Retaining local TOTP instead of Auth0 MFA is also defensible for a shared tenant, but only after the remaining key-rotation gap is closed.

Confidence: 97/100

VERDICT: REVISE

### Claude's response (Round 2, 2026-07-18)

All 15 findings accepted; PLAN.md is now Revision 3. No rejections this round.

- **1 (blocker)** -> Execution chronology contract in Sprint 4.3 + invariant 16: strategies see only closed candles <= N, orders execute at N+1 (open +/- slippage, bounded by N+1 [low,high]); lookahead impossible by API construction; dedicated regression gate.
- **2** -> D7 amended: leased outbox claims + Resend idempotency key = job_event.id; at-least-once claims with provider dedupe; retry state on the row; crash-between-send-and-stamp gate added.
- **3-4** -> D13 amended: Subscription object is authoritative; checkout.session.completed only binds ids; per-subscription `last_event_created` ordering; permutation suite (replay, out-of-order, incomplete, async-failure, trial, cancel-at-period-end, refund, dispute) in gates.
- **5-6** -> D3 amended: payload columns immutable via DB trigger (tested with direct owner SQL); lifecycle columns (`published`, `revoked_at`) are the mutable exception; deletion prohibited.
- **7** -> New D14: one-shot migrate job holds the only DIRECT_URL (owner); App Worker runtime uses service_role (BYPASSRLS DML, no DDL) + app_user; prod gate asserts runtime env lacks DIRECT_URL.
- **8-9** -> D12 amended: atomic finalization transaction (INSERT ... WHERE EXISTS fenced by attempt/claimed_by/status + guarded UPDATE with rowcount=1 commit condition); zombie partial writes roll back atomically, so results keep PK(backtest_id) with no attempt in unique keys; simulations + job_events written in the same txn.
- **10** -> A2 amended: per-user concurrency via pg_advisory_xact_lock(hashtext(sub)) + count check in the submit txn; slots free on terminal status; no user cancellation in MVP (stated out of scope).
- **11** -> New D15: deletion state machine (mark deleting -> error queued jobs -> fence running via attempt bump -> sever Stripe -> cascade delete); idempotent steps; gate tests deletion against live jobs.
- **12** -> MFA amended: versioned key map (MFA_ENC_KEYS + MFA_ENC_KEY_ACTIVE, per-row key_version, lazy re-encryption, drain metric, rotation drill in Sprint 9.2); recovery codes bcrypt-hashed so key loss cannot lock users out.
- **13** -> --force removed; production bootstrap refuses when admins exist; break-glass = human via Neon console (documented in human-todo).
- **14** -> Gap policy: >0.5% missing candles -> insufficient_data; below threshold recorded in manifest + UI.
- **15** -> Manifest extended: uv.lock hash, Python version, tzdata version, decimal-context policy id.

## Round 3 — Codex (same thread, 2026-07-18)

Revision 3 resolves all 15 Round 2 findings as written. New review exposes several domain and lifecycle gaps.

1. [BLOCKER] Firm Rulesets can require five-minute stop-loss placement, but Backtests allow 1h/1d candles whose Simulation Ledgers cannot prove or disprove that rule; declaring required Ledger fields does not solve insufficient temporal resolution (`PLAN.md:91,120,124,127`). Fix: make each rule primitive declare minimum data resolution and reject incompatible Dataset/Ruleset combinations before submission.

2. [MAJOR] The portfolio model remains underspecified for crypto prop Challenges: initial balance, account currency, leverage, margin, liquidation, shorting, funding fees, position limits, and mark-price versus candle-price equity are absent, yet they materially determine drawdowns and verdicts (`PLAN.md:22,126-127`). Fix: define a versioned account/execution model in the Backtest manifest and restrict supported Firm Rulesets to mechanics the model faithfully represents.

3. [MAJOR] D15 calls deletion “one service_role transaction” while performing an external Stripe cancellation inside it; database transactions cannot atomically commit with Stripe, and “best-effort cancel + sever mapping” can leave an actively billing subscription with no local user association (`PLAN.md:90,133,193`). Fix: use a persisted deletion workflow that retains the Stripe mapping until cancellation is confirmed or placed in a reconciliation queue, then finalize database deletion.

4. [MAJOR] D15 cascades “events,” which risks deleting Stripe webhook deduplication/audit records; subsequent delayed or replayed events could be reprocessed after the user mapping is gone (`PLAN.md:62,90`). Fix: retain or pseudonymize billing-event records under an immutable billing identity with a defined retention period instead of cascading them with user data.

5. [MAJOR] Local-only deletion does not revoke the Auth0 application session or prevent the normal login upsert from immediately recreating the deleted user (`PLAN.md:89-90,112,133`). Fix: revoke the local session during deletion and retain a deletion tombstone or require explicit account recreation consent before `users` upsert can restore access.

6. [MAJOR] D13 says entitlement derives exclusively from Subscription lifecycle events but also expects refunds and disputes to change access; refunds/disputes are payment-domain events and do not necessarily alter Subscription status, producing an unresolved policy contradiction (`PLAN.md:87,140,191`). Fix: define separate subscription, payment, refund, and dispute inputs to one explicit entitlement policy and test each without assuming Stripe cancels the Subscription.

7. [MAJOR] Equal-timestamp Stripe events remain unsafe: “reconcile from the object” is ambiguous when two embedded event snapshots differ but share `event.created`; arrival order can still select stale state (`PLAN.md:87`). Fix: on equal or ambiguous ordering, retrieve the current Subscription from Stripe and reconcile from that authoritative live object before committing entitlement state.

8. [MAJOR] Allowing up to 0.5% missing candles regardless of location can silently cross a gap containing the true price extreme, daily reset, stop-loss deadline, or liquidation event and still produce a confident verdict (`PLAN.md:124,188`). Fix: reject gaps intersecting positions or rule-sensitive intervals and label any remaining gap-tolerant verdict as incomplete rather than definitive PASS.

9. [MINOR] The fill rule clamps slippage-adjusted prices into the next candle’s range, which can manufacture favorable execution when modeled slippage lies outside observed OHLC (`PLAN.md:126`). Fix: treat out-of-range modeled fills as unfilled or apply a documented conservative fill rule instead of clipping the price.

10. [MINOR] The migration credential is confined to a one-shot container but remains inspectable in the stopped container configuration unless removed; “runtime env lacks DIRECT_URL” alone does not prove credential disposal (`PLAN.md:88,105,150-151`). Fix: inject the owner URL through a short-lived secret mechanism and remove the completed migration container before runtime verification.

Confidence: 96/100

VERDICT: REVISE

### Claude's response (Round 3, 2026-07-18)

All 10 findings accepted; PLAN.md is now Revision 4.

- **1 (blocker)** -> New D16: rule primitives declare minimum data resolution; submission rejects Dataset/Ruleset combinations the timeframe cannot prove (e.g. SL-within-5-min requires <=1m); UI disables incompatible picks with reasons; evaluation double-checks.
- **2** -> D16 Account Model v1 (`spot-long-v1`): quote-USDT accounting, long-only, no leverage/margin/funding/liquidation; initial balance = ruleset account size; equity marks at close; model version recorded in the manifest; only mechanically-representable rulesets offered.
- **3** -> D15 reworked to a persisted workflow (deletion_state machine); Stripe mapping RETAINED until cancel confirmed; reconciliation sweep + admin alert on failure; row deleted only after billing_severed.
- **4** -> app.stripe_events has no user FK and is never cascaded (immutable billing audit, 2y retention); late events for deleted users reconcile against tombstones as archived no-ops.
- **5** -> Deletion destroys the web session, writes an app.deleted_subs tombstone, and provisioning refuses sessions issued before deleted_at (iat guard) — stale-session resurrection impossible; fresh login intentionally provisions a new empty account (A1 semantics).
- **6** -> D13 restated as a two-domain policy: subscription lifecycle primary; refund/dispute payment-domain overrides that never assume Stripe cancels the subscription (refund -> revoke + best-effort cancel + alert; dispute -> immediate suspend + alert).
- **7** -> Equal-timestamp/ambiguous ordering -> fetch the CURRENT Subscription from the Stripe API and reconcile from the live object before committing.
- **8** -> Gap policy is location-aware: gaps intersecting open positions, daily resets, or rule-sensitive windows downgrade PASS to `incomplete` (never definitive); FAIL stands when provable from present data; global 0.5% submission bar retained.
- **9** -> Fill rule: adverse-slippage price used as-is, clamping removed (clamping manufactured favorable fills).
- **10** -> Migrations run via `docker compose run --rm migrate` in the deploy script; post-deploy gate asserts no completed migrate container (and runtime env without DIRECT_URL).

## Round 4 — Codex (same thread, 2026-07-18)

Revision 4 resolves all 10 Round 3 findings directly. Four implementation-significant gaps remain.

1. [BLOCKER] Account Model v1 derives initial balance from the Firm Ruleset, but one Backtest can produce multiple Simulations against different Rulesets; Rulesets with different account sizes cannot share one Simulation Ledger or results hash (`PLAN.md:68,87,92`). Fix: either restrict each Backtest to Rulesets with an identical account size or create a separate Backtest/Ledger per account-model configuration.

2. [MAJOR] D16 may exclude every named crypto prop-firm Ruleset if those Challenges depend on leverage, margin, liquidation, or short selling, leaving the advertised core catalog empty while technically satisfying compatibility filtering (`PLAN.md:9,92,122,193`). Fix: add a Phase 0 compatibility audit requiring at least one named, provenance-verified Firm Ruleset to be fully representable by `spot-long-v1`, or change the MVP claim/account model.

3. [MAJOR] A gap can preserve an overall FAIL verdict but invalidate the promised “first violated rule and when”; an unseen violation may have occurred earlier inside the gap (`CONTEXT.md:56-58`; `PLAN.md:126,194`). Fix: retain FAIL only as “failure proven,” but mark first-violation identity/timestamp indeterminate whenever an earlier rule-sensitive gap exists.

4. [MAJOR] Deletion tombstones are keyed only by Auth0 `sub`, while fresh login intentionally recreates an account with the same `sub`; late events from the deleted Stripe customer and valid events for a new customer therefore need an account-generation boundary (`PLAN.md:63,91,120,197`). Fix: introduce an immutable account-incarnation ID and retain deleted customer/subscription IDs so webhook reconciliation distinguishes old billing identities from the recreated account.

5. [MAJOR] Refund-triggered subscription cancellation is only “best-effort,” unlike deletion cancellation, with no retry/reconciliation contract; a failed cancel can leave future invoices charging and automatically clear the local override (`PLAN.md:88`). Fix: persist refund cancellation work with retries and alerts, and prohibit invoice-driven override clearing until cancellation or an explicit admin decision resolves the refund.

6. [MINOR] The Definition of Done still promises a pass/fail verdict even though `incomplete` is now a legitimate terminal Simulation state (`PLAN.md:126,134,220`). Fix: change the product and DoD contract to `PASS | FAIL | INCOMPLETE` and test all three terminal outcomes.

Confidence: 97/100

VERDICT: REVISE

### Claude's response (Round 4, 2026-07-18)

All 6 findings accepted; PLAN.md is now Revision 5.

- **1 (blocker)** -> D16 amended: a Backtest pins exactly ONE account size (config + manifest); ruleset picker groups by size; different sizes = separate Backtests. (Normalization was considered but rejected for MVP as hidden complexity.)
- **2** -> D16 representability audit gate in Sprint 3.4: all four seeded firms' rulesets must map fully to `spot-long-v1` primitives at declared resolutions before Phase 4; shortfalls force an explicit scope decision. Note: the four firms' core rules (profit target, drawdowns, min days, consistency, SL discipline) are account-value rules and evaluable under spot-long; leverage/liquidation are trading mechanics, not evaluated rules — the audit proves this per firm instead of assuming it.
- **3** -> Verdict FAIL is retained as "failure proven" but `first_violation_indeterminate=true` whenever a rule-sensitive gap precedes the observed violation; CONTEXT.md updated to "first OBSERVABLE violated rule".
- **4** -> `app.users.incarnation` uuid per provision; tombstones retain retired stripe customer/subscription ids; webhook reconciliation matches billing ids first (tombstoned ids archive as no-ops); recreated accounts get a fresh Stripe customer.
- **5** -> Refund/dispute cancels unified into persisted `app.billing_actions` work items (retries + alert after 3 failures, same sweep as D15); overrides never auto-clear — admin action or confirmed resolution only.
- **6** -> Verdict domain is PASS | FAIL | INCOMPLETE across schema CHECK, UI, gates, and Definition of Done; all three terminal states tested.

## Round 5 — Codex (same thread, 2026-07-18)

No implementation-significant findings.

Revision 5 resolves all Round 4 issues at plan-level readiness:

- Backtests pin one account size; incompatible Rulesets require separate Backtests.
- Sprint 3.4 blocks Phase 4 until the seeded Rulesets pass the representability audit.
- Verdicts consistently support `PASS | FAIL | INCOMPLETE`, including indeterminate first-violation handling.
- Billing incarnations isolate recreated accounts from retired Stripe identities.
- Refund cancellation and deletion use persisted, retryable billing actions.
- Verification gates cover concurrency, fencing, deletion recovery, billing reordering, no-lookahead behavior, data gaps, compatibility, and determinism.

Remaining details belong appropriately in sprint guides and implementation tests. The open pricing, capacity, tenant, and Ruleset-verification decisions are explicitly gated and do not prevent execution from starting.

Confidence: 98/100

VERDICT: APPROVED

## Resolution: APPROVED (Round 5 of 5, 2026-07-18)

Act 2 converged. PLAN.md Revision 5 stands as the locked spec. Cross-model review totals: 56 findings across 4 REVISE rounds (Round 1: 25, Round 2: 15, Round 3: 10, Round 4: 6), 53 accepted, 2 rejected with logged reasons (R1-13 Auth0-MFA switch, R1-21 archive ordering — both rejections endorsed by Codex), 1 partial (R1-18 targeted shift-left instead of a reshuffle). Sprint guides in docs/sprints/ synced to Revision 5 after this entry. Next step per skill: human chooses — Codex builds (/codex-build with SPEC_FILE=PLAN.md after committing plan artifacts), Claude builds, or stop.

## Act 3 — Build

### Round 1 — Codex build (thread 019f75e5-24f3-7812-bc8b-3db9ae88e115, 2026-07-18)

Scope: Phase 1 (Sprint Guide 01) only. Sandbox: workspace-write + network. Codex reported `status: "blocked"` honestly: all scaffolds built and locally validated (frontend build+ESLint, ruff, backend fail-fast, compose config, DIRECT_URL confinement), but the sandbox denied (a) the git index (.git is read-only under codex workspace-write -> git mv / git rm --cached / staging impossible) and (b) the Docker named pipe (compose proof unrunnable). 41 files declared in the report contract; git cross-check found no undeclared non-artifact changes. Deviations declared: legacy relocation not performed, .env still tracked, proof stopped at Docker, middleware.ts deprecation warning retained per frozen spec.

### Claude's verdict (Round 1)

Report contract: VALID. Diff review (full PR-style read of compose, backend config/index/migration runner, backtester Dockerfile/config/service/health/pyproject, frontend middleware/i18n/layout/theme/content/page, root file diffs): faithful to spec, no gamed criteria, no stubs-as-done; the Phase-1 worker loop is an honest declared placeholder. One undeclared minor deviation: backend base image node:22-alpine vs the contract's node:22-slim (defensible — busybox wget enables the healthcheck; noted, not actioned).

Takeover (environmental, no fix rounds burned): (1) performed the sprint-01 git relocation myself — 118 renames staged into archive/legacy-bot/ (docs/source -> docs-sphinx), `git rm --cached .env` staged; (2) parameterized the compose host port as `${MAIN_PORT:-4200}` after the proof hit a host collision with the sibling gtm-engineering stack on 4000 (+ .env.example documents MAIN_PORT, API_BASE_URL now 4200); (3) fixed the backend healthcheck target localhost -> 127.0.0.1 (busybox wget resolves localhost to ::1; listener is IPv4-only).

Proof (run by Claude, not delegated): `docker compose -f docker-compose-dev.yml up -d --build --wait && ... ps && curl -sf localhost:4200/health && (cd app/frontend && npm run build) && (cd backtester && uv run python -m backtester.health)` -> **PROOF_EXIT=0**. Evidence: postgres/backend/backtester all (healthy); migrate exited 0 twice with `migrations_complete count:0` (idempotent); curl returned `{"ok":true}`; Next.js 16.2.10 production build clean (TS strict, /en SSG; known middleware->proxy deprecation warning retained per invariant 5); backtester prints ok.

**Phase 1 exit gate: PASS.** Awaiting human diff sign-off + commit (nothing committed).
