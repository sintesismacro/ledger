# Contributing

This repository is maintained by SINTESIS UG. External contributions are
accepted by invitation; open an issue first if you want to propose one.

## Branching

- `main` is the only long-lived branch and is always releasable.
- Work on short-lived branches named `type/short-description`, where `type` is
  one of `feat`, `fix`, `refactor`, `docs`, `ci`.
- Merge by pull request only, after green CI, using rebase merging. Rebase keeps
  every commit's author, so `git blame` on `main` still shows who wrote each
  `probability:` line (METHOD.md § 3). Squash and merge commits are disabled.
- No force-pushes or deletions on `main` or `evidence`; administrators are bound
  by the same rules.

## Commits

Conventional Commits, in the imperative:

```text
feat(risk-ticket): add stress replay for March 2020 window
fix(macro-brief): correct VIX state threshold
docs: expand abbreviations on first use
```

Keep each commit to one change. Reference the issue or record it serves.

## Code

- Python 3.12. `ruff check` and `ruff format` must pass; CI enforces both.
- Tests live in `tests/` and run with `pytest`. A behaviour change without a
  test needs a reason in the pull request.
- Every figure, threshold or rule in code or documentation carries its source:
  the file and section it comes from, or the calculation that produced it.

## Documents

- Markdown is the record format. Word and PDF are rendered outputs, not
  sources of truth.
- Dates are absolute: `2026-10-22` in filenames and front matter,
  `22 October 2026` in prose. Never "today", "currently" or "recently".
- After editing a document, re-read every date in it and correct the ones the
  edit made untrue.
- British English: organisation, recognised, analyse.

## Releases

- Semantic versioning. Tags `vMAJOR.MINOR.PATCH`, annotated, signed where
  possible.
- Every release has a short changelog entry: what changed, what it affects,
  what to re-check.

## Never commit

Credentials, tokens, private keys, broker configuration, raw market-data
snapshots, or anything that would let code place an order without the gates
described in the documentation. See `SECURITY.md`.
