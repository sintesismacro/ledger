"""Probability ownership: only the named forecaster may write a forecast's probability.

The check reads ``git blame`` for the ``probability:`` line of every forecast changed on the
branch and compares the commit author's e-mail with ``editorial/forecasters.yaml``. It fails
closed: a forecaster with no registered e-mail cannot merge a probability.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from .model import parse


def load_forecasters(root: Path) -> dict[str, set[str]]:
    path = root / "editorial" / "forecasters.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, set[str]] = {}
    for handle, info in (data.get("forecasters") or {}).items():
        emails = (info or {}).get("emails") or []
        out[str(handle)] = {e.strip().lower() for e in emails if isinstance(e, str) and e.strip()}
    return out


def _changed(root: Path, base_ref: str) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=AM", f"{base_ref}...HEAD", "--", "forecasts/"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [p for p in out.splitlines() if p.endswith(".yaml") and not Path(p).name.startswith("_")]


def _probability_author(root: Path, rel: str) -> str | None:
    lines = (root / rel).read_text(encoding="utf-8").splitlines()
    for no, line in enumerate(lines, start=1):
        if line.lstrip().startswith("probability:"):
            blame = subprocess.run(
                ["git", "blame", "--porcelain", "-L", f"{no},{no}", "HEAD", "--", rel],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            for b in blame.splitlines():
                if b.startswith("author-mail "):
                    return b.split(" ", 1)[1].strip().strip("<>").lower()
    return None


def check(root: Path, base_ref: str) -> dict[str, list[str]]:
    registry = load_forecasters(root)
    problems: dict[str, list[str]] = {}
    for rel in _changed(root, base_ref):
        data = parse((root / rel).read_text(encoding="utf-8"))
        handle = str(data.get("forecaster", ""))
        allowed = registry.get(handle, set())
        if not allowed:
            problems[rel] = [f"forecaster '{handle}' has no registered e-mail in editorial/forecasters.yaml"]
            continue
        author = _probability_author(root, rel)
        if author is None:
            problems[rel] = ["no 'probability:' line found"]
        elif author not in allowed:
            problems[rel] = [f"probability line was written by <{author}>, not by forecaster '{handle}'"]
    return problems
