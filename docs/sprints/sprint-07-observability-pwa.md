---
date: 2026-07-17
description: Phase 7 guide. Sentry across browser, Node server, edge, and the Python worker; Serwist PWA with offline shell; manifest and icons from the brand mark.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 07 — Observability & PWA (Phase 7)

**Preconditions**: Phase 6 gate green; Sentry project DSNs provisioned (human-todo H-OBS).
**Phase exit gate**: a forced error surfaces in Sentry from each of the four runtimes; `/serwist/sw.js` served; `/offline` renders with network disabled.

## Sprint 7.1 — Sentry, four runtimes

- Frontend: `npx @sentry/wizard@latest -i nextjs` equivalent manual setup — `sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`, `withSentryConfig` in `next.config.ts`, tunnel route `/monitoring` (ad-block bypass), `SENTRY_DSN_FRONTEND` (+ `NEXT_PUBLIC_` variant for client). `tracesSampleRate: 0.1`, `enabled: NODE_ENV==='production'`.
- App Worker: `@sentry/node` init FIRST line of `src/index.js` (before express import so auto-instrumentation patches http/pg/express), `SENTRY_DSN_BACKEND`; error middleware captures before the safe-error envelope.
- Backtester: `sentry-sdk` `init` FIRST line of `worker.py` (patches sqlalchemy/httpx), `SENTRY_DSN_WORKER`; job-loop try/except captures with `job_id` tag then marks job error (never crash the loop on a job failure).
- Debug endpoints (admin-gated, removed in Sprint 9.1 or env-gated): `GET /admin/debug/error` in backend; `--raise-test-error` flag in worker; a dev-only button throwing client-side.

## Sprint 7.2 — Serwist PWA

- `@serwist/turbopack` per current Serwist Next.js docs: `app/serwist/sw.ts` source → served at `/serwist/sw.js`; register in root layout.
- Runtime caching: `NetworkOnly` for `/api/*`, `/monitoring*`, `/auth/*`, Vercel Analytics scripts; `defaultCache` for static assets; precache `/offline` fallback page (document fallback on navigation failure).
- `/offline` page: brand mark + "You're offline; backtests keep running server-side."

## Sprint 7.3 — Manifest + icons

- Brand mark: simple "CAT" monogram / candle-glyph SVG in DESIGN.md palette (`#1A1C1E` on `#F7F5F2`), generated as `icon-192.png`, `icon-512.png`, `maskable-512.png`, `apple-touch-icon.png`, `favicon.ico`.
- `app/manifest.ts`: name CloudAITrader, short_name CloudAITrader, `display: standalone`, `background_color #F7F5F2`, `theme_color #1A1C1E`, icons array with maskable purpose.

**Correlation IDs (PLAN.md R1 finding 25)**: the BFF generates `request_id` (forwarded header); the backend logs and Sentry-tags it; job submission stamps it onto the backtest row; the worker tags logs and Sentry events with `job_id`, `attempt`, and the originating `request_id`; the outbox notifier carries `job_id` through send logs. One job must be traceable end-to-end: request_id → backtest_id → attempt → job_event → email.

## Acceptance (phase)

- Four Sentry events visible (browser, node, edge via a middleware-thrown test, worker) each tagged by runtime AND correlation IDs; a seeded job traced end-to-end through logs by request_id/job_id.
- Lighthouse PWA installable check passes locally; DevTools offline → `/offline` renders; `/api/*` never served from SW cache (network tab).
