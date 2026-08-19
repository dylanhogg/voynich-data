"""Finite-state acceptor induction over word forms (plan §3.4).

A prefix-tree acceptor is built from word types, then quotiented by Moore
refinement: states are merged when they are indistinguishable by (accepting?,
which symbol leads to which block). The quotient is deterministic and accepts a
superset of the training words, so it can be scored the way a slot grammar
should be — held-out acceptance versus over-generation.
"""

from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass, field

Units = tuple[str, ...]


@dataclass
class Automaton:
    """A deterministic acceptor over unit sequences."""

    transitions: list[dict[str, int]] = field(default_factory=lambda: [{}])
    accepting: set[int] = field(default_factory=set)

    @property
    def n_states(self) -> int:
        """Number of states."""
        return len(self.transitions)

    @property
    def n_transitions(self) -> int:
        """Number of transitions."""
        return sum(len(row) for row in self.transitions)

    def accepts(self, units: Iterable[str]) -> bool:
        """Whether the automaton accepts a unit sequence."""
        state = 0
        for unit in units:
            following = self.transitions[state].get(unit)
            if following is None:
                return False
            state = following
        return state in self.accepting

    def sample(self, rng: random.Random, max_length: int = 15) -> Units | None:
        """Random accepted string, or ``None`` if the walk ran out of length."""
        state = 0
        output: list[str] = []
        for _ in range(max_length):
            options = sorted(self.transitions[state])
            if state in self.accepting and (not options or rng.random() < 1 / (len(options) + 1)):
                return tuple(output)
            if not options:
                return None
            unit = rng.choice(options)
            output.append(unit)
            state = self.transitions[state][unit]
        return tuple(output) if state in self.accepting else None


def prefix_tree(words: Iterable[Units]) -> Automaton:
    """Prefix-tree acceptor over word types."""
    automaton = Automaton()
    for word in words:
        state = 0
        for unit in word:
            following = automaton.transitions[state].get(unit)
            if following is None:
                automaton.transitions.append({})
                following = len(automaton.transitions) - 1
                automaton.transitions[state][unit] = following
            state = following
        automaton.accepting.add(state)
    return automaton


def _tails(automaton: Automaton, state: int, depth: int) -> frozenset[Units]:
    """Accepted continuations of length at most ``depth`` from ``state``."""
    found: set[Units] = set()
    frontier: list[tuple[int, Units]] = [(state, ())]
    for _ in range(depth):
        following: list[tuple[int, Units]] = []
        for current, prefix in frontier:
            for unit, target in automaton.transitions[current].items():
                extended = (*prefix, unit)
                if target in automaton.accepting:
                    found.add(extended)
                following.append((target, extended))
        frontier = following
    if state in automaton.accepting:
        found.add(())
    return frozenset(found)


def merge_k_tails(automaton: Automaton, k: int = 2) -> Automaton:
    """Merge states with identical accepted tails up to length ``k``.

    Unlike exact minimisation — which on a finite word list just rebuilds the
    word list — k-tails merging *generalises*: it is what turns a list of words
    into a slot grammar with an opinion about words it has never seen.
    """
    parent = list(range(automaton.n_states))

    def find(state: int) -> int:
        while parent[state] != state:
            parent[state] = parent[parent[state]]
            state = parent[state]
        return state

    def union(left: int, right: int) -> bool:
        left, right = find(left), find(right)
        if left == right:
            return False
        parent[max(left, right)] = min(left, right)
        return True

    groups: dict[frozenset[Units], int] = {}
    for state in range(automaton.n_states):
        signature = _tails(automaton, state, k)
        if signature in groups:
            union(groups[signature], state)
        else:
            groups[signature] = state

    # Restore determinism: if a merged state has two targets on one symbol, merge them.
    changed = True
    while changed:
        changed = False
        targets: dict[tuple[int, str], int] = {}
        for state in range(automaton.n_states):
            block = find(state)
            for unit, target in automaton.transitions[state].items():
                key = (block, unit)
                if key in targets:
                    changed |= union(targets[key], target)
                else:
                    targets[key] = target

    blocks = sorted({find(state) for state in range(automaton.n_states)})
    remap = {block: index for index, block in enumerate(blocks)}
    remap = {
        block: (0 if block == find(0) else index + 1)
        for index, block in enumerate([block for block in blocks if block != find(0)])
    } | {find(0): 0}

    merged = Automaton(transitions=[{} for _ in blocks], accepting=set())
    for state in range(automaton.n_states):
        block = remap[find(state)]
        for unit, target in automaton.transitions[state].items():
            merged.transitions[block][unit] = remap[find(target)]
        if state in automaton.accepting:
            merged.accepting.add(block)
    return merged


@dataclass(frozen=True)
class FsaScore:
    """How well an induced acceptor describes a vocabulary."""

    states: int
    transitions: int
    train_types: int
    heldout_type_acceptance: float
    token_acceptance: float
    overgeneration: float

    def as_dict(self) -> dict[str, float]:
        """JSON-friendly form."""
        return {
            "states": float(self.states),
            "transitions": float(self.transitions),
            "train_types": float(self.train_types),
            "heldout_type_acceptance": self.heldout_type_acceptance,
            "token_acceptance": self.token_acceptance,
            "overgeneration": self.overgeneration,
        }


def score(
    words: list[list[str]],
    rng: random.Random,
    holdout: float = 0.2,
    samples: int = 2000,
    k: int = 2,
) -> FsaScore:
    """Induce an acceptor on 80% of word types and score it on the rest.

    ``overgeneration`` is the share of strings the automaton generates that
    never occur in the corpus — a slot grammar that accepts everything is not a
    description of anything.
    """
    types = sorted({tuple(word) for word in words})
    shuffled = list(types)
    rng.shuffle(shuffled)
    cut = int(len(shuffled) * (1 - holdout))
    train, test = shuffled[:cut], shuffled[cut:]

    automaton = merge_k_tails(prefix_tree(train), k)
    vocabulary = set(types)
    generated = [automaton.sample(rng) for _ in range(samples)]
    valid = [word for word in generated if word is not None]
    unseen = sum(1 for word in valid if word not in vocabulary)

    return FsaScore(
        states=automaton.n_states,
        transitions=automaton.n_transitions,
        train_types=len(train),
        heldout_type_acceptance=(
            sum(automaton.accepts(word) for word in test) / len(test) if test else 0.0
        ),
        token_acceptance=(
            sum(automaton.accepts(word) for word in words) / len(words) if words else 0.0
        ),
        overgeneration=unseen / len(valid) if valid else 0.0,
    )
