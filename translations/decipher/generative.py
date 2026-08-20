"""Description lengths for the "no plaintext" and "structure only" hypotheses.

H6a (Rugg grille) and H6b (Timm autocopying) are live rivals, not strawmen, so
they are coded on exactly the same scale as the cipher hypotheses: bits to
reconstruct the observed glyph stream. H8 (morphology) and H9 (slot grammar)
describe word structure without claiming a plaintext, and are coded the same way.
"""

from __future__ import annotations

import math
from collections import Counter

from translations.analysis.common import View
from translations.analysis.fsa import Automaton, merge_k_tails, prefix_tree
from translations.analysis.segmentation import description_length, induce_slots
from translations.analysis.syntax import edit_within
from translations.decipher.score import Description
from translations.nulls.pseudo import induce_table

GRILLE_SIZES: tuple[int, ...] = (24, 48, 96)
GRILLE_COUNTS: tuple[int, ...] = (4, 8, 16)
SELFCITE_WINDOW = 20
MAX_EDIT = 3


def literal_bits(word: list[str], alphabet: int) -> float:
    """Bits to spell a word out glyph by glyph, plus its length."""
    return (len(word) + 1) * math.log2(alphabet + 1)


def grille_description(view: View) -> Description:
    """H6a: syllable table plus Cardan grilles, fitted by minimum description length."""
    alphabet = len({unit for word in view.words for unit in word})
    best: Description | None = None

    for size in GRILLE_SIZES:
        table = induce_table(view.words, size=size)
        rows = max(len(column) for column in table.columns)
        table_bits = sum(
            len(part) * math.log2(alphabet) + 1.0 for column in table.columns for part in column
        )
        for count in GRILLE_COUNTS:
            vocabulary = {
                "".join(
                    column[(row + offset) % len(column)]
                    for offset, column in zip(offsets, table.columns, strict=True)
                )
                for offsets in _grille_offsets(count, table, rows)
                for row in range(rows)
            }
            model = table_bits + count * len(table.columns) * math.log2(max(rows, 2)) + 32
            index_bits = math.log2(max(len(vocabulary), 2))
            data = 0.0
            for word in view.words:
                form = "".join(word)
                data += 1.0 + (index_bits if form in vocabulary else literal_bits(word, alphabet))
            candidate = Description(
                hypothesis="H6a",
                model_bits=model,
                data_bits=data,
                n_tokens=view.n_words,
                detail=f"table={size}, grilles={count}, generated types={len(vocabulary)}",
            )
            if best is None or candidate.total_bits < best.total_bits:
                best = candidate

    assert best is not None
    return best


def _grille_offsets(count: int, table: object, rows: int) -> list[tuple[int, ...]]:
    """Evenly spread grille offsets — deterministic, and cheaper to encode than random ones."""
    columns = 3
    return [
        tuple(
            (index * (rows // max(count, 1)) + column) % max(rows, 1) for column in range(columns)
        )
        for index in range(count)
    ]


def selfcite_description(view: View, window: int = SELFCITE_WINDOW) -> Description:
    """H6b:每 token is a copy of a recent token plus an edit script, or a literal."""
    alphabet = len({unit for word in view.words for unit in word})
    words = view.words
    copy_index_bits = math.log2(max(window, 2))
    operation_bits = math.log2(max(alphabet, 2)) + 2

    data = 0.0
    copies = 0
    for position, word in enumerate(words):
        literal = literal_bits(word, alphabet)
        best = literal
        if position:
            length_bits = math.log2(max(len(word) + 1, 2))
            for previous in words[max(0, position - window) : position]:
                distance = edit_within(word, previous, MAX_EDIT)
                if distance > MAX_EDIT:
                    continue
                cost = copy_index_bits + distance * (operation_bits + length_bits) + 2
                best = min(best, cost)
        data += 1.0 + best
        copies += best < literal
    return Description(
        hypothesis="H6b",
        model_bits=64.0,
        data_bits=data,
        n_tokens=view.n_words,
        detail=f"window={window}, tokens coded as copies={copies}",
    )


def morphology_description(view: View) -> Description:
    """H8: the MDL slot inventory from Phase 1, priced as a code."""
    words = [tuple(word) for word in view.words]
    alphabet = len({unit for word in words for unit in word}) or 1
    model, stats = induce_slots(words)
    total = description_length(model, Counter(words), alphabet)
    inventory_bits = sum(
        len(affix) * math.log2(alphabet) + 1.0 for affix in (*model.prefixes, *model.suffixes)
    )
    return Description(
        hypothesis="H8",
        model_bits=inventory_bits,
        data_bits=total - inventory_bits,
        n_tokens=view.n_words,
        detail=(
            f"{len(model.prefixes)} prefixes, {len(model.suffixes)} suffixes, "
            f"{stats['bits_saved']:.0f} bits saved vs no affixes"
        ),
    )


def _automaton_bits(automaton: Automaton, alphabet: int) -> float:
    return automaton.n_transitions * (
        math.log2(max(alphabet, 2)) + math.log2(max(automaton.n_states, 2))
    ) + automaton.n_states * (1 + math.log2(max(alphabet, 2)))


def slot_grammar_description(view: View, k: int = 2) -> Description:
    """H9: a generated vocabulary — the induced acceptor priced as a code."""
    words = [tuple(word) for word in view.words]
    alphabet = len({unit for word in words for unit in word}) or 1
    automaton = merge_k_tails(prefix_tree(sorted(set(words))), k)

    data = 0.0
    accepted = 0
    for word in view.words:
        state = 0
        bits = 0.0
        walk_ok = True
        for unit in word:
            transitions = automaton.transitions[state]
            options = len(transitions) + (1 if state in automaton.accepting else 0)
            following = transitions.get(unit)
            if following is None:
                walk_ok = False
                break
            bits += math.log2(max(options, 2))
            state = following
        if walk_ok and state in automaton.accepting:
            options = len(automaton.transitions[state]) + 1
            data += 1.0 + bits + math.log2(max(options, 2))
            accepted += 1
        else:
            data += 1.0 + literal_bits(word, alphabet)
    return Description(
        hypothesis="H9",
        model_bits=_automaton_bits(automaton, alphabet),
        data_bits=data,
        n_tokens=view.n_words,
        detail=(
            f"k={k}, {automaton.n_states} states, "
            f"{accepted / max(view.n_words, 1):.1%} of tokens accepted"
        ),
    )
