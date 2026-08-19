"""Extraction and normalisation of reference corpora to a common form.

Two steps, kept separate so each is testable:

1. **extract** — remove the delivery format's furniture (Project Gutenberg
   header/footer, verse references) leaving running text;
2. **normalise** — casefold, optionally fold diacritics, drop everything that
   is not a letter or a space.

The normalised form yields a word stream and a char stream. The char stream is
the words concatenated *without* separators, matching how
``translations.tokenize.unit_stream`` drops word boundaries on the Voynich side.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable

from vcat.exceptions import ConfigurationError

_GUTENBERG_START = re.compile(r"^\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG.*$", re.M)
_GUTENBERG_END = re.compile(r"^\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG.*$", re.M)
_VERSE_REF = re.compile(r"^\[\d+:\d+\]\s*", re.M)
_BOOK_HEADING = re.compile(r"^###.*$", re.M)
_NOT_LETTER = re.compile(r"[^a-z ]+")

# Ligatures and letters that NFKD does not decompose.
_LIGATURES = {"æ": "ae", "œ": "oe", "ß": "ss", "ø": "o", "đ": "d", "ð": "d", "þ": "th"}


def strip_gutenberg(text: str) -> str:
    """Return the body of a Project Gutenberg text, without header or footer."""
    start = _GUTENBERG_START.search(text)
    end = _GUTENBERG_END.search(text)
    body = text[start.end() if start else 0 : end.start() if end else len(text)]
    return body.strip()


def strip_verse_refs(text: str) -> str:
    """Drop ``### Book`` headings and ``[chapter:verse]`` references."""
    return _VERSE_REF.sub("", _BOOK_HEADING.sub("", text)).strip()


EXTRACTORS: dict[str, Callable[[str], str]] = {
    "gutenberg": strip_gutenberg,
    "verses": strip_verse_refs,
    "plain": str.strip,
}


def extract(text: str, format: str) -> str:
    """Apply the extractor named by a corpus spec's ``format`` field."""
    if format not in EXTRACTORS:
        raise ConfigurationError("Unknown corpus format", {"format": format})
    return EXTRACTORS[format](text)


def normalise(text: str, fold_diacritics: bool = True) -> str:
    """Lowercase, optionally fold diacritics, keep only letters and spaces."""
    result = text.lower()
    for ligature, replacement in sorted(_LIGATURES.items()):
        result = result.replace(ligature, replacement)
    if fold_diacritics:
        decomposed = unicodedata.normalize("NFKD", result)
        result = "".join(char for char in decomposed if not unicodedata.combining(char))
    result = _NOT_LETTER.sub(" ", result)
    return " ".join(result.split())


def word_stream(text: str) -> list[str]:
    """Words of already-normalised text."""
    return text.split()


def char_stream(text: str) -> str:
    """Characters of already-normalised text, word separators removed."""
    return text.replace(" ", "")
