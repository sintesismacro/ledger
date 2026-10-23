"""SVG renders in the SINTESIS identity: scorecard, calibration chart and the Atlas.

Source of the identity: Sintesis Brand.pdf (Berlin, September 2026) and the website tokens
(tokens.css, revised 18 October 2026). Ink ground, Paper subject, grey context, one Cadmium point
at most; flush left on a visible grid with 2px rules; square corners; numerals in IBM Plex Mono,
headlines in Archivo 800. The two typefaces are embedded as data URIs, because an SVG shown as an
image cannot load external fonts; their SIL Open Font Licence texts sit next to them in ``fonts/``.

Pure string generation, no plotting dependency, so CI stays small and the output is diffable.
"""

from __future__ import annotations

import base64
import math
from functools import lru_cache
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

# Corporate palette (exact brand swatches) and the Ink-theme roles of tokens.css.
INK = "#201E1D"  # ground
PAPER = "#F3F2F2"  # subject, headlines, hard rules
FG_BODY = "#E4E1E0"  # long-reading text on ink
FG_2 = "#B8B3B3"  # secondary text on ink, 8.01:1
CONTEXT = "#8E8989"  # comparison series, 4.81:1 on ink
GRID = "#3B3838"  # chart grid
RULE_SOFT = "#4A4746"  # 1px rules
ELEV = "#2A2827"  # tracks, fields
CADMIUM = "#F2C300"  # one decision point per composition

DISPLAY = "Archivo, 'Helvetica Neue', Arial, sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, Menlo, Consolas, monospace"
THESIS = "Intelligence becomes abundant; verified judgement becomes scarce."
MARGIN = 48

FONTS = Path(__file__).parent / "fonts"


@lru_cache(maxsize=1)
def _font_css() -> str:
    faces = (
        ("Archivo", "100 900", "Archivo-latin.woff2"),
        ("IBM Plex Mono", "400", "IBMPlexMono-400-latin.woff2"),
        ("IBM Plex Mono", "500", "IBMPlexMono-500-latin.woff2"),
    )
    rules = []
    for family, weight, name in faces:
        path = FONTS / name
        if not path.exists():  # renders still work with the fallback stacks
            continue
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
        )
    return "".join(rules)


def _t(
    x: float,
    y: float,
    s: str,
    size: float,
    fill: str = PAPER,
    weight: int = 400,
    anchor: str = "start",
    mono: bool = False,
    caps: bool = False,
    extra: str = "",
) -> str:
    family = MONO if mono else DISPLAY
    if caps:
        s = s.upper()
        extra += f' letter-spacing="{size * 0.08:.2f}"'
    elif weight >= 800:
        extra += f' letter-spacing="{-size * 0.015:.2f}"'
    if mono:
        extra += ' font-variant-numeric="tabular-nums"'
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>{escape(s)}</text>'
    )


def _rule(x1: float, y: float, x2: float, hard: bool = True) -> str:
    colour, width = (PAPER, 2) if hard else (RULE_SOFT, 1)
    return f'<rect x="{x1:.1f}" y="{y:.1f}" width="{x2 - x1:.1f}" height="{width}" fill="{colour}"/>'


def _header(w: int, label: str) -> str:
    """Brand page header: section label left, SINTESIS · MACRO right, a 1px rule beneath."""
    return (
        _t(MARGIN, 44, label, 13, FG_2, 500, mono=True, caps=True)
        + _t(w - MARGIN, 44, "SINTESIS · MACRO", 13, FG_2, 500, anchor="end", mono=True, caps=True)
        + _rule(MARGIN, 60, w - MARGIN, hard=False)
    )


def _fmt(v: float | None, digits: int = 3) -> str:
    return "—" if v is None else f"{v:.{digits}f}"


def _svg(w: int, h: int, label: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{_font_css()}</style>"
        f'<rect width="{w}" height="{h}" fill="{INK}"/>{body}</svg>\n'
    )


def scorecard_svg(card: dict[str, Any], stamped: int | None = None) -> str:
    o = card["overall"]
    w, h = 1200, 400
    parts = [
        _header(w, "Forward Evidence Ledger"),
        _t(MARGIN, 114, THESIS, 32, PAPER, 800),
        _t(
            MARGIN,
            148,
            "Becoming vs Returning — every forecast dated, sourced and scored, misses included.",
            17,
            FG_2,
        ),
        _rule(MARGIN, 176, w - MARGIN),
    ]
    resolved = o["resolved"]
    if resolved:
        brier_sub = f"skill vs a permanent 50%: {_fmt(o['skill_vs_50pct'], 2)}"
        log_sub = f"log score {_fmt(o['log_score'], 3)}"
    else:
        nxt = o.get("next_resolution")
        brier_sub = f"first resolution due {nxt}" if nxt else "no forecast resolved yet"
        log_sub = "scored when forecasts resolve"
    columns = [
        (
            "Open forecasts",
            str(o["open"]),
            f"{o['overdue']} awaiting resolution data" if o["overdue"] else "all within their dates",
        ),
        ("Resolved", str(resolved), f"{o['annulled']} annulled under METHOD.md"),
        ("Brier score", _fmt(o["brier"]), brier_sub),
        (
            "Calibration",
            "live" if o["calibration"] else "pending",
            log_sub if o["calibration"] else f"shown from {card['calibration_min_resolved']} resolved",
        ),
    ]
    col_w = (w - 2 * MARGIN) / 4
    for i, (label, value, sub) in enumerate(columns):
        x = MARGIN + i * col_w
        if i:
            parts.append(f'<rect x="{x - 12:.1f}" y="196" width="1" height="124" fill="{RULE_SOFT}"/>')
        tx = x + (12 if i else 0)
        if label == "Brier score":  # the one decision point: the score that judges the judgement
            parts.append(f'<rect x="{tx}" y="203" width="10" height="10" fill="{CADMIUM}"/>')
            parts.append(_t(tx + 18, 212, label, 12, FG_2, 500, mono=True, caps=True))
        else:
            parts.append(_t(tx, 212, label, 12, FG_2, 500, mono=True, caps=True))
        numeric = any(ch.isdigit() for ch in value) or value == "—"
        if numeric:  # numerals in Plex Mono, words in Archivo
            parts.append(_t(tx, 282, value, 48, PAPER, 500, mono=True))
        else:
            parts.append(_t(tx, 278, value, 40, PAPER, 800))
        parts.append(_t(tx, 312, sub, 14, FG_2))
    parts.append(_rule(MARGIN, 340, w - MARGIN, hard=False))
    foot = f"As of {card['as_of']} (UTC) · Brier score: 0 is perfect, 0.25 is a permanent 50%"
    if stamped is not None:
        foot += f" · {stamped} of {o['forecasts']} commitments carry a qualified timestamp"
    parts.append(_t(MARGIN, 370, foot, 12, FG_2, mono=True))
    parts.append(_t(w - MARGIN, 370, "Not investment advice", 12, FG_2, anchor="end", mono=True))
    return _svg(w, h, "SINTESIS Forward Evidence Ledger scorecard", "".join(parts))


def calibration_svg(card: dict[str, Any]) -> str:
    w = h = 640
    m, top, side = 96, 92, 470
    bottom = top + side
    o = card["overall"]
    parts = [_header(w, "Calibration")]
    for k in range(0, 11, 2):
        v = k / 10
        x = m + v * side
        y = bottom - v * side
        if k:
            parts.append(f'<rect x="{x:.1f}" y="{top}" width="1" height="{side}" fill="{GRID}"/>')
            parts.append(f'<rect x="{m}" y="{y:.1f}" width="{side}" height="1" fill="{GRID}"/>')
        parts.append(_t(x, bottom + 26, f"{v:.1f}", 12, FG_2, anchor="middle", mono=True))
        parts.append(_t(m - 12, y + 4, f"{v:.1f}", 12, FG_2, anchor="end", mono=True))
    parts.append(_rule(m, bottom, m + side))  # baseline drawn, frame not
    parts.append(
        f'<line x1="{m}" y1="{bottom}" x2="{m + side}" y2="{top}" stroke="{CONTEXT}" '
        f'stroke-width="1.5" stroke-dasharray="6 6"/>'
    )
    parts.append(_t(m + side / 2, h - 24, "Forecast probability", 12, FG_2, 500, "middle", True, True))
    parts.append(
        _t(
            30,
            top + side / 2,
            "Observed frequency",
            12,
            FG_2,
            500,
            "middle",
            True,
            True,
            extra=f' transform="rotate(-90 30 {top + side / 2})"',
        )
    )
    if not o["calibration"]:
        parts.append(
            _t(
                m + 24,
                top + 48,
                f"Shown once {card['calibration_min_resolved']} forecasts have resolved",
                18,
                PAPER,
                600,
            )
        )
        parts.append(_t(m + 24, top + 76, f"Resolved so far: {o['resolved']}", 13, FG_2, mono=True))
    else:
        for b in o["calibration"]:
            if not b["n"]:
                continue
            x = m + b["mean_forecast"] * side
            y = bottom - b["observed_rate"] * side
            r = 4 + 2.5 * math.sqrt(b["n"])
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{PAPER}"/>')
            parts.append(_t(x + r + 6, y + 4, f"n={b['n']}", 11, FG_2, mono=True))
    return _svg(w, h, "Calibration of the SINTESIS ledger", "".join(parts))


def atlas_svg(rows: list[dict[str, Any]], as_of: str) -> str:
    w = 1200
    row_h = 54
    top = 196
    h = top + row_h * max(len(rows), 1) + 88
    bar_x, bar_w = 400, 560
    parts = [
        _header(w, "The Atlas"),
        _t(MARGIN, 112, "Becoming vs Returning — the physical body of intelligence", 30, PAPER, 800),
        f'<rect x="{MARGIN}" y="138" width="14" height="10" fill="{PAPER}"/>',
        _t(MARGIN + 22, 147, "Becoming: build momentum", 12, FG_2, 500, mono=True, caps=True),
        f'<rect x="{MARGIN + 300}" y="138" width="14" height="10" fill="{CONTEXT}"/>',
        _t(
            MARGIN + 322, 147, "Returning: overcapacity, commoditisation", 12, FG_2, 500, mono=True, caps=True
        ),
        _rule(MARGIN, 172, w - MARGIN),
    ]
    half = bar_x + bar_w / 2
    phase = None
    for i, r in enumerate(rows):
        y = top + i * row_h
        if i:
            parts.append(_rule(MARGIN, y, w - MARGIN, hard=False))
        if r.get("phase") and r["phase"] != phase:
            phase = r["phase"]
            parts.append(_t(w - MARGIN, y + 20, phase, 11, FG_2, 500, anchor="end", mono=True, caps=True))
        parts.append(_t(MARGIN, y + 33, r["label"], 16, PAPER, 600))
        for j, (stance, colour) in enumerate((("becoming", PAPER), ("returning", CONTEXT))):
            by = y + 14 + j * 16
            parts.append(f'<rect x="{bar_x}" y="{by}" width="{bar_w}" height="10" fill="{ELEV}"/>')
            v = r.get(stance)
            if v is None:
                parts.append(_t(bar_x + 8, by + 9, "no open forecast", 10, FG_2, mono=True))
            else:
                parts.append(
                    f'<rect x="{bar_x}" y="{by}" width="{bar_w * v:.1f}" height="10" fill="{colour}"/>'
                )
                parts.append(
                    _t(bar_x + bar_w + 12, by + 9, f"{v:.2f}  (n={r[stance + '_n']})", 11, FG_2, mono=True)
                )
        parts.append(
            f'<line x1="{half}" y1="{y + 10}" x2="{half}" y2="{y + row_h - 10}" '
            f'stroke="{RULE_SOFT}" stroke-dasharray="2 3"/>'
        )
    parts.append(_rule(MARGIN, h - 70, w - MARGIN, hard=False))
    parts.append(_t(MARGIN, h - 44, f"As of {as_of} (UTC) · No issuer is named", 12, FG_2, mono=True))
    parts.append(
        _t(
            MARGIN,
            h - 24,
            "Each bar is the mean probability of the open forecasts linked to that layer "
            "whose YES outcome favours that voice",
            12,
            FG_2,
            mono=True,
        )
    )
    return _svg(w, h, "The Atlas: Becoming vs Returning", "".join(parts))
