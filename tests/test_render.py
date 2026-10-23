import datetime as dt
import xml.etree.ElementTree as ET

from ledger.model import load_all, load_atlas
from ledger.render import atlas_svg, calibration_svg, scorecard_svg
from ledger.score import atlas_state, scorecard

from .conftest import make, write


def test_empty_ledger_renders(repo):
    card = scorecard([], today=dt.date(2099, 1, 1))
    for svg in (
        scorecard_svg(card, 0),
        calibration_svg(card),
        atlas_svg(atlas_state([], load_atlas(repo)), "2099-01-01"),
    ):
        ET.fromstring(svg)
    assert "no forecast resolved yet" in scorecard_svg(card)


def test_full_ledger_renders(repo):
    res = {"resolved_on": "2099-02-01", "value": "synthetic", "source_url": "https://example.org"}
    for i in range(12):
        p = 0.1 + 0.07 * i
        write(
            repo,
            make(
                f"FEL-2099-{i + 1:04d}",
                probability=round(p, 2),
                status="resolved-yes" if i % 3 else "resolved-no",
                resolution=res,
            ),
        )
    card = scorecard(load_all(repo), today=dt.date(2099, 6, 1))
    assert card["overall"]["calibration"] is not None
    ET.fromstring(scorecard_svg(card, 12))
    ET.fromstring(calibration_svg(card))


def test_renders_follow_the_brand(repo):
    """Brand palette and embedded typefaces only; the stand-in identity of 22 October 2026 must not return."""
    card = scorecard([], today=dt.date(2099, 1, 1))
    svgs = [
        scorecard_svg(card, 0),
        calibration_svg(card),
        atlas_svg(atlas_state([], load_atlas(repo)), "2099-01-01"),
    ]
    for svg in svgs:
        assert "#201E1D" in svg and "#F3F2F2" in svg
        for legacy in ("#0B0D12", "#161A24", "#F2EFE8", "#8A94A6", "#2DB89F", "Inter,"):
            assert legacy not in svg
        assert "font-family:'Archivo'" in svg and "font-family:'IBM Plex Mono'" in svg
        assert ' rx="' not in svg  # square corners, always
    assert scorecard_svg(card).count("#F2C300") == 1  # one Cadmium point
