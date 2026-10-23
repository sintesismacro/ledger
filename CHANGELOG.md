# Changelog

All notable changes to this repository are recorded here, newest first.
Format: `## vMAJOR.MINOR.PATCH — YYYY-MM-DD`, then **Changed**, **Affects**, **Re-check**.

## v0.1.1 — 2026-10-23

**Changed** — Merge method set to rebase only; CONTRIBUTING.md states it and drops the
code-owner approval that the `main` rule does not require.
**Affects** — How every pull request is merged; probability authorship on `main`.
**Re-check** — After the first forecast merge, `git blame` the `probability:` line on `main` and
confirm the author is the registered forecaster e-mail.

## v0.1.0 — 2026-10-23

**Changed** — Ledger published: METHOD v1.0, forecast template, Atlas layers, validation
(schema, editorial perimeter, no-backfill, probability ownership), scoring, SVG renders,
qualified-timestamp client and CI.
**Affects** — Everything; no forecast exists yet.
**Re-check** — First publish run creates the `evidence` branch and the scorecard.
