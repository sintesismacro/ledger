"""Scoring: Brier score, skill against a permanent 50%, log score and calibration.

Brier (1950): mean of (p - o)^2 over resolved binary forecasts, o in {0, 1}.
A forecaster who always says 50% scores 0.25, so skill = 1 - Brier / 0.25.
Annulled forecasts are excluded. Nothing here sets or alters a probability.
"""

from __future__ import annotations

import datetime as dt
import math
from collections import defaultdict
from typing import Any

from .model import Forecast, as_date

BASELINE_BRIER = 0.25
CALIBRATION_MIN_RESOLVED = 10
BINS = 10


def brier(pairs: list[tuple[float, int]]) -> float | None:
    if not pairs:
        return None
    return sum((p - o) ** 2 for p, o in pairs) / len(pairs)


def log_score(pairs: list[tuple[float, int]]) -> float | None:
    """Mean natural-log probability assigned to what happened (closer to 0 is better)."""
    if not pairs:
        return None
    return sum(math.log(p if o == 1 else 1.0 - p) for p, o in pairs) / len(pairs)


def skill(b: float | None) -> float | None:
    return None if b is None else 1.0 - b / BASELINE_BRIER


def calibration(pairs: list[tuple[float, int]], bins: int = BINS) -> list[dict[str, Any]]:
    buckets: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for p, o in pairs:
        buckets[min(int(p * bins), bins - 1)].append((p, o))
    out = []
    for k in range(bins):
        items = buckets.get(k, [])
        out.append(
            {
                "bin": [k / bins, (k + 1) / bins],
                "n": len(items),
                "mean_forecast": (sum(p for p, _ in items) / len(items)) if items else None,
                "observed_rate": (sum(o for _, o in items) / len(items)) if items else None,
            }
        )
    return out


def _block(forecasts: list[Forecast], today: dt.date) -> dict[str, Any]:
    pairs = [(f.probability, f.outcome) for f in forecasts if f.outcome is not None]
    open_ = [f for f in forecasts if f.status == "open"]
    overdue = [f for f in open_ if (as_date(f.data.get("resolves_on")) or today) < today]
    upcoming = sorted(as_date(f.data.get("resolves_on")) for f in open_ if as_date(f.data.get("resolves_on")))
    b = brier(pairs)
    return {
        "forecasts": len(forecasts),
        "open": len(open_),
        "resolved": len(pairs),
        "annulled": sum(1 for f in forecasts if f.status == "annulled"),
        "overdue": len(overdue),
        "next_resolution": upcoming[0].isoformat() if upcoming else None,
        "brier": b,
        "skill_vs_50pct": skill(b),
        "log_score": log_score(pairs),
        "calibration": calibration(pairs) if len(pairs) >= CALIBRATION_MIN_RESOLVED else None,
    }


def scorecard(forecasts: list[Forecast], today: dt.date | None = None) -> dict[str, Any]:
    today = today or dt.datetime.now(dt.UTC).date()
    valid = [f for f in forecasts if not f.errors]
    by_domain: dict[str, list[Forecast]] = defaultdict(list)
    by_forecaster: dict[str, list[Forecast]] = defaultdict(list)
    for f in valid:
        by_domain[str(f.data["domain"])].append(f)
        by_forecaster[str(f.data["forecaster"])].append(f)
    return {
        "as_of": today.isoformat(),
        "baseline_brier": BASELINE_BRIER,
        "calibration_min_resolved": CALIBRATION_MIN_RESOLVED,
        "overall": _block(valid, today),
        "by_domain": {k: _block(v, today) for k, v in sorted(by_domain.items())},
        "by_forecaster": {k: _block(v, today) for k, v in sorted(by_forecaster.items())},
        "invalid_files": sorted(str(f.path.name) for f in forecasts if f.errors),
    }


def atlas_state(forecasts: list[Forecast], nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per node: mean probability of linked open forecasts whose YES favours each voice."""
    out = []
    for node in nodes:
        linked = [
            f
            for f in forecasts
            if not f.errors and f.status == "open" and node["id"] in (f.data.get("atlas_nodes") or [])
        ]
        row: dict[str, Any] = {"id": node["id"], "label": node.get("label", node["id"])}
        row["phase"] = node.get("phase", "")
        for stance in ("becoming", "returning"):
            ps = [f.probability for f in linked if f.data.get("stance") == stance]
            row[stance] = (sum(ps) / len(ps)) if ps else None
            row[f"{stance}_n"] = len(ps)
        out.append(row)
    return out
