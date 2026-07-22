---
date: 2026-07-17
description: Phase 2 guide. Auth0 v4 server session, BFF Bearer proxy, jose JWKS verification, users upsert keyed to sub, TOTP MFA with durable lockout, DB-backed admins.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 02 — Auth & Identity (Phase 2)

**Preconditions**: Sprint 1 exit gate green; human has provisioned Auth0 (human-todo H-AUTH, done): tenant `cloudaitrader.us.auth0.com`, regular web app + M2M app authorized for Management API, API with identifier `https://cloudaitrader.com` (the provisioned `AUTH0_AUDIENCE` — authoritative everywhere, R9-6). Issuer and JWKS URI are DERIVED from `AUTH0_DOMAIN` in `lib/env.ts` / backend config — never separate env vars.
**Phase exit gate**: signed-in user hits a protected backend route through the BFF; a bare-pool query returns zero rows (RLS proof once Sprint 3.1 lands roles; until then the gate is JWKS verify + users upsert working end-to-end).

## Sprint 2.1 — Auth0 server session

- `app/frontend/lib/env.ts` FIRST (PLAN.md invariant 17): the frontend's server-only env loader — exports typed getters for every non-public server var (`AUTH0_*`, `APP_BASE_URL`, `API_BASE_URL`); marked `import "server-only"`; all server code reads env exclusively through it. Build-time `NEXT_PUBLIC_*` reads stay inline (compile-time constants, exempt).
- `app/frontend/lib/auth0.ts`: `new Auth0Client({ domain, clientId, clientSecret, secret, appBaseUrl, authorizationParameters: { audience: env.AUTH0_AUDIENCE, scope: 'openid profile email' } })` — vars via `lib/env.ts`.
- `middleware.ts`: single middleware that (a) delegates `/auth/*` to `auth0.middleware`, (b) otherwise runs the next-intl middleware. Matcher excludes `_next`, static assets, `/api/*` (API routes handle auth themselves). Keep the file named `middleware.ts` (I5).
- Login/logout links point at `/auth/login` and `/auth/logout` (v4 mounts routes, no `[...auth0]` route file).
- The access token NEVER reaches client components (I2): no token in props, no `useUser().accessToken` usage.

## Sprint 2.2 — BFF proxy

`app/frontend/app/api/[...path]/route.ts` (runtime `nodejs`):

1. `const session = await auth0.getSession()`; 401 JSON if absent.
2. `const { token } = await auth0.getAccessToken()` (server-side refresh included).
3. Forward method/body/query to `${API_BASE_URL}/${path.join('/')}` with `Authorization: Bearer ${token}`, `content-type` passthrough; return backend status/body verbatim (no re-wrapping), never cache (`dynamic = 'force-dynamic'`).
4. Static local routes (`/api/contact`, later `/api/stripe/*` if any) are separate route files — Next prefers specific routes over the catch-all.
5. On backend 403 body `{error:{code:'MFA_REQUIRED'}}` pass through untouched (frontend modal consumes it, Sprint 2.4).

## Sprint 2.3 — Backend verify + identity

- `src/services/db.js`: `pool` (DATABASE_URL, `app_user`), `servicePool` (SERVICE_DATABASE_URL, `app_service` — BYPASSRLS DML, no DDL; webhooks, outbox, admin reads, provisioning; PLAN.md D14 — the backend never holds DIRECT_URL and refuses to start with it in production); each pool boot-asserts its `SELECT current_user` (app_user / app_service) and throws on mismatch (Format B inv 14); and `withUser(sub, fn)`:
  `BEGIN; SELECT set_config('app.user_id', $sub, true);` run `fn(client)`, `COMMIT` (rollback on throw, release always).
- `src/middleware/require-auth.js`: `createRemoteJWKSet(new URL('https://'+AUTH0_DOMAIN+'/.well-known/jwks.json'))`; `jwtVerify(token, jwks, { issuer: 'https://'+AUTH0_DOMAIN+'/', audience: AUTH0_AUDIENCE })` (I3); attach `req.auth = { sub, email, name, nickname }` from payload claims.
- Migration `001_identity.sql` (numbered, idempotent, run-on-start via `migrations/run.js` with a `schema_migrations` table): `CREATE SCHEMA IF NOT EXISTS app;` `app.users(id TEXT PRIMARY KEY, email TEXT, display_name TEXT, created_at timestamptz DEFAULT now(), last_login_at timestamptz)`.
- Upsert middleware after verify: `INSERT INTO app.users(id,email,display_name,last_login_at) VALUES($1,$2,$3,now()) ON CONFLICT(id) DO UPDATE SET email=EXCLUDED.email, display_name=EXCLUDED.display_name, last_login_at=now()`; `display_name` mirror = `nickname || name` — via servicePool in a `provisionUser` service. **Deletion guards (PLAN.md D15)**: provisioning consults `app.deleted_subs` — a session whose `iat` predates the sub's latest `deleted_at` → 401 (forces re-login); a genuinely fresh login re-provisions with a NEW `incarnation` uuid.
- Baseline global rate limit (express-rate-limit, 300/min/IP) mounted now, not Phase 9; `request_id` accepted from the BFF header and attached to every log line.
- `GET /me` (protected) returns the app.users row.

## Sprint 2.4 — MFA + admins

- Migration `002_mfa_admins.sql`: `app.user_mfa(user_id TEXT PK REFERENCES app.users ON DELETE CASCADE, secret_enc bytea NOT NULL, key_version int NOT NULL, last_used_step bigint, recovery_codes_hashed text[] NOT NULL DEFAULT '{}', verified_at timestamptz, last_stepup_at timestamptz, failed_attempts int NOT NULL DEFAULT 0, locked_until timestamptz)`; `app.admins(user_id TEXT PK REFERENCES app.users ON DELETE CASCADE, created_at timestamptz DEFAULT now())`.
- **MFA lifecycle (PLAN.md MFA decision)**: secrets encrypted AES-256-GCM with the key from `MFA_ENC_KEYS[key_version]`; encrypt with `MFA_ENC_KEY_ACTIVE`, decrypt by stored version, lazily re-encrypt on successful verify (rotation drains organically; drain metric exposed to admin). 10 one-time recovery codes issued at enroll, bcrypt-HASHED (key loss can never lock users out); replay protection: reject a TOTP step ≤ `last_used_step`; ±1-step skew window; disable/reset requires step-up and revokes the MFA session state.
- **Admin bootstrap (PLAN.md D12)**: `scripts/bootstrap-admin.js <sub>` run manually; in production it REFUSES whenever `app.admins` is non-empty (no `--force`); break-glass is direct SQL via the Neon console by the human. Guards: cannot delete the last admin row (tested under concurrency); admins cannot remove other admins via API.
- TOTP endpoints (all under require-auth):
  - `POST /mfa/setup`: if a verified factor exists, require step-up (fresh `last_stepup_at` within 24h) BEFORE issuing a new secret (Format B: ungated setup lets a bare session strip the factor). Generate `otpauth` secret, return provisioning URI + QR data URL (`qrcode`).
  - `POST /mfa/verify`: validate code (window 1). On success: set `verified_at`/`last_stepup_at=now()`, `failed_attempts=0`, `locked_until=NULL`. On failure: increment; at `MFA_MAX_ATTEMPTS` set `locked_until=now()+MFA_LOCKOUT_MS`; while locked return `429` with `Retry-After` seconds header.
  - `POST /mfa/disable`: step-up required.
- `requireMfa` middleware: user has verified factor AND `last_stepup_at` within 24h → pass; verified factor but stale step-up → `403 {error:{code:'MFA_REQUIRED'}}`; no factor → pass EXCEPT routes tagged admin (`/admin/*` always require an enrolled factor: no factor → `403 {error:{code:'MFA_ENROLL_REQUIRED'}}`).
- Frontend: global fetch wrapper catches `MFA_REQUIRED` → modal (AntD) collects TOTP → `POST /api/mfa/verify` (with `skipAuthRedirect`) → retry original request once.

## Acceptance (phase)

- `curl -s localhost:4000/me` → 401 envelope. Same via BFF with a real session → 200 user row; `app.users` has the row with `display_name` = Auth0 nickname.
- Tampered token (bad aud) → 401 from jose, logged without stack trace.
- MFA: wrong code x5 → 429 + `Retry-After`; correct code after cooldown resets counters. `/admin/ping` without factor → `MFA_ENROLL_REQUIRED`.
- Deleting the only row in `app.admins` via API → 409 guard error.
