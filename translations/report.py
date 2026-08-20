"""Report emitters. Every artifact carries the speculative banner (plan §0.4)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from translations.config import SPECULATIVE_BANNER


@dataclass(frozen=True)
class Topic:
    """One Phase 1 topic report: markdown sections plus machine-readable data."""

    topic: str
    title: str
    sections: list[str]
    data: dict[str, Any]


def banner_markdown(banner: str = SPECULATIVE_BANNER) -> str:
    """The mandatory banner, as a markdown blockquote."""
    return f"> **{banner}**"


def table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Render a markdown table."""
    lines = [
        "| " + " | ".join(_escape(str(header)) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines += ["| " + " | ".join(_escape(fmt(cell)) for cell in row) + " |" for row in rows]
    return "\n".join(lines)


def _escape(cell: str) -> str:
    """Escape pipes so view names like ``T1-glyph|CB=break`` do not split cells."""
    return cell.replace("|", "\\|")


def fmt(value: Any) -> str:
    """Format a cell: floats to 3 significant decimals, None as an em dash."""
    if value is None:
        return "—"
    if hasattr(value, "item"):  # numpy scalar
        value = value.item()
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.3f}" if abs(value) < 1000 else f"{value:,.0f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _json_safe(value: Any) -> Any:
    """Convert numpy scalars (and anything else exotic) to plain JSON types."""
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def write_report(
    directory: Path,
    topic: str,
    title: str,
    sections: list[str],
    data: dict[str, Any],
    banner: str = SPECULATIVE_BANNER,
) -> tuple[Path, Path]:
    """Write ``<topic>.md`` and ``<topic>.json`` with the banner attached."""
    directory.mkdir(parents=True, exist_ok=True)
    md_path = directory / f"{topic}.md"
    json_path = directory / f"{topic}.json"

    body = "\n\n".join([f"# {title}", banner_markdown(banner), *sections])
    md_path.write_text(body.rstrip() + "\n")
    json_path.write_text(
        json.dumps(
            {"banner": banner, "topic": topic, **data},
            indent=2,
            sort_keys=True,
            default=_json_safe,
        )
        + "\n"
    )
    return md_path, json_path
