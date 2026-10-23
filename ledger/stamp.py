"""Qualified timestamps for forecast commitments (RFC 3161, eIDAS Art. 41–42).

What is stamped is the *commitment*: the canonical JSON of a forecast's locked fields.
Stamping the commitment rather than the file means evidence and resolutions can be added
later without changing what was proved. Git dates prove nothing; the receipt does.

The time-stamping authority (TSA) is configured by the ``TSA_URL`` environment variable and
must be a qualified trust service on the EU Trusted List (PLAN-05 gate G7). Without it the
step is skipped and the scorecard says so.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Any

from .immutability import LOCKED
from .model import Forecast


def commitment(data: dict[str, Any]) -> bytes:
    locked = {k: data.get(k) for k in LOCKED}
    return json.dumps(locked, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str).encode(
        "utf-8"
    )


def load_manifest(out: Path) -> dict[str, Any]:
    path = out / "receipts" / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def stamp_all(forecasts: list[Forecast], out: Path, tsa_url: str | None = None) -> dict[str, Any]:
    """Stamp every valid forecast not yet in the manifest. Existing receipts are never touched."""
    tsa_url = tsa_url or os.environ.get("TSA_URL")
    manifest = load_manifest(out)
    if not tsa_url:
        return manifest
    if not tsa_url.startswith("https://"):
        raise ValueError("TSA_URL must be an https:// URL of a qualified time-stamping authority")
    folder = out / "receipts"
    folder.mkdir(parents=True, exist_ok=True)
    for f in forecasts:
        if f.errors or f.id in manifest:
            continue
        body = commitment(f.data)
        (folder / f"{f.id}.json").write_bytes(body)
        with tempfile.TemporaryDirectory() as tmp:
            tsq = Path(tmp) / "q.tsq"
            subprocess.run(
                [
                    "openssl",
                    "ts",
                    "-query",
                    "-data",
                    str(folder / f"{f.id}.json"),
                    "-sha256",
                    "-cert",
                    "-out",
                    str(tsq),
                ],
                check=True,
                capture_output=True,
            )
            req = urllib.request.Request(  # noqa: S310 — https enforced above
                tsa_url,
                data=tsq.read_bytes(),
                headers={"Content-Type": "application/timestamp-query"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 — https enforced above
                tsr = resp.read()
        (folder / f"{f.id}.tsr").write_bytes(tsr)
        status = subprocess.run(
            ["openssl", "ts", "-reply", "-in", str(folder / f"{f.id}.tsr"), "-text"],
            capture_output=True,
            text=True,
        ).stdout
        if "Granted" not in status:
            (folder / f"{f.id}.tsr").unlink(missing_ok=True)
            raise RuntimeError(f"TSA did not grant a timestamp for {f.id}")
        manifest[f.id] = {
            "sha256": hashlib.sha256(body).hexdigest(),
            "commitment": f"receipts/{f.id}.json",
            "receipt": f"receipts/{f.id}.tsr",
            "requested_utc": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        }
        (folder / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return manifest
