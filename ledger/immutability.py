"""The no-backfill rule: what may change in a forecast once it is on the main branch.

Locked fields never change. Evidence and atlas links may only grow. Status may move once,
from open to a final state, and the resolution block is written once with it.
Forecast files are never deleted or renamed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .model import FINAL_STATUSES, parse

LOCKED = (
    "id",
    "domain",
    "forecaster",
    "question",
    "stance",
    "resolution_source",
    "resolution_rule",
    "resolves_on",
    "threshold",
    "probability",
    "becoming",
    "returning",
    "synthesis",
    "supersedes",
    "self_resolved",
)
APPEND_ONLY = ("evidence", "atlas_nodes")


def compare(base: dict[str, Any], head: dict[str, Any]) -> list[str]:
    """Return violations of the no-backfill rule between the merged and proposed versions."""
    err: list[str] = []
    for key in LOCKED:
        if base.get(key) != head.get(key):
            err.append(f"'{key}' is locked once merged (was {base.get(key)!r})")
    for key in APPEND_ONLY:
        old = base.get(key) or []
        new = head.get(key) or []
        if new[: len(old)] != old:
            err.append(f"'{key}' is append-only: existing entries may not change or be removed")
    b_status, h_status = base.get("status"), head.get("status")
    if b_status in FINAL_STATUSES:
        if h_status != b_status or base.get("resolution") != head.get("resolution"):
            err.append(f"status '{b_status}' is final; it and its resolution cannot change")
    elif b_status == "open" and h_status not in ("open", *FINAL_STATUSES):
        err.append(f"invalid status change {b_status!r} -> {h_status!r}")
    return err


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def check_against(root: Path, base_ref: str) -> dict[str, list[str]]:
    """Compare every forecast on ``base_ref`` with the working tree."""
    problems: dict[str, list[str]] = {}
    listed = _git(root, "ls-tree", "-r", "--name-only", base_ref, "--", "forecasts/")
    for rel in listed.splitlines():
        if not rel.endswith(".yaml") or Path(rel).name.startswith("_"):
            continue
        head_path = root / rel
        if not head_path.exists():
            problems[rel] = ["forecast files are never deleted or renamed"]
            continue
        base = parse(_git(root, "show", f"{base_ref}:{rel}"))
        head = parse(head_path.read_text(encoding="utf-8"))
        errs = compare(base, head)
        if errs:
            problems[rel] = errs
    return problems
