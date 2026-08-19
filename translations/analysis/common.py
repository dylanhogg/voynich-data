"""Corpus views: the unit of analysis shared by every Phase 1 module.

A :class:`View` is a tokenized corpus — lines of words of units — carrying its
own name so that every reported number says which slice of which transcription
under which tokenization produced it. Voynich views, baseline views (reference
corpora, sample-size matched) and null views (surrogates) are all the same type,
so a metric written once runs on all three.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from translations.config import CONFIG, CommaPolicy, Tokenizer, Transcription
from translations.corpora import load_corpus, subsample_words
from translations.io import Line, Mismatch, load_lines, load_mismatches, transcription_text
from translations.nulls import (
    grille,
    markov_chars,
    markov_words,
    selfcite,
    shuffle_chars,
    shuffle_within_word,
    shuffle_word_order,
)
from translations.nulls.pseudo import SyllableTable, induce_table
from translations.strata import StratumRow, build_strata
from translations.tokenize import tokenize_line

Word = list[str]
LineWords = list[Word]

BOUNDARY = "#"


@dataclass
class View:
    """A tokenized corpus slice."""

    name: str
    lines: list[LineWords]
    rows: list[StratumRow] = field(default_factory=list)
    words: list[Word] = field(init=False)
    forms: list[str] = field(init=False)
    units: list[str] = field(init=False)

    def __post_init__(self) -> None:
        self.words = [word for line in self.lines for word in line]
        self.forms = ["".join(word) for word in self.words]
        self.units = [unit for word in self.words for unit in word]

    @property
    def n_words(self) -> int:
        """Token count."""
        return len(self.words)

    @property
    def n_units(self) -> int:
        """Unit (glyph or character) count, separators excluded."""
        return len(self.units)

    @property
    def n_types(self) -> int:
        """Word type count."""
        return len(set(self.forms))

    def with_lines(self, name: str, lines: list[LineWords]) -> View:
        """A derived view with the same provenance but different content."""
        return View(name=name, lines=lines)


@lru_cache(maxsize=1)
def _source_data() -> tuple[list[Line], dict[str, Mismatch], list[StratumRow]]:
    return load_lines(), load_mismatches(), build_strata()


def voynich_view(
    name: str | None = None,
    tokenizer: Tokenizer = CONFIG.default_tokenizer,
    comma: CommaPolicy = CONFIG.default_comma_policy,
    transcription: Transcription = CONFIG.default_transcription,
    keep: Callable[[StratumRow], bool] | None = None,
    alternative: int = 0,
) -> View:
    """Build a Voynich view, optionally filtered by a stratum predicate."""
    lines, mismatches, strata = _source_data()
    by_id = {row.line_id: row for row in strata}

    kept_lines: list[LineWords] = []
    kept_rows: list[StratumRow] = []
    for line in lines:
        row = by_id[line.line_id]
        if keep is not None and not keep(row):
            continue
        text = transcription_text(line, mismatches.get(line.line_id), transcription, alternative)
        if not text:
            continue
        kept_lines.append(tokenize_line(text, tokenizer, comma))
        kept_rows.append(row)

    label = name or f"voynich|{tokenizer}|{comma}|{transcription}"
    return View(name=label, lines=kept_lines, rows=kept_rows)


def is_prose(row: StratumRow) -> bool:
    """Running-prose rule: paragraph lines off circular/radial pages (§3.6)."""
    return (
        row.line_type == "paragraph"
        and row.illustration_type not in CONFIG.prose_exclude_illustration
    )


def baseline_view(corpus_id: str, n_words: int, rng: random.Random, line_length: int = 8) -> View:
    """A reference corpus subsampled to ``n_words`` and cut into pseudo-lines.

    Characters are the units, and lines are fixed-length blocks: reference
    corpora have no line structure comparable to the manuscript's, so the block
    length only exists to give the block bootstrap something to resample.
    """
    corpus = load_corpus(corpus_id)
    sample = subsample_words(corpus, n_words, rng)
    words = [list(word) for word in sample]
    lines = [words[start : start + line_length] for start in range(0, len(words), line_length)]
    return View(name=f"baseline|{corpus_id}", lines=lines)


def _relines(words: list[Word], template: list[LineWords]) -> list[LineWords]:
    """Cut a flat word list into lines matching the template's line lengths."""
    lines: list[LineWords] = []
    cursor = 0
    for line in template:
        lines.append(words[cursor : cursor + len(line)])
        cursor += len(line)
    if cursor < len(words):
        lines.append(words[cursor:])
    return [line for line in lines if line]


def null_view(kind: str, view: View, rng: random.Random, order: int = 2) -> View:
    """Build a surrogate of ``view``. ``kind`` is one of :data:`NULL_KINDS`."""
    if kind == "shuffle_chars":
        words = shuffle_chars(view.words, rng)
    elif kind == "shuffle_within_word":
        words = shuffle_within_word(view.words, rng)
    elif kind == "shuffle_word_order":
        words = shuffle_word_order(view.words, rng)
    elif kind == "markov_chars":
        words = markov_chars(view.words, order, rng)
    elif kind == "markov_words":
        words = markov_words(view.words, order, rng)
    else:
        raise ValueError(f"unknown null kind: {kind}")
    suffix = f"|n={order}" if kind.startswith("markov") else ""
    return View(name=f"null|{kind}{suffix}", lines=_relines(words, view.lines))


NULL_KINDS: tuple[str, ...] = (
    "shuffle_chars",
    "shuffle_within_word",
    "shuffle_word_order",
    "markov_chars",
    "markov_words",
)


def grille_view(view: View, rng: random.Random, table_size: int = 16, n_grilles: int = 1) -> View:
    """Rugg-style table-generated pseudo-Voynich, matched in token count."""
    table: SyllableTable = induce_table(view.words, size=table_size)
    words = grille(table, view.n_words, rng, n_grilles=n_grilles)
    name = f"pseudo|grille|size={table_size}|g={n_grilles}"
    return View(name=name, lines=_relines(words, view.lines))


def selfcite_view(
    view: View, rng: random.Random, window: int = 20, mutation_rate: float = 0.3
) -> View:
    """Timm-style autocopying pseudo-Voynich, matched in token count."""
    words = selfcite(view.words, view.n_words, rng, window=window, mutation_rate=mutation_rate)
    name = f"pseudo|selfcite|w={window}|m={mutation_rate}"
    return View(name=name, lines=_relines(words, view.lines))


def encode_lines(view: View, with_boundaries: bool = True) -> list[np.ndarray]:
    """Encode each line separately, sharing one vocabulary across the view.

    Lines are the blocks the bootstrap resamples, so they must be encoded
    independently but comparably.
    """
    per_line: list[list[str]] = []
    for line in view.lines:
        stream: list[str] = []
        for word in line:
            stream.extend(word)
            if with_boundaries:
                stream.append(BOUNDARY)
        per_line.append(stream)
    vocabulary = {
        unit: index for index, unit in enumerate(sorted({u for s in per_line for u in s}))
    }
    return [
        np.fromiter((vocabulary[unit] for unit in stream), dtype=np.int64, count=len(stream))
        for stream in per_line
    ]


def text_of(view: View, separator: str = ".") -> str:
    """The view as flat text, for compression-based estimates."""
    return separator.join(view.forms)


def encode_units(view: View, with_boundaries: bool = True) -> np.ndarray:
    """Encode the view as an integer array for fast n-gram counting.

    With ``with_boundaries``, a boundary symbol separates words, so word-length
    structure is part of the sequence rather than silently discarded.
    """
    stream: list[str] = []
    for word in view.words:
        stream.extend(word)
        if with_boundaries:
            stream.append(BOUNDARY)
    vocabulary = {unit: index for index, unit in enumerate(sorted(set(stream)))}
    return np.fromiter((vocabulary[unit] for unit in stream), dtype=np.int64, count=len(stream))


def encode_forms(forms: Iterable[str]) -> np.ndarray:
    """Encode word forms as integers, ids assigned in sorted order."""
    materialised = list(forms)
    vocabulary = {form: index for index, form in enumerate(sorted(set(materialised)))}
    return np.fromiter(
        (vocabulary[form] for form in materialised), dtype=np.int64, count=len(materialised)
    )
