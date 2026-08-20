"""Structural priors from Phase 1 (plan §4.3.4).

A search that starts from uniform noise wastes its budget rediscovering things
Phase 1 already established. Three priors are used:

- the **merge pool** for H2 is seeded with the morphs Harris segmentation and the
  MDL induction found (`qo`, `che`, `ol`, `dy`, …), not only with frequent n-grams;
- key search starts from a **frequency-matched** assignment (in `search.py`);
- **A/B structure** is a prior on the search *design*: Currier A and B are
  searched separately as well as together, because Phase 1 showed they behave
  like different systems.
"""

from __future__ import annotations

import json

from translations.config import PATHS
from translations.decipher.channel import CipherText, Merge
from translations.decipher.search import candidate_merges
from translations.tokenize import glyphs

MORPHOLOGY_REPORT = PATHS.reports_dir / "morphology.json"


def phase1_morphs(limit: int = 20) -> tuple[str, ...]:
    """Morph strings induced in Phase 1, most frequent first."""
    if not MORPHOLOGY_REPORT.exists():
        return ()
    data = json.loads(MORPHOLOGY_REPORT.read_text())
    harris = [morph for morph, _ in data.get("harris", {}).get("top_morphs", [])][:limit]
    slots = data.get("slot_model", {})
    return tuple(dict.fromkeys([*harris, *slots.get("prefixes", []), *slots.get("suffixes", [])]))


def morph_merges(minimum_units: int = 2) -> tuple[Merge, ...]:
    """Phase 1 morphs expressed as merges over glyph units."""
    merges = []
    for morph in phase1_morphs():
        units = tuple(glyphs(morph))
        if len(units) >= minimum_units:
            merges.append(units)
    return tuple(dict.fromkeys(merges))


def merge_pool(ciphertext: CipherText, top: int = 40) -> tuple[Merge, ...]:
    """Frequent unit n-grams plus the Phase 1 morphs, de-duplicated."""
    frequent = candidate_merges(ciphertext, top)
    return tuple(dict.fromkeys([*morph_merges(), *frequent]))
