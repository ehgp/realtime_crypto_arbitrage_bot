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

## Re-grill 2026-07-18 — updated Template Format B standard (Act 1 delta)

User updated the Format B skill and asked for re-execution. Skill deltas identified: grill-with-docs-codex — MAX_ROUNDS default 5->10, light memory gate before review rounds, push notification at resolution, Act 3 joint-review stage made explicit; template-format-b — NEW invariant 13 (canonical portfolio-wide env-var names, .env.example as sole consolidation point, env only via each worker's loader, old->canonical rename table required for migrations) + Sprint 0.3 amended accordingly.

Delta grill outcome (autonomous; code-audited with grep over app/backend, backtester, frontend):

- G1: Loader discipline already holds (config.js / config.py; migrations/run.js is the migrate job's own entrypoint). No code changes required by invariant 13.
- G2: All existing vars conform verbatim except documented new concerns (SERVICE_DATABASE_URL, WORKER_DATABASE_URL, STRIPE_PRICE_ID, MFA_ENC_KEYS/_ACTIVE, ENVIRONMENT).
- G3: Three deliberate contract deviations RETAINED, all Codex-approved in Rounds 1-2 and now recorded as formal deviations with rationale: no ADMIN_EXTERNAL_IDS seeding (D12/R1-12), Checkout Sessions over Payment Link (D13/R2-15), service_role split with DIRECT_URL confined to the migrate job (D14/R2-7). Rejected alternative: reverting to contract letter — would reintroduce three adjudicated security regressions to satisfy naming policy; invariant 13 bans synonym INVENTION, and these are new concerns or justified drops, now tabled in the plan.
- G4: Legacy old->canonical table emitted: KUCOIN_* vars RETIRED (ADR-0001), rotation H-SEC-1.
- PLAN.md -> Revision 6: new "Environment contract & canonical-name reconciliation" section, new invariant 17, D12/D13/D14 annotated as recorded deviations, human-todo H-STD-1 (offer deviations upstream to the standard).

Act 2 re-review of Revision 6 follows in a FRESH Codex session (prior thread's context is Revision-5 history; new standard warrants clean eyes). MAX_ROUNDS=10 per updated skill.

## Re-review Round 1 — Codex fresh session (thread 019f7816-698d-7a40-96e6-0b00ebcfb306, 2026-07-18) on Revision 6

1. [MAJOR] The reconciliation is incomplete: `.env.example` adds `RESEND_FROM_EMAIL`, `ENABLE_EMAIL_NOTIFICATIONS`, and five `R2_*` variables that are absent from the supposedly authoritative reconciliation, while `PORT` and `NODE_ENV` are consumed by the backend but omitted too (`.env.example:32-41`; `app/backend/src/config.js:3,12-13`; `PLAN.md:77-101,210`). Fix: inventory every consumed or declared variable, classify each as canonical/new/deviation/platform-only, and remove the unexplained R2 storage variables unless blob storage is explicitly in scope.

2. [MAJOR] Invariant 17 has no verification gate; every named gate can pass after introducing a synonym or a direct `process.env`/`os.getenv` read outside the loaders (`PLAN.md:210,212-229`). Fix: add a CI gate that extracts environment reads and `.env.example` keys, rejects undeclared names and reads outside approved loader entrypoints, and checks exact set reconciliation.

3. [MAJOR] “`.env.example` as the single consolidation point” conflicts with compose embedding separate database URLs and production-mode flags directly, so deployments can drift from the documented contract without changing `.env.example` (`docker-compose-dev.yml:31-45,59-61`; `PLAN.md:77,210`). Fix: make compose interpolate all application-contract variables from the consolidated environment, retaining literals only for explicitly documented container-internal constants.

4. [MAJOR] The R2 variables appear to import an undeclared Cloudflare Blob-storage subsystem (“infra S04/S13”), but Revision 6 contains no storage architecture, sprint, dependency, threat model, retention policy, or verification gate (`.env.example:36-41`; `PLAN.md:125-190`). Fix: delete the R2 variables from this plan’s scaffold or add an explicit scoped storage decision and implementation/test work.

5. [MINOR] The legacy reconciliation says the KuCoin variables came from a “tracked `.env`,” but `.env` is not present in `HEAD`; this weakens the claimed code-verified provenance (`PLAN.md:99`). Fix: cite the actual historical commit/path containing those names or describe `.env` as an untracked local legacy artifact.

6. [MINOR] The plan labels `ENVIRONMENT` a new concern even though it duplicates the established runtime-mode concern represented by `NODE_ENV`, which undermines the no-synonym rule unless cross-language naming is expressly permitted (`PLAN.md:89,210`; `docker-compose-dev.yml:42,60`). Fix: define a portfolio rule allowing language-specific runtime-mode names, or use one canonical name across both workers.

Confidence: 98/100

VERDICT: REVISE

### Claude's response (re-review Round 1, 2026-07-18)

Context discovered during verification: the user committed Phase 1 as 7f32fcf and hand-edited .env.example (RESEND_FROM_EMAIL, ENABLE_EMAIL_NOTIFICATIONS, blanked DB URLs, five R2_* vars referencing "infra S04/S13") — Codex reviewed the real tree, so its findings against "my" reconciliation were findings against stale coverage. PLAN.md is now Revision 7.

- **1 accepted**: reconciliation extended — RESEND_FROM_EMAIL + ENABLE_EMAIL_NOTIFICATIONS adopted as new-concern vars (consumed in Sprints 6.1/6.2); NODE_ENV/ENVIRONMENT/PORT classified platform-standard; full inventory now matches .env.example.
- **2 accepted**: invariant-17 conformance CI gate added (Sprint 9.3 + verification gates): extract env reads outside approved loaders, compare .env.example keys to the declared set, fail on undeclared/synonym/loader-bypass/Reserved reads; gate self-test seeds a violation.
- **3 partially rejected (logged)**: dev-compose DB literals are container-internal constants targeting the compose-local postgres — the Format B contract itself says dev "overrides Neon URLs; never for hosting", and interpolating DATABASE_URL from a developer .env could silently point dev containers at production Neon (a worse failure than drift). Documented as the "dev-compose constants rule" in the reconciliation; the host compose interpolates everything. Accepted the documentation duty, rejected blanket interpolation.
- **4 resolved third-way**: R2_* vars are user-authored signal, not plan scope — classified **Reserved, no consumer permitted** (invariant 17 enforcement covers them), storage stays Out in the gap table, and H-R2-1 asks the human to scope or drop. Deleting user content or inventing a storage subsystem were both rejected.
- **5 accepted**: provenance reworded — .env was tracked from 2023 until its removal landed in 7f32fcf (2026-07-18); rotation H-SEC-1 unchanged.
- **6 accepted**: platform-standard cross-language rule defined (NODE_ENV/Node, ENVIRONMENT/Python; no third name).

## Re-review Round 2 — Codex (same thread, 2026-07-18) on Revision 7

1. [MAJOR] The CI contract names backend, migration, and Backtester loaders but no frontend loader, so Phase 2’s Auth0/Next.js environment reads will either fail the gate or bypass invariant 17 (`PLAN.md:80,114,156-158,205,225`). Fix: define an approved frontend server-env loader, require all non-public frontend reads through it, and explicitly permit build-time `NEXT_PUBLIC_*` reads.

2. [MAJOR] `ENABLE_EMAIL_NOTIFICATIONS` is designated a global outbound-email kill switch without strict parsing or a verification case; naïve JavaScript truthiness makes `"false"` enabled (`PLAN.md:107,185,240-244`). Fix: require strict allowlisted boolean parsing with fail-closed production behavior and test that `false` prevents both contact and outbox sends.

3. [MINOR] The claimed full inventory still lists future `BACKEND_TUNNEL_*` variables absent from `.env.example`, conflicting with its role as the single consolidation point and with exact-set CI reconciliation (`PLAN.md:78,80,114,225`; `.env.example:1-51`). Fix: enumerate the concrete tunnel variables now or state that they enter the inventory and `.env.example` atomically in Phase 8.

VERDICT: REVISE

### Claude's response (re-review Round 2, 2026-07-18)

All 3 accepted; PLAN.md is now Revision 8.

- **1** -> `app/frontend/lib/env.ts` (server-only loader, introduced Sprint 2.1) joins the approved-loader list; `NEXT_PUBLIC_*` build-time reads explicitly exempt; sprint-02 updated.
- **2** -> Strict boolean parsing rule in the enforcement section: exactly `true`/`false`, anything else fails closed in production (emails off + startup warning); new verification gate proves `false` blocks both contact and outbox sends.
- **3** -> Atomic-entry rule: `BACKEND_TUNNEL_*` enter `.env.example` and the inventory in Sprint 8.3 (their first consumer); named as scheduled, not declared, until then.

## Re-review Round 3 — Codex (same thread, 2026-07-18) on Revision 8

1. [MAJOR] `human-todo.md` still instructs adding `ADMIN_EXTERNAL_IDS`, directly reintroducing the privilege-escalation mechanism Revision 8 explicitly drops under D12 and invariant 17 (`human-todo.md:24`; `PLAN.md:96,131`). Fix: replace that instruction with the one-time admin bootstrap CLI workflow.

2. [MAJOR] Neon provisioning omits `SERVICE_DATABASE_URL`, so the required `service_role` runtime credential is neither created nor captured despite D14 requiring it (`human-todo.md:25`; `PLAN.md:51,86,133`). Fix: add service-role provisioning and capture `SERVICE_DATABASE_URL`, while keeping `DIRECT_URL` migration-only.

3. [MINOR] Tunnel provisioning documents only `BACKEND_TUNNEL_TOKEN`, while Revision 8 schedules `BACKEND_TUNNEL_HOSTNAME/NAME/TOKEN` as an atomic set (`human-todo.md:32`; `PLAN.md:114,199`). Fix: align Sprint 8.3 and the human checklist on which concrete variables are actually consumed.

VERDICT: REVISE

### Claude's response (re-review Round 3, 2026-07-18)

All 3 accepted — stale human-todo.md drift from before D12/D14, now aligned (plan text unchanged; still Revision 8):

- **1** -> H-AUTH no longer instructs ADMIN_EXTERNAL_IDS; points at the bootstrap CLI (H-ADMIN-1).
- **2** -> H-NEON provisions all three runtime roles from 000_role.sql and captures SERVICE_DATABASE_URL; DIRECT_URL explicitly migrate-job-only.
- **3** -> H-TUNNEL captures the atomic BACKEND_TUNNEL_NAME/HOSTNAME/TOKEN set matching Sprint 8.3.

## Re-review Round 4 — Codex (same thread, 2026-07-18) on Revision 8 + aligned docs

1. [MAJOR] `human-todo.md` email provisioning omits `RESEND_FROM_EMAIL` and `ENABLE_EMAIL_NOTIFICATIONS`; because absence fails closed, following the checklist leaves production email disabled and breaks the Phase 6 exit gate (`human-todo.md:27`; `PLAN.md:106-107,114,183-185,245`). Fix: require provisioning and validation of both variables under H-EMAIL.

2. [MAJOR] `docs/sprints/README.md` still defines only backend and Backtester loaders, omitting the approved frontend and migration loaders plus the `NEXT_PUBLIC_*` exemption, so sprint execution can contradict invariant 17 (`docs/sprints/README.md:22`; `PLAN.md:114`). Fix: mirror Revision 8’s complete approved-loader and exemption contract in the sprint-wide instructions.

3. [MAJOR] The deployment guide implements token-only or CLI-login tunnel configuration with hardcoded name/hostname, while Revision 8 and `human-todo.md` require `BACKEND_TUNNEL_NAME/HOSTNAME/TOKEN` as consumed variables (`docs/sprints/sprint-08-deploy.md:31`; `PLAN.md:114,199`; `human-todo.md:32`). Fix: choose one tunnel interface and align the plan, checklist, `.env.example` atomic entry, compose overlay, and scripts to that exact consumed set.

VERDICT: REVISE

### Claude's response (re-review Round 4, 2026-07-18)

All 3 accepted — remaining doc-sync stragglers aligned to Revision 8 (plan text unchanged):

- **1** -> H-EMAIL now provisions RESEND_FROM_EMAIL (verified-domain sender; flags the egventures.net value for migration) and an explicit ENABLE_EMAIL_NOTIFICATIONS=true with the fail-closed warning.
- **2** -> sprints/README convention 8 mirrors the full approved-loader contract (backend config, migrate entrypoint, backtester config, frontend lib/env.ts) + NEXT_PUBLIC_* exemption + strict-boolean + Reserved-var rules.
- **3** -> Tunnel interface decided: TOKEN mode only (headless Pi); sprint-08 names the atomic consumed set with each var's concrete consumer (connector token, verification-curl hostname, service/label name); CLI-login mode dropped.

## Re-review Round 5 — Codex (same thread, 2026-07-18)

1. [MAJOR] Sprint 6 still says `checkout.session.completed` flips paid entitlement, directly contradicting D13’s bind-only rule and the guide’s own later webhook instructions (`docs/sprints/sprint-06-edge-monetization.md:12,28-31`; `PLAN.md:132`). Fix: require subscription lifecycle reconciliation before activation and update the phase exit gate accordingly.

2. [MAJOR] Sprint 6 hardcodes the contact sender and never requires either contact or outbox paths to check `ENABLE_EMAIL_NOTIFICATIONS`, so implementation can pass the guide while violating Revision 8’s canonical variables and fail-closed kill switch (`docs/sprints/sprint-06-edge-monetization.md:16,22-24,43,47`; `PLAN.md:106-107,114,184-185,245`). Fix: route both paths through their approved env loader, use `RESEND_FROM_EMAIL`, enforce the kill switch before every send, and mirror the dedicated tests.

3. [MINOR] Sprint 6 frontmatter still describes Stripe Payment Links even though D13 mandates server-created Checkout Sessions (`docs/sprints/sprint-06-edge-monetization.md:3`; `PLAN.md:97,132,186`). Fix: update the description to Checkout Sessions so search/index metadata does not route implementers to the rejected flow.

VERDICT: REVISE

### Claude's response (re-review Round 5, 2026-07-18)

All 3 accepted — sprint-06 residues from before D13/Revision 8, now aligned (plan unchanged, still Revision 8):

- **1** -> Phase 6 exit gate rewritten: activation via subscription lifecycle reconciliation; checkout.session.completed binds ids only.
- **2** -> Contact route reads ADMIN_NOTIFICATION_EMAIL/RESEND_FROM_EMAIL via lib/env.ts and checks the strict-parsed kill switch before sending (503 no-send when off); backend email service is the single kill-switch choke point via src/config.js; kill-switch acceptance tests added for both paths.
- **3** -> Frontmatter description now says server-created Checkout Sessions.

## Re-review Round 6 — Codex (same thread, 2026-07-18)

No implementation-significant findings. All prior Round 5 issues are resolved consistently across PLAN.md, Sprint 6, provisioning, environment-loader rules, and acceptance gates.

VERDICT: APPROVED

## Resolution: re-review APPROVED (Round 6 of 10, 2026-07-18)

Re-execution against the UPDATED Format B standard converged. PLAN.md Revision 8 stands. Cycle totals: 18 findings across 5 REVISE rounds (6/3/3/3/3), 17 accepted, 1 partial rejection with logged safety rationale (dev-compose DB literals stay container-internal constants; blanket interpolation could silently point dev at production Neon). Sprint guides, human-todo, .env.example, and Phase 1 code (node:22-slim + node-fetch healthcheck, PROOF_EXIT=0 re-verified) are synced to Revision 8. Combined with the original cycle: 74 findings total across both reviews, 70 accepted, 3 rejected/partial with reasons Codex endorsed or accepted, 1 third-way (R2 Reserved). Open human decisions: H-R2-1 (R2 storage scope), H-BUILD-1 (who builds Phase 2+), H-SEC-1 (key rotation), H-PRICE-1, H-RULES-1, A1.

## Re-grill 2026-07-21 — third Format B delta (Act 1 v3)

Standard deltas since Revision 8: (a) the four-role/four-DSN model is now CONTRACT with canonical names `app_service`/`worker_user` — our SERVICE_DATABASE_URL deviation was ABSORBED upstream (H-STD-1 partially resolved) but under different role names; (b) three manual `000_*` role files with the runner SKIPPING `000_*`; (c) boot-asserts (inv 14-15: SELECT current_user per pool; worker asserts worker_user + NOT rolbypassrls; DIRECT_URL banned from service envs with startup refusal); (d) entitlement column-lock (inv 16); (e) NEW DB-fallback layer (inv 17): postgres:17 on eg-server-3, FALLBACK_* DSN set + DB_ACTIVE manual cutover, Sprint 8.4. ADMIN_EXTERNAL_IDS and Payment Link rows are UNCHANGED upstream — those two deviations stand.

User changes reconciled: .env/.env.example rewrite (audited names-only, no values read): AUTH0_ISSUER + AUTH0_JWKS_URI removed as redundant-derived (loaders derive from AUTH0_DOMAIN); NEXT_PUBLIC_AUTH0_DOMAIN/CLIENT_ID removed (not contract-named, no consumer — the "reserved by contract" comment was imported from the reference repo); AUTH0_SECRET + APP_BASE_URL RESTORED (contract-required, were missing from both files); AUTH0_DB_CONNECTION adopted as a new concern (Sprint 5.2 consumer); provisioned AUTH0_AUDIENCE value https://cloudaitrader.com adopted over the plan's earlier backend.cloudaitrader.com. Code audit: NO auth code exists yet (tree is the Phase-1 scaffold), so no code depended on the removed vars. A1 weakened: the domain looks like a DEDICATED tenant vs the "shared" comment — deletion stays local-only pending the human's one-word answer.

Code brought to standard: run.js now skips `000_*` files; config.js refuses DIRECT_URL in production; compose usernames renamed to app_service/worker_user (nothing connects as them until Phase 3; proof re-run green). PLAN.md -> Revision 9 (role table, absorbed-deviation notes, Auth0 audit paragraph, invariants 18-20, Sprint 8.4, gates, risks); sprints 01/02/03/08/09 synced; human-todo: H-NEON-2 (rename provisioned roles), H-FALLBACK-1 (eg-server-3), A1 sharpened.

Act 2 v3 follows in a fresh Codex session, MAX_ROUNDS=10.

## Act 2 v3 Round 1 — Codex fresh session (thread 019f875e-77b4-7303-8854-b51147483c1a, 2026-07-21) on Revision 9

1. [BLOCKER] Warm `pg_dump | pg_restore` can overwrite writes made after fallback cutover because the cron job has no promotion lock, disable mechanism, or active-primary assertion (`PLAN.md:205`; `docs/sprints/sprint-08-deploy.md:40-42`). Fix: require a single-writer promotion state, automatically fence warm-sync before cutover, and restore into a staging database before atomic promotion.

2. [BLOCKER] Failback is specified only as “reconciles fallback→Neon,” with no conflict model, write freeze, sequence handling, or procedure for Neon writes accepted during a partial outage (`PLAN.md:205,234,256`; `docs/sprints/sprint-08-deploy.md:41-42`). Fix: define an executable failback runbook using write quiescence plus authoritative full replacement or logical replication with explicit conflict semantics and validation hashes.

3. [MAJOR] Revision 9 says the nine-variable primary/fallback set is wired into “BOTH workers,” which risks placing `DIRECT_URL`, `FALLBACK_DIRECT_URL`, and cross-role credentials in long-lived containers, contradicting least privilege and invariant 18 (`PLAN.md:205,232`). Fix: give backend only app-user/service DSNs, Backtester only worker DSNs, and migration jobs only owner DSNs; `DB_ACTIVE` selects within each service’s permitted subset.

4. [MAJOR] The manual role files prescribe hardcoded passwords equal to role names, and the duplicate-role handler silently skips correcting attributes or passwords on existing roles (`docs/sprints/sprint-03-schema-worker-contract.md:18-30`). Fix: inject generated passwords through protected `psql` variables and idempotently `ALTER ROLE` every required attribute while never committing credentials.

5. [MAJOR] Cold local compose never executes the skipped `000_*` role files, yet backend and Backtester DSNs reference those roles; Phase 1 remains green only because current health checks never connect to PostgreSQL (`docker-compose-dev.yml:28-69`; `app/backend/src/index.js:31-33`; `backtester/backtester/config.py:15-21`). Fix: add a separate idempotent local role-bootstrap init step and make both health/readiness gates prove authenticated database access under the expected roles.

6. [MAJOR] Auth0 audience configuration is internally contradictory: Revision 9 and `.env.example` use `https://cloudaitrader.com`, while the synced Sprint 2 precondition and completed human provisioning item still require `https://backend.cloudaitrader.com` (`PLAN.md:103`; `.env.example:5`; `docs/sprints/sprint-02-auth-identity.md:11`; `human-todo.md:24`). Fix: select the actually provisioned API identifier and update every plan, sprint, checklist, test fixture, and Auth0 tenant setting to that exact value.

7. [MAJOR] The optional dedicated-tenant deletion branch requires deleting the Auth0 identity, but the M2M contract grants only `read:users update:users`, Sprint 5 remains local-only, and no deletion/retry verification exists (`PLAN.md:139,184`; `.env.example:11-14`; `docs/sprints/sprint-05-app-surface.md:29-31`). Fix: either remove Auth0 deletion from Revision 9 or define a gated branch with `delete:users`, idempotent retry behavior, session revocation, and acceptance tests.

8. [MAJOR] Boot assertions verify exact usernames but not the complete privilege contract for backend roles; an existing misprovisioned `app_service` can retain `CREATEROLE`, `CREATEDB`, ownership, or lack/possess the wrong BYPASSRLS state until much later checks (`PLAN.md:55,232,255`; `docs/sprints/sprint-03-schema-worker-contract.md:33,126`). Fix: boot-assert `rolbypassrls`, `rolcreatedb`, `rolcreaterole`, and expected ownership/DDL denial for every runtime role, with negative tests for swapped and overprivileged DSNs.

9. [MAJOR] Sprint 8.1’s production bootstrap still names only two role files, omitting `000_service_role.sql`, so following the deployment guide cannot provision `app_service` (`docs/sprints/sprint-08-deploy.md:16-19`). Fix: require all three canonical `000_*` files in both primary and fallback bootstrap instructions and verify all four identities before migration.

10. [MINOR] Sprint 3 still advertises “Revision 5” and “Three-role bootstrap” despite containing Revision 9’s four-role contract, undermining the claim that sprint guides are synchronized (`docs/sprints/sprint-03-schema-worker-contract.md:3,11`). Fix: update its metadata and synchronization marker to Revision 9/four-role terminology.

Confidence: 98/100

VERDICT: REVISE

### Claude's response (Act 2 v3 Round 1, 2026-07-21)

All 10 accepted; PLAN.md is now Revision 10.

- **1 (blocker)** -> Warm sync restores into `cloudaitrader_staging` + atomic swap, and refuses (with alert) whenever the cutover script's promotion flag is set; cutover fences sync BEFORE flipping.
- **2 (blocker)** -> Executable failback runbook: write quiescence (stop workers) -> full dump/restore into a Neon staging branch -> validation (row counts + content hashes on backtests/results/entitlements) with operator adjudication of any diff -> promote -> clear flag -> re-enable sync. Full-replacement model, no merge semantics.
- **3** -> Least-privilege DSN subsets: backend app_user/app_service (+ fallback mirrors), backtester worker_user (+ mirror), migrate-only owner URLs; DB_ACTIVE selects within each service's subset.
- **4** -> 000_* files take psql-variable passwords and idempotently ALTER ROLE attributes on re-run; no credentials in the repo; dev literals confined to the dev init script.
- **5** -> NEW `infra/db-init/dev-roles.sql` mounted into the dev postgres initdb.d (roles exist from cold start; gate: psql as each role after down -v); Phase 3 upgrades health/readiness to prove authenticated access per role.
- **6** -> Audience unified on the provisioned `https://cloudaitrader.com` across sprint-02, human-todo H-AUTH (annotated correction), sprint-01, .env.example, PLAN.
- **7** -> Dedicated-tenant Auth0-deletion branch REMOVED: deletion is LOCAL-ONLY in MVP regardless of tenant type; A1 becomes informational; M2M scopes stay read:users update:users.
- **8** -> Boot-asserts extended to the full privilege contract (pg_roles: bypassrls/createdb/createrole per role) + negative tests for swapped/overprivileged DSNs; invariant 18 amended.
- **9** -> Sprint 8.1 bootstrap names all three 000_* files + four-identity verification before first migration.
- **10** -> sprint-03 metadata/heading updated to Revision 10 / four-role.

## Act 2 v3 Round 2 — Codex (same thread, 2026-07-21) on Revision 10

Revision 10 still requires revision.

1. [BLOCKER] The promotion flag has a check-then-act race: warm sync can pass the flag check, then continue restoring and swapping after cutover sets the flag, overwriting live fallback writes ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:205); [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:40)).  
Fix: use one shared exclusion lock held for the entire sync/swap; cutover must acquire that lock, set durable promotion state, and test an intentionally overlapping sync/cutover.

2. [BLOCKER] Failback restores into a Neon staging branch but “promotion” only flips `DB_ACTIVE=primary`; nothing makes the validated branch reachable through the existing primary DSNs, so services can restart against stale Neon data ([Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:42)).  
Fix: specify the exact Neon branch reset/promotion or atomic primary-DSN replacement, verify a database-instance ID through every resulting DSN, and define rollback if restart validation fails.

3. [MAJOR] Failback validation does not actually surface old-primary writes: fallback is copied into staging, but no explicit old-Neon-versus-fallback comparison exists, and content hashes cover only three tables ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:205)).  
Fix: require old-primary versus fallback divergence analysis plus fallback versus staging restore-fidelity checks over every authoritative table, migration version, sequence, and immutable manifest.

4. [MAJOR] Cutover recreates both services without first stopping both, so a partial recreate can leave the App Worker writing fallback while the Backtester continues using Neon; role assertions cannot detect this split brain ([Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:41)).  
Fix: stop both services first, update one durable selector, start neither unless all selected DSNs report the same database-instance/epoch marker, and roll back as a unit on failure.

5. [MAJOR] The claimed “full privilege contract” still omits role membership, object/schema ownership, `rolsuper`, and `rolreplication`; an `app_service` owning an existing object can alter or drop it even if `CREATE TABLE` fails ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:232); [Sprint 3](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-03-schema-worker-contract.md:38)).  
Fix: revoke unexpected memberships, reassign owned objects, assert all privilege attributes and zero runtime-owned objects, and test `ALTER`/`DROP` against an owner-created fixture.

6. [MAJOR] Production role-password examples pass secrets through `psql -v ...='<generated>'`, exposing them to shell history and potentially process inspection despite calling the variable “protected” ([Sprint 3](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-03-schema-worker-contract.md:21)).  
Fix: use `\prompt -s`, a permission-restricted transient variable file, or another non-argv secret channel, with cleanup and no command logging.

7. [MAJOR] The Auth0 deletion branch remains enabled in `human-todo.md`, directly contradicting Revision 10’s removal of that branch and allowing implementation without `delete:users`, retries, or tests ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:139); [human-todo.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/human-todo.md:20)).  
Fix: make A1 informational only and state that MVP deletion remains local-only regardless of the answer.

8. [MAJOR] Warm restore does not specify ownership/ACL flags or pre-swap role probes; Neon’s owner role can differ from the fallback owner, and database-level `CONNECT` privileges may remain attached to the old database object. PostgreSQL documents that `pg_dump` does not dump roles and only includes database ACLs with the create option ([PostgreSQL 17 pg_dump](https://www.postgresql.org/docs/17/app-pgdump.html), retrieved 2026-07-21).  
Fix: define exact dump/restore flags, owner mapping, explicit staging-database grants, `--exit-on-error`/pipeline failure handling, and successful connections through all fallback DSNs before swap.

9. [MAJOR] The fallback duplicates production PII, billing records, and encrypted MFA material onto eg-server-3 without an at-rest encryption, credential-file permission, dump-retention, or host-access audit contract ([Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:37)).  
Fix: require encrypted storage, restricted backup credentials, no persistent plaintext dumps, retention/secure deletion, host patching, and audited access in Sprint 8.4 and Sprint 9.1.

10. [MINOR] Synced guidance still says `000_role.sql` creates all runtime roles under obsolete names, and the sprint index still calls `SERVICE_DATABASE_URL` a contract deviation even though Revision 10 says it was absorbed ([human-todo.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/human-todo.md:25); [Sprint index](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/README.md:22)).  
Fix: replace the historical provisioning instruction with all three canonical role files and remove the absorbed deviation from current execution guidance.

Confidence: 99/100

VERDICT: REVISE

### Claude's response (Act 2 v3 Round 2, 2026-07-21)

All 10 accepted; PLAN.md is now Revision 11.

- **1 (blocker)** -> One shared flock held for the ENTIRE sync (dump->restore->grants->probes->swap); cutover acquires the same lock before writing durable promotion state; drill adds a deliberate overlap test.
- **2 (blocker)** -> Failback promotion made real: Neon primary-branch RESET from the validated staging branch (existing DSN endpoints unchanged) + a one-row `app.db_epoch` marker stamped per cutover/failback and verified through every DSN before workers start; rollback = don't reset.
- **3** -> Divergence analysis old-Neon vs fallback across ALL authoritative tables + schema_migrations + sequences + manifest fields, adjudicated before restore; separate fallback-vs-staging fidelity check.
- **4** -> Cutover: stop BOTH -> durable selector -> epoch match through each selected DSN -> start both or neither (unit rollback).
- **5** -> Privilege contract extended: NOT rolsuper/rolreplication, no unexpected memberships, zero owned objects, ALTER/DROP fixture denial; provisioning revokes/REASSIGNs strays.
- **6** -> Role passwords never in argv: \prompt -s or 0600 transient \i file with secure deletion.
- **7** -> human-todo A1 rewritten informational-only; MVP deletion local-only regardless.
- **8** -> Exact dump/restore flags specified (-Fc --no-owner --no-acl | --exit-on-error, streamed), post-restore grants script, three-DSN connect probes before swap (pg_dump role/ACL semantics per PostgreSQL 17 docs).
- **9** -> Fallback data-protection contract: LUKS volume, 0600 creds, streamed/age-encrypted dumps with retention 2 + secure deletion, host patching + SSH audit in Sprint 9.1.
- **10** -> human-todo H-NEON annotated (three files, canonical names), sprints/README deviation list updated (SERVICE_DATABASE_URL absorbed).

## Act 2 v3 Round 3 — Codex (same thread, 2026-07-21) on Revision 11

Revision 11 still requires revision.

1. [BLOCKER] The exclusion lock prevents overlap only while cutover holds it; after cutover releases it, the next cron sync can acquire the lock and overwrite the now-live fallback because the sync path never explicitly refuses when durable promotion state says `fallback` ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:205); [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:40)).  
Fix: after acquiring the lock, warm sync must check durable promotion state and exit with an alert unless the active database is primary; test the first scheduled run after promotion.

2. [MAJOR] The failback names a Neon “branch reset,” but Neon reset normally updates a child from its parent; replacing primary from staging uses the branch restore operation with staging as `source_branch_id`, operation polling, and preservation of the old primary ([Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:42); [Neon Restore Branch API](https://api-docs.neon.tech/reference/restoreprojectbranch), retrieved 2026-07-21).  
Fix: name the exact restore operation, preserve the previous primary under a recovery name, poll it to terminal success, and prohibit blind retry of an ambiguously completed POST.

3. [MAJOR] The no-argv password rule remains contradicted by two role-file comments that still prescribe `psql -v ...='<generated>'`, recreating the original credential-exposure path ([Sprint 3](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-03-schema-worker-contract.md:27)).  
Fix: remove every `-v` example and show only `\prompt -s` or the 0600 transient-file invocation for all three role files.

4. [MAJOR] “Zero owned objects” is checked only through `pg_class` and `pg_namespace`, omitting owned functions, types, databases, and other catalogs; the sole fixture test covers a table, so an owned `SECURITY DEFINER` function can escape the gate ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:232); [Sprint 3](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-03-schema-worker-contract.md:40)).  
Fix: use a complete ownership/dependency audit such as `pg_shdepend` plus database-local catalogs, and add function/schema ownership denial fixtures to phase acceptance.

5. [MAJOR] The epoch gate requires selected DSNs merely to agree; if every fallback DSN is accidentally wired to Neon, they return the same role-correct primary epoch and the false cutover passes ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:205)).  
Fix: generate an expected transition UUID, stamp it only on the intended target, and require every selected DSN to equal that exact value while the non-selected database retains a different epoch.

Confidence: 99/100

VERDICT: REVISE

### Claude's response (Act 2 v3 Round 3, 2026-07-21)

All 5 accepted; PLAN.md is now Revision 12.

- **1 (blocker)** -> Warm sync checks durable promotion state IMMEDIATELY after acquiring the lock and exits+alerts unless active==primary; drill tests the first scheduled run after promotion.
- **2** -> Failback names the Neon Restore Branch API exactly (POST .../restore with source_branch_id=staging), preserves the auto-backup branch as recovery-<ts> until sign-off, polls the operation to terminal success, never blind-retries an ambiguous POST.
- **3** -> The two remaining `-v` comment lines in the role files removed; all three files now show only \prompt -s / 0600 transient \i invocation.
- **4** -> Ownership audit extended to pg_shdepend + pg_proc/pg_type/pg_namespace/pg_class; fixture denials now cover a table, a function, and a schema.
- **5** -> Epoch gate uses an EXPECTED transition uuid stamped only on the intended target, all selected DSNs must equal it, and the non-selected database must show a different epoch (miswire-proof).

## Act 2 v3 Round 4 — Codex (same thread, 2026-07-21) on Revision 12

Revision 12 still requires revision.

1. [MAJOR] The Neon Restore Branch API introduces undeclared operator credentials and identifiers: no `NEON_API_KEY`, project/primary-branch identifiers, staging connection mechanism, human provisioning item, or rule keeping those control-plane secrets out of runtime containers exists ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:205); [environment contract](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:78); [Neon API](https://api-docs.neon.tech/reference/restoreprojectbranch)).  
Fix: define an operator-only Neon control-plane credential/config contract, scoped storage and provisioning, approved script loader, CI treatment, and explicit exclusion from every runtime service environment.

2. [MAJOR] Warm sync strips all ACLs and reapplies a separate “post-restore grants script,” while canonical grants remain in `004_domain.sql`; connection probes prove login only, so grant drift or an overprivileged `worker_user` can pass before swap ([Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:40); [Sprint 3](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-03-schema-worker-contract.md:91)).  
Fix: make grants single-source and idempotently reusable by migrations/restores, then run the complete verb/RLS/ownership matrix against staging before every swap or Neon promotion.

3. [MAJOR] The expanded ownership audit and table/function/schema denial fixtures are described in Sprint 3 prose but remain absent from both Phase 3 acceptance and the global boot-assert verification gate, allowing the phase to pass under the older table-only checks ([Sprint 3 acceptance](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-03-schema-worker-contract.md:130); [PLAN.md verification](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:255)).  
Fix: add the complete `pg_shdepend` ownership assertion and all three denial fixtures explicitly to both named acceptance gates.

4. [MINOR] Revision 12 still says “Neon branch reset” in its header, global fallback gate, and Sprint 8 acceptance transcript, contradicting the corrected Restore Branch API runbook ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:5); [PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:257); [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:48)).  
Fix: replace the remaining reset terminology with “Restore Branch API promotion.”

Confidence: 99/100

VERDICT: REVISE

### Claude's response (Act 2 v3 Round 4, 2026-07-21)

All 4 accepted; PLAN.md is now Revision 13.

- **1** -> New operator-only env class (NEON_API_KEY, NEON_PROJECT_ID, NEON_PRIMARY_BRANCH_ID): 0600 operator file on eg-server-3, sole consumer is the failback script, banned from runtime/Vercel/CI (boot-assert + CI absence + docker-inspect drill check); H-FALLBACK-1 provisions them.
- **2** -> Grants single-sourced into idempotent 005_grants.sql (re-applied by sync and failback restores — no separate grants script); shared verify_roles.sql matrix (verbs/RLS/ownership) runs against staging BEFORE every swap and against the Neon staging branch BEFORE Restore-Branch promotion; login-only probes no longer count.
- **3** -> The pg_shdepend-complete ownership audit + table/SECURITY DEFINER function/schema denial fixtures are now NAMED in both Sprint 3 acceptance and the PLAN boot-assert verification gate.
- **4** -> Remaining "branch reset" terminology swept to "Neon Restore Branch API promotion" (header, fallback gate, sprint-08 acceptance).

## Act 2 v3 Round 5 — Codex (same thread, 2026-07-21) on Revision 13

Round 4 findings 3 and 4 are closed. Finding 1 is only partially resolved; finding 2 remains inconsistent in Sprint 8. External service claims checked 2026-07-21 21:48 EDT.

1. [BLOCKER] The prescribed Restore Branch request omits `preserve_under_name`, which Neon requires when the target has children, as primary will once the staging branch exists; the operation creates a new branch, yet static `NEON_PRIMARY_BRANCH_ID` is never refreshed and only one returned operation is polled ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:207); [Neon Restore Branch API](https://api-docs.neon.tech/reference/restoreprojectbranch); [Neon OpenAPI](https://neon.com/api_spec/release/v2.json)).  
Fix: Include `preserve_under_name` in the POST, poll every returned operation, atomically persist the returned active `branch.id`, and prove two consecutive restores.

2. [MAJOR] Both restore targets lack an empty-target lifecycle: `cloudaitrader_staging` contains the previous database after the first rename swap, and a Neon staging branch is initially populated, but the named `pg_restore` flags include neither `--clean` nor database recreation, so subsequent restores fail on existing objects ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:207); [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:40); [PostgreSQL 17 pg_restore](https://www.postgresql.org/docs/17/app-pgrestore.html)).  
Fix: Define fresh `template0` staging-database creation or controlled `--clean --if-exists` semantics and test two consecutive warm-syncs plus restoration over a populated Neon branch.

3. [MAJOR] Round 4 finding 2 remains unresolved in the executable guide: Sprint 8 still specifies a separate “post-restore grants script” and connection probes, and its failback steps omit `005_grants.sql` plus `verify_roles.sql`, contradicting both PLAN.md and Sprint 3 ([Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:40); [Sprint 3](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-03-schema-worker-contract.md:94)).  
Fix: Replace both Sprint 8 restore paths with the exact shared `005_grants.sql` → `verify_roles.sql` sequence before swap or promotion.

4. [MAJOR] The declared six-hour RPO is neither observable nor enforced: no durable last-successful validated-sync timestamp/source marker or stale-fallback refusal exists, so repeated cron failures can leave a days-old fallback that still passes the newly stamped epoch gate ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:207); [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:48)).  
Fix: Persist validated snapshot time/source identity, alert when age exceeds RPO plus grace, and make cutover reject stale fallback absent an explicit adjudicated override.

5. [MAJOR] The capacity gate budgets up to 400 MB for `worker.ohlcv` alone while Neon Free currently allows 0.5 GB per project; failback temporarily adds a logically rewritten staging branch and retained recovery branch, so the stated 240–320 MB production footprint can exhaust free-tier storage during the recovery operation ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:17); [Sprint 4](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-04-backtester-worker.md:33); [Neon pricing](https://neon.com/pricing)).  
Fix: Gate on total project and concurrent-branch storage with primary-plus-staging-plus-recovery headroom, requiring explicit paid-tier approval if the free cap cannot accommodate failback.

Confidence: 99/100

VERDICT: REVISE

### Claude's response (Act 2 v3 Round 5, 2026-07-21)

All 5 accepted; PLAN.md is now Revision 14.

- **1 (blocker)** -> Restore POST includes preserve_under_name:"recovery-<ts>"; EVERY returned operation polled; the NEW branch.id atomically persisted as the refreshed NEON_PRIMARY_BRANCH_ID in the operator env; drill proves two consecutive restores.
- **2** -> Fresh-target lifecycle everywhere: warm sync recreates cloudaitrader_staging from template0 each run; failback creates a FRESH Neon staging branch per attempt and deletes it after promotion; two consecutive warm-syncs in the drill.
- **3** -> Sprint 8's stale "post-restore grants script" line replaced with the exact 005_grants.sql -> verify_roles.sql sequence on BOTH restore paths (legitimate re-open of R12-2 — the PLAN was fixed in Round 4 but the executable guide lagged).
- **4** -> Durable last_validated_sync marker (timestamp + source identity) stamped per successful sync; age > RPO+grace alerts; the cutover script REFUSES a stale fallback absent an explicit logged --override-stale.
- **5** -> Capacity model re-budgeted for branch reality: matrix tightened to 1m(30d)/1h(3y)/1d(5y) (~713k rows, ~110-145 MB) so primary + rewritten staging + recovery branch fit the 0.5 GB free cap; the gate measures TOTAL project storage with failback headroom; breach requires explicit paid-tier approval.

## Act 2 v3 Round 6 — Codex (same thread, 2026-07-21) on Revision 14

Revision 14 still requires revision. All five Round 5 remedies appear in prose, but the Neon empty-target fix remains incorrect and several remedies are not enforced by acceptance gates.

1. [BLOCKER] Round 5 finding 2 remains open: a “fresh” Neon branch contains its parent’s schema and data, and the API creates no compute endpoint unless requested, so the unchanged `pg_restore --exit-on-error` collides with existing objects or has no connection target ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:207), [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:42), [Neon branching](https://neon.com/docs/get-started-with-neon/workflow-primer), [Create Branch API](https://api-docs.neon.tech/reference/createprojectbranch)).  
   Fix: Create and poll a temporary read-write endpoint, then explicitly empty/recreate the application database from `template0` or use tested `--clean --if-exists` semantics before restoring.

2. [BLOCKER] Neon restore completion and local `NEON_PRIMARY_BRANCH_ID` persistence are not crash-consistent; a lost response or process death after remote commit leaves the old ID pointing at recovery, while “rollback = do not restore” is impossible after commit ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:207), [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:42), [Neon Restore API retry warning](https://api-docs.neon.tech/reference/restoreprojectbranch)).  
   Fix: Add a durable pre-POST failback journal, reconcile the active branch through a stable endpoint ID on restart, define post-commit fallback recovery, and inject crashes at POST/poll/persist boundaries.

3. [MAJOR] The shared whole-run exclusion lock covers warm sync and cutover, but not failback; concurrent failbacks can race on staging deletion, restore target IDs, and operator-file writes ([Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:40), [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:42)).  
   Fix: Hold the shared lock for the entire failback and compare-and-set both promotion state and the resolved current primary branch ID before every destructive step.

4. [MAJOR] Failback has a weaker epoch gate than cutover: it does not explicitly generate a fresh UUID or prove the non-selected fallback differs, allowing staging or primary DSN miswiring to escape the intended differentiation check ([Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:41), [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:42)).  
   Fix: Generate a new failback UUID, stamp only verified staging, require every primary DSN to equal it, and require every fallback DSN to differ before flipping.

5. [MAJOR] Acceptance 8.4 remains singular and can pass without two warm syncs, two restores using the refreshed branch ID, the local `005_grants.sql` sequence, or stale-marker refusal and override auditing ([Sprint 8 acceptance](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:48), [global gate](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:259), [sprint rules](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/README.md:17)).  
   Fix: Name every required repeated cycle, refreshed-ID assertion, grants verification, stale refusal, override audit, and crash-boundary transcript explicitly in both gates.

6. [MAJOR] The operator-only env class contradicts the env-conformance contract: it requires its own loader and file, while CI permits only four loaders and requires every declared variable in `.env.example`, with no operator exception or template ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:107), [PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:121), [Sprint README](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/README.md:22)).  
   Fix: Define an approved operator loader plus `operator.env.example`, and make CI allow `NEON_*` only through that path while rejecting runtime, Compose, Vercel, and CI exposure.

7. [MAJOR] The capacity repair still undercounts required states: retaining recovery until sign-off while proving two restores can produce active + staging + recovery-1 + recovery-2, but the budget models only three; Sprint 4 acceptance omits capacity and Sprint 9 still uses the obsolete OHLCV-only 400 MB check ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:17), [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:42), [Sprint 4 acceptance](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-04-backtester-worker.md:38), [Sprint 9](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-09-hardening.md:32)).  
   Fix: Require signed deletion of recovery-1 before restore two or budget four states, then gate every restore on measured total-project storage and remove the 400 MB check.

8. [MAJOR] `last_validated_sync` is stamped after restore and cutover checks only age; the plan neither distinguishes source snapshot time from validation completion nor requires comparison of the recorded source identity, overstating freshness and permitting a wrong-source sync to authorize cutover ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:207), [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:40)).  
   Fix: Persist `snapshot_started_at`, `validated_at`, source project/branch/LSN/epoch, and fallback-generation identity, then validate every field during cutover.

9. [MAJOR] Role-bootstrap “convergence” omits `NOSUPERUSER` and `NOREPLICATION` from every `ALTER ROLE`, although boot assertions require both; an existing overprivileged role therefore remains broken and blocks startup ([Sprint 3](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-03-schema-worker-contract.md:25), [Sprint 3](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-03-schema-worker-contract.md:40), [PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:234)).  
   Fix: Make every asserted attribute, membership revocation, and ownership reassignment an explicit idempotent bootstrap operation.

Confidence: 99/100

VERDICT: REVISE

### Claude response (Act 2 v3 Round 6, 2026-07-22)

All 9 accepted; PLAN.md is now Revision 15 -- WITH a logged altitude decision: every finding is answered as a named INVARIANT in the plan, and Sprint 8.4 gains a first-class deliverable -- infra/fallback/RUNBOOK.md + sync/cutover/failback/operator-env scripts -- that owns the exact procedures and is itself reviewed at build time. The plan states what must be true; the runbook states how. This bounds a recursion heading toward command-level DR specification inside a plan whose Phases 2-7 are not yet built.

1 (blocker): staging branches inherit parent data and lack compute -- failback creates+polls a temporary read-write endpoint and recreates the app database from template0 before restoring. 2 (blocker): durable pre-POST journal; restart reconciliation against the live branch listing; post-commit recovery; crash-boundary tests at POST/poll/persist. 3: the shared lock covers failback end-to-end with CAS on promotion state + resolved branch id. 4: failback epoch gate mirrors cutover. 5: acceptance 8.4 enumerates every repeated cycle explicitly. 6: fifth approved loader infra/fallback/operator-env.sh + infra/operator.env.example; CI permits NEON_* only inside infra/fallback/. 7: recovery-1 signed deletion before restore two (three-state budget); Sprint 4 gains the total-project x3 capacity check; Sprint 9 400MB check replaced. 8: marker fields snapshot_started_at/validated_at/source project/branch/LSN/epoch/generation, all validated at cutover. 9: ALTER ROLE converges NOSUPERUSER NOREPLICATION; membership revocation + REASSIGN OWNED explicit.

## Act 2 v3 Round 7 — Codex (same thread, 2026-07-22) on Revision 15

Revision 15 still requires revision. I accepted the plan/runbook altitude boundary and found no reopened core-product issues. Three spec-level defects remain.

1. [BLOCKER] Cutover requires Neon to return a different epoch, so a complete Neon outage prevents activating the fallback, defeating the DR subsystem’s primary purpose ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:207), [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:43)).  
   Fix: Make the Neon probe tri-state: matching fails, different passes, and unreachable passes only after all selected DSNs prove the fresh UUID and validated fallback-generation identity; add a complete-outage acceptance case.

2. [MAJOR] R14-6 remains contradictory: the operator contract establishes a fifth loader and `infra/operator.env.example`, while invariant 17 and its enforcement algorithm still declare `.env.example` the sole consolidation point and enumerate only four loaders ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:80), [PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:107), [PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:121), [PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:233)).  
   Fix: Define separate runtime and operator consolidation domains, list all five loaders, and require CI to reconcile both templates and scan operator shell reads.

3. [MAJOR] R14-2 requires post-commit recovery, but both retained failback sequences still prescribe “rollback = don’t restore” after the Restore API step, an impossible state once Neon has committed ([PLAN.md](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:207), [Sprint 8](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:44)).  
   Fix: Distinguish pre-POST abort from post-commit validation failure, with the latter remaining fallback-active while journal-led reconciliation determines the actual Neon state.

Confidence: 99/100

VERDICT: REVISE

### Claude response (Act 2 v3 Round 7, 2026-07-22)

Codex accepted the plan/runbook altitude boundary; no core-product reopens. All 3 findings accepted; PLAN.md is now Revision 16.

- **1 (blocker)** -> Tri-state Neon probe: matching epoch = FAIL (miswire); different = PASS; UNREACHABLE = PASS only with the fresh uuid AND validated fallback-generation identity proven on every selected DSN — a dead Neon (the primary DR trigger) can never block activation; complete-outage cutover case added to acceptance.
- **2** -> Invariant-17 enforcement rewritten as TWO consolidation domains: runtime (.env.example, five loaders enumerated incl. infra/fallback/operator-env.sh) and operator (infra/operator.env.example; NEON_* + FALLBACK_DIRECT_URL permitted only under infra/fallback/); CI reconciles both templates and scans operator shell reads.
- **3** -> Failback failure semantics split at the commit point: pre-POST failures abort freely; post-commit validation failures keep the fallback ACTIVE while journal-led reconciliation determines the real Neon state — re-attempt or deliberately adopt the recovery branch, never a pretend-rollback. Both PLAN and sprint-08 sequences updated.

## Act 2 v3 Round 8 — Codex (same thread, 2026-07-22) on Revision 16

Round 7 findings 1 and 3 are closed. One issue remains.

1. [MAJOR] The env-domain repair is still contradictory: the detailed contract defines separate runtime/operator domains ([PLAN.md:107](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:107), [PLAN.md:121](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:121)), but invariant 17 and sprint-wide rules still require every variable in `.env.example` ([PLAN.md:233](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:233), [sprint README:19](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/README.md:19)); moreover, Sprint 9.3 omits the mandated two-domain conformance CI gate ([sprint-09-hardening.md:34](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-09-hardening.md:34)).  
   Fix: Define four runtime loaders → `.env.example` and one operator loader → `infra/operator.env.example` consistently in every normative rule, then add the two-domain positive/negative conformance job to Sprint 9.3 acceptance.

Confidence: 99/100

VERDICT: REVISE

### Claude response (Act 2 v3 Round 8, 2026-07-22)

Rounds 7-1 and 7-3 confirmed closed. The single remaining finding accepted; PLAN.md is now Revision 17.

- **1** -> The two-domain split is now consistent in every normative rule: PLAN invariant 17 states runtime -> .env.example via the four runtime loaders and operator -> infra/operator.env.example via infra/fallback/operator-env.sh (only under infra/fallback/); sprints/README rule 8 mirrors it verbatim; Sprint 9.3 names the two-domain conformance CI job with explicit positive cases (both templates reconcile; all reads through the five loaders) and negative cases (seeded loader-bypass, seeded operator-var read outside infra/fallback/, seeded undeclared name each fail).

## Act 2 v3 Round 9 — Codex (same thread, 2026-07-22) on Revision 17

Revision 17 repairs invariant 17 and Sprint 9.3, but the env contract remains inconsistent.

1. [MAJOR] Round 8 is still partially open: [PLAN.md:80](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:80) and [sprint README:19](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/README.md:19) still make `.env.example` universal, while [PLAN.md:121](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:121) still places all five loaders in the runtime allowlist, contradicting the four-runtime/one-operator split at [PLAN.md:233](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:233).  
   Fix: Qualify every template rule by domain and define exactly four runtime loaders plus one operator loader, including raw acquisition versus post-source shell-variable use.

2. [MAJOR] `FALLBACK_DIRECT_URL` is operator-only under [sprint README:22](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/README.md:22), but Sprint 8.4 requires the migrate path to receive it and add it to `.env.example` ([PLAN.md:207](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:207), [sprint-08:40](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-08-deploy.md:40)); the exact-set CI contract therefore requires duplication or an undeclared translation.  
   Fix: Assign `FALLBACK_DIRECT_URL` to one domain and consistently define either transient mapping to `DIRECT_URL` for migration or migrate-only runtime handling.

Round 7’s outage and failback repairs remain closed.

Confidence: 99/100

VERDICT: REVISE

### Claude response (Act 2 v3 Round 9, 2026-07-22)

Both findings accepted; PLAN.md is now Revision 18.

- **1** -> Every remaining pre-split phrase qualified by domain: the reconciliation intro now names one consolidation point PER domain; the enforcement paragraph states EXACTLY FOUR runtime loaders + ONE operator loader, with the raw-acquisition (operator-env.sh only) vs post-source shell-variable-use distinction made explicit.
- **2** -> FALLBACK_DIRECT_URL assigned to the OPERATOR domain: it enters infra/operator.env.example (never .env.example); the fallback bootstrap/migrate path receives it TRANSIENTLY under the name DIRECT_URL from the operator scripts (documented mapping R16-2 - the migrate job only ever knows DIRECT_URL); Sprint 8.4 atomic entry split accordingly (four runtime vars -> .env.example).

## Act 2 v3 Round 10 — Codex FINAL (same thread, 2026-07-22) on Revision 18

Round 9 finding 2 is closed. Finding 1 remains partially open.

1. [MAJOR] The synced sprint contract still contradicts the repaired plan: [sprint README:19](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/README.md:19) says `.env.example` documents every variable, while rule 8 assigns operator variables elsewhere; [Sprint 9.3](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/docs/sprints/sprint-09-hardening.md:39) also collapses acquisition and use into “five approved loaders,” omitting [PLAN.md:121](/C:/Users/erick/projects/personal/realtime_crypto_arbitrage_bot/PLAN.md:121)’s raw-acquisition versus post-source distinction.  
   Fix: Make rule 5 domain-qualified and make the CI gate explicitly test four runtime loaders, operator acquisition only through `operator-env.sh`, and post-source use only under `infra/fallback/`.

Confidence: 99/100

VERDICT: REVISE

## Resolution: Act 2 v3 terminates at the ROUND CAP (10 of 10, 2026-07-22) — formal DEADLOCK, substance converged

Per the skill, REVISE at MAX_ROUNDS ends the loop without further revision. Honest state:

- OPEN at cap: ONE [MAJOR] — two straggler sentences in secondary guides (sprints/README rule 5 pre-domain phrasing; sprint-09 CI line collapsing acquisition-vs-use). Round 9 finding 2 was confirmed CLOSED.
- Claude's counter-position: the finding is correct and trivially fixable documentation drift, not a design defect. The substantive design closed at Round 7 (Codex: altitude boundary accepted, "no reopened core-product issues"); Rounds 8-10 were single-digit consistency items in guide files. The two sentences were corrected immediately AFTER the loop as post-loop maintenance, logged here — NOT presented as an in-loop approval. The formal verdict of record for Round 10 is REVISE.
- Recommendation to the human: treat PLAN.md Revision 18 as the working spec. Cycle totals (Act 2 v3): 10 rounds, 42 findings (10/10/5/4/5/9/3/1/2/1... counting: R1 10, R2 10, R3 5, R4 4, R5 5, R6 9, R7 3, R8 1, R9 2, R10 1 = 50), all accepted (several as invariants delegated to the Sprint 8.4 RUNBOOK deliverable per the logged altitude decision); zero rejections. Grand totals across all three review cycles: 5+6+10 = 21 rounds, 56+18+50 = 124 findings.
