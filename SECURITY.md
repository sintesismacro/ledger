# Security policy

## Reporting a vulnerability or a leaked credential

Do not open a public issue. Email **<office@sintesismacro.com>** with the subject
line `SECURITY` and include:

- the repository and commit or version affected;
- what you found and how to reproduce it;
- whether the finding is already public.

You will receive an acknowledgement within three working days. Please allow a
reasonable period for a fix before any public disclosure.

## What we treat as a security issue

- Any credential, token, private key or broker configuration committed to a
  repository, in any branch or in history.
- Any path by which code in this repository could place an order, move funds or
  change a risk limit without the gates described in the documentation.
- Dependency vulnerabilities with a plausible exploit path in our use.

## Rules we apply to ourselves

- Secrets live in environment variables or a secrets manager, never in the
  repository. `.gitignore` blocks the common cases; `gitleaks` scans every push.
- Raw market-data snapshots are not committed; they are stored outside git.
- Two-factor authentication is required for every account with write access.
- `main` is protected: pull request, one approving review from a code owner,
  passing CI, linear history, no force-push.

<sub>Prepared 22 October 2026 · Revised 22 October 2026</sub>
