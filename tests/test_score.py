import datetime as dt
import math

from ledger.model import load_all
from ledger.score import atlas_state, brier, calibration, log_score, scorecard, skill

from .conftest import make, write


def test_brier_skill_log_exact():
    pairs = [(0.8, 1), (0.3, 0)]
    assert math.isclose(brier(pairs), (0.04 + 0.09) / 2)
    assert math.isclose(skill(brier(pairs)), 1 - 0.065 / 0.25)
    assert math.isclose(log_score(pairs), (math.log(0.8) + math.log(0.7)) / 2)


def test_permanent_half_has_zero_skill():
    pairs = [(0.5, 1), (0.5, 0), (0.5, 1)]
    assert math.isclose(skill(brier(pairs)), 0.0)


def test_empty_is_none():
    assert brier([]) is None and log_score([]) is None and skill(None) is None


def test_calibration_bins():
    bins = calibration([(0.05, 0), (0.07, 1), (0.95, 1)])
    assert bins[0]["n"] == 2 and math.isclose(bins[0]["observed_rate"], 0.5)
    assert bins[9]["n"] == 1 and bins[5]["n"] == 0


def test_scorecard_excludes_annulled_and_counts_overdue(repo):
    res = {"resolved_on": "2099-02-01", "value": "synthetic", "source_url": "https://example.org"}
    write(repo, make("FEL-2099-0001", probability=0.8, status="resolved-yes", resolution=res))
    write(repo, make("FEL-2099-0002", probability=0.3, status="resolved-no", resolution=res))
    write(repo, make("FEL-2099-0003", status="annulled", resolution=res))
    write(repo, make("FEL-2099-0004", resolves_on="2000-01-01"))
    card = scorecard(load_all(repo), today=dt.date(2099, 6, 1))
    o = card["overall"]
    assert o["resolved"] == 2 and o["annulled"] == 1 and o["open"] == 1 and o["overdue"] == 1
    assert math.isclose(o["brier"], 0.065)
    assert o["calibration"] is None  # fewer than 10 resolved


def test_atlas_state_by_stance(repo):
    write(repo, make("FEL-2099-0001", probability=0.6, stance="becoming"))
    write(repo, make("FEL-2099-0002", probability=0.4, stance="becoming"))
    write(repo, make("FEL-2099-0003", probability=0.7, stance="returning", atlas_nodes=["grid"]))
    from ledger.model import load_atlas

    rows = {r["id"]: r for r in atlas_state(load_all(repo), load_atlas(repo))}
    assert math.isclose(rows["generation"]["becoming"], 0.5) and rows["generation"]["returning"] is None
    assert math.isclose(rows["grid"]["returning"], 0.7)
    assert rows["robotics"]["becoming_n"] == 0
