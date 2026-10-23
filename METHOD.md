# Method

How the SINTESIS Forward Evidence Ledger works. Every rule below is written before the first
forecast and changes only by a dated, versioned amendment at the end of this file.

Version 1.0 · Prepared 22 October 2026 · Licence: CC BY 4.0

## 1. What a forecast is

A binary question about a public, observable indicator. Each question has:

- a resolution date and a named source;
- a written rule that decides YES or NO;
- a probability set by its forecaster;
- two voices: **Becoming** (the case that the physical body of intelligence keeps extending, after
  Spinoza) and **Returning** (the case that necessity is removed and the build-out exhausts itself,
  after Mainländer);
- a short **synthesis** explaining where the probability sits between the two voices.

The `stance` field records which voice a YES outcome supports. The Atlas reads it.

## 2. What is never forecast here

- No named company, security or issuer, and no statement that suggests buying, selling or holding
  anything. Questions concern factors, methods, regimes and physical indicators only.
- No performance figures of any portfolio.

A deny-list in `editorial/denylist.txt` enforces this on every pull request. Nothing here is
investment advice.

## 3. Who sets the probability

Only the named forecaster. Agents may draft the question, rule, source, threshold and both voices,
and they append evidence. The `probability:` line must be written in a commit by an e-mail
registered to the forecaster in `editorial/forecasters.yaml`. CI checks this with `git blame` and
fails closed. Probabilities lie between 0.03 and 0.97, so that no single forecast can dominate a score.

## 4. No backfill

Once merged, these fields are locked:

- `id`, `domain`, `forecaster`, `question`, `stance`;
- `resolution_source`, `resolution_rule`, `resolves_on`, `threshold`, `probability`;
- `becoming`, `returning`, `synthesis`;
- `supersedes`, `self_resolved`.

`evidence` and `atlas_nodes` may only grow. The status moves once, from `open` to `resolved-yes`,
`resolved-no` or `annulled`, and the resolution is written once with it. Files are never deleted or
renamed. A changed view is a **new** forecast whose `supersedes` names the old one. The old one
stays and is scored. CI enforces all of this against the main branch.

## 5. Proof of time

Git dates are set by whoever commits and prove nothing. Each merged forecast's **commitment** is
timestamped instead: the canonical JSON of its locked fields (`python -m ledger commitment FILE`).
The timestamp comes from a qualified time-stamping authority under eIDAS (Regulation (EU)
No 910/2014, Art. 41–42), following RFC 3161.

Receipts are kept on the `evidence` branch under `receipts/` and are never overwritten. To verify one:

```bash
python -m ledger commitment forecasts/FEL-YYYY-NNNN.yaml > c.json
openssl ts -verify -data c.json -in receipts/FEL-YYYY-NNNN.tsr -CAfile <TSA chain>
```

Because the commitment covers only locked fields, evidence and resolutions can be added later
without disturbing what was proved.

## 6. Scoring

- **Brier score** (Brier, 1950): the mean of (p − o)², where o is 1 for YES and 0 for NO. A score
  of 0 is perfect, and 0.25 is what a permanent 50% earns.
- **Skill** against that baseline: 1 − Brier / 0.25. Above zero beats a coin.
- **Log score**: the mean natural log of the probability given to what happened. Closer to zero is
  better.
- **Calibration**: forecasts are grouped in ten probability bins, each showing its mean forecast
  against the observed frequency. Shown once 10 forecasts have resolved.

Scores are reported overall, by domain and by forecaster. Annulled forecasts are not scored.
Misses are never removed.

## 7. Resolution and annulment

A forecast resolves on the first print of its named source on or after `resolves_on`, read under
its own rule. Later revisions to the printed value do not reopen it, unless the rule says
otherwise. It is **annulled** only if the named source stops publishing, or changes the
definition of the measured series, before resolution. The annulment is recorded with a source
link and is shown on the scorecard.

## 8. Self-resolved questions

Questions resolved by SINTESIS's own replication work carry `self_resolved: true`. The rule that
selects what is replicated is fixed in the question before any replication is run.

## 9. Amendments

None.
