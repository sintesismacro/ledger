"""The editorial perimeter (SINTESIS-PLAN-05 § 6): words and names that never appear in public files.

The deny-list lives in ``editorial/denylist.txt`` and is maintained by the owner.
"""

from __future__ import annotations

import re
from pathlib import Path

SCANNED_GLOBS = (
    "forecasts/*.yaml",
    "atlas/*.yaml",
    "atlas/*.md",
    "letters/*.md",
    "README.md",
    "METHOD.md",
    "GUILD.md",
)


def load_terms(root: Path) -> list[str]:
    path = root / "editorial" / "denylist.txt"
    if not path.exists():
        return []
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            terms.append(line)
    return terms


def _pattern(term: str) -> re.Pattern[str]:
    words = [re.escape(w) for w in term.split()]
    return re.compile(r"(?<![\w-])" + r"[\s-]+".join(words) + r"(?![\w-])", re.IGNORECASE)


def scan(root: Path) -> list[str]:
    """Return 'file:line: term' for every deny-listed term found in a public file."""
    terms = load_terms(root)
    patterns = [(t, _pattern(t)) for t in terms]
    hits: list[str] = []
    for glob in SCANNED_GLOBS:
        for path in sorted(root.glob(glob)):
            if path.name.startswith("_"):
                continue
            for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                for term, pat in patterns:
                    if pat.search(line):
                        hits.append(f"{path.relative_to(root)}:{no}: '{term}'")
    return hits
