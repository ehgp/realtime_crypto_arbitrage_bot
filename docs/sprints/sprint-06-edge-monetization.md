---
date: 2026-07-17
description: Phase 6 guide. Turnstile contact form, Resend notifications, Stripe Payment Link + webhook flipping the Entitlement, quota counters, Vercel Analytics.
tags:
  - sprints
  - cloudaitrader
---

# Sprint Guide 06 — Edge Services & Monetization (Phase 6)

**Preconditions**: Phase 5 gate green; human has Stripe/Resend/Turnstile accounts (human-todo H-PAY, H-EMAIL, H-EDGE).
**Phase exit gate**: contact form delivers via Resend behind Turnstile; `stripe trigger checkout.session.completed` flips `entitlements.is_paid` and the worker accepts a previously-refused premium job; free-tier quota enforced.

## Sprint 6.1 — Contact form

- `app/frontend/app/api/contact/route.ts` (local route, NOT proxied): parse name/email/message + turnstile token; verify `https://challenges.cloudflare.com/turnstile/v0/siteverify` with `secret`, `response`, `remoteip` (from `x-forwarded-for` first hop); on success send via Resend to `ADMIN_NOTIFICATION_EMAIL` (from `noreply@cloudaitrader.com` once domain verified — H-EMAIL); dev fallback: console log when `RESEND_API_KEY` empty.
- Page `app/[locale]/contact/` with `@marsidev/react-turnstile` widget (`NEXT_PUBLIC_TURNSTILE_SITE_KEY`).
- Rate limit: 5/min/IP in-route (simple LRU) — full tiered limiting in Sprint 9.2.

## Sprint 6.2 — Notifications (outbox per PLAN.md D7)

- `src/services/email.js`: Resend wrapper, console fallback in dev, template functions (plain HTML, brand tokens).
- Backtest-complete email: the Backtester wrote an `app.job_events` row inside its finalization txn; the App Worker notifier (30s interval, servicePool) CLAIMS events with a lease (`UPDATE ... SET claimed_at=now(), lease_expires_at=now()+'2 min' WHERE id IN (SELECT id FROM app.job_events WHERE sent_at IS NULL AND (claimed_at IS NULL OR lease_expires_at < now()) LIMIT 10 FOR UPDATE SKIP LOCKED) RETURNING *`), joins prefs, sends via Resend with **idempotency key = job_event.id** (provider-side dedupe makes crash-between-send-and-stamp duplicates inert), stamps `sent_at`; failures increment `attempts` + `last_error` and the lease expiry retries them.
- Admin alert: first-login signup notification to `ADMIN_NOTIFICATION_EMAIL` (fire-and-forget).

## Sprint 6.3 — Stripe + quotas (PLAN.md D13)

- **Server-created Checkout Sessions** (no Payment Links): `POST /billing/checkout` (require-auth) creates a Session for `STRIPE_PRICE_ID` with `metadata.user_id = sub` + `metadata.incarnation`, locked customer email; returns the session URL. Settings "Upgrade" button hits this endpoint.
- Webhook `POST /stripe/webhook` mounted with `express.raw` BEFORE `express.json()` (I7); verify signature; FIRST insert into `app.stripe_events` (`ON CONFLICT (event_id) DO NOTHING` — a conflict means replay: stop). Then:
  - `checkout.session.completed` → bind customer/subscription ids to the user (metadata.user_id + incarnation; unmatched or tombstoned mapping → archive no-op + admin alert; NEVER activates by itself).
  - `customer.subscription.*` → reconcile `entitlements.status` from the FULL embedded subscription object, guarded by per-subscription `last_event_created`; on equal/ambiguous ordering fetch the live Subscription from the Stripe API before committing.
  - `charge.refunded` (latest invoice) → revoke (status `canceled`) + enqueue `app.billing_actions` cancel (retries, alert after 3 failures); `charge.dispute.created` → status `suspended` + alert. **Overrides never auto-clear** — admin resolution only.
- Billing portal: `POST /billing/portal` (require-auth) → portal session for the stored customer id.
- `billing_actions` sweep: 15-min interval draining unresolved actions (shared with D15 deletion severance).
- Quotas: `tier_limits` seed (migration `008_tiers.sql`): free = `{backtests_per_month:10, max_candles_per_job:50000, timeframes:['1h','1d'], max_active_jobs:2, premium_rulesets:false}`; paid = `{backtests_per_month:200, max_candles_per_job:1000000, timeframes:['1m','1h','1d'], max_active_jobs:10, premium_rulesets:true}` (A2 placeholders — H-PRICE-1; values are DATA). The transactional reservation + advisory-lock concurrency check live in the submit path (Sprint 5.1); settings page shows the usage meter.

## Sprint 6.4 — Analytics

- `@vercel/analytics` `<Analytics/>` in root layout; production-only. No GTM in MVP (privacy-lean default; add only on human request).

## Acceptance (phase)

- Contact: missing/invalid Turnstile token → 400; valid → Resend dashboard shows delivery (or dev console line).
- `stripe listen --forward-to localhost:4000/stripe/webhook` + triggered flow: checkout completes → binds ids only; `customer.subscription.created(active)` → status active; premium submit accepted; worker honors on next claim. Replayed event id → no-op (stripe_events conflict). Out-of-order pair → converges to subscription-object truth. `charge.refunded` without cancel → revoked + billing_action enqueued. Subscription cancel → next premium submit 402/upgrade hint.
- 11th free-tier Backtest in a month → 402 QUOTA_EXCEEDED; two concurrent submissions at quota-1 → exactly one accepted; at active-job cap → rejected until a job reaches terminal status.
- Raw-body proof: tampered payload → 400 signature error; verified event ids logged.
- Outbox: kill the notifier between send and stamp → restart resends with the same idempotency key → exactly one visible email.
