"""Reference-corpus declarations, extraction, normalisation and sample matching."""

from __future__ import annotations

import pytest

from translations.corpora import Corpus, available, load_corpus, load_specs, subsample_words
from translations.corpora.normalise import (
    char_stream,
    extract,
    normalise,
    strip_gutenberg,
    strip_verse_refs,
    word_stream,
)
from translations.determinism import derived_rng, sha256_file

GUTENBERG = (
    "The Project Gutenberg eBook of Something\nboilerplate\n"
    "*** START OF THE PROJECT GUTENBERG EBOOK SOMETHING ***\n"
    "Gallia est omnis divisa in partes tres.\n"
    "*** END OF THE PROJECT GUTENBERG EBOOK SOMETHING ***\n"
    "more boilerplate\n"
)
VERSES = "### Genesis\n\n[1:1] In principio creavit Deus cælum et terram.\n"


def test_strip_gutenberg_keeps_only_the_body() -> None:
    assert strip_gutenberg(GUTENBERG) == "Gallia est omnis divisa in partes tres."


def test_strip_verse_refs() -> None:
    assert strip_verse_refs(VERSES) == "In principio creavit Deus cælum et terram."


def test_extract_dispatches_on_format() -> None:
    assert extract(VERSES, "verses").startswith("In principio")
    assert extract("  plain  ", "plain") == "plain"


def test_normalise_folds_case_diacritics_and_ligatures() -> None:
    assert normalise("In principio creavit Deus cælum et terram.") == (
        "in principio creavit deus caelum et terram"
    )
    assert normalise("Übermäßig, naïve") == "ubermassig naive"


def test_normalise_can_keep_diacritics_distinct_from_folding() -> None:
    assert normalise("créé", fold_diacritics=False) == "cr"


def test_word_and_char_streams_agree() -> None:
    text = normalise(extract(VERSES, "verses"))
    assert word_stream(text)[:2] == ["in", "principio"]
    assert char_stream(text) == "".join(word_stream(text))


def test_specs_are_well_formed() -> None:
    specs = load_specs()
    assert specs
    assert [spec.corpus_id for spec in specs] == sorted(spec.corpus_id for spec in specs)
    for spec in specs:
        assert len(spec.sha256) == 64
        assert spec.format in {"gutenberg", "verses", "plain"}
        assert spec.kind in {"text", "lexicon"}
        assert spec.licence and spec.role and spec.retrieved


def test_latin_and_english_groups_are_represented() -> None:
    groups = {spec.group for spec in load_specs()}
    assert {"latin", "english", "germanic", "romance", "contrast", "lexicon"} <= groups


@pytest.mark.skipif(not available(), reason="corpora not fetched; run `make corpora`")
def test_cached_corpora_match_their_checksums() -> None:
    for spec in available():
        assert sha256_file(spec.path) == spec.sha256


@pytest.mark.skipif(not available(), reason="corpora not fetched; run `make corpora`")
def test_load_corpus_normalises() -> None:
    corpus = load_corpus("vulgate_clementine")
    assert corpus.words[:3] == ["in", "principio", "creavit"]
    assert corpus.n_chars == len(corpus.chars)
    assert all(word.isalpha() for word in corpus.words[:1000])


def test_subsample_is_contiguous_and_matched() -> None:
    corpus = Corpus(spec=load_specs()[0], words=[f"w{index}" for index in range(100)])
    sample = subsample_words(corpus, 10, derived_rng("test"))
    assert len(sample) == 10
    start = corpus.words.index(sample[0])
    assert sample == corpus.words[start : start + 10]
    assert sample == subsample_words(corpus, 10, derived_rng("test"))
    assert subsample_words(corpus, 500, derived_rng("test")) == corpus.words
