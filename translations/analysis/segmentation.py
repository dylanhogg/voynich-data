"""Word-internal segmentation: Harris boundaries and an MDL slot inventory.

Two independent routes to the same question — where do Voynichese words break
internally? Harris successor/predecessor entropy is distribution-free; the MDL
inventory is a model-selection answer. Where they agree, the boundary is real;
where they disagree, the report says so. The MDL inventory is what defines the
``T2-slot`` tokenization.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

Units = tuple[str, ...]

MAX_AFFIX_LENGTH = 3


def _entropy(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total <= 1:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counts.values() if count)


def successor_entropies(words: list[Units], reverse: bool = False) -> dict[Units, float]:
    """Successor (or predecessor) entropy of every prefix of every word."""
    following: dict[Units, Counter[str]] = {}
    for word in words:
        sequence = tuple(reversed(word)) if reverse else word
        for index in range(len(sequence)):
            following.setdefault(sequence[:index], Counter())[sequence[index]] += 1
    return {prefix: _entropy(counts) for prefix, counts in following.items()}


def harris_segment(
    word: Units, forward: dict[Units, float], backward: dict[Units, float]
) -> list[Units]:
    """Split a word at successor-entropy peaks confirmed from both directions."""
    if len(word) < 3:
        return [word]
    cuts: list[int] = []
    for index in range(1, len(word)):
        here = forward.get(word[:index], 0.0)
        before = forward.get(word[: index - 1], 0.0)
        after = forward.get(word[: index + 1], 0.0)
        reversed_word = tuple(reversed(word))
        back = backward.get(reversed_word[: len(word) - index], 0.0)
        back_after = backward.get(reversed_word[: len(word) - index + 1], 0.0)
        if here > before and here >= after and back >= back_after:
            cuts.append(index)
    pieces: list[Units] = []
    start = 0
    for cut in cuts:
        pieces.append(word[start:cut])
        start = cut
    pieces.append(word[start:])
    return [piece for piece in pieces if piece]


@dataclass(frozen=True)
class SlotModel:
    """Prefix / root / suffix inventories induced by MDL (defines ``T2-slot``)."""

    prefixes: tuple[Units, ...]
    suffixes: tuple[Units, ...]

    def __post_init__(self) -> None:
        # Stored longest-first so that segmentation is longest-match without re-sorting.
        object.__setattr__(self, "prefixes", tuple(sorted(self.prefixes, key=len, reverse=True)))
        object.__setattr__(self, "suffixes", tuple(sorted(self.suffixes, key=len, reverse=True)))

    def segment(self, word: Units) -> list[Units]:
        """Split a word into (prefix?, root, suffix?), longest match first."""
        prefix: Units = ()
        suffix: Units = ()
        remainder = word
        for candidate in self.prefixes:
            if len(remainder) > len(candidate) and remainder[: len(candidate)] == candidate:
                prefix, remainder = candidate, remainder[len(candidate) :]
                break
        for candidate in self.suffixes:
            if len(remainder) > len(candidate) and remainder[-len(candidate) :] == candidate:
                suffix, remainder = candidate, remainder[: -len(candidate)]
                break
        return [piece for piece in (prefix, remainder, suffix) if piece]

    def as_dict(self) -> dict[str, list[str]]:
        """JSON-friendly form."""
        return {
            "prefixes": ["".join(prefix) for prefix in self.prefixes],
            "suffixes": ["".join(suffix) for suffix in self.suffixes],
        }


def description_length(model: SlotModel, types: Counter[Units], alphabet: int) -> float:
    """Bits to encode the segment inventory plus the corpus under it."""
    segments: Counter[Units] = Counter()
    for word, count in types.items():
        for piece in model.segment(word):
            segments[piece] += count
    total = sum(segments.values())
    corpus_bits = -sum(count * math.log2(count / total) for count in segments.values())
    model_bits = sum(len(piece) * math.log2(alphabet) + 1 for piece in segments)
    return corpus_bits + model_bits


def induce_slots(
    words: list[Units], candidates: int = 20, max_affixes: int = 10
) -> tuple[SlotModel, dict[str, float]]:
    """Greedily add the affix that most reduces description length.

    Deliberately small: a big inventory would fit anything, and the point is to
    find the few affixes that actually pay for themselves.
    """
    types = Counter(words)
    alphabet = len({unit for word in words for unit in word}) or 1

    prefix_counts: Counter[Units] = Counter()
    suffix_counts: Counter[Units] = Counter()
    for word, count in types.items():
        for size in range(1, min(MAX_AFFIX_LENGTH, len(word) - 1) + 1):
            prefix_counts[word[:size]] += count
            suffix_counts[word[-size:]] += count

    pool = [("prefix", affix) for affix, _ in prefix_counts.most_common(candidates)]
    pool += [("suffix", affix) for affix, _ in suffix_counts.most_common(candidates)]

    model = SlotModel(prefixes=(), suffixes=())
    best = description_length(model, types, alphabet)
    history = [best]
    for _ in range(max_affixes):
        scored: list[tuple[float, SlotModel]] = []
        for kind, affix in pool:
            if affix in (model.prefixes if kind == "prefix" else model.suffixes):
                continue
            candidate = (
                SlotModel((*model.prefixes, affix), model.suffixes)
                if kind == "prefix"
                else SlotModel(model.prefixes, (*model.suffixes, affix))
            )
            scored.append((description_length(candidate, types, alphabet), candidate))
        if not scored:
            break
        length, candidate = min(scored, key=lambda item: item[0])
        if length >= best:
            break
        model, best = candidate, length
        history.append(best)

    return model, {
        "initial_description_length": history[0],
        "final_description_length": best,
        "bits_saved": history[0] - best,
        "affixes": float(len(model.prefixes) + len(model.suffixes)),
    }
