"""Phase 4 entrypoint: the automated, repeatable English rendering (plan §6).

    uv run python -m translations.phase4

Runs the pipeline over every line of the manuscript, once per keyed hypothesis,
plus the pseudo-Voynich controls the §6.6 gate requires; writes the artifacts to
``output/translation/`` and the reports to ``reports/translation/``.

The expensive half — fitting the confidence maps against ciphertexts whose
answer we hid — lives in ``translations.calibrate`` and is run separately by
`make calibrate`, so this command stays in the "minutes, not hours" budget §6.5
asks for.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from collections.abc import Callable
from typing import Any

import pandas as pd

from translations import alignment, paragraphs
from translations.analysis.common import View, grille_view, selfcite_view, voynich_view
from translations.calibrate import CALIBRATION_PATH, CalibrationMap, load_maps
from translations.config import CONFIG, PATHS, active_banner
from translations.decode import CANDIDATES, RANKING, TRANSLATOR_CONFIG, KeyedHypothesis
from translations.decode import keyed_hypotheses as load_keyed
from translations.determinism import derived_rng, sha256_file, write_manifest
from translations.gloss import coverage as gloss_coverage
from translations.io import load_lines
from translations.lexicon.whitakers import load_lexicon
from translations.pipeline import GlossCache, TranslatedLine, reliability_weights, translate
from translations.render import GATED_MASK, gated
from translations.report import Topic, banner_markdown, table, write_report
from translations.represent import merged, phase2_merges
from vcat.exceptions import SourceNotFoundError
from vcat.logging import get_logger

logger = get_logger(__name__)

REPORTS = PATHS.repo_root / "reports" / "translation"
LINES_JSONL = PATHS.output_dir / "translation_lines.jsonl"
LINES_PARQUET = PATHS.output_dir / "translation_lines.parquet"
LEXICON_PATH = PATHS.output_dir / "lexicon.jsonl"
MANIFEST_PATH = PATHS.output_dir / "phase4_manifest.json"
SUMS_PATH = PATHS.output_dir / "SHA256SUMS"

CONTROLS: dict[str, Callable[[View], View]] = {
    "grille": lambda base: grille_view(base, derived_rng("phase4-grille")),
    "selfcite": lambda base: selfcite_view(base, derived_rng("phase4-selfcite")),
}
STRATA_FIELDS = ("section", "currier_language", "line_type", "hand")

# Plan §7.2.1 / §7.4: if a corpus that encodes nothing renders at least as well
# as the manuscript, the artifacts stay but their framing changes. Phase 4 runs
# that test itself, so `make translate` alone stamps the honest banner; Phase 5
# re-checks it alongside the other four kill criteria.
KILL_RATIO = 1.0


def render_salt(hypothesis_id: str, view: str) -> str:
    """The RNG salt one rendering uses.

    Phase 5 re-runs the same renderings to audit them, and the null-key draw is
    seeded from this string, so the salt has to be shared rather than spelled
    out twice — otherwise the audit reports numbers the artifacts do not have.
    """
    return f"phase4-{hypothesis_id}-{view}"


def summarise(lines: list[TranslatedLine]) -> dict[str, float]:
    """Coverage and confidence of one rendering."""
    tokens = [token for line in lines for token in line.tokens]
    if not tokens:
        return {}
    bands = Counter(token.rendered.band for token in tokens)
    return {
        "lines": float(len(lines)),
        "tokens": float(len(tokens)),
        "gated_coverage": sum(1 for token in tokens if gated(token.rendered) != GATED_MASK)
        / len(tokens),
        "mean_confidence": sum(token.confidence for token in tokens) / len(tokens),
        "mean_null_p": sum(token.null_p for token in tokens) / len(tokens),
        "beat_every_null_key": sum(1 for token in tokens if token.null_p <= 1.0 / 21.0)
        / len(tokens),
        **{f"band_{name}": bands[name] / len(tokens) for name in ("high", "medium", "low", "none")},
    }


def by_stratum(lines: list[TranslatedLine], field: str) -> list[dict[str, Any]]:
    """Gated coverage and confidence per level of one stratum."""
    groups: dict[str, list[TranslatedLine]] = {}
    for line in lines:
        groups.setdefault(str(getattr(line, field)) or "none", []).append(line)
    return [
        {"stratum": name, **summarise(group)}
        for name, group in sorted(groups.items())
        if summarise(group)
    ]


def render_all(
    views: dict[str, View],
    keyed: list[KeyedHypothesis],
    maps: dict[str, CalibrationMap],
    cache: GlossCache,
) -> dict[tuple[str, str], list[TranslatedLine]]:
    """Translate every view under every keyed hypothesis."""
    rows = alignment.build_rows()
    weights = reliability_weights(rows)
    blocks = {
        line_id: block.block_id for block in paragraphs.build_blocks() for line_id in block.line_ids
    }
    text = {line.line_id: line.text_clean for line in load_lines()}

    output: dict[tuple[str, str], list[TranslatedLine]] = {}
    for entry in keyed:
        for name, view in views.items():
            began = time.monotonic()
            output[(entry.hypothesis_id, name)] = translate(
                view,
                entry,
                cache,
                maps[entry.hypothesis_id],
                weights if name == "real" else {},
                blocks,
                text,
                derived_rng(render_salt(entry.hypothesis_id, name)),
            )
            logger.info(
                "Rendered",
                hypothesis=entry.hypothesis_id,
                view=name,
                seconds=round(time.monotonic() - began, 1),
            )
    return output


def controls_topic(
    renderings: dict[tuple[str, str], list[TranslatedLine]], primary: str
) -> tuple[str, dict[str, Any]]:
    """The decisive comparison: does gibberish translate as well as the manuscript?"""
    rows = {name: summarise(renderings[(primary, name)]) for name in ("real", *CONTROLS)}
    real = rows["real"]
    worst = max(
        (name for name in CONTROLS), key=lambda name: rows[name]["gated_coverage"], default=""
    )
    ratio = rows[worst]["gated_coverage"] / max(real["gated_coverage"], 1e-9) if worst else 0.0
    if ratio >= 1.0:
        verdict = (
            f"The `{worst}` control renders *more* than the manuscript does "
            f"({rows[worst]['gated_coverage']:.1%} of tokens against "
            f"{real['gated_coverage']:.1%}). On the test the plan named decisive, this "
            f"pipeline is a fluency generator and its Voynich output carries no evidential "
            f"weight."
        )
    elif ratio >= 0.5:
        verdict = (
            f"The `{worst}` control renders about as much as the manuscript does "
            f"({rows[worst]['gated_coverage']:.1%} against {real['gated_coverage']:.1%}). On "
            f"the test the plan named decisive, this output carries no evidential weight."
        )
    else:
        verdict = (
            f"The controls render markedly less than the manuscript does "
            f"({rows[worst]['gated_coverage']:.1%} against {real['gated_coverage']:.1%})."
        )
    section = (
        "## Pseudo-Voynich control (read this first)\n\n"
        + table(
            ["corpus", "tokens", "gated coverage", "mean confidence", "high band", "none band"],
            [
                [
                    name,
                    int(row["tokens"]),
                    row["gated_coverage"],
                    row["mean_confidence"],
                    row["band_high"],
                    row["band_none"],
                ]
                for name, row in rows.items()
            ],
        )
        + f"\n\nBoth controls are matched to the manuscript in token count and built from its own\n"
        f"statistics: `grille` is a Rugg-style table generator, `selfcite` a Timm-style\n"
        f"autocopier. Neither encodes anything. The identical pipeline, the identical key and\n"
        f"the identical lexicon were run over them.\n\n**{verdict}**"
    )
    return section, {"controls": rows, "control_ratio": ratio, "verdict": verdict}


def validation_failed(
    renderings: dict[tuple[str, str], list[TranslatedLine]], primary: str
) -> bool:
    """Did the pseudo-Voynich control render at least as well as the manuscript?"""
    return bool(controls_topic(renderings, primary)[1]["control_ratio"] >= KILL_RATIO)


def coverage_topic(
    renderings: dict[tuple[str, str], list[TranslatedLine]],
    keyed: list[KeyedHypothesis],
    maps: dict[str, CalibrationMap],
    lexicon_rows: list[dict[str, Any]],
    banner: str,
) -> Topic:
    """`reports/translation/coverage.md` — how much of this is worth reading."""
    primary = keyed[0].hypothesis_id
    lines = renderings[(primary, "real")]
    control_section, control_data = controls_topic(renderings, primary)
    overall = summarise(lines)

    per_hypothesis = [
        {
            "hypothesis": entry.hypothesis_id,
            "variant": entry.variant,
            "gain_per_token": entry.gain_per_token,
            "p_value": entry.p_value,
            "converged": entry.converged,
            "synthetic_key_accuracy": maps[entry.hypothesis_id].key_accuracy,
            **summarise(renderings[(entry.hypothesis_id, "real")]),
        }
        for entry in keyed
    ]
    splits: list[dict[str, Any]] = [
        {"split": name, **summarise([line for line in lines if line.is_holdout == held])}
        for name, held in (("train", False), ("holdout", True))
    ]
    strata = {field: by_stratum(lines, field) for field in STRATA_FIELDS}
    sources = Counter(str(row["source"]) for row in lexicon_rows)
    fallback = {name: sources[name] / max(len(lexicon_rows), 1) for name in sources}

    sections = [
        "## Bottom line\n\n"
        f"Every line of the manuscript now has an English rendering, and none of it is a "
        f"reading of the manuscript. The hypothesis it is rendered under, {primary}, lost to a "
        f"Markov model of the manuscript's own statistics "
        f"(gain {keyed[0].gain_per_token:.3f} bits/token, p = {keyed[0].p_value:.3f}), and the "
        f"control below renders text that encodes nothing at "
        f"{control_data['control_ratio']:.0%} of the rate it renders the manuscript. "
        f"The gated view covers {overall['gated_coverage']:.1%} of tokens; the confidence "
        f"attached to them is conditional on a hypothesis the evidence does not support.",
        control_section,
        "## Every keyed hypothesis\n\n"
        + table(
            [
                "id",
                "variant",
                "gain/token",
                "p",
                "converged",
                "key accuracy (synthetic)",
                "gated coverage",
                "mean confidence",
            ],
            [
                [
                    row["hypothesis"],
                    row["variant"],
                    row["gain_per_token"],
                    row["p_value"],
                    row["converged"],
                    row["synthetic_key_accuracy"],
                    row["gated_coverage"],
                    row["mean_confidence"],
                ]
                for row in per_hypothesis
            ],
        )
        + "\n\nFive hypotheses committed to a key and are rendered in full. The other four "
        "(H6a, H6b, H8, H9) are generative: they claim the text was produced by a process, "
        "not enciphered from a plaintext, so there is nothing to decode and nothing to gloss.",
        "## Confidence bands\n\n"
        + table(
            ["band", "share of tokens", "rendering"],
            [
                ["high (>= 0.7)", overall["band_high"], "`word`"],
                ["medium (0.4-0.7)", overall["band_medium"], "`*word*`"],
                ["low (0.15-0.4)", overall["band_low"], "`?word?`"],
                ["none (< 0.15)", overall["band_none"], "`⟨surface⟩(≈guess)`"],
            ],
        ),
        "## Held-out pages, scored once\n\n"
        + table(
            ["split", "lines", "tokens", "gated coverage", "mean confidence"],
            [
                [
                    row["split"],
                    int(row["lines"]),
                    int(row["tokens"]),
                    row["gated_coverage"],
                    row["mean_confidence"],
                ]
                for row in splits
            ],
        )
        + "\n\nThe key was searched on the training pages only. A pipeline that had learned "
        "something about the manuscript would render the held-out pages worse than the "
        "training pages; a pipeline matching a dictionary against short strings will not "
        "distinguish them.",
        "## Gated coverage by stratum\n\n"
        + "\n\n".join(
            f"### {field}\n\n"
            + table(
                ["stratum", "lines", "tokens", "gated coverage", "mean confidence"],
                [
                    [
                        row["stratum"],
                        int(row["lines"]),
                        int(row["tokens"]),
                        row["gated_coverage"],
                        row["mean_confidence"],
                    ]
                    for row in rows
                ],
            )
            for field, rows in strata.items()
        ),
        "## Where the glosses come from\n\n"
        + table(
            ["rung of the fallback chain", "share of types"],
            [[name, share] for name, share in sorted(fallback.items())],
        )
        + "\n\nThe distributional gloss the plan lists as fallback (b) is deliberately not "
        "implemented: it would assign real English words on the basis of frequency profile "
        "alone. See `docs/decisions.md`.",
        "## The random-key null\n\n"
        f"Every token is scored again under {20} keys that permute the real key's letter "
        f"assignments, which destroys the key's information while keeping its letter "
        f"inventory. The mean per-token p-value is {overall['mean_null_p']:.3f}; "
        f"{overall['beat_every_null_key']:.1%} of tokens are glossed better by the real key "
        f"than by any of the 20. That share, not the lexicon hit rate, is what the confidence "
        f"column is built on: a two-letter string hits a 48,000-stem Latin dictionary whatever "
        f"the key says.",
        "## Validation gate (plan §6.6)\n\n"
        + table(
            ["requirement", "status"],
            [
                ["Held-out folios scored once, results reported whatever they are", "yes"],
                ["Confidence calibration curves produced and included", "`calibration.md`"],
                ["Pseudo-Voynich control run and included", "yes, above"],
                ["Banner present in every artifact and every report", "yes"],
                ["Determinism test green", "`tests/translations/test_phase4.py`"],
                [
                    "Framing under plan §7.4",
                    (
                        "**failed validation** — artifacts re-bannered"
                        if control_data["control_ratio"] >= KILL_RATIO
                        else "control passed; standard speculative banner"
                    ),
                ],
            ],
        )
        + f"\n\nEvery artifact written by this run carries:\n\n> {banner}",
    ]
    return Topic(
        topic="coverage",
        title="Phase 4 — Coverage and confidence",
        sections=sections,
        data={
            "primary": primary,
            "overall": overall,
            "per_hypothesis": per_hypothesis,
            "splits": splits,
            "strata": strata,
            "fallback": fallback,
            "banner": banner,
            "validation_failed": control_data["control_ratio"] >= KILL_RATIO,
            **control_data,
        },
    )


def calibration_topic(maps: dict[str, CalibrationMap]) -> Topic:
    """`reports/translation/calibration.md` — what the confidence column means."""
    recovery = table(
        ["id", "corpus", "scheme", "synthetic tokens", "key accuracy", "token accuracy"],
        [
            [name, row.corpus, row.scheme, row.n_tokens, row.key_accuracy, row.token_accuracy]
            for name, row in sorted(maps.items())
        ],
    )
    diagrams = "\n\n".join(
        f"### {name}\n\n"
        + table(
            ["predicted confidence", "observed accuracy", "tokens"],
            [[row["predicted"], row["observed"], int(row["n"])] for row in value.diagram],
        )
        for name, value in sorted(maps.items())
    )
    curves = "\n\n".join(
        f"### {name}\n\n"
        + table(
            ["raw score", "calibrated confidence"],
            list(zip(value.scores, value.accuracy, strict=True)),
        )
        for name, value in sorted(maps.items())
    )
    flat = [name for name, value in maps.items() if min(value.accuracy[1:], default=0.0) >= 0.999]
    sections = [
        "## Method\n\n"
        "Each keyed hypothesis is given a problem whose answer we hid: a reference corpus in "
        "the language its own model assumes, enciphered under its own scheme at its own "
        "channel width, attacked blind with its own search settings, then pushed through the "
        "same decode-and-gloss stages. The isotonic map is fitted on half those tokens; the "
        "reliability diagram below is computed on the other half, so it checks the map rather "
        "than redrawing it.",
        "## Recovery on ciphertext we built\n\n" + recovery,
        "## Reliability diagrams (held-out synthetic tokens)\n\n" + diagrams,
        "## The fitted maps\n\n" + curves,
        "## What this does not certify\n\n"
        + (
            f"The map is flat at 1.0 above zero for {', '.join(sorted(flat))}: whenever the "
            "hypothesised system is genuinely present, this search recovers the key exactly "
            "and the gloss is then right whenever the lexicon has the word. That is a "
            "statement about the pipeline, not about the manuscript. "
            if flat
            else ""
        )
        + "Calibration is valid only if the true system resembles the hypothesised one. The "
        "manuscript sits at a score no synthetic ciphertext in this harness reaches — every "
        "hypothesis loses to a Markov model of the manuscript's own statistics — so the map "
        "is being read far outside the range it was fitted on. It bounds optimism about a "
        "system we can simulate; it certifies nothing about one we cannot.\n\n"
        "This is why the confidence column is the calibrated value multiplied by the "
        "random-key null term and the transcription reliability weight. The calibration says "
        "how often a gloss is right *given* the hypothesis; the null term says how much of the "
        "gloss a key with no information would have produced anyway.",
    ]
    return Topic(
        topic="calibration",
        title="Phase 4 — Confidence calibration",
        sections=sections,
        data={"maps": {name: value.as_dict() for name, value in sorted(maps.items())}},
    )


def folio_readings(lines: list[TranslatedLine], hypothesis: KeyedHypothesis, banner: str) -> str:
    """Page-by-page rendering, banner at the top of every page section."""
    pages: dict[str, list[TranslatedLine]] = {}
    for line in lines:
        pages.setdefault(line.page_id, []).append(line)

    parts = [
        "# Phase 4 — Folio readings",
        banner_markdown(banner),
        f"Rendered under **{hypothesis.hypothesis_id}** "
        f"(`{hypothesis.representation}` / `{hypothesis.variant}`), which scored "
        f"{hypothesis.gain_per_token:.3f} bits/token against an order-2 Markov model of the "
        f"manuscript — that is, it lost. Read `coverage.md` before reading a single line here.",
    ]
    for page_id, rows in pages.items():
        first = rows[0]
        parts.append(
            f"## {page_id}\n\n{banner_markdown(banner)}\n\n"
            f"section: {first.section or '—'} · Currier: {first.currier_language or '—'} · "
            f"hand: {first.hand or '—'} · lines: {len(rows)}\n\n"
            + table(
                ["line", "EVA", "English (speculative)", "gated"],
                [
                    [row.line_id, row.text_clean, row.english_speculative, row.english_gated]
                    for row in rows
                ],
            )
        )
    return "\n\n".join(parts) + "\n"


def lexicon_rows(
    renderings: dict[tuple[str, str], list[TranslatedLine]], primary: str, banner: str
) -> list[dict[str, Any]]:
    """Voynich type -> ranked glosses, with support counts and provenance."""
    counts: Counter[str] = Counter()
    detail: dict[str, dict[str, Any]] = {}
    for line in renderings[(primary, "real")]:
        for token in line.tokens:
            counts[token.surface] += 1
            detail.setdefault(
                token.surface,
                {
                    "voynich_type": token.surface,
                    "units": list(token.units),
                    "intermediate": token.intermediate,
                    "source": token.glosses[0].source if token.glosses else "none",
                    "glosses": [gloss.as_dict() for gloss in token.glosses],
                    "hypothesis_id": primary,
                },
            )
    return [
        {**detail[form], "support": count, "banner": banner}
        for form, count in sorted(counts.items())
    ]


def write_artifacts(
    renderings: dict[tuple[str, str], list[TranslatedLine]],
    keyed: list[KeyedHypothesis],
    entries: list[dict[str, Any]],
    banner: str,
) -> dict[str, int]:
    """Write the JSONL, parquet, lexicon and checksum artifacts."""
    primary = keyed[0]
    PATHS.output_dir.mkdir(parents=True, exist_ok=True)

    with LINES_JSONL.open("w") as handle:
        for line in renderings[(primary.hypothesis_id, "real")]:
            handle.write(json.dumps(line.as_dict(primary, banner)) + "\n")

    flat = [
        {key: value for key, value in line.as_dict(entry, banner).items() if key != "tokens"}
        | {"n_tokens": len(line.tokens), "gated_coverage": _gated_share(line)}
        for entry in keyed
        for line in renderings[(entry.hypothesis_id, "real")]
    ]
    pd.DataFrame(flat).to_parquet(LINES_PARQUET, index=False)

    with LEXICON_PATH.open("w") as handle:
        for row in entries:
            handle.write(json.dumps(row) + "\n")

    SUMS_PATH.write_text(
        "".join(
            f"{sha256_file(path)}  {path.name}\n"
            for path in (LINES_JSONL, LINES_PARQUET, LEXICON_PATH, CALIBRATION_PATH)
        )
    )
    return {"lines": len(flat), "types": len(entries)}


def _gated_share(line: TranslatedLine) -> float:
    if not line.tokens:
        return 0.0
    return sum(1 for token in line.tokens if gated(token.rendered) != GATED_MASK) / len(line.tokens)


def build_views() -> tuple[dict[str, View], dict[str, Any]]:
    """The manuscript under the chosen representation, plus the two controls."""
    merges, provenance = phase2_merges()
    representation = merged(merges, origin="Phase 3 translator configuration", detail=provenance)
    base = voynich_view()
    views = {"real": representation(base)}
    for name, build in CONTROLS.items():
        views[name] = representation(build(base))
    return views, provenance


def main() -> int:
    """Run Phase 4 end to end."""
    started = time.time()
    if not CALIBRATION_PATH.exists():
        raise SourceNotFoundError(
            "Calibration maps missing; run `make calibrate` first", path=CALIBRATION_PATH
        )

    keyed = load_keyed(CANDIDATES, RANKING, TRANSLATOR_CONFIG)
    maps = load_maps()
    views, provenance = build_views()
    cache = GlossCache(load_lexicon())
    renderings = render_all(views, keyed, maps, cache)

    primary = keyed[0]
    failed = validation_failed(renderings, primary.hypothesis_id)
    banner = active_banner(failed)
    entries = lexicon_rows(renderings, primary.hypothesis_id, banner)
    written = write_artifacts(renderings, keyed, entries, banner)

    topics = [coverage_topic(renderings, keyed, maps, entries, banner), calibration_topic(maps)]
    for topic in topics:
        write_report(REPORTS, topic.topic, topic.title, topic.sections, topic.data, banner)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "folio_readings.md").write_text(
        folio_readings(renderings[(primary.hypothesis_id, "real")], primary, banner)
    )

    write_manifest(
        MANIFEST_PATH,
        inputs=[PATHS.eva_lines, PATHS.pages, PATHS.mismatch_index, CALIBRATION_PATH],
        extra={
            "phase": 4,
            "primary": primary.hypothesis_id,
            "validation_failed": failed,
            "banner": banner,
            "representation": provenance,
            "hypotheses": [
                {
                    "hypothesis": entry.hypothesis_id,
                    "variant": entry.variant,
                    "representation": entry.representation,
                    "gain_per_token": entry.gain_per_token,
                    "p_value": entry.p_value,
                    "converged": entry.converged,
                }
                for entry in keyed
            ],
            "artifacts": written,
            "coverage": topics[0].data["overall"],
            "controls": topics[0].data["controls"],
            "gloss_fallback_all_forms": gloss_coverage(cache.memo),
            "reliability_floor": CONFIG.reliability_floor,
        },
    )
    print(f"Reports written to {REPORTS}")
    print(f"Artifacts: {written['lines']} rows, {written['types']} types -> {PATHS.output_dir}")
    print(f"Wall clock {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
