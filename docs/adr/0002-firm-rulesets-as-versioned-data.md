---
status: accepted
date: 2026-07-17
---

# Firm Rulesets are versioned data, not code

Prop firm Challenge rules change frequently (rulebook churn is the top product risk in docs/competitor-analysis.md). Firm Rulesets live in Postgres as dated, versioned configuration rows interpreted by one generic evaluator built from composable rule primitives (profit target, daily drawdown, max drawdown, minimum trading days, stop-loss discipline, consistency). Adding a firm or correcting a rule is a data change with provenance (source URL, verified date), not a deploy.

## Considered Options

Hardcoded per-firm evaluator classes were rejected: every firm rule change would demand a code release, maintenance would eat the product, and stale rules destroy the product's core trust promise.

## Consequences

- The evaluator's rule-primitive vocabulary is the real extension surface; a rule that cannot be expressed as a primitive forces an evaluator release.
- Ruleset provenance fields are first-class and shown to users.
- Admin surface needs Ruleset CRUD with versioning (never in-place edits of a published version).
