# Changelog

All notable changes to this repository are recorded here, newest first.
Format: `## vMAJOR.MINOR.PATCH — YYYY-MM-DD`, then **Changed**, **Affects**, **Re-check**.

## v0.1.3 — 2026-10-24

**Changed** — Letter 0 published (`letters/2026-10-letter-0.md`). `GUILD.md` rewritten for the
owner's decision of 24 October 2026: an open Arena that opens with the first questions, and a
Guild wall that collects forecasters after ten resolved forecasts.
**Affects** — Public text only; no rule in `METHOD.md` changes.
**Re-check** — Contributor terms must be cleared by counsel and published here before the Arena
opens.

## v0.1.2 — 2026-10-23

**Changed** — Scorecard, calibration chart and Atlas redrawn in the SINTESIS identity of
`Sintesis Brand.pdf` and the website tokens: Ink ground, Paper subject, grey context, one Cadmium
point, 2px rules, square corners, Archivo 800 and IBM Plex Mono embedded under the SIL Open Font
License 1.1. Replaces the stand-in palette of v0.1.0.
**Affects** — The three SVGs on the `evidence` branch and every page that embeds them.
**Re-check** — After merge, the publish run redraws the SVGs; confirm they render on the
organisation page, this README and the personal profile.

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
