---
version: alpha
name: Realtime Crypto Arbitrage Bot
description: One-line description of the visual identity. Replace this.
colors:
  # Required-ish: include `primary` to silence the `missing-primary` warning.
  primary: "#1A1C1E"
  secondary: "#6C7278"
  tertiary: "#B8422E"
  neutral: "#F7F5F2"

  # Surface scale (Material-ish). Drop what you don't need.
  surface: "#FFFFFF"
  surface-container: "#F5F2EF"
  on-surface: "#1A1C1E"
  on-primary: "#FFFFFF"

  # Status colors.
  error: "#BA1A1A"
  warning: "#A06800"
  success: "#1F6E2E"

typography:
  # Display / headings.
  display:
    fontFamily: Public Sans
    fontSize: 3.5rem
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: -0.02em
  h1:
    fontFamily: Public Sans
    fontSize: 3rem
    fontWeight: 600
    lineHeight: 1.1
  h2:
    fontFamily: Public Sans
    fontSize: 2.25rem
    fontWeight: 600
  body:
    fontFamily: Public Sans
    fontSize: 1rem
    lineHeight: 1.5
  body-sm:
    fontFamily: Public Sans
    fontSize: 0.875rem
    lineHeight: 1.45
  label:
    fontFamily: Space Grotesk
    fontSize: 0.75rem
    fontWeight: 500
    letterSpacing: 0.04em
    textTransform: uppercase

rounded:
  sm: 4px
  md: 8px
  lg: 12px
  xl: 24px
  full: 9999px

spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px

components:
  button:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 12px

  button-hover:
    backgroundColor: "{colors.tertiary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 12px

  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: 24px

  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: 12px
---

## Overview

REPLACE: Two or three sentences capturing the design intent. Name the
metaphor (e.g., "Architectural Minimalism meets Journalistic Gravitas"),
the audience, and the emotional register the product is trying to hit.

## Colors

REPLACE: Describe the palette philosophy. Why these neutrals? What does
each accent communicate? When to deploy the warning / error / success
trio. Reference tokens by name (`primary`, `tertiary`) so prose stays
synced with the YAML above.

## Typography

REPLACE: Pairing rationale (e.g., a humanist sans for body, a geometric
sans for labels). Hierarchy rules. Maximum line length. When italics are
permitted.

## Layout

REPLACE: Grid model (fluid vs. fixed-max-width), breakpoint set, gutter
and margin behavior. Whether the system uses an 8-pt rhythm or a custom
modular scale.

## Elevation & Depth

REPLACE: How depth is conveyed — shadows, tonal layers, borders, or
nothing at all (flat by intent). If shadows are used, describe spread,
blur, and color philosophy.

## Shapes

REPLACE: Corner-radius personality (sharp / soft / mixed). Whether
buttons and cards share the same radius or diverge. Any non-rectangular
shapes the brand reaches for (pills, capsules, organic blobs).

## Components

REPLACE: For each component above, write a paragraph on how it should
*feel* in use, what states it supports, and what it must never do.

## Do's and Don'ts

- Do: REPLACE with a concrete invariant (e.g., "Always pair `display`
  with generous whitespace — at least 64px above and 32px below.").
- Do: REPLACE.
- Don't: REPLACE with a concrete failure mode you've seen agents commit
  (e.g., "Never substitute `tertiary` for `primary` in CTAs — it reads
  as a warning state in this palette.").
- Don't: REPLACE.
