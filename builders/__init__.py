"""
VCAT Builders Module
====================

Dataset builders for VCAT outputs.

This module provides builders that transform parsed transcription data
into standardized dataset formats suitable for publication on HuggingFace
and analysis.

Main functions:
    build_eva_lines: Build the EVA lines dataset from parsed IVTFF data
    build_metadata_datasets: Build page/folio/quire metadata datasets
    build_mismatch_index: Build cross-transcription comparison index
    run_smoke_test: Run validation smoke tests on the built dataset

Classes:
    LineRecord: Dataclass representing a single line in the dataset
    BuildReport: Dataclass containing build statistics and metadata
    PageRecord: Page-level metadata record
    FolioRecord: Folio-level metadata record
    QuireRecord: Quire-level metadata record
    MetadataBuildResult: Result from metadata build process
    MetadataBuildReport: Report from metadata build process
    MismatchRecord: Cross-transcription comparison record
    MismatchIndexBuilder: Builder for mismatch index

Example:
    >>> from builders import build_eva_lines, run_smoke_test
    >>> records, report = build_eva_lines(
    ...     source_path="data_sources/raw_sources/ZL3b-n.txt",
    ...     output_dir="output"
    ... )
    >>> len(records)
    4072
    >>> report.page_count
    226
    >>> run_smoke_test("output/eva_lines.parquet")
    True

    >>> from builders import build_metadata_datasets
    >>> result = build_metadata_datasets("ZL3b-n.txt", "output/metadata")
    >>> len(result.pages)
    226

    >>> from builders import build_mismatch_index
    >>> result = build_mismatch_index()
    >>> result['records_count']
    4072

Output formats:
    - Parquet: Efficient columnar format for analysis
    - JSONL: Human-readable line-delimited JSON
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

# Public name -> "module:attribute" it is re-exported from.
#
# Resolved on first access rather than at import time: eager re-exports would put
# builders.build_metadata (and friends) in sys.modules whenever the package is
# imported, so `python -m builders.build_metadata` would execute that file a
# second time as __main__ and warn about it. Two copies of a module mean two
# copies of its dataclasses, so isinstance() across them fails.
_EXPORTS = {
    # EVA Lines Builder
    "BuildReport": ".build_eva_lines:BuildReport",
    "LineRecord": ".build_eva_lines:LineRecord",
    "build_eva_lines": ".build_eva_lines:build_eva_lines",
    "run_smoke_test": ".build_eva_lines:run_smoke_test",
    # Metadata Builder
    "MetadataBuildReport": ".build_metadata:MetadataBuildReport",
    "MetadataBuildResult": ".build_metadata:MetadataBuildResult",
    "build_metadata_datasets": ".build_metadata:build_metadata_datasets",
    "export_metadata": ".build_metadata:export_metadata",
    "export_metadata_to_parquet": ".build_metadata:export_to_parquet",
    # Mismatch Index Builder
    "MismatchIndexBuilder": ".build_mismatch_index:MismatchIndexBuilder",
    "MismatchRecord": ".build_mismatch_index:MismatchRecord",
    "TranscriptionLine": ".build_mismatch_index:TranscriptionLine",
    "build_mismatch_index": ".build_mismatch_index:build_mismatch_index",
    # Metadata Records (from parsers)
    "PageRecord": "parsers:PageRecord",
    "FolioRecord": "parsers:FolioRecord",
    "QuireRecord": "parsers:QuireRecord",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Import a re-exported name on first access (PEP 562)."""
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, _, attr_name = _EXPORTS[name].partition(":")
    value = getattr(import_module(module_name, __package__), attr_name)
    globals()[name] = value  # subsequent lookups skip __getattr__
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
