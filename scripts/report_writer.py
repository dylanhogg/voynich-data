"""Tiny helper: collect analysis output for console and a markdown report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


class Report:
    """Echo lines to stdout and accumulate them for a markdown report."""

    def __init__(self, title: str, filename: str) -> None:
        self.title = title
        self.path = REPORTS_DIR / filename
        self.lines: list[str] = []

    def print(self, *args: Any) -> None:
        line = " ".join(str(a) for a in args)
        print(line)
        self.lines.append(line)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        body = "\n".join(self.lines)
        self.path.write_text(f"# {self.title}\n\n```\n{body}\n```\n")
        print(f"\nReport written to {self.path}")
