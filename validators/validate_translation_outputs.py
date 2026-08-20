#!/usr/bin/env python3
"""
Phase 4 Translation Output Validator
====================================

Checks the speculative translation artifacts against their schema and against
the invariants the honesty policy depends on.

Usage:
    python -m validators.validate_translation_outputs

Checks performed:
    1. Schema validation of translation_lines.jsonl
    2. Banner present on every row and every report
    3. Coverage: one row per manuscript line, no line silently dropped
    4. Gated view never renders a token the confidence bands mark as low or none
    5. SHA256SUMS matches the artifacts on disk
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from translations.config import SPECULATIVE_BANNER
from translations.phase4 import LEXICON_PATH, LINES_JSONL, REPORTS, SUMS_PATH
from translations.render import GATED_MASK
from validators.schema import validate_against_schema

EXPECTED_LINES = 4072


def check_schema(rows: list[dict]) -> list[str]:
    """Every row conforms to `schemas/translation_lines.schema.json`."""
    return validate_against_schema(rows, "translation_lines.schema")[1]


def check_banner(rows: list[dict]) -> list[str]:
    """Every row and every report carries the speculative banner."""
    errors = [
        f"Row {row.get('line_id', '?')}: banner missing"
        for row in rows
        if row.get("banner") != SPECULATIVE_BANNER
    ]
    errors += [
        f"{path.name}: banner missing"
        for path in sorted(REPORTS.glob("*.md"))
        if SPECULATIVE_BANNER not in path.read_text()
    ]
    return errors


def check_coverage(rows: list[dict]) -> list[str]:
    """One row per manuscript line, and every line renders something."""
    errors = []
    if len(rows) != EXPECTED_LINES:
        errors.append(f"Expected {EXPECTED_LINES} lines, found {len(rows)}")
    if len({row["line_id"] for row in rows}) != len(rows):
        errors.append("Duplicate line_id")
    blank = [row["line_id"] for row in rows if row["tokens"] and not row["english_speculative"]]
    if blank:
        errors.append(f"{len(blank)} lines have tokens but no rendering (e.g. {blank[0]})")
    return errors


def check_gating(rows: list[dict]) -> list[str]:
    """The gated view masks everything below the medium band."""
    errors = []
    for row in rows:
        expected = " ".join(
            (
                token["chosen"]
                if token["band"] in ("high", "medium") and token["chosen"]
                else GATED_MASK
            )
            for token in row["tokens"]
        )
        if expected != row["english_gated"]:
            errors.append(f"{row['line_id']}: gated view does not match the confidence bands")
    return errors


def check_checksums() -> list[str]:
    """`SHA256SUMS` matches what is on disk."""
    if not SUMS_PATH.exists():
        return ["SHA256SUMS missing"]
    errors = []
    for line in SUMS_PATH.read_text().splitlines():
        digest, name = line.split("  ")
        path = SUMS_PATH.parent / name
        if not path.exists():
            errors.append(f"{name}: listed in SHA256SUMS but absent")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append(f"{name}: checksum mismatch")
    return errors


def main() -> int:
    """Run every check and report."""
    if not LINES_JSONL.exists():
        print(f"Translation artifacts missing; run `make translate` ({LINES_JSONL})")
        return 1
    rows = [json.loads(line) for line in LINES_JSONL.read_text().splitlines() if line.strip()]

    failures: dict[str, list[str]] = {
        "schema": check_schema(rows),
        "banner": check_banner(rows),
        "coverage": check_coverage(rows),
        "gating": check_gating(rows),
        "checksums": check_checksums(),
    }
    if not Path(LEXICON_PATH).exists():
        failures["lexicon"] = ["lexicon.jsonl missing"]

    for name, errors in failures.items():
        status = "OK" if not errors else f"FAIL ({len(errors)})"
        print(f"{name:12s} {status}")
        for error in errors[:5]:
            print(f"    {error}")
    return 1 if any(failures.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
