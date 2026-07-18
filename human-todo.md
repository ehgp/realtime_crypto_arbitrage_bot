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
- [ ] **A1 — Confirm the Auth0 tenant is the shared portfolio tenant.** The plan assumes shared (account deletion = local-only). If CloudAITrader gets its own tenant, tell Claude/Codex to flip the Sprint 5.2 deletion semantics.

## Provisioning (Sprint 0.3 — needed by the phase in parens)

- [ ] **H-AUTH (Phase 2)** — Auth0: Regular Web App (callbacks `http://localhost:3000/auth/callback`, later `https://cloudaitrader.com/auth/callback`), API with identifier `https://backend.cloudaitrader.com` (this is `AUTH0_AUDIENCE`), M2M app authorized for the Management API (`read:users update:users`). Drop values into `.env`: `AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_SECRET (openssl rand -hex 32), AUTH0_M2M_CLIENT_ID, AUTH0_M2M_CLIENT_SECRET`. Add your own `sub` to `ADMIN_EXTERNAL_IDS`.
- [ ] **H-NEON (Phase 3 for prod; local compose needs nothing)** — Neon project (Postgres 17, free tier): create DB `cloudaitrader`; run `migrations/000_role.sql` + `000_worker_role.sql` as owner with real passwords; capture `DATABASE_URL` (pooled, app_user), `DIRECT_URL` (owner, direct), `WORKER_DATABASE_URL` (worker_role, direct).
- [ ] **H-EDGE (Phase 6)** — Cloudflare Turnstile site for cloudaitrader.com → `NEXT_PUBLIC_TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET`.
- [ ] **H-EMAIL (Phase 6)** — Resend: verify domain cloudaitrader.com (DNS records), create `RESEND_API_KEY`, set `ADMIN_NOTIFICATION_EMAIL`.
- [ ] **H-PAY (Phase 6)** — Stripe: product + monthly price → `STRIPE_PRICE_ID` (checkout sessions are server-created — no Payment Link needed, PLAN.md D13); API key `STRIPE_SECRET_KEY`; enable the customer Billing Portal in the dashboard; webhook endpoint (local: `stripe listen`; prod: `https://backend.cloudaitrader.com/stripe/webhook`) → `STRIPE_WEBHOOK_SECRET`. Live-mode versions at Phase 8.
- [ ] **H-OBS (Phase 7)** — Sentry: three DSNs (frontend Next.js project, backend Node project, worker Python project) → `SENTRY_DSN_FRONTEND/_BACKEND/_WORKER`.
- [ ] **H-VERCEL (Phase 8)** — Vercel project rooted at `app/frontend`, attach domain cloudaitrader.com (+ www redirect), paste production env set.
- [ ] **H-DNS (Phase 8)** — Cloudflare DNS for cloudaitrader.com: apex + www → Vercel per Vercel's instructions; `backend.cloudaitrader.com` is created automatically by the named tunnel route; leave `worker.cloudaitrader.com` unallocated (reserved, PLAN.md D5).
- [ ] **H-TUNNEL (Phase 8)** — Cloudflare named tunnel `cloudaitrader-backend` (dashboard: Zero Trust → Networks → Tunnels), public hostname `backend.cloudaitrader.com` → `http://backend:4000`, copy token → `BACKEND_TUNNEL_TOKEN` on the Pi.
- [ ] **H-PI (Phase 8)** — Pick the eg-server-N Pi for the stack (prefer SSD-boot, least loaded; check with the eg-pi-ops runbook). Confirm Docker + buildx present. No reboots without checking what else runs there.

## Product decisions (data, not code — change anytime)

- [ ] **H-PRICE-1** — Confirm pricing/quota placeholders (A2): free = 10 backtests/mo, 180-day window, 1h/1d timeframes, non-premium rulesets; paid = $29/mo fair-use. Stored in `tier_limits`; adjust there.
- [ ] **H-RULES-1** — Verify the four seeded Firm Rulesets (HyroTrader, Breakout, Crypto Fund Trader, FTMO-crypto) against each firm's CURRENT published rules before launch; seeds carry `estimate=true` flags where I could not verify numbers. Update `verified_at` when checked. This is the product's credibility surface.
- [ ] **H-CI-1 (Phase 9)** — GitHub branch protection on `main` (require CI green); decide if `ai` merges via PR.

## Launch/positioning (from docs/competitor-analysis.md)

- [ ] Marketing language review: never promise Challenge outcomes ("pass your challenge") — regulatory posture; show ruleset provenance and `verified_at` prominently.
- [ ] PropFirmMatch listing/affiliate outreach once the demo is live (their ~4M monthly views is the distribution channel).
- [ ] Decide on a re-verify cadence for competitor pricing/rules (competitor analysis is dated 2026-07-17; 30-day staleness rule).
