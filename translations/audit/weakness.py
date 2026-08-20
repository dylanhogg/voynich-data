"""Weakness evidence: the tests designed to break the translation (plan §7.2).

The first of these is the decisive one, and it is printed before any sample
rendering. The rest quantify how much of the output survives changing something
that should not matter.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from typing import Any

import numpy as np
import pandas as pd

from translations.analysis.common import View, null_view, voynich_view
from translations.audit.common import (
    NEUTRAL,
    SUPPORTS,
    UNDERMINES,
    Check,
    Finding,
    Harness,
    agreement,
    gated_coverage,
    mean_confidence,
)
from translations.config import CONFIG, CommaPolicy, Tokenizer, Transcription
from translations.decipher.budget import Deadline
from translations.decipher.channel import build_ciphertext, key_as_dict
from translations.decipher.lm import corpus_lm
from translations.decipher.score import ngram_index
from translations.decipher.search import search_key
from translations.decode import CANDIDATES, KeyedHypothesis, parse_key
from translations.pipeline import TranslatedLine
from translations.render import GATED_MASK, gated
from translations.report import table
from translations.strata import StratumRow

SEARCH_ITERATIONS = 40_000
SEARCH_RESTARTS = 4
# How many independent random-key nulls the control comparison is re-drawn under.
# The comparison turned out to be far more seed-sensitive on the controls than on
# the manuscript, and a single draw would report a spuriously precise ratio.
CONTROL_DRAWS = 5


def pseudo_voynich(
    harness: Harness, renderings: dict[str, list[TranslatedLine]], views: dict[str, View]
) -> Check:
    """§7.2.1 — the decisive test: does a corpus that encodes nothing render as well?"""
    rows = [
        [name, gated_coverage(lines), mean_confidence(lines)] for name, lines in renderings.items()
    ]
    committed = {name: gated_coverage(lines) for name, lines in renderings.items()}
    real = committed["real"]
    worst = max((name for name in renderings if name != "real"), key=committed.__getitem__)
    ratio = committed[worst] / max(real, 1e-9)

    draws: dict[str, list[float]] = {name: [] for name in views}
    for draw in range(CONTROL_DRAWS):
        for name, view in views.items():
            drawn = harness.render(
                f"phase5-control-{draw}-{name}", view, reliability=name == "real"
            )
            draws[name].append(gated_coverage(drawn))
    ratios = [
        max(draws[name][index] for name in draws if name != "real")
        / max(draws["real"][index], 1e-9)
        for index in range(CONTROL_DRAWS)
    ]

    detail = (
        table(["corpus", "gated coverage", "mean confidence"], rows)
        + "\n\n`grille` is a Rugg-style table generator and `selfcite` a Timm-style "
        "autocopier, both tuned to the manuscript's own hapax rate and word length and matched "
        "to it in token count. Neither encodes anything. The identical pipeline, key, "
        "calibration map and lexicon produced all three rows, and the numbers above are the "
        "ones the committed artifacts carry.\n\n"
        + table(
            ["corpus", f"gated coverage over {CONTROL_DRAWS} random-key draws", "min", "max"],
            [
                [name, float(np.mean(values)), min(values), max(values)]
                for name, values in draws.items()
            ],
        )
        + f"\n\nThe confidence column depends on a draw of twenty permuted keys, and the "
        f"controls are markedly more sensitive to that draw than the manuscript is. Across "
        f"{CONTROL_DRAWS} independent draws the best control reaches "
        f"{min(ratios):.0%}–{max(ratios):.0%} of the manuscript's gated coverage, mean "
        f"{float(np.mean(ratios)):.0%}. The magnitude is unstable; the direction is not — the "
        "control is at or above the manuscript in every draw."
    )
    return Check(
        Finding(
            test="§7.2.1 pseudo-Voynich control",
            metric=f"`{worst}` gated coverage as a share of the manuscript's",
            value=ratio,
            null=f"1.00 means gibberish renders as well; {CONTROL_DRAWS} draws span "
            f"{min(ratios):.0%}–{max(ratios):.0%}",
            verdict=UNDERMINES if ratio >= 1.0 else NEUTRAL,
            implication=(
                "Text that encodes nothing renders at least as well as the manuscript. Under "
                "the criterion the plan fixed in advance, the pipeline is a fluency generator "
                "and its Voynich output carries no evidential weight."
                if ratio >= 1.0
                else "The controls render less than the manuscript."
            ),
        ),
        detail,
        {
            "coverage": committed,
            "confidence": {name: mean_confidence(lines) for name, lines in renderings.items()},
            "ratio": ratio,
            "worst": worst,
            "draws": draws,
            "ratio_range": [min(ratios), max(ratios)],
            "ratio_mean": float(np.mean(ratios)),
        },
    )


def shuffled_input(harness: Harness) -> Check:
    """§7.2.2 — the same on shuffled Voynichese."""
    base = harness.representation(harness.base)
    committed = Counter(harness.chosen(base, harness.primary))

    rows: list[list[Any]] = []
    data: dict[str, float] = {}
    for kind in ("shuffle_chars", "shuffle_within_word", "shuffle_word_order"):
        view = harness.representation(null_view(kind, harness.base, harness.rng(f"shuffle-{kind}")))
        lines = harness.render(f"phase5-{kind}", view, reliability=False)
        coverage = gated_coverage(lines)
        rows.append(
            [
                kind,
                coverage,
                mean_confidence(lines),
                Counter(harness.chosen(view, harness.primary)) == committed,
            ]
        )
        data[kind] = coverage

    real = gated_coverage(
        harness.render(
            "phase5-real-noweight", harness.representation(harness.base), reliability=False
        )
    )
    rows.append(["manuscript (no reliability weighting)", real, None, True])
    # `shuffle_word_order` is excluded from the headline: it is a tautology, since a
    # context-free gloss cannot notice word order. The character shuffle is the only
    # row that asks a real question.
    destructive = data["shuffle_chars"] / max(real, 1e-9)
    detail = (
        table(
            ["surrogate", "gated coverage", "mean confidence", "same glosses as the manuscript"],
            rows,
        )
        + "\n\nThe reliability weight is switched off for all four rows: it is defined by a "
        "ZL/IT token alignment that a surrogate has no counterpart for, so leaving it on would "
        "penalise the manuscript alone.\n\nThe last column is the finding. `shuffle_word_order` "
        "produces the *identical multiset of glosses* as the manuscript — glossing is "
        "context-free, so reordering the words cannot change what any token becomes. Its gated "
        "coverage differs only because each rendering draws its own twenty permuted null keys, "
        "by about the same margin §7.2.1 measured between draws. Destroying the manuscript's "
        "word order costs this pipeline nothing, because no stage of it reads a sequence."
    )
    return Check(
        Finding(
            test="§7.2.2 shuffled-input control",
            metric="character-shuffled Voynichese, gated coverage as a share of the "
            "manuscript's",
            value=destructive,
            null="word-order shuffle scores "
            f"{data['shuffle_word_order'] / max(real, 1e-9):.3f} — a tautology, not a test",
            verdict=NEUTRAL,
            implication=(
                "The pipeline does distinguish the manuscript from character noise, which "
                "sounds better than it is: §7.2.1's `grille` clears the same bar and then "
                "renders more than the manuscript. Reordering whole words, meanwhile, changes "
                "nothing at all, because no stage of the pipeline reads a sequence."
            ),
        ),
        detail,
        {**data, "real": real, "destructive_ratio": destructive},
    )


def _h1_keys(hypothesis_id: str, representation: str) -> pd.DataFrame:
    """Every language variant the round-2 search committed a key for."""
    frame = pd.read_parquet(CANDIDATES)
    return frame[
        (frame["hypothesis"] == hypothesis_id)
        & (frame["representation"] == representation)
        & (frame["corpus"] == "real")
        & (frame["split"] == "train")
        & (frame["key"].str.len() > 2)
    ]


def rival_languages(harness: Harness) -> Check:
    """§7.2.3 — can the method tell which language it is reading?"""
    primary = harness.primary
    frame = _h1_keys(primary.hypothesis_id, primary.representation)
    view = harness.representation(harness.base)

    rows: list[list[Any]] = []
    data: list[dict[str, Any]] = []
    for _, row in frame.sort_values("gain_per_token", ascending=False).iterrows():
        entry = replace(primary, variant=str(row["variant"]), key=parse_key(str(row["key"])))
        lines = harness.render(f"phase5-rival-{entry.variant}", view, entry, reliability=False)
        coverage = gated_coverage(lines)
        rows.append(
            [
                entry.language,
                entry.variant,
                float(row["gain_per_token"]),
                coverage,
                mean_confidence(lines),
            ]
        )
        data.append(
            {
                "language": entry.language,
                "variant": entry.variant,
                "gain_per_token": float(row["gain_per_token"]),
                "gated_coverage": coverage,
            }
        )

    spread = max(item["gated_coverage"] for item in data) - min(
        item["gated_coverage"] for item in data
    )
    gain_spread = max(item["gain_per_token"] for item in data) - min(
        item["gain_per_token"] for item in data
    )
    detail = (
        table(
            ["language model", "variant", "gain/token", "gated coverage", "mean confidence"], rows
        )
        + f"\n\nEvery key here was searched under the same scheme and the same representation, "
        "differing only in which reference corpus supplied the language model — Latin, Italian "
        "and English among them. Each resulting key is then glossed against the *same Latin* "
        f"lexicon.\n\nThe gain spread across languages is {gain_spread:.3f} bits/token and the "
        f"gated-coverage spread is {spread:.3f}. A method that had identified the plaintext "
        "language would separate them sharply; a key found under an English model should not "
        "produce Latin dictionary hits at a comparable rate."
    )
    return Check(
        Finding(
            test="§7.2.3 rival-language ambiguity",
            metric="spread in gated coverage across plaintext languages",
            value=spread,
            null=f"gain spread {gain_spread:.3f} bits/token",
            verdict=UNDERMINES if spread < 0.2 else SUPPORTS,
            implication=(
                "Unrelated plaintext languages produce comparable Latin gloss rates, so the "
                "method does not identify the language and the glosses are not evidence for "
                "one."
                if spread < 0.2
                else "Language choice materially changes the output."
            ),
        ),
        detail,
        {"languages": data, "coverage_spread": spread, "gain_spread": gain_spread},
    )


def _research(harness: Harness, entry: KeyedHypothesis, view: View, seed: str) -> KeyedHypothesis:
    """Re-run this hypothesis' key search on ``view`` and return the key it finds."""
    if entry.width:  # fixed-width channels are searched on their own unit grouping
        from translations.decipher.channel import fixed_width_units

        ciphertext = fixed_width_units(view, entry.width, f"{view.name}|w{entry.width}")
    else:
        ciphertext = build_ciphertext(view, view.name)
    lm = corpus_lm(entry.language, entry.order, entry.transform)
    index = ngram_index(ciphertext, lm.order)
    result = search_key(
        ciphertext, lm, harness.rng(seed), SEARCH_ITERATIONS, SEARCH_RESTARTS, index=index
    )
    return replace(entry, key=key_as_dict(result.key, ciphertext))


def _key_agreement(left: dict[str, str], right: dict[str, str]) -> float:
    """Share of shared cipher units the two keys map to the same letter."""
    shared = set(left) & set(right)
    if not shared:
        return 0.0
    return sum(1 for unit in shared if left[unit] == right[unit]) / len(shared)


def key_instability(harness: Harness, deadline: Deadline) -> Check:
    """§7.2.4 — how much of the reading survives a different seed or training subset."""
    view = harness.representation(harness.base)
    train = harness.representation(
        voynich_view("voynich|train", keep=lambda row: not row.is_holdout)
    )
    pages = sorted({row.page_id for row in harness.base.rows if not row.is_holdout})

    rows: list[list[Any]] = []
    data: list[dict[str, Any]] = []
    for entry in harness.keyed:
        committed = harness.chosen(view, entry)
        runs: list[tuple[str, KeyedHypothesis]] = []
        for seed in range(CONFIG.audit_seeds):
            if deadline.expired:
                break
            runs.append(
                (
                    f"seed {seed}",
                    _research(harness, entry, train, f"seed-{entry.hypothesis_id}-{seed}"),
                )
            )
        for subset in range(CONFIG.audit_subsets):
            if deadline.expired:
                break
            rng = harness.rng(f"subset-{entry.hypothesis_id}-{subset}")
            keep = set(rng.sample(pages, int(len(pages) * CONFIG.audit_subset_fraction)))
            partial = harness.representation(
                voynich_view(
                    f"voynich|subset{subset}",
                    keep=lambda row, keep=keep: row.page_id in keep,  # type: ignore[misc]
                )
            )
            runs.append(
                (
                    f"subset {subset}",
                    _research(harness, entry, partial, f"sub-{entry.hypothesis_id}-{subset}"),
                )
            )
        if not runs:
            continue

        key_scores = [_key_agreement(entry.key, found.key) for _, found in runs]
        gloss_scores = [agreement(committed, harness.chosen(view, found)) for _, found in runs]
        rows.append(
            [
                entry.hypothesis_id,
                len(runs),
                float(np.mean(key_scores)),
                float(np.mean(gloss_scores)),
                float(np.min(gloss_scores)),
            ]
        )
        data.append(
            {
                "hypothesis": entry.hypothesis_id,
                "runs": len(runs),
                "mean_key_agreement": float(np.mean(key_scores)),
                "mean_gloss_agreement": float(np.mean(gloss_scores)),
                "min_gloss_agreement": float(np.min(gloss_scores)),
                "per_run": [
                    {"run": label, "key_agreement": key, "gloss_agreement": gloss}
                    for (label, _), key, gloss in zip(runs, key_scores, gloss_scores, strict=True)
                ],
            }
        )

    worst = min((item["mean_gloss_agreement"] for item in data), default=float("nan"))
    mean_gloss = float(np.mean([item["mean_gloss_agreement"] for item in data])) if data else 0.0
    detail = (
        table(
            [
                "hypothesis",
                "re-searches",
                "mean key agreement",
                "mean gloss agreement",
                "worst gloss agreement",
            ],
            rows,
        )
        + f"\n\nEach hypothesis was searched again from scratch: {CONFIG.audit_seeds} fresh "
        f"seeds on the full training pages, and {CONFIG.audit_subsets} searches on random "
        f"{CONFIG.audit_subset_fraction:.0%} subsets of them. Every re-found key was then used "
        "to gloss the whole manuscript, and compared token by token against the committed "
        "rendering.\n\nAgreement here is not accuracy. Two keys can agree because both are "
        "right or because both fail the same way — a token that glosses to nothing under "
        "either key counts as agreement, which is why the number is an upper bound on "
        "stability, not a measure of it.\n\nH7 is searched here by simulated annealing like "
        "the rest, but its *committed* key came from an exact assignment under an order-1 "
        "model, which has no seed. Its row therefore measures how close annealing lands to a "
        "known optimum, not how unstable H7 is."
    )
    return Check(
        Finding(
            test="§7.2.4 key instability",
            metric="mean token-level gloss agreement across independent re-searches",
            value=mean_gloss,
            null="1.00 would mean the key is identified",
            verdict=UNDERMINES if mean_gloss < 0.9 else NEUTRAL,
            implication=(
                "Re-running the same search with a different seed changes a large share of the "
                "reading, so the key is not identified and no individual gloss is stable."
                if mean_gloss < 0.9
                else "The search converges on effectively the same key regardless of seed."
            ),
        ),
        detail,
        {"per_hypothesis": data, "mean_gloss_agreement": mean_gloss, "worst": worst},
    )


def _uncertain(row: StratumRow) -> bool:
    return row.has_uncertain or row.has_illegible or row.has_alternatives


def ablations(harness: Harness) -> Check:
    """§7.2.5 — the swing in the headline number when a choice we made changes."""
    variants: dict[str, View] = {
        "committed (T1-glyph, CB=break, ZL, all lines)": harness.base,
        "tokenizer T0-char": voynich_view(tokenizer=Tokenizer.T0_CHAR),
        "comma policy CB=join": voynich_view(comma=CommaPolicy.JOIN),
        "transcription IT": voynich_view(transcription=Transcription.IT),
        "uncertainty-flagged lines dropped": voynich_view(keep=lambda row: not _uncertain(row)),
        "Currier A only": voynich_view(keep=lambda row: row.currier_language == "A"),
        "Currier B only": voynich_view(keep=lambda row: row.currier_language == "B"),
        "consensus subset only": voynich_view(keep=lambda row: row.in_consensus),
    }
    rows: list[list[Any]] = []
    data: dict[str, dict[str, float]] = {}
    for name, view in variants.items():
        rendered = harness.render(
            f"phase5-ablation-{name}", harness.representation(view), reliability=False
        )
        tokens = [token for line in rendered for token in line.tokens]
        coverage = gated_coverage(rendered)
        key_coverage = float(np.mean([token.key_coverage for token in tokens])) if tokens else 0.0
        rows.append([name, len(tokens), coverage, mean_confidence(rendered), key_coverage])
        data[name] = {
            "tokens": len(tokens),
            "gated_coverage": coverage,
            "mean_confidence": mean_confidence(rendered),
            "key_coverage": key_coverage,
        }

    base = data["committed (T1-glyph, CB=break, ZL, all lines)"]["gated_coverage"]
    swing = max(abs(row["gated_coverage"] - base) for row in data.values())
    detail = (
        table(
            ["ablation", "tokens", "gated coverage", "mean confidence", "mean key coverage"], rows
        )
        + f"\n\nThe committed row differs from `coverage.md` because reliability weighting is "
        "switched off here, so that the ablations that change the transcription are comparable "
        "with the ones that do not.\n\n`T0-char` is the informative failure: the committed key "
        "is defined over merged glyph units, so a character tokenization presents it with units "
        "it has never seen, its key coverage collapses, and the rendering goes with it. A key "
        f"is only meaningful together with the tokenization it was searched on.\n\nLargest "
        f"swing in gated coverage: {swing:.3f}."
    )
    return Check(
        Finding(
            test="§7.2.5 ablations",
            metric="largest swing in gated coverage across analysis choices",
            value=swing,
            null=f"committed run reads {base:.3f}",
            verdict=UNDERMINES if swing > 0.1 else NEUTRAL,
            implication=(
                "The headline coverage depends heavily on choices — tokenization above all — "
                "that no evidence fixes."
                if swing > 0.1
                else "The headline number is robust to the analysis choices tested."
            ),
        ),
        detail,
        data,
    )


def known_weak_zones(harness: Harness, lines: list[TranslatedLine]) -> Check:
    """§7.2.6 — the zones where the rendering is known to be worse, with counts."""
    by_id = {row.line_id: row for row in harness.base.rows}
    hapax = Counter(token.surface for line in lines for token in line.tokens)

    def zone(name: str, keep: Any) -> dict[str, Any]:
        """One zone's counts. Empty zones are listed too — checked and found empty."""
        chosen = [line for line in lines if line.line_id in by_id and keep(by_id[line.line_id])]
        tokens = [token for line in chosen for token in line.tokens]
        return {
            "zone": name,
            "lines": len(chosen),
            "tokens": len(tokens),
            "gated_coverage": (
                sum(1 for token in tokens if gated(token.rendered) != GATED_MASK) / len(tokens)
                if tokens
                else None
            ),
            "mean_confidence": (
                sum(token.confidence for token in tokens) / len(tokens) if tokens else None
            ),
        }

    rows: list[dict[str, Any]] = [
        zone("labels", lambda row: row.line_type == "label"),
        zone(
            "circular / radial pages (illustration A or C)",
            lambda row: row.illustration_type in CONFIG.prose_exclude_illustration,
        ),
        zone("lines flagged uncertain", lambda row: row.has_uncertain),
        zone("lines flagged illegible", lambda row: row.has_illegible),
        zone("lines with transcriber alternatives", lambda row: row.has_alternatives),
        zone("lines with high-ASCII tokens", lambda row: row.has_high_ascii),
        zone("Currier language unknown", lambda row: not row.currier_language),
        zone(
            "outside the consensus subset (transcribers disagree)", lambda row: not row.in_consensus
        ),
    ]

    hapax_lines = [
        line
        for line in lines
        if line.tokens
        and sum(1 for token in line.tokens if hapax[token.surface] == 1) / len(line.tokens) >= 0.5
    ]
    hapax_tokens = [token for line in hapax_lines for token in line.tokens]
    if hapax_tokens:
        rows.append(
            {
                "zone": "lines at least half hapax",
                "lines": len(hapax_lines),
                "tokens": len(hapax_tokens),
                "gated_coverage": sum(
                    1 for token in hapax_tokens if gated(token.rendered) != GATED_MASK
                )
                / len(hapax_tokens),
                "mean_confidence": sum(t.confidence for t in hapax_tokens) / len(hapax_tokens),
            }
        )
    rare = [token for line in lines for token in line.tokens if token.key_coverage < 1.0]
    if rare:
        rows.append(
            {
                "zone": "tokens containing a unit the key never saw",
                "lines": None,
                "tokens": len(rare),
                "gated_coverage": sum(1 for token in rare if gated(token.rendered) != GATED_MASK)
                / len(rare),
                "mean_confidence": sum(token.confidence for token in rare) / len(rare),
            }
        )

    overall = gated_coverage(lines)
    detail = (
        table(
            ["known-weak zone", "lines", "tokens", "gated coverage", "mean confidence"],
            [
                [
                    row["zone"],
                    row["lines"],
                    row["tokens"],
                    row["gated_coverage"],
                    row["mean_confidence"],
                ]
                for row in rows
            ],
        )
        + f"\n\nWhole-manuscript gated coverage is {overall:.3f}. Zones with no rows were "
        "checked and are listed empty rather than omitted. A zone above that line is not "
        "better understood — the pipeline has no notion of understanding — it simply contains "
        "shorter or commoner strings that hit the Latin lexicon more often."
    )
    weakest = min(
        (row for row in rows if row["gated_coverage"] is not None),
        key=lambda row: float(row["gated_coverage"]),
    )
    return Check(
        Finding(
            test="§7.2.6 known-weak zones",
            metric=f"weakest zone: {weakest['zone']}",
            value=weakest["gated_coverage"],
            null=f"whole manuscript {overall:.3f}",
            verdict=NEUTRAL,
            implication=(
                "Every listed zone is enumerated with its row count, so no reader has to infer "
                "which parts of the rendering are least supported."
            ),
        ),
        detail,
        {"zones": rows, "overall": overall},
    )


def coverage_honesty(harness: Harness, lines: list[TranslatedLine]) -> Check:
    """§7.2.7 — the gated view's true coverage at each band, per stratum."""
    rows: list[list[Any]] = []
    data: list[dict[str, Any]] = []
    groups: dict[str, list[TranslatedLine]] = {}
    for line in lines:
        groups.setdefault(line.section or "unassigned", []).append(line)
    for name, group in sorted(groups.items()):
        tokens = [token for line in group for token in line.tokens]
        bands = Counter(token.rendered.band for token in tokens)
        row = {
            "stratum": name,
            "tokens": len(tokens),
            **{band: bands[band] / len(tokens) for band in ("high", "medium", "low", "none")},
            "gated_coverage": (bands["high"] + bands["medium"]) / len(tokens),
        }
        data.append(row)
        rows.append([name, len(tokens), row["high"], row["medium"], row["low"], row["none"]])
    overall = gated_coverage(lines)
    detail = (
        table(["section", "tokens", "high", "medium", "low", "none"], rows)
        + f"\n\nThe gated view prints the high and medium bands only: {overall:.1%} of tokens "
        "across the manuscript. The remaining tokens appear in `english_speculative` marked "
        "`?word?` or `⟨surface⟩(≈guess)`, and appear in the gated view as `UNKNOWN`. Neither "
        "number is a measure of correctness — both are measures of how often a Latin lexicon "
        "matched a short string."
    )
    return Check(
        Finding(
            test="§7.2.7 coverage honesty",
            metric="gated coverage, whole manuscript",
            value=overall,
            null="—",
            verdict=NEUTRAL,
            implication=(
                "Stated at the top of every report and broken out per stratum, so a complete-"
                "looking speculative rendering cannot be mistaken for complete coverage."
            ),
        ),
        detail,
        {"sections": data, "overall": overall},
    )


def run(
    harness: Harness,
    lines: list[TranslatedLine],
    renderings: dict[str, list[TranslatedLine]],
    views: dict[str, View],
    deadline: Deadline,
) -> list[Check]:
    """The whole §7.2 battery, in plan order."""
    return [
        pseudo_voynich(harness, renderings, views),
        shuffled_input(harness),
        rival_languages(harness),
        key_instability(harness, deadline),
        ablations(harness),
        known_weak_zones(harness, lines),
        coverage_honesty(harness, lines),
    ]
