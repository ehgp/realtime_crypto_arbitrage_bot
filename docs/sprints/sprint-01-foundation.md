---
date: 2026-07-17
description: Phase 1 guide. Relocate the legacy bot to archive/, scaffold the Format B monorepo (frontend, App Worker, Backtester Worker), one compose file, i18n and theme baseline.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 01 — Foundation & Scaffold (Phase 1)

**Preconditions**: PLAN.md approved; branch `ai`. No external accounts needed yet.
**Phase exit gate**: `docker compose -f docker-compose-dev.yml up` boots Postgres + App Worker + Backtester healthy; `npm run dev` in `app/frontend` serves the shell; legacy code lives under `archive/` only.

## Sprint 1.1 — Legacy relocation + monorepo scaffold

### Relocation (zero data loss; use `git mv` only)

Create `archive/legacy-bot/` and `git mv` into it: `main.py`, `analysis.py`, `bellmanford.py`, `triarb.py`, `trade.py`, `history.py`, `kucoinlive.py`, `coinbaselive.py`, `geminilive.py`, `parameters.yaml`, `log_config.yaml`, `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `Pipfile`, `execute_comparison.bat`, `execute_comparison.sh`, `.pre-commit-config.yaml`, `.dockerignore`, `graph.png`, and the directories `comparison/`, `db/`, `eda/`, `indicators/`, `sql/`, `log/`, `presentation/`, `docs/source/` (legacy Sphinx → `archive/legacy-bot/docs-sphinx/`). Keep `bib/` at root (research references), keep `docs/` product docs, ADRs, sprints.

**Security**: `.env` (221 bytes, committed 2023) — `git rm --cached .env`, add `.env` to `.gitignore`, keep a local copy only if it still has value. Do NOT rewrite history yourself; history purge + key rotation is a human decision (human-todo.md item H-SEC-1). Engines stay importable: Sprint 4.2 extracts from `archive/legacy-bot/`, so relocation must not edit file contents.

### Scaffold

```
app/frontend/    # npx create-next-app@latest (TS, App Router, ESLint, Turbopack, src/ NO, alias @/*)
app/backend/     # npm init; "type":"module"; Node 22
backtester/      # uv init; Python 3.12
```

- Env names are governed by PLAN.md's "Environment contract & canonical-name reconciliation" (invariant 17) — the `.env.example` below uses them verbatim.
- Frontend deps: `antd@^5`, `@ant-design/nextjs-registry`, `@ant-design/icons`, `next-intl`.
- App Worker deps: `express@^5`, `pg`, `jose`, `helmet`, `cors`, `express-rate-limit`, `stripe`, `resend`, `otpauth`, `qrcode`, `pino`; dev: `nodemon`, `supertest`, `jest` (or `node:test`).
- Backtester deps (`pyproject.toml`, managed by `uv`): `ccxt`, `sqlalchemy>=2.0`, `psycopg[binary]`, `pandas`, `numpy`, `networkx`, `structlog`, `sentry-sdk`, `tenacity`; dev: `ruff`, `pytest`. No APScheduler — the scheduler is a plain sleep-loop (simplest thing that works).
- Root: `package.json` workspaces optional — SKIP (two Node apps deploy separately; keep independent lockfiles). Add root `README.md` note pointing at PLAN.md until Sprint 9 rewrites it.

### Acceptance
- `git status` shows only renames/moves for legacy files (`R` status), no deletions.
- `ls *.py` at repo root → no matches.
- `cd app/frontend && npm run build` exits 0. `cd app/backend && node src/index.js` starts and serves `GET /health` → `{"ok":true}`. `cd backtester && uv run python -m backtester.health` prints `ok`.

## Sprint 1.2 — Compose + env contract

`docker-compose-dev.yml` at root (PLAN.md D14: one-shot migrate job owns DDL credentials):

- `postgres`: `postgres:17-alpine`, `POSTGRES_DB=cloudaitrader`, healthcheck `pg_isready`, volume `pgdata`.
- `pgadmin`: `dpage/pgadmin4`, profile `tools` (not default).
- `migrate`: build `app/backend`, command `node migrations/run.js`, env `DIRECT_URL` (ONLY service that gets it), `depends_on: postgres: condition: service_healthy`, `restart: "no"` — runs to completion.
- `backend`: build `app/backend`, command `node src/index.js` (no migration step), env `DATABASE_URL` + `SERVICE_DATABASE_URL` (never DIRECT_URL), `depends_on: migrate: condition: service_completed_successfully`, port `4000:4000`.
- `backtester`: build `backtester/`, env `WORKER_DATABASE_URL`, `depends_on: migrate: condition: service_completed_successfully`, no ports (D5).

`.env.example` (documents every var; dev compose overrides DB URLs to local Postgres — never point dev compose at Neon):

```
# Auth0 (frontend)
AUTH0_DOMAIN=cloudaitrader.us.auth0.com AUTH0_CLIENT_ID= AUTH0_CLIENT_SECRET= AUTH0_SECRET= APP_BASE_URL=http://localhost:3000 AUTH0_AUDIENCE=https://cloudaitrader.com AUTH0_DB_CONNECTION=Username-Password-Authentication
# issuer + jwks are DERIVED from AUTH0_DOMAIN in the loaders — never separate vars (PLAN.md invariant 17)
# Auth0 (backend verify + management)
AUTH0_M2M_CLIENT_ID= AUTH0_M2M_CLIENT_SECRET=
# DB (dev values point at compose postgres; roles per PLAN.md D14)
DATABASE_URL=postgres://app_user:app_user@localhost:5432/cloudaitrader
SERVICE_DATABASE_URL=postgres://app_service:app_service@localhost:5432/cloudaitrader
DIRECT_URL=postgres://postgres:postgres@localhost:5432/cloudaitrader   # migrate job ONLY
WORKER_DATABASE_URL=postgres://worker_user:worker_user@localhost:5432/cloudaitrader
# Edge / services (empty until Phase 6+)
TURNSTILE_SECRET= NEXT_PUBLIC_TURNSTILE_SITE_KEY= RESEND_API_KEY= ADMIN_NOTIFICATION_EMAIL=
STRIPE_SECRET_KEY= STRIPE_WEBHOOK_SECRET= STRIPE_PRICE_ID=
SENTRY_DSN_FRONTEND= SENTRY_DSN_BACKEND= SENTRY_DSN_WORKER=
# App (admin bootstrap is a CLI, not env — PLAN.md D12)
API_BASE_URL=http://localhost:4000 MFA_MAX_ATTEMPTS=5 MFA_LOCKOUT_MS=900000
MFA_ENC_KEYS={"1":"<32-byte-hex>"} MFA_ENC_KEY_ACTIVE=1
```

Env loaders: backend `src/config.js` reads and, when `NODE_ENV=production`, throws on any missing required var (I8); backtester `backtester/config.py` same behavior.

### Acceptance
- `docker compose -f docker-compose-dev.yml up -d && docker compose -f docker-compose-dev.yml ps` → three services `healthy`/`running`.
- `NODE_ENV=production node src/index.js` without env → exits non-zero naming the first missing var.

## Sprint 1.3 — i18n + theme baseline

- next-intl with `localePrefix: "as-needed"`, locales `['en']`, default `en`; `app/[locale]/layout.tsx` + root passthrough per next-intl App Router docs. `middleware.ts` (NOT `proxy.ts`, I5) holds the intl middleware now; Auth0 mounts into it in Sprint 2.1.
- Copy pattern: `content/en.json` + `lib/content.ts` exporting `pickContent(section)` (typed JSON import). No `t()` calls.
- AntD `ConfigProvider` theme in `app/[locale]/layout.tsx` from DESIGN.md tokens: `colorPrimary #1A1C1E`, error `#BA1A1A`, warning `#A06800`, success `#1F6E2E`, accent/tertiary `#B8422E` for CTAs-hover, `borderRadius: 4`, fonts Public Sans (body/display) + Space Grotesk (labels) via `next/font`.
- DESIGN.md: rename `name:` to `CloudAITrader`, fill the Overview/Colors/Typography REPLACE blocks with two sentences each consistent with the tokens (keep tokens unchanged).

### Acceptance
- `/` renders a landing shell with AntD button themed `#1A1C1E`; `/es` → 404 (only `en` configured); build passes with typed content import.
