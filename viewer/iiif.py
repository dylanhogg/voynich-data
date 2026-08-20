"""Folio -> Beinecke IIIF image service map.

The map is committed (`viewer/iiif_folio_map.json`) so `viewer.build` runs
offline; `python -m viewer.iiif` refreshes it from Yale's IIIF manifest.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import requests

from vcat.logging import get_logger

logger = get_logger(__name__)

MANIFEST_URL = "https://collections.library.yale.edu/manifests/2002046"
CATALOG_URL = "https://collections.library.yale.edu/catalog/2002046"
MAP_PATH = Path(__file__).parent / "iiif_folio_map.json"

_FOLIO_RE = re.compile(r"\b(\d{1,3}[rv])\b")
_PANEL_RE = re.compile(r"^f(\d{1,3}[rv])\d*$")


def load_map() -> dict[str, str]:
    """Folio key (`1r`) -> IIIF image service base URL."""
    if not MAP_PATH.exists():
        logger.warning("IIIF map missing; pages will link out without thumbnails")
        return {}
    return dict(json.loads(MAP_PATH.read_text())["folios"])


def image_url(services: dict[str, str], page_id: str, size: int) -> str | None:
    """A IIIF `!size,size` URL for a page id (`f68r2` -> the 68r canvas)."""
    match = _PANEL_RE.match(page_id)
    if match is None:
        return None
    service = services.get(match.group(1))
    return f"{service}/full/!{size},{size}/0/default.jpg" if service else None


def refresh() -> dict[str, str]:
    """Re-derive the map from the live manifest and write it to disk."""
    manifest: dict[str, Any] = requests.get(MANIFEST_URL, timeout=60).json()
    folios: dict[str, str] = {}
    for canvas in manifest["items"]:
        label = " ".join(canvas.get("label", {}).get("none", []))
        service = canvas["items"][0]["items"][0]["body"]["service"][0]["@id"]
        for folio in _FOLIO_RE.findall(label):
            folios.setdefault(folio, service)
    MAP_PATH.write_text(
        json.dumps({"source": MANIFEST_URL, "folios": folios}, indent=1, sort_keys=True) + "\n"
    )
    logger.info("Refreshed IIIF map", folios=len(folios))
    return folios


if __name__ == "__main__":
    refresh()
