"""SVG renders in the SINTESIS identity: scorecard, calibration chart and the Atlas.

Pure string generation, no plotting dependency, so CI stays small and the output is diffable.
"""

from __future__ import annotations

import math
from typing import Any
from xml.sax.saxutils import escape

INK, GRAPHITE, PAPER, SLATE, SIGNAL = "#0B0D12", "#161A24", "#F2EFE8", "#8A94A6", "#2DB89F"
FONT = "Inter, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
THESIS = "Intelligence becomes abundant; verified judgement becomes scarce."


def _t(
    x: float,
    y: float,
    s: str,
    size: int,
    fill: str = PAPER,
    weight: int = 400,
    anchor: str = "start",
    extra: str = "",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{escape(s)}</text>'
    )


def _sigma(x: float, y: float, size: float) -> str:
    k = size / 100.0
    return (
        f'<g transform="translate({x},{y}) scale({k})">'
        f'<path d="M82 18 H22 L52 50 L22 82 H82" fill="none" stroke="{PAPER}" stroke-width="11" '
        f'stroke-linecap="square" stroke-linejoin="miter"/>'
        f'<circle cx="52" cy="50" r="7.5" fill="{SIGNAL}"/></g>'
    )


def _fmt(v: float | None, digits: int = 3) -> str:
    return "—" if v is None else f"{v:.{digits}f}"


def _svg(w: int, h: int, label: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f'<rect width="{w}" height="{h}" rx="14" fill="{INK}"/>'
        f'<rect x="0" y="14" width="6" height="{h - 28}" fill="{SIGNAL}"/>{body}</svg>\n'
    )


def scorecard_svg(card: dict[str, Any], stamped: int | None = None) -> str:
    o = card["overall"]
    w, h = 1200, 400
    parts = [
        _sigma(48, 34, 44),
        _t(108, 64, "SINTESIS · FORWARD EVIDENCE LEDGER", 15, SLATE, 500, extra='letter-spacing="2.2"'),
        _t(48, 132, THESIS, 30, PAPER, 600),
        _t(
            48,
            168,
            "Becoming vs Returning — every forecast dated, sourced and scored, misses included.",
            17,
            SLATE,
        ),
    ]
    resolved = o["resolved"]
    if resolved:
        brier_sub = f"skill vs a permanent 50%: {_fmt(o['skill_vs_50pct'], 2)}"
        log_sub = f"log score {_fmt(o['log_score'], 3)}"
    else:
        nxt = o.get("next_resolution")
        brier_sub = f"first resolution due {nxt}" if nxt else "no forecast resolved yet"
        log_sub = "scored when forecasts resolve"
    tiles = [
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
    tw, gap, x0, y0 = 264, 18, 48, 204
    for i, (label, value, sub) in enumerate(tiles):
        x = x0 + i * (tw + gap)
        parts.append(f'<rect x="{x}" y="{y0}" width="{tw}" height="128" rx="10" fill="{GRAPHITE}"/>')
        parts.append(_t(x + 20, y0 + 32, label.upper(), 13, SLATE, 500, extra='letter-spacing="1.6"'))
        parts.append(_t(x + 20, y0 + 84, value, 44, PAPER, 600))
        parts.append(_t(x + 20, y0 + 112, sub, 13, SLATE))
    foot = f"As of {card['as_of']} (UTC) · Brier score: 0 is perfect, 0.25 is a permanent 50%"
    if stamped is not None:
        foot += f" · {stamped} of {o['forecasts']} commitments carry a qualified timestamp"
    parts.append(_t(48, 372, foot, 13, SLATE))
    parts.append(_t(w - 48, 372, "Not investment advice", 13, SLATE, anchor="end"))
    return _svg(w, h, "SINTESIS Forward Evidence Ledger scorecard", "".join(parts))


def calibration_svg(card: dict[str, Any]) -> str:
    w = h = 640
    m = 84
    side = w - 2 * m
    o = card["overall"]
    parts = [_t(m, 52, "CALIBRATION", 14, SLATE, 500, extra='letter-spacing="2.2"')]
    parts.append(f'<rect x="{m}" y="{m}" width="{side}" height="{side}" fill="{GRAPHITE}" rx="6"/>')
    for k in range(0, 11, 2):
        v = k / 10
        x = m + v * side
        y = m + side - v * side
        parts.append(
            f'<line x1="{x:.1f}" y1="{m}" x2="{x:.1f}" y2="{m + side}" stroke="{INK}" stroke-width="1"/>'
        )
        parts.append(
            f'<line x1="{m}" y1="{y:.1f}" x2="{m + side}" y2="{y:.1f}" stroke="{INK}" stroke-width="1"/>'
        )
        parts.append(_t(x, m + side + 24, f"{v:.1f}", 12, SLATE, anchor="middle"))
        parts.append(_t(m - 12, y + 4, f"{v:.1f}", 12, SLATE, anchor="end"))
    parts.append(
        f'<line x1="{m}" y1="{m + side}" x2="{m + side}" y2="{m}" stroke="{SLATE}" '
        f'stroke-width="1.5" stroke-dasharray="6 6"/>'
    )
    parts.append(_t(m + side / 2, h - 22, "Forecast probability", 13, SLATE, anchor="middle"))
    parts.append(
        _t(
            26,
            m + side / 2,
            "Observed frequency",
            13,
            SLATE,
            anchor="middle",
            extra=f'transform="rotate(-90 26 {m + side / 2})"',
        )
    )
    if not o["calibration"]:
        parts.append(
            _t(
                m + side / 2,
                m + side / 2 - 8,
                f"Shown once {card['calibration_min_resolved']} forecasts have resolved",
                16,
                PAPER,
                anchor="middle",
            )
        )
        parts.append(
            _t(
                m + side / 2,
                m + side / 2 + 18,
                f"Resolved so far: {o['resolved']}",
                14,
                SLATE,
                anchor="middle",
            )
        )
    else:
        for b in o["calibration"]:
            if not b["n"]:
                continue
            x = m + b["mean_forecast"] * side
            y = m + side - b["observed_rate"] * side
            r = 5 + 3 * math.sqrt(b["n"])
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{SIGNAL}" fill-opacity="0.85"/>'
            )
            parts.append(_t(x + r + 4, y + 4, f"n={b['n']}", 11, SLATE))
    return _svg(w, h, "Calibration of the SINTESIS ledger", "".join(parts))


def atlas_svg(rows: list[dict[str, Any]], as_of: str) -> str:
    w = 1200
    row_h = 54
    top = 168
    h = top + row_h * max(len(rows), 1) + 70
    bar_x, bar_w = 360, 600
    parts = [
        _sigma(48, 30, 40),
        _t(104, 58, "THE ATLAS", 15, SLATE, 500, extra='letter-spacing="2.2"'),
        _t(48, 104, "Becoming vs Returning — the physical body of intelligence", 26, PAPER, 600),
        f'<rect x="{bar_x}" y="132" width="14" height="10" fill="{SIGNAL}"/>',
        _t(bar_x + 20, 141, "Becoming: build momentum", 13, SLATE),
        f'<rect x="{bar_x + 230}" y="132" width="14" height="10" fill="{SLATE}"/>',
        _t(bar_x + 250, 141, "Returning: overcapacity, commoditisation", 13, SLATE),
    ]
    half = bar_x + bar_w / 2
    phase = None
    for i, r in enumerate(rows):
        y = top + i * row_h
        if r.get("phase") and r["phase"] != phase:
            phase = r["phase"]
            parts.append(
                _t(w - 48, y + 22, phase.upper(), 11, SLATE, 500, anchor="end", extra='letter-spacing="1.6"')
            )
        parts.append(
            f'<rect x="48" y="{y + 4}" width="{w - 96}" height="{row_h - 8}" rx="8" fill="{GRAPHITE}"/>'
        )
        parts.append(_t(68, y + 32, r["label"], 16, PAPER, 500))
        for j, (stance, colour) in enumerate((("becoming", SIGNAL), ("returning", SLATE))):
            by = y + 13 + j * 16
            parts.append(f'<rect x="{bar_x}" y="{by}" width="{bar_w}" height="10" rx="2" fill="{INK}"/>')
            v = r.get(stance)
            if v is None:
                parts.append(
                    _t(bar_x + 8, by + 9, "no open forecast", 10, SLATE, extra='font-style="italic"')
                )
            else:
                parts.append(
                    f'<rect x="{bar_x}" y="{by}" width="{bar_w * v:.1f}" height="10" rx="2" fill="{colour}"/>'
                )
                parts.append(_t(bar_x + bar_w + 12, by + 9, f"{v:.2f}  (n={r[stance + '_n']})", 11, SLATE))
        parts.append(
            f'<line x1="{half}" y1="{y + 10}" x2="{half}" y2="{y + row_h - 10}" '
            f'stroke="{SLATE}" stroke-opacity="0.5" stroke-dasharray="2 3"/>'
        )
    parts.append(
        _t(
            48,
            h - 28,
            f"As of {as_of} (UTC) · Each bar is the mean probability of the open "
            "forecasts linked to that layer whose YES outcome favours that voice · "
            "No issuer is named",
            12,
            SLATE,
        )
    )
    return _svg(w, h, "The Atlas: Becoming vs Returning", "".join(parts))
