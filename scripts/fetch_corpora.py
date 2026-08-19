#!/usr/bin/env python3
"""Fetch and verify the reference corpora declared in data_sources/sources.yaml.

Idempotent: files that exist and match their recorded SHA256 are left alone.
A mismatch is fatal — the checksum is the provenance contract (plan §2.4).

Usage:
    uv run python scripts/fetch_corpora.py
"""

from __future__ import annotations

import sys
from urllib.error import URLError
from urllib.request import Request, urlopen

from translations.corpora.registry import load_specs
from translations.determinism import sha256_bytes

USER_AGENT = "VCAT/0.2.3 (Voynich Computational Analysis Toolkit)"


def fetch(url: str) -> bytes:
    """Download a URL, or exit with a clear message."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request) as response:  # noqa: S310 (URLs come from sources.yaml)
            data: bytes = response.read()
    except URLError as error:
        sys.exit(f"  ERROR: failed to download {url}: {error}")
    return data


def main() -> int:
    """Fetch every declared corpus and verify its checksum."""
    specs = load_specs()
    specs[0].path.parent.mkdir(parents=True, exist_ok=True)

    failures = 0
    for spec in specs:
        print(f"{spec.corpus_id} ({spec.language}, {spec.group})")
        if spec.path.exists() and sha256_bytes(spec.path.read_bytes()) == spec.sha256:
            print("  ✓ cached, checksum matches")
            continue

        data = fetch(spec.url)
        actual = sha256_bytes(data)
        if actual != spec.sha256:
            print(f"  ✗ checksum mismatch\n    expected {spec.sha256}\n    actual   {actual}")
            failures += 1
            continue
        spec.path.write_bytes(data)
        print(f"  ✓ downloaded and verified ({len(data):,} bytes)")

    if failures:
        print(f"\n{failures} corpus/corpora failed verification")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
