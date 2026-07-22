---
date: 2026-07-17
description: Everything only the human can do to unblock the CloudAITrader build - account provisioning, DNS, keys, pricing decisions, and the blocked Codex plan review.
tags:
  - todo
  - cloudaitrader
---

# Human TODO — CloudAITrader

What only you can do, ordered roughly by when the sprints need it. IDs are referenced from [docs/sprints/](docs/sprints/) and [PLAN-REVIEW-LOG.md](PLAN-REVIEW-LOG.md).

## Immediate (before/while Codex starts Phase 1)

- [x] **H-REVIEW-1 — Codex plan review (Act 2): DONE 2026-07-18.** After you freed RAM, the review ran 5 rounds on one Codex thread and ended `VERDICT: APPROVED` (confidence 98/100). 56 findings raised, 53 accepted into PLAN.md (now Revision 5), 2 rejected with logged reasons that Codex endorsed. Full transcript in PLAN-REVIEW-LOG.md.
- [ ] **H-BUILD-1 — Choose who builds.** The plan is approved and the sprint guides are synced. Options: (a) Codex builds — commit the plan artifacts first (PLAN.md, PLAN-REVIEW-LOG.md, CONTEXT.md, docs/) then run `/codex-build` with SPEC_FILE=PLAN.md; (b) Claude builds sprint-by-sprint; (c) hold.
- [ ] **H-ADMIN-1 — After Phase 2 deploys: bootstrap your admin.** Run `node scripts/bootstrap-admin.js <your-auth0-sub>` once (it refuses when an admin already exists in production; break-glass afterwards is direct SQL via the Neon console). Also generate the MFA encryption key: `MFA_ENC_KEYS={"1":"<openssl rand -hex 32>"}`, `MFA_ENC_KEY_ACTIVE=1`.
- [ ] **H-SEC-1 — Rotate/retire the committed `.env` secrets.** A 221-byte `.env` has been tracked in git since 2023 (KuCoin/exchange credentials pattern). Assume leaked: rotate or delete those exchange API keys at the source. Decide whether to purge git history (`git filter-repo`) — destructive, your call; Sprint 1.1 only untracks it going forward.
- [ ] **H-BRANCH-1 — Confirm branch/PR flow.** Plan executes on branch `ai` (current). Confirm you want Codex committing there vs. PR-per-sprint into `main`.
- [ ] **A1 (informational only, resolved conservatively 2026-07-21)** — Your provisioned domain `cloudaitrader.us.auth0.com` looks dedicated; the old env comment said "shared portfolio tenant". Either way, **MVP account deletion is LOCAL-ONLY** (PLAN.md R9-7: the Auth0-identity-deletion branch was removed — it would need `delete:users` scope, idempotent retries, session revocation, and tests; post-MVP if you ask for it). Answer "dedicated"/"shared" purely for the record.

## Provisioning (Sprint 0.3 — needed by the phase in parens)

- [x] **H-AUTH (Phase 2)** — Auth0: Regular Web App (callbacks `http://localhost:3000/auth/callback`, later `https://cloudaitrader.com/auth/callback`), API with identifier `https://cloudaitrader.com` (the provisioned `AUTH0_AUDIENCE` — corrected 2026-07-21 to match your tenant; the earlier `backend.cloudaitrader.com` value in this item was superseded), M2M app authorized for the Management API (`read:users update:users`). Drop values into `.env`: `AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_SECRET (openssl rand -hex 32), AUTH0_M2M_CLIENT_ID, AUTH0_M2M_CLIENT_SECRET`. Admin access comes from the one-time bootstrap CLI (H-ADMIN-1), NOT an env var — `ADMIN_EXTERNAL_IDS` was removed by PLAN.md D12.
- [x] **H-NEON (Phase 3 for prod; local compose needs nothing)** — Neon project (Postgres 17, free tier), DB `cloudaitrader`, four DSNs captured. _Correction 2026-07-21: the current contract uses THREE role files (`000_role.sql`→`app_user`, `000_worker_role.sql`→`worker_user`, `000_service_role.sql`→`app_service`) with passwords supplied via `\prompt -s` (never argv), and the canonical role names changed — see H-NEON-2 below for the rename you still owe._
- [ ] **H-NEON-2 (before Phase 3 connects anything)** — The Format B contract now fixes the role NAMES: `app_service` and `worker_user` (you provisioned under the older `service_role`/`worker_role` names per H-NEON). Nothing connects yet, so re-provision cleanly in the Neon SQL console: `ALTER ROLE service_role RENAME TO app_service; ALTER ROLE worker_role RENAME TO worker_user;` (or drop/recreate via the three `000_*` files), then update the usernames inside your captured `SERVICE_DATABASE_URL`/`WORKER_DATABASE_URL` values.
- [ ] **H-FALLBACK-1 (Phase 8, Sprint 8.4)** — DB fallback per the new Format B invariant 17: confirm eg-server-3 has capacity for a `postgres:17` container + LUKS-encrypted volume; the fallback Postgres binds to the WireGuard/fleet network only; accept the default 6h dump/restore RPO or name a different interval. **Also provision the operator-only Neon control-plane credentials** (PLAN.md R12-1): create a Neon API key and record `NEON_API_KEY`, `NEON_PROJECT_ID`, `NEON_PRIMARY_BRANCH_ID` in a 0600 operator env file on eg-server-3 ONLY — never in any runtime container, Vercel, or CI secret store (the failback script is their sole consumer).
- [ ] **H-EDGE (Phase 6)** — Cloudflare Turnstile site for cloudaitrader.com → `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET`.
- [x] **H-EMAIL (Phase 6)** — Resend: verify domain cloudaitrader.com (DNS records), create `RESEND_API_KEY`, set `ADMIN_NOTIFICATION_EMAIL`, set `RESEND_FROM_EMAIL` (verified-domain sender, e.g. `CloudAITrader <noreply@cloudaitrader.com>` — your current egventures.net value must move to a verified domain), and set `ENABLE_EMAIL_NOTIFICATIONS=true` explicitly (strict parsing: absence or any value other than `true`/`false` fails CLOSED in production and no email sends).
- [ ] **H-PAY (Phase 6)** — Stripe: product + monthly price → `STRIPE_PRICE_ID` (checkout sessions are server-created — no Payment Link needed, PLAN.md D13); API key `STRIPE_SECRET_KEY`; enable the customer Billing Portal in the dashboard; webhook endpoint (local: `stripe listen`; prod: `https://backend.cloudaitrader.com/stripe/webhook`) → `STRIPE_WEBHOOK_SECRET`. Live-mode versions at Phase 8.
- [ ] **H-OBS (Phase 7)** — Sentry: three DSNs (frontend Next.js project, backend Node project, worker Python project) → `SENTRY_DSN_FRONTEND/_BACKEND/_WORKER`.
- [ ] **H-VERCEL (Phase 8)** — Vercel project rooted at `app/frontend`, attach domain cloudaitrader.com (+ www redirect), paste production env set.
- [ ] **H-DNS (Phase 8)** — Cloudflare DNS for cloudaitrader.com: apex + www → Vercel per Vercel's instructions; `backend.cloudaitrader.com` is created automatically by the named tunnel route; leave `worker.cloudaitrader.com` unallocated (reserved, PLAN.md D5). (YOU WILL DO THIS)
- [ ] **H-TUNNEL (Phase 8)** — Cloudflare named tunnel (dashboard: Zero Trust → Networks → Tunnels): capture the atomic set Sprint 8.3 consumes — `BACKEND_TUNNEL_NAME=cloudaitrader-backend`, `BACKEND_TUNNEL_HOSTNAME=backend.cloudaitrader.com` (public hostname → `http://backend:4000`), and `BACKEND_TUNNEL_TOKEN` (connector token) — all three into the Pi's `.env`. (YOU WILL DO THIS ONCE PI IS READY)
- [ ] **H-PI (Phase 8)** — Pick the eg-server-N Pi for the stack (prefer SSD-boot, least loaded; check with the eg-pi-ops runbook). Confirm Docker + buildx present. No reboots without checking what else runs there.

## Product decisions (data, not code — change anytime)

- [ ] **H-PRICE-1** — Confirm pricing/quota placeholders (A2): free = 10 backtests/mo, 180-day window, 1h/1d timeframes, non-premium rulesets; paid = $29/mo fair-use. Stored in `tier_limits`; adjust there.
- [ ] **H-RULES-1** — Verify the four seeded Firm Rulesets (HyroTrader, Breakout, Crypto Fund Trader, FTMO-crypto) against each firm's CURRENT published rules before launch; seeds carry `estimate=true` flags where I could not verify numbers. Update `verified_at` when checked. This is the product's credibility surface.
- [ ] **H-CI-1 (Phase 9)** — GitHub branch protection on `main` (require CI green); decide if `ai` merges via PR.
- [ ] **H-R2-1** — You added five `R2_*` vars to `.env.example` (2026-07-18, "infra S04/S13"). Blob storage is currently OUT of MVP scope and nothing reads them (they're classified Reserved in PLAN.md's env reconciliation). Decide: does Cloudflare R2 enter scope? If yes, say so and a storage decision + sprint + threat model gets added; if no, the vars can stay reserved or be removed.
- [ ] **H-STD-1** — The plan carries three Codex-approved deviations from the Format B contract (no `ADMIN_EXTERNAL_IDS` seeding, Checkout Sessions instead of Payment Link, `SERVICE_DATABASE_URL` credential split). Consider absorbing them into the Format B skill + trending-today reference so the portfolio standard and its hardened offspring don't drift (details: PLAN.md env reconciliation section).

## Launch/positioning (from docs/competitor-analysis.md)

- [ ] Marketing language review: never promise Challenge outcomes ("pass your challenge") — regulatory posture; show ruleset provenance and `verified_at` prominently.
- [ ] PropFirmMatch listing/affiliate outreach once the demo is live (their ~4M monthly views is the distribution channel).
- [ ] Decide on a re-verify cadence for competitor pricing/rules (competitor analysis is dated 2026-07-17; 30-day staleness rule).
