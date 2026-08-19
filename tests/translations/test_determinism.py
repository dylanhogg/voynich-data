"""The determinism contract: same seed and inputs, same bytes."""

from __future__ import annotations

import json
from pathlib import Path

from translations.config import PATHS
from translations.determinism import (
    build_manifest,
    config_hash,
    derived_rng,
    sha256_bytes,
    stable_json,
    write_manifest,
)


def test_derived_rng_is_reproducible_and_salt_dependent() -> None:
    assert [derived_rng("a").random() for _ in range(3)] == [
        derived_rng("a").random() for _ in range(3)
    ]
    assert derived_rng("a").random() != derived_rng("b").random()


def test_config_hash_is_stable() -> None:
    assert config_hash() == config_hash()
    assert len(config_hash()) == 64


def test_stable_json_sorts_keys() -> None:
    assert stable_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_manifest_has_no_varying_fields() -> None:
    inputs = [PATHS.eva_lines]
    first = build_manifest(inputs, {"phase": 0})
    second = build_manifest(inputs, {"phase": 0})
    assert first == second
    assert "eva_lines.jsonl" in str(first["inputs"])
    assert not any("time" in key for key in first)


def test_write_manifest_is_byte_identical_across_runs(tmp_path: Path) -> None:
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"
    write_manifest(first, [PATHS.eva_lines])
    write_manifest(second, [PATHS.eva_lines])
    assert sha256_bytes(first.read_bytes()) == sha256_bytes(second.read_bytes())
    assert json.loads(first.read_text())["banner"].startswith("SPECULATIVE OUTPUT")
