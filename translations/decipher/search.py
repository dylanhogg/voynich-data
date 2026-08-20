"""Deterministic key search: EM initialisation, annealing, and the merge search.

All searches are seeded, iteration-counted and *anytime*: they carry their
best-so-far, so a truncated run is still a reportable result (plan §4.3.6).
Determinism is defined by iteration count, never by elapsed time.

Not implemented: Bayesian/Gibbs decipherment (Ravi & Knight). With a 25-symbol
cipher alphabet and a quadgram-class LM, annealing with restarts reaches the
same optimum far inside the budget; Gibbs earns its keep on key spaces an order
of magnitude larger, which is H5 territory and H5 is unfunded here.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from translations.decipher.channel import CipherText, Merge, merge_units
from translations.decipher.lm import ALPHABET, CharLM
from translations.decipher.score import (
    NgramIndex,
    ambiguity_bits,
    lm_bits,
    ngram_index,
)

if TYPE_CHECKING:  # imported for typing only; keeps the search layer dependency-light
    from translations.analysis.common import View
    from translations.decipher.budget import Deadline

LETTER_IDS = tuple(range(1, len(ALPHABET)))


@dataclass
class SearchResult:
    """Best key found, with everything needed to report it honestly."""

    key: np.ndarray
    bits: float
    iterations: int
    restarts: int
    evaluations: int
    converged: bool
    truncated: bool = False
    trace: list[float] = field(default_factory=list)


def score_key(key: np.ndarray, index: NgramIndex, lm: CharLM) -> float:
    """Data bits for a key: plaintext under the LM plus ambiguity."""
    return lm_bits(key, index, lm) + ambiguity_bits(key, index)


def can_be_injective(size: int) -> bool:
    """Whether a cipher alphabet of ``size`` (boundary included) fits in the letters.

    A 263-unit fixed-width channel cannot have an injective key into 26 letters,
    and pretending otherwise silently disables most of the annealer's moves.
    """
    return size - 1 <= len(LETTER_IDS)


def random_key(size: int, rng: random.Random, injective: bool = True) -> np.ndarray:
    """A starting key. Injective keys are permutations of distinct letters."""
    injective = injective and can_be_injective(size)
    key = np.zeros(size, dtype=np.int64)
    letters = list(LETTER_IDS)
    rng.shuffle(letters)
    for unit in range(1, size):
        key[unit] = (
            letters[unit - 1] if injective and unit - 1 < len(letters) else rng.choice(LETTER_IDS)
        )
    return key


def em_initialise(index: NgramIndex, lm: CharLM, size: int, iterations: int = 20) -> np.ndarray:
    """Frequency-matching initialisation by iterative proportional assignment.

    This is the cheap end of statistical decipherment (Knight et al.): match the
    cipher unit frequencies to the language's letter frequencies, then let the
    annealer do the contextual work. It costs nothing and starts the search in a
    far better place than noise.
    """
    unigram = lm.table
    for _ in range(lm.order - 1):
        unigram = unigram.mean(axis=0)
    letter_order = [letter for letter in np.argsort(-unigram) if letter != 0]
    unit_order = [unit for unit in np.argsort(-index.unit_counts) if unit != 0]

    key = np.zeros(size, dtype=np.int64)
    for position, unit in enumerate(unit_order):
        key[unit] = letter_order[min(position, len(letter_order) - 1)]
    return key


def anneal(
    index: NgramIndex,
    lm: CharLM,
    size: int,
    rng: random.Random,
    iterations: int,
    initial: np.ndarray | None = None,
    injective: bool = True,
    start_fraction: float = 0.01,
    end_fraction: float = 0.00002,
) -> tuple[np.ndarray, float, int]:
    """Simulated annealing over substitution keys. Returns (key, bits, evaluations).

    Temperatures are set as a fraction of the initial score, so the schedule is
    scale-free: the same settings work for a 10k-token synthetic ciphertext and
    for the whole manuscript.
    """
    injective = injective and can_be_injective(size)
    key = (initial if initial is not None else random_key(size, rng, injective)).copy()
    current = score_key(key, index, lm)
    best_key, best_bits = key.copy(), current
    start_temperature = max(current * start_fraction, 1e-6)
    end_temperature = max(current * end_fraction, 1e-9)
    ratio = end_temperature / start_temperature

    for step in range(iterations):
        temperature = start_temperature * ratio ** (step / max(iterations - 1, 1))
        unit = rng.randrange(1, size)
        if injective:
            other = rng.randrange(1, size)
            if other == unit:
                unused = [letter for letter in LETTER_IDS if letter not in set(key[1:])]
                if not unused:
                    continue
                proposal = key.copy()
                proposal[unit] = rng.choice(unused)
            else:
                proposal = key.copy()
                proposal[unit], proposal[other] = key[other], key[unit]
        else:
            proposal = key.copy()
            proposal[unit] = rng.choice(LETTER_IDS)

        candidate = score_key(proposal, index, lm)
        delta = candidate - current
        if delta <= 0 or rng.random() < np.exp(-delta / temperature):
            key, current = proposal, candidate
            if current < best_bits:
                best_key, best_bits = key.copy(), current

    return best_key, best_bits, iterations


def search_key(
    ciphertext: CipherText,
    lm: CharLM,
    rng: random.Random,
    iterations: int,
    restarts: int,
    injective: bool = True,
    index: NgramIndex | None = None,
) -> SearchResult:
    """Multi-restart annealing. Restart 0 starts from the EM initialisation."""
    index = index or ngram_index(ciphertext, lm.order)
    best_key: np.ndarray | None = None
    best_bits = float("inf")
    evaluations = 0
    trace: list[float] = []

    for restart in range(restarts):
        initial = (
            em_initialise(index, lm, ciphertext.size)
            if restart == 0
            else random_key(ciphertext.size, rng, injective)
        )
        key, bits, used = anneal(index, lm, ciphertext.size, rng, iterations, initial, injective)
        evaluations += used
        trace.append(bits)
        if bits < best_bits:
            best_key, best_bits = key, bits

    assert best_key is not None
    # Converged when the best two restarts agree to within a bit per thousand tokens.
    ordered = sorted(trace)
    converged = len(ordered) > 1 and (ordered[1] - ordered[0]) < ciphertext.n_tokens / 1000
    return SearchResult(
        key=best_key,
        bits=best_bits,
        iterations=iterations,
        restarts=restarts,
        evaluations=evaluations,
        converged=converged,
        trace=trace,
    )


def candidate_merges(ciphertext: CipherText, top: int = 24) -> tuple[Merge, ...]:
    """Frequent unit bigrams and trigrams — the pool the H2 search chooses from."""
    ids = ciphertext.ids
    pairs: dict[Merge, int] = {}
    for length in (2, 3):
        columns = [ids[offset : ids.size - length + 1 + offset] for offset in range(length)]
        stacked = np.stack(columns, axis=1)
        valid = (stacked != 0).all(axis=1)
        for row in stacked[valid]:
            merge = tuple(ciphertext.units[unit] for unit in row)
            pairs[merge] = pairs.get(merge, 0) + 1
    ranked = sorted(pairs.items(), key=lambda item: (-item[1], item[0]))
    return tuple(merge for merge, _ in ranked[:top])


@dataclass
class MergeResult:
    """Best merge partition found for the verbose-cipher hypothesis (H2)."""

    merges: tuple[Merge, ...]
    ciphertext: CipherText
    key: np.ndarray
    total_bits: float
    outer_steps: int
    evaluations: int
    truncated: bool = False
    trace: list[float] = field(default_factory=list)


def merge_search(
    view: View,
    lm: CharLM,
    rng: random.Random,
    pool: tuple[Merge, ...],
    outer_steps: int,
    inner_iterations: int,
    inner_restarts: int,
    width: int = 8,
    initial: tuple[Merge, ...] = (),
    deadline: Deadline | None = None,
) -> MergeResult:
    """Search over glyph-merge partitions, scoring each by its best key.

    This is the plan's highest-value single experiment (§4.3.3): if Voynichese
    spells one plaintext letter with several glyphs, the right merge should make
    the text look like language and the wrong ones should not.

    Stochastic steepest descent: each step samples ``width`` moves (add, remove
    or swap a merge), scores them all with a full inner key search, and takes the
    best improvement. Plain hill-climbing wanders in this space — verifiable on
    the synthetic verbose cipher, where steepest descent recovers the hidden
    pairs and hill-climbing does not.
    """
    from translations.decipher.score import substitution_description

    def evaluate(merges: tuple[Merge, ...]) -> tuple[float, CipherText, np.ndarray]:
        ciphertext = merge_units(view, merges, f"merged|{len(merges)}")
        index = ngram_index(ciphertext, lm.order)
        result = search_key(ciphertext, lm, rng, inner_iterations, inner_restarts, index=index)
        description = substitution_description(
            result.key, index, lm, ciphertext, "H2", merges=merges
        )
        return description.total_bits, ciphertext, result.key

    def propose(current: tuple[Merge, ...]) -> tuple[Merge, ...] | None:
        available = [merge for merge in pool if merge not in current]
        moves = ["add"] if not current else ["add", "remove", "swap"]
        move = rng.choice([m for m in moves if m != "add" or available] or ["remove"])
        candidate = list(current)
        if move in {"remove", "swap"}:
            candidate.remove(rng.choice(candidate))
        if move in {"add", "swap"} and available:
            candidate.append(rng.choice(available))
        proposal = tuple(sorted(set(candidate)))
        return proposal if proposal != current else None

    current: tuple[Merge, ...] = tuple(sorted(set(initial)))
    best_bits, best_cipher, best_key = evaluate(current)
    best_merges = current
    trace = [best_bits]
    evaluations = 1
    truncated = False

    for _ in range(outer_steps):
        if deadline is not None and deadline.expired:
            truncated = True
            break
        scored: list[tuple[float, tuple[Merge, ...], CipherText, np.ndarray]] = []
        seen: set[tuple[Merge, ...]] = set()
        for _ in range(width):
            proposal = propose(current)
            if proposal is None or proposal in seen:
                continue
            seen.add(proposal)
            bits, ciphertext, key = evaluate(proposal)
            evaluations += 1
            scored.append((bits, proposal, ciphertext, key))
        if not scored:
            break
        bits, proposal, ciphertext, key = min(scored, key=lambda item: item[0])
        trace.append(bits)
        if bits >= best_bits:
            break
        best_bits, best_merges, best_cipher, best_key = bits, proposal, ciphertext, key
        current = proposal

    return MergeResult(
        merges=best_merges,
        ciphertext=best_cipher,
        key=best_key,
        total_bits=best_bits,
        outer_steps=outer_steps,
        evaluations=evaluations,
        truncated=truncated,
        trace=trace,
    )
