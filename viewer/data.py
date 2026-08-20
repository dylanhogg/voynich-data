"""Assemble the payload both viewer templates render.

Everything here is derived from committed artifacts (`output/translation/`,
`reports/translation/`, `output/metadata/`); nothing is invented and no value
is recomputed from the manuscript.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vcat.exceptions import SourceNotFoundError
from vcat.logging import get_logger
from viewer.iiif import image_url, load_map

logger = get_logger(__name__)

ROOT = Path(__file__).resolve().parents[1]
LINES_PATH = ROOT / "output" / "translation" / "translation_lines.jsonl"
LEXICON_PATH = ROOT / "output" / "translation" / "lexicon.jsonl"
PAGES_PATH = ROOT / "output" / "metadata" / "pages.jsonl"
COVERAGE_PATH = ROOT / "reports" / "translation" / "coverage.json"
AUDIT_PATH = ROOT / "reports" / "translation" / "strengths_weaknesses.json"
CALIBRATION_PATH = ROOT / "reports" / "translation" / "calibration.json"
MANIFEST_PATH = ROOT / "output" / "translation" / "phase4_manifest.json"

BANDS = {"none": 0, "low": 1, "medium": 2, "high": 3}
GATE = 2  # medium and high survive the confidence gate
THUMB_PX = 400
PLATE_PX = 1000
MAX_ALTERNATIVES = 4

SECTION_LABELS = {
    "herbal": "Herbal",
    "astronomical": "Astronomical",
    "cosmological": "Cosmological",
    "biological": "Biological",
    "pharmaceutical": "Pharmaceutical",
    "stars": "Recipes / Stars",
    "text_only": "Text only",
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SourceNotFoundError(f"missing artifact: {path} (run `make translate`)")
    with path.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SourceNotFoundError(f"missing artifact: {path} (run `make translate`)")
    return dict(json.loads(path.read_text()))


def _pct(value: float) -> int:
    return round(value * 100)


@dataclass
class Payload:
    """The JSON blob embedded in both pages, plus template-side extras."""

    banner: str
    hypothesis: dict[str, Any]
    stats: dict[str, Any]
    pages: list[dict[str, Any]] = field(default_factory=list)
    lexicon: dict[str, list[str]] = field(default_factory=dict)
    freq: dict[str, int] = field(default_factory=dict)
    sections: list[dict[str, Any]] = field(default_factory=list)

    def as_json(self) -> str:
        return json.dumps(
            {
                "banner": self.banner,
                "hypothesis": self.hypothesis,
                "stats": self.stats,
                "pages": self.pages,
                "lexicon": self.lexicon,
                "freq": self.freq,
                "sections": self.sections,
            },
            separators=(",", ":"),
            ensure_ascii=False,
            sort_keys=True,
        )


def _encode_line(line: dict[str, Any], blocks: dict[str, int]) -> list[Any]:
    tokens = [
        [
            token["surface"],
            token["intermediate"],
            token["chosen"],
            BANDS[token["band"]],
            _pct(token["confidence"]),
            _pct(token["null_p"]),
            _pct(token["reliability"]),
        ]
        for token in line["tokens"]
    ]
    return [
        int(line["line_id"].split(":")[1]),
        line["text_clean"],
        _pct(line["line_confidence"]),
        blocks.setdefault(line["block_id"], len(blocks)),
        1 if line["line_type"] == "label" else 0,
        1 if line["is_holdout"] else 0,
        tokens,
    ]


def _page_summary(lines: list[dict[str, Any]]) -> tuple[int, int, int]:
    tokens = [token for line in lines for token in line["tokens"]]
    if not tokens:
        return 0, 0, 0
    gated = sum(1 for token in tokens if BANDS[token["band"]] >= GATE)
    confidence = sum(token["confidence"] for token in tokens)
    return len(tokens), round(100 * gated / len(tokens)), round(100 * confidence / len(tokens))


def _lexicon_alternatives(used_types: set[str]) -> dict[str, list[str]]:
    alternatives: dict[str, list[str]] = {}
    for entry in _read_jsonl(LEXICON_PATH):
        voynich_type = entry["voynich_type"]
        if voynich_type not in used_types:
            continue
        glosses = [gloss["english"] for gloss in entry["glosses"][:MAX_ALTERNATIVES]]
        if len(glosses) > 1:
            alternatives[voynich_type] = glosses
    return alternatives


def build_payload() -> Payload:
    """Read every artifact once and fold it into the embedded payload."""
    lines = _read_jsonl(LINES_PATH)
    coverage = _read_json(COVERAGE_PATH)
    audit = _read_json(AUDIT_PATH)
    calibration = _read_json(CALIBRATION_PATH)
    manifest = _read_json(MANIFEST_PATH)
    metadata = {page["page_id"]: page for page in _read_jsonl(PAGES_PATH)}
    services = load_map()

    by_page: dict[str, list[dict[str, Any]]] = {}
    for line in lines:
        by_page.setdefault(line["page_id"], []).append(line)

    pages: list[dict[str, Any]] = []
    for page_id, page_lines in by_page.items():
        first = page_lines[0]
        meta = metadata.get(page_id, {})
        blocks: dict[str, int] = {}
        tokens, gated, confidence = _page_summary(page_lines)
        pages.append(
            {
                "id": page_id,
                "folio": meta.get("folio_number", 0),
                "side": meta.get("side", ""),
                "quire": meta.get("quire_id", ""),
                "section": first["section"] or "text_only",
                "currier": first["currier_language"] or "-",
                "hand": first["hand"] or "-",
                "illustration": meta.get("illustration_type", ""),
                "thumb": image_url(services, page_id, THUMB_PX),
                "plate": image_url(services, page_id, PLATE_PX),
                "tokens": tokens,
                "gated": gated,
                "confidence": confidence,
                "lines": [_encode_line(line, blocks) for line in page_lines],
            }
        )

    frequencies: dict[str, int] = {}
    for line in lines:
        for token in line["tokens"]:
            frequencies[token["surface"]] = frequencies.get(token["surface"], 0) + 1
    used_types = set(frequencies)
    sections = [
        {
            "id": row["stratum"],
            "label": SECTION_LABELS.get(row["stratum"], row["stratum"]),
            "lines": int(row["lines"]),
            "tokens": int(row["tokens"]),
            "gated": round(100 * row["gated_coverage"]),
            "confidence": round(100 * row["mean_confidence"]),
        }
        for row in coverage["strata"]["section"]
    ]

    primary = next(
        row for row in coverage["per_hypothesis"] if row["hypothesis"] == coverage["primary"]
    )
    payload = Payload(
        banner=coverage["banner"],
        hypothesis={
            "id": primary["hypothesis"],
            "variant": primary["variant"],
            "gain_per_token": round(primary["gain_per_token"], 3),
            "p_value": round(primary["p_value"], 3),
            "key_id": manifest.get("key_id", primary["variant"]),
        },
        stats={
            "overall": coverage["overall"],
            "controls": coverage["controls"],
            "control_ratio": round(coverage["control_ratio"], 3),
            "hypotheses": coverage["per_hypothesis"],
            "splits": coverage["splits"],
            "strata": coverage["strata"],
            "fallback": coverage["fallback"],
            "kill_criteria": audit["kill_criteria"],
            "audit": sorted(
                (
                    {
                        "test": row["test"],
                        "metric": row["metric"],
                        "null": row["null"],
                        "verdict": row["verdict"],
                        "implication": row["implication"],
                    }
                    for row in list(audit["strength"].values()) + list(audit["weakness"].values())
                ),
                key=lambda row: str(row["test"]),
            ),
            "calibration": calibration["maps"][coverage["primary"]]["diagram"],
            "declared_unsuccessful": audit["declared_unsuccessful"],
        },
        pages=pages,
        lexicon=_lexicon_alternatives(used_types),
        freq=frequencies,
        sections=sections,
    )
    logger.info("Payload built", pages=len(pages), lines=len(lines), types=len(payload.lexicon))
    return payload
