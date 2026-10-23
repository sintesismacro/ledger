"""Synthetic fixtures only. Nothing in tests/ is a forecast or a view held by anyone."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

FIX = Path(__file__).parent / "fixtures"


def make(fid: str, **over) -> dict:
    base = {
        "id": fid,
        "domain": "physical-ai-power",
        "forecaster": "test-forecaster",
        "question": "Will synthetic indicator Z exceed synthetic threshold T in period P?",
        "stance": "becoming",
        "atlas_nodes": ["generation"],
        "resolution_source": "Synthetic source used only by the test suite",
        "resolution_rule": "YES if the synthetic print exceeds T on first publication.",
        "resolves_on": "2099-01-31",
        "threshold": 1.0,
        "probability": 0.6,
        "becoming": "Synthetic Becoming case for testing only.",
        "returning": "Synthetic Returning case for testing only.",
        "synthesis": "Synthetic synthesis for testing only.",
        "evidence": [],
        "status": "open",
    }
    base.update(over)
    return base


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "ledger"
    (root / "forecasts").mkdir(parents=True)
    (root / "atlas").mkdir()
    (root / "editorial").mkdir()
    shutil.copy(FIX / "atlas" / "nodes.yaml", root / "atlas" / "nodes.yaml")
    (root / "editorial" / "denylist.txt").write_text("alpha\nSK Hynix\nprice target\n", encoding="utf-8")
    return root


def write(root: Path, data: dict) -> Path:
    path = root / "forecasts" / f"{data['id']}.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path
