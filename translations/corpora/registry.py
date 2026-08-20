"""Reference-corpus declarations, read from ``data_sources/sources.yaml``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from translations.config import PATHS
from vcat.exceptions import ConfigurationError


@dataclass(frozen=True)
class CorpusSpec:
    """One declared reference corpus (see ``reference_corpora`` in sources.yaml)."""

    corpus_id: str
    name: str
    group: str
    language: str
    role: str
    urls: tuple[str, ...]
    filename: str
    format: str
    sha256: str
    licence: str
    retrieved: str
    kind: str

    @property
    def url(self) -> str:
        """First declared URL — the whole source for single-file corpora."""
        return self.urls[0]

    @property
    def path(self) -> Path:
        """Local cache location of the raw file."""
        return PATHS.corpora_cache / self.filename

    @property
    def is_text(self) -> bool:
        """Whether a text loader exists for this entry."""
        return self.kind == "text"


def _urls(corpus_id: str, entry: dict[str, Any]) -> tuple[str, ...]:
    """A spec declares either one ``url`` or an ordered list of ``urls``."""
    if "urls" in entry:
        return tuple(str(url) for url in entry["urls"])
    if "url" in entry:
        return (str(entry["url"]),)
    raise ConfigurationError("Corpus declares no url", {"corpus_id": corpus_id})


def load_specs(sources_yaml: Path | None = None) -> list[CorpusSpec]:
    """Load all corpus specs, ordered by id."""
    path = sources_yaml or PATHS.sources_yaml
    document = yaml.safe_load(path.read_text())
    entries = document.get("reference_corpora")
    if not entries:
        raise ConfigurationError("No reference_corpora section", {"path": str(path)})
    return [
        CorpusSpec(
            corpus_id=corpus_id,
            name=entry["name"],
            group=entry["group"],
            language=entry["language"],
            role=entry["role"],
            urls=_urls(corpus_id, entry),
            filename=entry["filename"],
            format=entry["format"],
            sha256=entry["sha256"],
            licence=entry["licence"],
            retrieved=str(entry["retrieved"]),
            kind=entry.get("kind", "text"),
        )
        for corpus_id, entry in sorted(entries.items())
    ]


def get_spec(corpus_id: str, sources_yaml: Path | None = None) -> CorpusSpec:
    """Look up one corpus spec by id."""
    for spec in load_specs(sources_yaml):
        if spec.corpus_id == corpus_id:
            return spec
    raise ConfigurationError("Unknown corpus", {"corpus_id": corpus_id})
