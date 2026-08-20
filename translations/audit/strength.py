"""Strength evidence: what would make the translation credible (plan §7.1).

Each test produces a number and the null it has to beat. None of them is
allowed to be reported without its null, and a test that cannot run says so
rather than being quietly dropped.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import replace
from functools import lru_cache
from typing import Any

import numpy as np

from translations.alignment import build_rows
from translations.audit.common import (
    NEUTRAL,
    NOT_RUN,
    SUPPORTS,
    UNDERMINES,
    VACUOUS,
    Check,
    Finding,
    Harness,
    gated_words,
)
from translations.config import CONFIG
from translations.corpora import load_corpus
from translations.decipher.anchors import CATALOGUE
from translations.decipher.lm import corpus_lm
from translations.decode import KeyedHypothesis
from translations.pipeline import GlossCache, TranslatedLine
from translations.render import GATED_MASK, gated
from translations.report import table
from translations.tokenize import Merges, apply_merges, glyphs

# Published in `reports/phase3/round2_findings.md` and the dataset card: how
# much the two EVA transcriptions agree with each other before any pipeline
# touches them. A gloss agreement below this is noise.
ZL_IT_LINE_IDENTITY = 0.293
ENGLISH_CORPORA: tuple[str, ...] = ("douay_rheims", "austen_pride_prejudice")
BIGRAM_WORDS = 300_000
REFERENCE_WORDS = 20_000


def synthetic_recovery(harness: Harness) -> Check:
    """§7.1.1 — the ceiling: how well the pipeline does when it is given a real cipher."""
    rows = [
        {
            "hypothesis": name,
            "corpus": value.corpus,
            "scheme": value.scheme,
            "tokens": value.n_tokens,
            "key_accuracy": value.key_accuracy,
            "token_accuracy": value.token_accuracy,
        }
        for name, value in sorted(harness.maps.items())
    ]
    primary = harness.maps[harness.primary.hypothesis_id]
    detail = (
        table(
            [
                "hypothesis",
                "corpus",
                "scheme",
                "synthetic tokens",
                "key accuracy",
                "gloss accuracy",
            ],
            [
                [
                    row["hypothesis"],
                    row["corpus"],
                    row["scheme"],
                    row["tokens"],
                    row["key_accuracy"],
                    row["token_accuracy"],
                ]
                for row in rows
            ],
        )
        + "\n\nThese are the numbers from `make calibrate`: a reference corpus in the language "
        "each hypothesis assumes, enciphered under its own scheme, attacked blind. They bound "
        "what this pipeline could achieve *if* the manuscript were the system the hypothesis "
        "describes. They say nothing about whether it is."
    )
    return Check(
        Finding(
            test="§7.1.1 synthetic recovery",
            metric=f"{harness.primary.hypothesis_id} gloss accuracy on ciphertext we built",
            value=primary.token_accuracy,
            null=f"key accuracy {primary.key_accuracy:.3f}",
            verdict=NEUTRAL,
            implication=(
                "A ceiling, not evidence. The pipeline recovers a key it is given, which is "
                "why a confident-looking rendering proves nothing on its own."
            ),
        ),
        detail,
        {"synthetic": rows},
    )


def _page_split(lines: list[TranslatedLine]) -> tuple[dict[str, float], dict[str, bool]]:
    """Per-page gated coverage and held-out flag."""
    covered: dict[str, list[float]] = {}
    held: dict[str, bool] = {}
    for line in lines:
        for token in line.tokens:
            covered.setdefault(line.page_id, []).append(
                1.0 if gated(token.rendered) != GATED_MASK else 0.0
            )
        held[line.page_id] = line.is_holdout
    return {page: float(np.mean(values)) for page, values in covered.items()}, held


def holdout_generalisation(harness: Harness, lines: list[TranslatedLine]) -> Check:
    """§7.1.2 — does the key learned on training pages degrade on held-out ones?"""
    covered, held = _page_split(lines)
    pages = sorted(covered)
    values = np.array([covered[page] for page in pages])
    flags = np.array([held[page] for page in pages])
    observed = float(values[~flags].mean() - values[flags].mean())

    rng = harness.rng("holdout-permutation")
    permuted = list(flags)
    hits = 0
    for _ in range(CONFIG.audit_permutations):
        rng.shuffle(permuted)
        mask = np.array(permuted)
        delta = float(values[~mask].mean() - values[mask].mean())
        hits += abs(delta) >= abs(observed)
    p_value = (hits + 1) / (CONFIG.audit_permutations + 1)

    detail = (
        table(
            ["split", "pages", "gated coverage"],
            [
                ["train", int((~flags).sum()), float(values[~flags].mean())],
                ["holdout", int(flags.sum()), float(values[flags].mean())],
                ["difference", "", observed],
            ],
        )
        + f"\n\nThe held-out pages were never seen by any key search. Permuting the held-out "
        f"label across the {len(pages)} pages {CONFIG.audit_permutations:,} times puts the "
        f"observed difference at p = {p_value:.3f}. A pipeline that had learned something "
        "specific to the training pages would degrade on the held-out ones; a pipeline "
        "matching a Latin dictionary against short strings has nothing page-specific to lose."
    )
    return Check(
        Finding(
            test="§7.1.2 held-out generalisation",
            metric="train − holdout gated coverage",
            value=observed,
            null=f"permutation p = {p_value:.3f}",
            verdict=UNDERMINES if p_value > 0.05 else SUPPORTS,
            implication=(
                "Held-out and training pages are indistinguishable, which is what a "
                "dictionary-matching pipeline looks like — it is not evidence of generalisation."
                if p_value > 0.05
                else "Held-out pages differ from training pages beyond chance."
            ),
        ),
        detail,
        {
            "train": float(values[~flags].mean()),
            "holdout": float(values[flags].mean()),
            "difference": observed,
            "p_value": p_value,
            "pages": len(pages),
        },
    )


def _gloss_of(form: str, hypothesis: KeyedHypothesis, merges: Merges, cache: GlossCache) -> str:
    """Decode and gloss one surface form, outside any view."""
    if not form:
        return ""
    gloss = cache.best(hypothesis.decode(apply_merges(glyphs(form), merges)).plaintext)
    return gloss.english if gloss else ""


def cross_transcription(harness: Harness) -> Check:
    """§7.1.3 — the same pipeline on IT: do the two transcriptions gloss the same?"""
    rows = [row for row in build_rows() if row.status == "aligned" and row.it_form]
    surface = sum(1 for row in rows if row.zl_form == row.it_form) / len(rows)
    glossed = [
        (
            _gloss_of(row.zl_form, harness.primary, harness.merges, harness.cache),
            _gloss_of(row.it_form, harness.primary, harness.merges, harness.cache),
        )
        for row in rows
    ]
    same = sum(1 for left, right in glossed if left == right) / len(rows)
    differing = [
        (left, right)
        for row, (left, right) in zip(rows, glossed, strict=True)
        if row.zl_form != row.it_form
    ]
    on_differing = (
        sum(1 for left, right in differing if left == right) / len(differing) if differing else 0.0
    )

    detail = (
        table(
            ["comparison", "tokens", "agreement"],
            [
                ["surface forms identical (ZL vs IT)", len(rows), surface],
                ["glosses identical, all aligned tokens", len(rows), same],
                ["glosses identical, tokens whose surfaces differ", len(differing), on_differing],
                ["published line-level identity baseline", "", ZL_IT_LINE_IDENTITY],
            ],
        )
        + f"\n\nThe headline agreement ({same:.1%}) is not a measure of stability: it is "
        f"carried almost entirely by the {surface:.1%} of tokens the two transcribers already "
        "write identically, plus the tokens that gloss to nothing under either reading.\n\n"
        f"On the tokens they actually disagree about, the glosses agree only {on_differing:.1%} "
        "of the time. Which English word a line receives is therefore decided by which "
        "transcriber's reading you happen to load — and only 29.3% of lines are identical "
        "between the two. A rendering this sensitive to transcription noise cannot be a "
        "property of the manuscript."
    )
    return Check(
        Finding(
            test="§7.1.3 cross-transcription stability",
            metric="gloss agreement on tokens whose ZL and IT surfaces differ",
            value=on_differing,
            null=f"surface agreement {surface:.3f}; line identity {ZL_IT_LINE_IDENTITY}",
            verdict=UNDERMINES,
            implication=(
                "Where the two transcriptions disagree, so do the glosses, four times out of "
                "five. The reading is a property of the transcription, not of the manuscript."
            ),
        ),
        detail,
        {
            "surface_agreement": surface,
            "gloss_agreement": same,
            "gloss_agreement_on_differing": on_differing,
            "aligned_tokens": len(rows),
            "differing_tokens": len(differing),
            "line_identity_baseline": ZL_IT_LINE_IDENTITY,
        },
    )


def internal_consistency(harness: Harness, lines: list[TranslatedLine]) -> Check:
    """§7.1.4 — the same type glossed the same way, and what that is worth."""
    by_type: dict[str, set[str]] = {}
    for line in lines:
        for token in line.tokens:
            by_type.setdefault(token.surface, set()).add(token.english)
    determinism = sum(1 for senses in by_type.values() if len(senses) == 1) / len(by_type)

    printed = gated_words(lines)
    distinct_words = len(set(printed))
    types_printed = len(
        {
            token.surface
            for line in lines
            for token in line.tokens
            if gated(token.rendered) != GATED_MASK
        }
    )
    collision = types_printed / max(distinct_words, 1)
    common = Counter(
        (token.surface, token.english)
        for line in lines
        for token in line.tokens
        if gated(token.rendered) != GATED_MASK
    )
    per_word: Counter[str] = Counter()
    for (_, english), _ in common.items():
        per_word[english] += 1
    worst = per_word.most_common(10)

    detail = (
        table(
            ["measure", "value"],
            [
                ["types glossed identically everywhere", determinism],
                ["distinct Voynich types printed by the gated view", types_printed],
                ["distinct English words they print", distinct_words],
                ["Voynich types per English word", collision],
            ],
        )
        + "\n\nThe first row is 1.000 **by construction**: glossing is a pure function of the "
        "type, so consistency across sections, paradigms and repeated phrases cannot come out "
        "any other way. The test as written is vacuous, and the honest number beside it is the "
        f"collapse ratio: {types_printed:,} distinct Voynich types print only {distinct_words:,} "
        f"distinct English words, {collision:.1f} to one.\n\n"
        + table(
            ["English word", "distinct Voynich types rendered as it"],
            [[word, count] for word, count in worst],
        )
    )
    return Check(
        Finding(
            test="§7.1.4 internal consistency",
            metric="Voynich types per distinct English word (gated view)",
            value=collision,
            null="1.0 would be a one-to-one reading",
            verdict=VACUOUS,
            implication=(
                "Consistency is guaranteed by context-free glossing, so it is not evidence. "
                "The collapse ratio it hides is: the rendering is heavily many-to-one."
            ),
        ),
        detail,
        {
            "determinism": determinism,
            "types_printed": types_printed,
            "distinct_words": distinct_words,
            "collision": collision,
            "most_collided": [[word, count] for word, count in worst],
        },
    )


def _jsd(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Jensen–Shannon divergence, row-wise, in bits."""
    m = 0.5 * (p + q)
    with np.errstate(divide="ignore", invalid="ignore"):
        left = np.where(p > 0, p * np.log2(p / m), 0.0)
        right = np.where(q > 0, q * np.log2(q / m), 0.0)
    return 0.5 * (left.sum(axis=-1) + right.sum(axis=-1))


def _concentration(counts: np.ndarray, labels: np.ndarray, n_labels: int) -> float:
    """Token-weighted mean divergence of each group's gloss profile from the pooled one."""
    totals = np.zeros((n_labels, counts.shape[1]))
    np.add.at(totals, labels, counts)
    weights = totals.sum(axis=1)
    keep = weights > 0
    pooled = totals.sum(axis=0)
    pooled = pooled / max(pooled.sum(), 1.0)
    profiles = totals[keep] / weights[keep, None]
    return float((_jsd(profiles, pooled) * weights[keep]).sum() / weights[keep].sum())


def _page_profiles(
    lines: list[TranslatedLine], strata: dict[str, str], surfaces: bool = False
) -> tuple[np.ndarray, np.ndarray, list[str], list[str]]:
    """Per-page vocabulary counts, and each page's illustration type.

    ``surfaces`` counts the untranslated Voynich types instead of the glosses,
    which is what the whole test has to be measured against.
    """
    vocabulary: dict[str, int] = {}
    per_page: dict[str, Counter[str]] = {}
    for line in lines:
        for token in line.tokens:
            if surfaces:
                word = token.surface
            elif (word := gated(token.rendered)) == GATED_MASK:
                continue
            vocabulary.setdefault(word, len(vocabulary))
            per_page.setdefault(line.page_id, Counter())[word] += 1

    pages = sorted(page for page in per_page if strata.get(page))
    types = sorted({strata[page] for page in pages})
    counts = np.zeros((len(pages), len(vocabulary)))
    for index, page in enumerate(pages):
        for word, count in per_page[page].items():
            counts[index, vocabulary[word]] = count
    return counts, np.array([types.index(strata[page]) for page in pages]), types, pages


def _permutation_p(
    harness: Harness,
    counts: np.ndarray,
    labels: np.ndarray,
    n_types: int,
    salt: str,
    within: np.ndarray | None = None,
) -> tuple[float, float]:
    """Observed concentration and its permutation p-value.

    ``within`` restricts the shuffle to pages sharing a value — Currier language,
    say — so a known confound is held constant instead of being permuted away
    along with the effect under test.
    """
    observed = _concentration(counts, labels, n_types)
    rng = harness.rng(salt)
    blocks = (
        [np.flatnonzero(within == value) for value in np.unique(within)]
        if within is not None
        else [np.arange(len(labels))]
    )
    hits = 0
    for _ in range(CONFIG.audit_permutations):
        permuted = labels.copy()
        for block in blocks:
            permuted[block] = rng.sample(list(labels[block]), len(block))
        hits += _concentration(counts, permuted, n_types) >= observed
    return observed, (hits + 1) / (CONFIG.audit_permutations + 1)


def illustration_congruence(
    harness: Harness, lines: list[TranslatedLine], control: list[TranslatedLine]
) -> Check:
    """§7.1.5 — do herbal pages yield plant words? Page level, permutation null."""
    strata = {row.page_id: row.illustration_type for row in harness.base.rows}
    currier = {row.page_id: row.currier_language for row in harness.base.rows}
    counts, labels, types, pages = _page_profiles(lines, strata)
    observed, p_value = _permutation_p(
        harness, counts, labels, len(types), "illustration-permutation"
    )
    # Illustration type is heavily confounded with Currier language, and Currier
    # A and B differ in word length, which alone changes how often a short string
    # hits the Latin lexicon. Permuting only within a Currier group holds that
    # constant.
    blocks = np.array([str(currier.get(page) or "unassigned") for page in pages])
    _, stratified_p = _permutation_p(
        harness, counts, labels, len(types), "illustration-stratified", within=blocks
    )

    # The same statistic on the *untranslated* types. Glossing is a deterministic
    # many-to-one map of the surface form, so by the data-processing inequality it
    # cannot create page structure that the surface types do not already have.
    surface_counts, surface_labels, surface_types, _ = _page_profiles(lines, strata, surfaces=True)
    surface_observed, surface_p = _permutation_p(
        harness, surface_counts, surface_labels, len(surface_types), "illustration-surface"
    )

    # The same test on pseudo-Voynich, wearing the manuscript's own page labels.
    # The control corpus has the manuscript's line and page structure but encodes
    # nothing, so any concentration it shows is a layout artifact.
    control_lines = [replace(line, page_id=page) for line, page in _relabel(lines, control)]
    control_counts, control_labels, control_types, _ = _page_profiles(control_lines, strata)
    control_observed, control_p = _permutation_p(
        harness, control_counts, control_labels, len(control_types), "illustration-control"
    )

    sizes = Counter(strata[page] for page in pages)
    detail = (
        table(
            ["illustration type", "pages", "glossed tokens"],
            [
                [
                    kind,
                    sizes[kind],
                    int(counts[labels == types.index(kind)].sum()),
                ]
                for kind in types
            ],
        )
        + f"\n\nStatistic: token-weighted mean Jensen–Shannon divergence between each "
        f"illustration type's gloss distribution and the pooled one. Observed "
        f"{observed:.4f} bits; permuting the page labels {CONFIG.audit_permutations:,} times "
        f"gives p = {p_value:.3f}.\n\n"
        + table(
            ["corpus scored", "divergence", "permutation p"],
            [
                ["glossed rendering", observed, p_value],
                ["glossed rendering, permuted within Currier language", observed, stratified_p],
                ["untranslated Voynich types", surface_observed, surface_p],
                ["pseudo-Voynich, same page labels", control_observed, control_p],
            ],
        )
        + "\n\nThe third row is what settles this test, and it settles it against the "
        f"rendering. The untranslated Voynich types score {surface_observed:.4f} bits at "
        f"p = {surface_p:.3f}: the manuscript's *own vocabulary* already varies with what is "
        "drawn on the page, which Phase 1 established and which needs no translation to "
        "observe. Glossing is a deterministic many-to-one map of the surface form, so by the "
        "data-processing inequality it cannot manufacture page structure the surface types do "
        f"not already have — and it does not: {observed:.4f} bits against "
        f"{surface_observed:.4f}. The rendering inherits this signal; it does not supply "
        "it.\n\nThe other two rows rule out the cheaper explanations. `grille` encodes "
        "nothing yet inherits the manuscript's line and page structure, so it shows what page "
        f"layout alone produces (p = {control_p:.3f}). And illustration type is heavily "
        "confounded with Currier language, whose two halves differ in word length; permuting "
        f"labels only among pages of the same Currier language still gives p = "
        f"{stratified_p:.3f}, so the effect is not purely that confound.\n\nThe "
        "label-level variant — the sharper test, matching an "
        "individual label to the thing it is drawn beside — needs the illustration↔label "
        "concordance that plan §5.1 lists as an **open gap**. It is not run, and no hand-built "
        "plant or body-part word list stands in for it: that list would be the answer smuggled "
        "into the question."
    )
    return Check(
        Finding(
            test="§7.1.5 illustration congruence",
            metric="gloss-profile divergence across illustration types",
            value=observed,
            null=f"permutation p = {p_value:.3f}",
            verdict=(SUPPORTS if p_value <= 0.05 and control_p > 0.05 else UNDERMINES),
            implication=(
                "Page topic and glossed vocabulary vary together beyond chance, and "
                "pseudo-Voynich under the same page labels does not."
                if p_value <= 0.05 and control_p > 0.05
                else (
                    "Pseudo-Voynich shows the same concentration under the same page labels, "
                    f"at p = {control_p:.3f}, so the signal is a layout artifact rather than "
                    "evidence that the glosses describe what is drawn."
                    if p_value <= 0.05
                    else "Glossed vocabulary carries no signal about what the page depicts. The "
                    "plan named a positive here the strongest possible evidence; this is its "
                    "negation."
                )
            ),
        ),
        detail,
        {
            "statistic": observed,
            "p_value": p_value,
            "stratified_p_value": stratified_p,
            "surface_statistic": surface_observed,
            "surface_p_value": surface_p,
            "control_statistic": control_observed,
            "control_p_value": control_p,
            "types": types,
            "pages": len(pages),
            "label_level": "blocked by open gap §5.1 (illustration↔label concordance)",
        },
    )


@lru_cache(maxsize=4)
def _corpus_split(corpus_id: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """A reference corpus cut into model words and unseen words.

    The two halves must not overlap: the "real English" floor is the corpus
    scoring text it has not seen, and Austen is short enough that a fixed
    300,000-word model slice would swallow the whole book.
    """
    words = load_corpus(corpus_id).words[: BIGRAM_WORDS + REFERENCE_WORDS]
    cut = min(BIGRAM_WORDS, int(len(words) * 0.8))
    return tuple(words[:cut]), tuple(words[cut:])


def _bigram_bits(corpus_id: str, words: list[str]) -> float:
    """Mean bits per word under an add-one bigram model of a reference corpus."""
    corpus, _ = _corpus_split(corpus_id)
    unigram = Counter(corpus)
    bigram = Counter(zip(corpus, corpus[1:], strict=False))
    size = len(unigram) + 1
    pairs = list(zip(words, words[1:], strict=False))
    if not pairs:
        return float("nan")
    total = sum(-math.log2((bigram[pair] + 1.0) / (unigram[pair[0]] + size)) for pair in pairs)
    return total / len(pairs)


def syntactic_plausibility(
    harness: Harness, lines: list[TranslatedLine], control: list[TranslatedLine]
) -> Check:
    """§7.1.6 — is the rendered English English, under models that never saw it?"""
    real = gated_words(lines)
    shuffled = list(real)
    harness.rng("gloss-shuffle").shuffle(shuffled)
    pseudo = gated_words(control)

    variants = {
        "manuscript rendering": real,
        "same glosses, shuffled order": shuffled,
        "pseudo-Voynich rendering": pseudo,
    }
    rows: list[list[Any]] = []
    data: dict[str, Any] = {}
    for corpus_id in ENGLISH_CORPORA:
        model_words, reference = _corpus_split(corpus_id)
        model = corpus_lm(corpus_id, 3, "plain", n_words=len(model_words))
        for name, words in {**variants, "the reference corpus itself": list(reference)}.items():
            chars = model.bits_per_symbol(model.index(" ".join(words)))
            bigram = _bigram_bits(corpus_id, words)
            rows.append([corpus_id, name, len(words), chars, bigram])
            data[f"{corpus_id}|{name}"] = {"char_bits": chars, "word_bits": bigram}

    detail = (
        table(["English model", "text scored", "words", "bits/char", "bits/word (bigram)"], rows)
        + "\n\nTwo models per corpus, because the character model is nearly blind to word "
        "order — it reads a shuffled rendering almost as happily as the original, which is why "
        "the plan's shuffle comparator needs the word-bigram column beside it to have any "
        "power at all. The reference row is the same corpus scoring unseen text from itself: "
        "the floor a genuinely English rendering would approach."
    )
    baseline = data[f"{ENGLISH_CORPORA[0]}|the reference corpus itself"]["word_bits"]
    observed = data[f"{ENGLISH_CORPORA[0]}|manuscript rendering"]["word_bits"]
    shuffle_bits = data[f"{ENGLISH_CORPORA[0]}|same glosses, shuffled order"]["word_bits"]
    return Check(
        Finding(
            test="§7.1.6 syntactic plausibility",
            metric=f"bits/word of the rendering under a {ENGLISH_CORPORA[0]} bigram model",
            value=observed,
            null=f"shuffled {shuffle_bits:.2f}; real English {baseline:.2f}",
            verdict=SUPPORTS if observed < shuffle_bits - 0.5 else UNDERMINES,
            implication=(
                "The rendering is no more English-like in its word order than the same words "
                "in random order, and both are far from real English."
                if observed >= shuffle_bits - 0.5
                else "Word order in the rendering carries information a bigram model can use."
            ),
        ),
        detail,
        data,
    )


def anchor_agreement(harness: Harness) -> Check:
    """§7.1.7 — do external cribs agree with the key? Blocked: the catalogue is empty."""
    detail = (
        "The anchor catalogue in `translations/decipher/anchors.py` is empty, and deliberately "
        "so: an anchor enters it only with a checksummed source behind it. Plan §5.1 lists the "
        "three sources that would fill it — the zodiac month-name marginalia, the f116v "
        "marginalia, and the v101 mapping — as **still open** after Phase 3. Entering them by "
        "hand would put an unsourced answer into the audit that is supposed to test the answer."
    )
    return Check(
        Finding(
            test="§7.1.7 anchor agreement",
            metric="catalogued anchors",
            value=len(CATALOGUE),
            null="—",
            verdict=NOT_RUN,
            implication="Blocked by the three open §5.1 gaps; no anchor evidence exists either way.",
        ),
        detail,
        {"anchors": len(CATALOGUE)},
    )


def _relabel(
    lines: list[TranslatedLine], control: list[TranslatedLine]
) -> list[tuple[TranslatedLine, str]]:
    """Pair control lines with the manuscript page each one stands in for.

    The control view is generated line-for-line from the manuscript, so the two
    lists are positionally aligned; the control's own line ids are synthetic.
    """
    return list(zip(control, [line.page_id for line in lines], strict=True))


def run(
    harness: Harness, lines: list[TranslatedLine], control: list[TranslatedLine]
) -> list[Check]:
    """The whole §7.1 battery, in plan order."""
    return [
        synthetic_recovery(harness),
        holdout_generalisation(harness, lines),
        cross_transcription(harness),
        internal_consistency(harness, lines),
        illustration_congruence(harness, lines, control),
        syntactic_plausibility(harness, lines, control),
        anchor_agreement(harness),
    ]
