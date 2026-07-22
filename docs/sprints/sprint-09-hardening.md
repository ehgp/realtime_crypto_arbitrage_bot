---
date: 2026-07-17
description: Phase 9 guide. Security review with worker least-privilege verification, tiered rate limits and scheduler audit, test suites and CI gates including the determinism hash gate.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 09 — Hardening & Verification (Phase 9)

**Preconditions**: Phase 8 gate green (production live).
**Phase exit gate**: security review yields no High/Critical; CI green on typecheck + lint + all suites incl. determinism gate; rate limits + CSP verified in prod.

## Sprint 9.1 — Security review

Run the security-review checklist and fix findings:
- RLS coverage audit: full cross-user policy MATRIX (SELECT/INSERT/UPDATE/DELETE per table) automated; bare-pool zero-row proof; `withUser` on every authed query path (grep-audit); servicePool usage confined to webhook/outbox/admin/provisioning modules (grep-audit).
- Role least-privilege: rerun the Sprint 3 verb matrix against PROD roles; `worker_user` lacks BYPASSRLS and any grant on users/mfa/admins/quota/stripe_events/billing_actions; `app_service` DDL attempt fails; runtime env lacks DIRECT_URL; all four boot-asserts verified in prod mode; fallback drill repeated once against eg-server-3 (Sprint 8.4).
- Helmet CSP: `default-src 'self'`; explicit allows for Auth0 domain, challenges.cloudflare.com (Turnstile), Sentry ingest, Vercel Analytics; frontend `next.config.ts` headers mirror.
- Safe errors: no stack traces or SQL in any 4xx/5xx body (integration test asserts envelope shape on a forced 500).
- Secrets: startup enforcement verified in prod images (I8); `.env` untracked (Sprint 1.1); no secret-looking strings in repo (`gitleaks` run; findings to human if history purge needed — H-SEC-1).
- Dependency audit: `npm audit --omit=dev` both Node apps, `uv run pip-audit` worker; pin or patch Highs.
- Fallback data-protection audit (R10-9): eg-server-3 volume encryption verified (`cryptsetup status`), credential files 0600, no plaintext dump artifacts, age-encrypted retained dumps within retention 2, host patch level current, SSH auth log reviewed for the drill window.
- Auth: audience enforced (tamper test), MFA lockout behavior re-verified in prod mode, admin routes MFA-enrollment-required.

## Sprint 9.2 — Rate limits + scheduler validation

- Tiered `express-rate-limit`: global 300/min/IP; auth-sensitive (`/mfa/*`) 10/min/IP; submit `POST /backtests` 12/min/user (keyed by sub); webhook path excluded (Stripe signs).
- Frontend contact route keeps its own limiter (Sprint 6.1).
- Backtester audit: every CCXT call inside tenacity backoff+jitter; ingest scheduler drift check (log if a matrix entry is >2 intervals overdue); reaper + heartbeat intervals asserted in tests; fencing test rerun in prod mode.
- MFA key-rotation drill: add key v2, flip active, verify lazy re-encryption drains (admin metric reaches zero v1 rows on active users), retire v1.
- Neon storage check (R14-7): measured TOTAL project storage (not just worker.ohlcv) with three-state failback headroom (primary + staging + recovery) inside the free cap; document actuals in the PR; retention policy adjusted or paid-tier approval obtained on breach.

## Sprint 9.3 — Tests + CI

- Frontend: RTL/Jest — content pickers, BFF 401/403 handling, MFA modal retry, dashboard form validation. `next build` in CI.
- App Worker: supertest integration against compose Postgres — auth envelope, RLS proof, quota 402, Stripe webhook signature + entitlement flip, notify loop stamps.
- Backtester: pytest — characterization goldens + independent invariants, fills/portfolio math, lookahead regression, evaluator primitives across all THREE verdicts (pass/fail/incomplete + indeterminacy), DD boundary suite, grants matrix, determinism manifest gate (run twice in CI → hashes equal; mutated candle → different).
- CI (GitHub Actions `ci.yml`): jobs lint+typecheck (tsc, eslint, ruff), test x3 apps (services: postgres:17), build images (arm64 cross-build smoke on main only), and the **two-domain env-conformance job** (PLAN.md invariant 17): positive — both templates reconcile exactly against their declared sets; runtime reads flow through the FOUR runtime loaders only; operator RAW ACQUISITION happens only in `infra/fallback/operator-env.sh`, with post-source use permitted only under `infra/fallback/`; negative — a seeded runtime loader-bypass read, a seeded operator-var acquisition outside `operator-env.sh`, a seeded operator-value use outside `infra/fallback/`, and a seeded undeclared name each FAIL the job. Branch protection note for human (H-CI-1).
- Rewrite root `README.md`: product description, architecture sketch, quickstart (compose-dev), link PLAN.md/docs; move bot history to a Heritage section. Update `AGENTS.md` to the new architecture map; check off AGENTS-TODO.md items (D1 resolved).

## Acceptance (phase)

- CI run URL green on all jobs; `curl -I https://backend.cloudaitrader.com` shows Helmet headers + CSP; 429 observed on a scripted 15-request `/mfa/verify` burst; security checklist committed at `docs/security-review-<date>.md` with all items checked or ticketed.
