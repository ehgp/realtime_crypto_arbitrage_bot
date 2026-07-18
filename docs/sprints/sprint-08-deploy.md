---
date: 2026-07-17
description: Phase 8 guide. compose-host on the Pi fleet against Neon, Vercel web tier at cloudaitrader.com, Cloudflare named tunnel for backend.cloudaitrader.com only.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 08 — Deploy (Phase 8)

**Preconditions**: Phase 7 gate green; human-todo H-DNS, H-NEON, H-TUNNEL, H-VERCEL done (domains, Neon prod project + roles bootstrapped, tunnel created, Vercel project linked).
**Phase exit gate**: cloudaitrader.com serves authed traffic via backend.cloudaitrader.com; Backtester on the Pi completes a real user Backtest; Stripe live webhook registered and verified.

## Sprint 8.1 — compose-host on the Pi fleet

- `docker-compose-host.yml`: services `backend` + `backtester` (+ `migrate` one-shot, profile `migrate`). No postgres/pgadmin, no published ports for backtester; backend exposes `4000` on the compose network only. Deploy script runs `docker compose -f docker-compose-host.yml run --rm migrate` FIRST (D14: `--rm` disposes the container and its DIRECT_URL env — Neon pooler breaks DDL so migrate uses the direct owner URL), then `up -d` the runtime services, whose env carries ONLY `DATABASE_URL` + `SERVICE_DATABASE_URL` (backend) and `WORKER_DATABASE_URL` (backtester) — never DIRECT_URL.
- Images: multi-arch build (`linux/arm64` for Pi) — `docker buildx` targets in a `build.sh`; Node 22-slim and `python:3.12-slim` bases both publish arm64.
- Manual bootstrap (documented header): run `000_role.sql` + `000_worker_role.sql` once against Neon as owner with human-set passwords (H-NEON).
- Pi selection + capacity check per eg-pi-ops conventions (worker is CPU-bound during Backtests; pick the Pi with SSD boot + least load; do NOT reboot without asking).
- Watchdog: `restart: unless-stopped` on both services.

## Sprint 8.2 — Vercel web tier

- Vercel project → `app/frontend` root; domains: cloudaitrader.com + www redirect (H-DNS/H-VERCEL).
- Env (Production): all `AUTH0_*`, `APP_BASE_URL=https://cloudaitrader.com`, `API_BASE_URL=https://backend.cloudaitrader.com`, `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, Sentry DSNs, `NEXT_PUBLIC_` analytics defaults.
- Auth0 app callback/logout URLs add production origins (H-AUTH).
- Stripe: switch webhook endpoint to `https://backend.cloudaitrader.com/stripe/webhook` (live mode, H-PAY); verify with `stripe trigger` against live-mode test clock or a $0 coupon flow.

## Sprint 8.3 — Backend named tunnel (backend only — D5)

- `infra/tunnel/`: `tunnel-up.sh` + `tunnel-up.ps1 [backend]` starting a profile-gated `cloudflared-backend` service (compose overlay `docker-compose.tunnel.yml`, profile `tunnel`): named tunnel `cloudaitrader-backend`, hostname `backend.cloudaitrader.com` → `http://backend:4000` over the compose network; token mode (`BACKEND_TUNNEL_TOKEN`) or CLI login mode; no inbound ports on the Pi, no `depends_on` (cloudflared retries origin).
- Worker tunnel intentionally ABSENT: assert in script that `[worker]` argument exits with "reserved, not provisioned (PLAN.md D5)".
- Backend CORS: allow origin `https://cloudaitrader.com` only; Helmet on; trust proxy 1 (Cloudflare) so `remoteip`/rate limits see real IPs.

## Acceptance (phase)

- From a cold Pi: deploy script (migrate `run --rm`, then `--profile tunnel up -d`) → `curl https://backend.cloudaitrader.com/health` 200 from the internet; no open ports on the Pi's LAN IP (`nmap` spot check); `docker ps -a` shows NO migrate container remaining; `docker inspect` of runtime containers shows no DIRECT_URL.
- Full prod loop: sign in at cloudaitrader.com → submit Backtest → worker on Pi picks it up (heartbeat visible in admin) → results render; Sentry receives a prod test event from all runtimes; Stripe live webhook test event verified in Stripe dashboard.
