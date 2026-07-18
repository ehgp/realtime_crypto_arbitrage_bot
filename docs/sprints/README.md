---
date: 2026-07-17
description: Index and execution conventions for the CloudAITrader sprint guides. One guide per phase; Codex executes sprints in order and must pass each exit gate before advancing.
tags:
  - sprints
  - cloudaitrader
---

# CloudAITrader Sprint Guides (for Codex)

Execution companion to [../../PLAN.md](../../PLAN.md). Domain language per [../../CONTEXT.md](../../CONTEXT.md). Decisions D1-D10, assumptions A1-A2, and invariants I1-I13 referenced below are defined in PLAN.md. ADRs in [../adr/](../adr/).

## How to execute

1. Work on branch `ai`. Never create a new branch unless the human asks.
2. Phases run in order; sprints within a phase run in order unless marked parallel-safe. Do not start a phase until the previous phase's exit gate passes.
3. Every sprint ends with its **Acceptance** commands run and passing. Paste command output as evidence in the PR/commit description. A sprint with failing acceptance is not done; no `test.skip`, no stub tests, no TODO placeholders left behind.
4. Migrations are append-only numbered files in `app/backend/migrations/`; never edit an applied migration (I6).
5. Secrets come from env; never commit values. `.env.example` documents every variable the moment it is introduced.
6. When a guide conflicts with PLAN.md, PLAN.md wins; when PLAN.md conflicts with CONTEXT.md language, CONTEXT.md wins. Flag the conflict in the commit message.
7. Human-owned prerequisites (account provisioning, DNS, dashboards) live in [../../human-todo.md](../../human-todo.md). If a sprint is blocked on one, implement everything up to the boundary, wire config through env, and mark the item blocked in the commit message rather than inventing credentials.

## Guides

| Guide | Phase | Ships |
|---|---|---|
| [sprint-01-foundation.md](sprint-01-foundation.md) | 1 | Legacy relocation, monorepo scaffold, compose-dev, i18n + theme |
| [sprint-02-auth-identity.md](sprint-02-auth-identity.md) | 2 | Auth0 session, BFF proxy, JWKS verify, users upsert, MFA, admins |
| [sprint-03-schema-worker-contract.md](sprint-03-schema-worker-contract.md) | 3 | Roles, RLS, domain schema, worker grants, ruleset seeds |
| [sprint-04-backtester-worker.md](sprint-04-backtester-worker.md) | 4 | Ingestion, Heritage Engine extraction, backtest harness, Challenge Simulation evaluator, job loop |
| [sprint-05-app-surface.md](sprint-05-app-surface.md) | 5 | Dashboard, account management, admin surface |
| [sprint-06-edge-monetization.md](sprint-06-edge-monetization.md) | 6 | Contact form, notifications, Stripe entitlements, quotas, analytics |
| [sprint-07-observability-pwa.md](sprint-07-observability-pwa.md) | 7 | Sentry x4 runtimes, Serwist PWA, manifest/icons |
| [sprint-08-deploy.md](sprint-08-deploy.md) | 8 | compose-host on Pi fleet, Vercel web tier, backend named tunnel |
| [sprint-09-hardening.md](sprint-09-hardening.md) | 9 | Security review, rate limits, tests + CI gates |

## Global conventions

- **Frontend**: TypeScript strict; App Router server components by default; AntD 5 via `@ant-design/nextjs-registry`; copy through `lib/content.ts` `pickContent` (JSON import), not `t()`.
- **App Worker**: Node 22, Express 5, ESM (`"type": "module"`); `src/modules/<area>/` routers + `src/services/` shared; errors as `{ error: { code, message } }`, never stack traces (I8 posture).
- **Backtester Worker**: Python 3.12, `pyproject.toml` + `uv.lock`, ruff (lint+format), SQLAlchemy 2.0 Core (sync, psycopg 3), structured logging via `structlog`-style JSON to stdout.
- **Timestamps**: UTC everywhere; `timestamptz` in Postgres; candle `ts` is the candle OPEN time.
- **Money/quantities**: `numeric` in Postgres; `Decimal` in Python; never float for balances (floats allowed inside engine math where documented, but persisted balances/prices are Decimal).
- **IDs**: `app.users.id` IS the Auth0 `sub` (TEXT, I4); all other PKs `uuid` default `gen_random_uuid()`.
