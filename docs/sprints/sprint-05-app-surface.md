---
date: 2026-07-17
description: Phase 5 guide. Trader dashboard (submit/watch/inspect Backtests), account management on the shared Auth0 tenant, MFA-gated admin surface with Ruleset CRUD and worker observability.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 05 — Core App Surface (Phase 5)

**Preconditions**: Phase 4 gate green (jobs run end-to-end).
**Phase exit gate**: sign in → submit Backtest → status updates → Equity Curve + verdicts render; profile edit + local-only delete work; admin sees worker health and manages Rulesets.

## Sprint 5.1 — Dashboard

Backend (`src/modules/backtests/`):
- `POST /backtests` (require-auth, withUser): validate config (strategy in registry — `buyhold`/`sma_cross` only, D11; SINGLE symbol; timeframe in matrix; window within Dataset coverage; fees_bps 0-100; `account_size` pinned and matching every selected ruleset's account size — D16; ruleset_ids exist+published+compatible with timeframe/account model, else 422 naming the incompatibility); complexity bounds per tier (candle count ≤ tier max); gap pre-check (>0.5% missing → 422 `insufficient_data`); compute `premium` from tier_limits data; transactional quota reservation + `pg_advisory_xact_lock(hashtext(sub))` concurrency-cap check (A2, Sprint 6.3 wires Stripe; the reservation mechanics land HERE); INSERT queued row; return id.
- `GET /backtests` (withUser, RLS-scoped, paginated) and `GET /backtests/:id` (row + results + simulations join).
- `GET /catalog` (public read via pool): strategies, symbol matrix, published rulesets (id, firm_name, version, premium, provenance) — free vs premium flagged.

Frontend (`app/[locale]/dashboard/`):
- Route guard: server component checks `auth0.getSession()`, redirect to `/auth/login?returnTo=/dashboard`.
- New-Backtest form (AntD Form): strategy select, venue+symbol (single), timeframe, date-range (bounded by coverage), account-size pick FIRST (groups the ruleset list — D16), Ruleset multi-select showing firm + version + `verified_at` provenance with incompatible entries disabled and the reason shown (resolution/account-model/size mismatch); complexity preview vs tier bounds; premium options disabled with upgrade hint when unpaid.
- Job list: AntD Table, status tags, poll `GET /backtests` every 5s while any row is queued/claimed/running (SWR/interval; no websockets in MVP).
- Detail page `dashboard/backtests/[id]`: balance+equity chart (`@ant-design/plots` Line — the one new dep), metrics cards, verdict cards per Simulation (**PASS green / FAIL red / INCOMPLETE amber** with violated rule + timestamp, `first_violation_indeterminate` and gap explanations surfaced honestly), trade log table (virtualized, `truncated` notice).

## Sprint 5.2 — Account management

- `src/services/auth0-mgmt.js`: M2M client-credentials token (cached until expiry) against `https://${AUTH0_DOMAIN}/api/v2/`.
- `GET /profile` = app.users row + entitlement + notification prefs. `PATCH /profile { nickname }`: Management API `PATCH /users/{sub}` `nickname` first, then mirror `display_name` locally (Format B identity rule: nickname is THE user-editable name; display_name is a derived mirror re-applied on every login).
- `DELETE /account`: **LOCAL-ONLY regardless of tenant type (A1 resolved conservatively, R9-7 — the Auth0-identity-deletion branch is post-MVP; M2M scopes stay `read:users update:users`) via the D15 persisted workflow** — set `deletion_state='deleting'` + tombstone (sub, incarnation, retired Stripe ids) + destroy the session; error queued jobs, fence running jobs (attempt bump); enqueue `billing_actions` subscription cancel and RETAIN the mapping until Stripe confirms (reconciliation sweep + admin alert on repeated failure); only then DELETE the row (cascades mfa, entitlements, backtests, results, simulations, job_events, prefs, quota — `stripe_events` untouched). Confirm modal explains: removes CloudAITrader data, login remains for other apps, re-login starts fresh.
- Settings page `dashboard/settings/`: profile card, MFA enroll/disable + recovery codes (Sprint 2.4), notification prefs toggle, danger zone.

## Sprint 5.3 — Admin surface

Backend (`src/modules/admin/`, require-auth + requireMfa, admin-checked via `app.is_admin()` in-query):
- `GET /admin/users` (paginated, search by email), `POST /admin/users/:id/entitlement` (manual comp override, audit-logged to a simple `app.audit_log` table added in migration `006_audit.sql`).
- Ruleset CRUD: `POST /admin/rulesets` creates version n+1 for a firm (never mutates published rows — ADR-0002); `PATCH .../publish` flips `published`; unknown primitive keys rejected against the evaluator vocabulary (shared constant exported by a small JSON file both tiers read: `shared/rule-primitives.json` — single source).
- Worker observability reads (ownerPool): `worker.heartbeats` (stale > 2 min flagged red), queue depth by status, `worker.ingest_runs` last 50 with gap warnings, dataset coverage summary (`min(ts), max(ts), count` per matrix entry).

Frontend `app/[locale]/admin/`: users table, ruleset editor (JSON form per primitive with validation), worker health page (heartbeat cards, ingest run table, coverage grid). Admin nav hidden for non-admins (server check), routes still server-enforced.

## Acceptance (phase)

- Playwright-style manual script (documented in PR): login → submit buyhold BTC/USDT 1h 3-month vs 2 rulesets → watch status → detail shows curve + verdicts; settings rename reflects in Auth0 (`nickname`) and header; delete account → tables empty for sub (verify via psql) → re-login → fresh empty account.
- Non-admin GET /admin/users → 403; admin without step-up → `MFA_REQUIRED` → modal → success.
- Ruleset publish v2 → catalog shows v2, old Backtests still reference v1 (FK by id — verdicts immutable).
