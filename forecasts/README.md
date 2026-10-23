# Forecasts

One file per forecast, named after its id (`FEL-YYYY-NNNN.yaml`). Start from `_TEMPLATE.yaml`.

Once a file is merged, its question, rule, source, date, threshold, probability and the three
voices are locked. Evidence may be appended; the status moves once, from `open` to a final
state, with its resolution. Files are never deleted. A changed view is a new file whose
`supersedes` field names the old one. The full rules are in [`METHOD.md`](../METHOD.md).

Licence: CC BY 4.0 (see [`LICENSE-DATA.md`](../LICENSE-DATA.md)).
