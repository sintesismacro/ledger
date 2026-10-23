"""Command line: python -m ledger {validate,publish,commitment} ...

validate [--base REF]   schema, editorial perimeter; with --base also the no-backfill rule
                        and probability ownership for the changes on this branch
publish  --out DIR      scorecard.json, scorecard.svg, calibration.svg, atlas.svg, and
                        qualified timestamps for new commitments when TSA_URL is set
commitment FILE         print the canonical commitment a receipt proves (for verification)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import editorial, immutability, owners
from .model import load_all, load_atlas, parse
from .render import atlas_svg, calibration_svg, scorecard_svg
from .score import atlas_state, scorecard
from .stamp import commitment, stamp_all


def cmd_validate(root: Path, base: str | None) -> int:
    failed = False
    for f in load_all(root):
        for e in f.errors:
            print(f"SCHEMA     {f.path.relative_to(root)}: {e}")
            failed = True
    for hit in editorial.scan(root):
        print(f"EDITORIAL  {hit} is outside the PLAN-05 perimeter")
        failed = True
    if base:
        for rel, errs in immutability.check_against(root, base).items():
            for e in errs:
                print(f"NO-BACKFILL {rel}: {e}")
                failed = True
        for rel, errs in owners.check(root, base).items():
            for e in errs:
                print(f"OWNERSHIP  {rel}: {e}")
                failed = True
    print("FAIL" if failed else "OK")
    return 1 if failed else 0


def cmd_publish(root: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    forecasts = load_all(root)
    card = scorecard(forecasts)
    manifest = stamp_all(forecasts, out)
    stamped = sum(1 for f in forecasts if not f.errors and f.id in manifest)
    (out / "scorecard.json").write_text(json.dumps(card, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "scorecard.svg").write_text(scorecard_svg(card, stamped), encoding="utf-8")
    (out / "calibration.svg").write_text(calibration_svg(card), encoding="utf-8")
    rows = atlas_state(forecasts, load_atlas(root))
    (out / "atlas.svg").write_text(atlas_svg(rows, card["as_of"]), encoding="utf-8")
    o = card["overall"]
    print(
        f"published: {o['forecasts']} forecasts, {o['resolved']} resolved, "
        f"{stamped} stamped, as of {card['as_of']}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ledger")
    ap.add_argument("--root", type=Path, default=Path.cwd())
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--base", default=None)
    p = sub.add_parser("publish")
    p.add_argument("--out", type=Path, required=True)
    c = sub.add_parser("commitment")
    c.add_argument("file", type=Path)
    a = ap.parse_args(argv)
    root = a.root.resolve()
    if a.cmd == "validate":
        return cmd_validate(root, a.base)
    if a.cmd == "publish":
        return cmd_publish(root, a.out.resolve())
    if a.cmd == "commitment":
        sys.stdout.buffer.write(commitment(parse(a.file.read_text(encoding="utf-8"))))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
