"""Forecast files: loading and schema validation.

A forecast is one YAML file in ``forecasts/`` named ``<id>.yaml``. Files whose name
starts with an underscore (templates) are ignored.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DOMAINS = ("physical-ai-power", "ai-finance-replication")
STANCES = ("becoming", "returning")
STATUSES = ("open", "resolved-yes", "resolved-no", "annulled")
FINAL_STATUSES = ("resolved-yes", "resolved-no", "annulled")
P_MIN, P_MAX = 0.03, 0.97
ID_RE = re.compile(r"^FEL-\d{4}-\d{4}$")
HANDLE_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")

REQUIRED = (
    "id",
    "domain",
    "forecaster",
    "question",
    "stance",
    "resolution_source",
    "resolution_rule",
    "resolves_on",
    "probability",
    "becoming",
    "returning",
    "synthesis",
    "status",
)
OPTIONAL = ("threshold", "evidence", "resolution", "supersedes", "self_resolved", "atlas_nodes")
TEXT_FIELDS = ("question", "resolution_source", "resolution_rule", "becoming", "returning", "synthesis")


@dataclass
class Forecast:
    path: Path
    data: dict[str, Any]
    errors: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return str(self.data.get("id", self.path.stem))

    @property
    def status(self) -> str:
        return str(self.data.get("status", ""))

    @property
    def probability(self) -> float | None:
        p = self.data.get("probability")
        return float(p) if isinstance(p, (int, float)) and not isinstance(p, bool) else None

    @property
    def outcome(self) -> int | None:
        return {"resolved-yes": 1, "resolved-no": 0}.get(self.status)


def as_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def parse(text: str) -> dict[str, Any]:
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("file is not a YAML mapping")
    return data


def validate(data: dict[str, Any], path: Path, atlas_ids: set[str] | None = None) -> list[str]:
    """Return a list of human-readable schema errors (empty when valid)."""
    err: list[str] = []
    for key in REQUIRED:
        if key not in data:
            err.append(f"missing field '{key}'")
    unknown = set(data) - set(REQUIRED) - set(OPTIONAL)
    if unknown:
        err.append(f"unknown field(s): {', '.join(sorted(unknown))}")

    fid = data.get("id")
    if not isinstance(fid, str) or not ID_RE.match(fid):
        err.append("id must look like FEL-YYYY-NNNN")
    elif fid != path.stem:
        err.append(f"id '{fid}' does not match file name '{path.name}'")

    if data.get("domain") not in DOMAINS:
        err.append(f"domain must be one of {', '.join(DOMAINS)}")
    if data.get("stance") not in STANCES:
        err.append("stance must be 'becoming' or 'returning' (the voice a YES outcome supports)")
    handle = data.get("forecaster")
    if not isinstance(handle, str) or not HANDLE_RE.match(handle):
        err.append("forecaster must be a GitHub handle")

    for key in TEXT_FIELDS:
        value = data.get(key)
        if key in data and (not isinstance(value, str) or len(value.strip()) < 10):
            err.append(f"'{key}' must be text of at least 10 characters")
    q = data.get("question")
    if isinstance(q, str) and not q.strip().endswith("?"):
        err.append("question must end with a question mark")

    if "resolves_on" in data and as_date(data.get("resolves_on")) is None:
        err.append("resolves_on must be a date (YYYY-MM-DD)")

    p = data.get("probability")
    if p is None:
        err.append("probability is not set: the forecaster sets it before merge, never an agent")
    elif isinstance(p, bool) or not isinstance(p, (int, float)):
        err.append("probability must be a number")
    elif not (P_MIN <= float(p) <= P_MAX):
        err.append(f"probability must lie between {P_MIN} and {P_MAX}")

    status = data.get("status")
    if status not in STATUSES:
        err.append(f"status must be one of {', '.join(STATUSES)}")
    res = data.get("resolution")
    if status in FINAL_STATUSES:
        if not isinstance(res, dict):
            err.append("a resolved or annulled forecast needs a 'resolution' block")
        else:
            if as_date(res.get("resolved_on")) is None:
                err.append("resolution.resolved_on must be a date")
            for key in ("value", "source_url"):
                if not isinstance(res.get(key), str) or not res.get(key).strip():
                    err.append(f"resolution.{key} is required")
    elif res not in (None, {}):
        err.append("an open forecast must not carry a 'resolution' block")

    evidence = data.get("evidence", [])
    if evidence is None:
        evidence = []
    if not isinstance(evidence, list):
        err.append("evidence must be a list")
    else:
        for i, item in enumerate(evidence):
            if not isinstance(item, dict) or as_date(item.get("date")) is None or not item.get("url"):
                err.append(f"evidence[{i}] needs a date and a url")

    sup = data.get("supersedes")
    if sup is not None and (not isinstance(sup, str) or not ID_RE.match(sup)):
        err.append("supersedes must be a forecast id")
    if "self_resolved" in data and not isinstance(data["self_resolved"], bool):
        err.append("self_resolved must be true or false")

    nodes = data.get("atlas_nodes", [])
    if nodes is None:
        nodes = []
    if not isinstance(nodes, list) or not all(isinstance(n, str) for n in nodes):
        err.append("atlas_nodes must be a list of node ids")
    elif atlas_ids is not None:
        missing = [n for n in nodes if n not in atlas_ids]
        if missing:
            err.append(f"unknown atlas node(s): {', '.join(missing)}")
    return err


def load_atlas(root: Path) -> list[dict[str, Any]]:
    path = root / "atlas" / "nodes.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("nodes", []))


def load_all(root: Path) -> list[Forecast]:
    atlas_ids = {n["id"] for n in load_atlas(root)}
    out: list[Forecast] = []
    folder = root / "forecasts"
    if not folder.exists():
        return out
    for path in sorted(folder.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        try:
            data = parse(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 — report any parse failure as a file error
            out.append(Forecast(path, {}, [f"cannot parse YAML: {exc}"]))
            continue
        out.append(Forecast(path, data, validate(data, path, atlas_ids)))
    ids = [f.id for f in out]
    for f in out:
        if ids.count(f.id) > 1:
            f.errors.append("duplicate id")
        sup = f.data.get("supersedes")
        if sup and sup not in ids:
            f.errors.append(f"supersedes unknown forecast '{sup}'")
    return out
