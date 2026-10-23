import subprocess
from pathlib import Path

from ledger import editorial, owners
from ledger.immutability import compare
from ledger.model import load_all
from ledger.stamp import commitment

from .conftest import make, write


def errors_for(repo, data):
    write(repo, data)
    return [e for f in load_all(repo) for e in f.errors]


def test_valid_fixture_passes(repo):
    assert errors_for(repo, make("FEL-2099-0001")) == []


def test_probability_must_be_set_and_bounded(repo):
    assert any("not set" in e for e in errors_for(repo, make("FEL-2099-0001", probability=None)))
    assert any("between" in e for e in errors_for(repo, make("FEL-2099-0002", probability=0.99)))


def test_id_must_match_file_and_resolution_required(repo):
    data = make("FEL-2099-0001", status="resolved-yes")
    errs = errors_for(repo, data)
    assert any("resolution" in e for e in errs)
    path = write(repo, make("FEL-2099-0002"))
    path.rename(path.with_name("FEL-2099-0009.yaml"))
    assert any("does not match" in e for f in load_all(repo) for e in f.errors)


def test_unknown_atlas_node_rejected(repo):
    assert any("unknown atlas" in e for e in errors_for(repo, make("FEL-2099-0001", atlas_nodes=["moon"])))


def test_no_backfill_rule():
    base = make("FEL-2099-0001", evidence=[{"date": "2099-01-02", "url": "https://a"}])
    assert compare(base, dict(base, probability=0.7))  # locked
    grown = dict(base, evidence=base["evidence"] + [{"date": "2099-01-09", "url": "https://b"}])
    assert compare(base, grown) == []  # append is fine
    assert compare(base, dict(base, evidence=[]))  # removal is not
    res = {"resolved_on": "2099-02-01", "value": "x", "source_url": "https://c"}
    resolved = dict(base, status="resolved-yes", resolution=res)
    assert compare(base, resolved) == []
    assert compare(resolved, dict(resolved, status="resolved-no"))  # final is final


def test_editorial_word_boundaries(repo):
    write(repo, make("FEL-2099-0001", synthesis="An alphabet of indicators, no recommendation."))
    assert editorial.scan(repo) == []
    write(repo, make("FEL-2099-0002", synthesis="Consensus price-target drift and an alpha claim."))
    hits = editorial.scan(repo)
    assert any("'alpha'" in h for h in hits) and any("'price target'" in h for h in hits)


def test_commitment_ignores_evidence_and_status():
    a = make("FEL-2099-0001")
    b = dict(a, evidence=[{"date": "2099-01-02", "url": "https://a"}], status="annulled")
    assert commitment(a) == commitment(b)
    assert commitment(a) != commitment(dict(a, probability=0.61))


def _git(root: Path, *args: str, email: str | None = None) -> None:
    env_args = ["-c", "user.name=t", "-c", f"user.email={email or 'founder@example.org'}"]
    subprocess.run(["git", *env_args, *args], cwd=root, check=True, capture_output=True)


def test_probability_ownership(repo):
    (repo / "editorial" / "forecasters.yaml").write_text(
        "forecasters:\n  test-forecaster:\n    emails: [founder@example.org]\n", encoding="utf-8"
    )
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "checkout", "-q", "-b", "feature")
    write(repo, make("FEL-2099-0001"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "agent drafts and sets p", email="agent@example.org")
    assert owners.check(repo, "main")  # agent wrote the probability: refused
    text = (
        (repo / "forecasts" / "FEL-2099-0001.yaml")
        .read_text()
        .replace("probability: 0.6", "probability: 0.55")
    )
    (repo / "forecasts" / "FEL-2099-0001.yaml").write_text(text)
    _git(repo, "commit", "-q", "-am", "founder sets p", email="founder@example.org")
    assert owners.check(repo, "main") == {}
