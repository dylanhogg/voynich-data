"""Determinism contract (plan §2.2).

Rules enforced here:

- every stochastic algorithm takes an explicit :class:`random.Random`, obtained
  from :func:`derived_rng` so that a run is a pure function of the global seed;
- run provenance is written as a manifest of input checksums, config hash, git
  commit and package versions — with no wall-clock or other varying fields, so
  two runs of the same code on the same inputs produce byte-identical output.
"""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np

from translations.config import CONFIG, PATHS, SPECULATIVE_BANNER
from vcat.logging import get_logger

logger = get_logger(__name__)

# Distributions whose versions are recorded in every run manifest.
RECORDED_PACKAGES: tuple[str, ...] = ("vcat-data", "pyyaml", "pandas", "numpy", "scipy")


def derived_rng(salt: str) -> random.Random:
    """Return an RNG seeded from the global seed and ``salt``.

    Distinct salts give independent streams; the same salt always gives the
    same stream, regardless of call order.
    """
    digest = hashlib.sha256(f"{CONFIG.seed}:{salt}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def derived_numpy_rng(salt: str) -> np.random.Generator:
    """NumPy generator seeded the same deterministic way as :func:`derived_rng`."""
    digest = hashlib.sha256(f"{CONFIG.seed}:{salt}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def sha256_bytes(data: bytes) -> str:
    """SHA256 of a byte string."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """SHA256 of a file's contents."""
    return sha256_bytes(path.read_bytes())


def stable_json(obj: Any) -> str:
    """Serialise ``obj`` to JSON with sorted keys and no incidental whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def config_hash() -> str:
    """Hash of the frozen experiment configuration (paths excluded)."""
    return sha256_bytes(stable_json(asdict(CONFIG)).encode())


def git_commit() -> str:
    """Current git commit, or ``"unknown"`` outside a checkout."""
    try:
        result = subprocess.run(
            ["git", "-C", str(PATHS.repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip()


def package_versions() -> dict[str, str]:
    """Versions of the distributions recorded in the manifest."""
    versions: dict[str, str] = {}
    for name in sorted(RECORDED_PACKAGES):
        try:
            versions[name] = version(name)
        except PackageNotFoundError:
            versions[name] = "absent"
    return versions


def build_manifest(
    inputs: Iterable[Path], extra: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Build a run manifest. Contains no timestamps by design."""
    return {
        "banner": SPECULATIVE_BANNER,
        "config_hash": config_hash(),
        "seed": CONFIG.seed,
        "git_commit": git_commit(),
        "packages": package_versions(),
        "inputs": {
            str(path.relative_to(PATHS.repo_root)): sha256_file(path) for path in sorted(inputs)
        },
        **(dict(extra) if extra else {}),
    }


def write_manifest(
    path: Path, inputs: Iterable[Path], extra: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Write a run manifest to ``path`` and return it."""
    manifest = build_manifest(inputs, extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    logger.info("Wrote manifest", path=str(path), config_hash=manifest["config_hash"])
    return manifest
