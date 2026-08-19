"""Report emitters: banner, tables, JSON safety."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from translations.report import banner_markdown, fmt, table, write_report


def test_banner_is_present_and_marked() -> None:
    assert banner_markdown().startswith("> **SPECULATIVE OUTPUT")


def test_fmt_handles_numpy_and_none() -> None:
    assert fmt(None) == "—"
    assert fmt(np.True_) == "yes"
    assert fmt(np.float64(1.23456)) == "1.235"
    assert fmt(12345) == "12,345"


def test_table_escapes_pipes_in_view_names() -> None:
    rendered = table(["view"], [["T1-glyph|CB=break"]])
    assert r"T1-glyph\|CB=break" in rendered


def test_write_report_emits_markdown_and_json(tmp_path: Path) -> None:
    md_path, json_path = write_report(
        tmp_path, "topic", "Title", ["## Section\n\ncontent"], {"value": np.float64(2.0)}
    )
    assert "SPECULATIVE OUTPUT" in md_path.read_text()
    assert md_path.read_text().startswith("# Title")
    payload = json.loads(json_path.read_text())
    assert payload["topic"] == "topic"
    assert payload["value"] == 2.0
