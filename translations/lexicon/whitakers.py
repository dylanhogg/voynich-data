"""Whitaker's Words as a Latin stem -> English gloss table (plan §6.2).

``DICTLINE.GEN`` is a fixed-column file: four 19-character stem slots, then the
part of speech and its codes, then the English meanings. Everything downstream
needs only three things from it — the stems a form could be built on, the
glosses, and the frequency code that decides which entry wins when several
share a stem.

Lookup is deliberately blunt. Latin inflection is stripped by a fixed ending
list rather than a morphological analyser, and the near-miss index covers edit
distance 1 only. A richer analyser would make the gloss *look* better without
making it more likely to be right: the input is a decoded string from a losing
key, not Latin.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from translations.analysis.syntax import edit_within
from translations.corpora.registry import get_spec
from vcat.exceptions import SourceNotFoundError

CORPUS_ID = "whitakers_words"
STEM_SLOTS = (0, 19, 38, 57)
STEM_WIDTH = 19
CODE_SLICE = slice(76, 110)
MEANING_START = 110
ABSENT = "zzz"

# Whitaker's frequency codes, commonest first; anything unrecognised sorts last.
FREQUENCY_ORDER = "ABCDEFIMNX"

# Inflectional endings stripped before a second lookup, longest first. This is a
# coverage device, not a morphology: it is applied to strings that are Latin
# only by hypothesis.
ENDINGS: tuple[str, ...] = (
    "ibus",
    "arum",
    "orum",
    "ntur",
    "erunt",
    "isse",
    "issem",
    "abam",
    "abat",
    "ebam",
    "ebat",
    "amus",
    "atis",
    "emus",
    "etis",
    "ium",
    "ibi",
    "ere",
    "ens",
    "ent",
    "ant",
    "unt",
    "que",
    "ae",
    "am",
    "as",
    "em",
    "es",
    "is",
    "os",
    "um",
    "us",
    "at",
    "et",
    "it",
    "or",
    "ur",
    "im",
    "in",
    "ii",
    "ia",
    "io",
    "iu",
    "a",
    "e",
    "i",
    "o",
    "u",
    "s",
    "m",
    "t",
)

_PARENTHETICAL = re.compile(r"\s*\([^)]*\)")
_BRACKETED = re.compile(r"\s*\[[^\]]*\]")


@dataclass(frozen=True)
class Entry:
    """One dictionary headword."""

    lemma: str
    stems: tuple[str, ...]
    pos: str
    frequency: str
    glosses: tuple[str, ...]

    @property
    def rank(self) -> int:
        """Sort key: commoner words win a contested stem."""
        return FREQUENCY_ORDER.find(self.frequency) % len(FREQUENCY_ORDER)

    @property
    def english(self) -> str:
        """The primary sense, annotations removed."""
        return self.glosses[0] if self.glosses else ""


def clean_gloss(text: str) -> str:
    """Drop parenthetical and bracketed notes from one sense."""
    return _BRACKETED.sub("", _PARENTHETICAL.sub("", text)).strip(" ;,/|")


def parse_line(line: str) -> Entry | None:
    """Parse one ``DICTLINE.GEN`` record, or ``None`` if it carries no gloss."""
    if len(line) <= MEANING_START:
        return None
    stems = tuple(
        stem
        for start in STEM_SLOTS
        if (stem := line[start : start + STEM_WIDTH].strip().lower()) and stem != ABSENT
    )
    codes = line[CODE_SLICE].split()
    glosses = tuple(
        cleaned for sense in line[MEANING_START:].split(";") if (cleaned := clean_gloss(sense))
    )
    if not stems or not glosses:
        return None
    return Entry(
        lemma=stems[0],
        stems=stems,
        pos=codes[0] if codes else "",
        frequency=codes[-2] if len(codes) >= 5 else "X",
        glosses=glosses,
    )


@dataclass(frozen=True)
class Lexicon:
    """Stem index plus a deletion index for edit-distance-1 near misses."""

    entries: tuple[Entry, ...]
    by_stem: dict[str, Entry]
    deletions: dict[str, tuple[str, ...]]

    def lookup(self, form: str) -> Entry | None:
        """Exact stem match."""
        return self.by_stem.get(form)

    def stripped(self, form: str) -> tuple[Entry, str] | None:
        """Match after removing one inflectional ending."""
        for ending in ENDINGS:
            if len(form) > len(ending) and form.endswith(ending):
                entry = self.by_stem.get(form[: -len(ending)])
                if entry is not None:
                    return entry, ending
        return None

    def near(self, form: str) -> Entry | None:
        """Best stem at edit distance 1, or ``None``.

        The deletion index over-generates — ``ab`` and ``ba`` share a deletion
        variant but are two edits apart — so every candidate is verified.
        """
        candidates: set[str] = set()
        for variant in _deletions(form):
            candidates.update(self.deletions.get(variant, ()))
        verified = [stem for stem in candidates if edit_within(list(form), list(stem), 1) <= 1]
        if not verified:
            return None
        best = min(verified, key=lambda stem: (self.by_stem[stem].rank, stem))
        return self.by_stem[best]


def _deletions(form: str) -> list[str]:
    """The form itself plus every single-character deletion of it."""
    return [form] + [form[:index] + form[index + 1 :] for index in range(len(form))]


def build_lexicon(entries: list[Entry]) -> Lexicon:
    """Index entries by stem, commonest entry winning, plus the deletion index."""
    by_stem: dict[str, Entry] = {}
    for entry in entries:
        for stem in entry.stems:
            current = by_stem.get(stem)
            if current is None or entry.rank < current.rank:
                by_stem[stem] = entry
    deletions: dict[str, list[str]] = defaultdict(list)
    for stem in by_stem:
        for variant in _deletions(stem):
            deletions[variant].append(stem)
    return Lexicon(
        entries=tuple(entries),
        by_stem=by_stem,
        deletions={variant: tuple(sorted(stems)) for variant, stems in deletions.items()},
    )


def load_entries(path: Path | None = None) -> list[Entry]:
    """Parse every record of the cached dictionary."""
    source = path or get_spec(CORPUS_ID).path
    if not source.exists():
        raise SourceNotFoundError("Lexicon not fetched; run `make corpora`", path=source)
    # latin-1: the file predates UTF-8 and carries a handful of accented glosses.
    text = source.read_text(encoding="latin-1")
    return [entry for line in text.splitlines() if (entry := parse_line(line)) is not None]


@lru_cache(maxsize=1)
def load_lexicon() -> Lexicon:
    """The cached Latin lexicon."""
    return build_lexicon(load_entries())
