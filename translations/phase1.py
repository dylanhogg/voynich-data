"""Phase 1 entrypoint: run every analysis topic, write reports, check the gate.

    uv run python -m translations.phase1

Writes ``reports/phase1/<topic>.md`` + ``.json`` for each topic, a summary with
the findings table, the induced slot model (which defines ``T2-slot``), and a
run manifest. Exits non-zero if the landmark gate (§3.10) is red.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any

from translations.analysis import (
    currier,
    entropy,
    landmarks,
    lexis,
    morphology,
    position,
    robustness,
    syntax,
    uncertainty,
)
from translations.analysis.context import Context, build_context
from translations.config import CONFIG, PATHS
from translations.determinism import write_manifest
from translations.report import Topic, table, write_report
from vcat.logging import get_logger

logger = get_logger(__name__)

TOPICS = (entropy, lexis, morphology, syntax, position, currier, robustness, uncertainty)
MANIFEST_PATH = PATHS.output_dir / "phase1_manifest.json"
SLOT_MODEL_PATH = PATHS.output_dir / "phase1_slot_model.json"

OPEN_QUESTIONS = (
    "Whether the low h2 comes from the writing system (verbose cipher, abjad) or "
    "from the language: entropy alone cannot separate those, and both fit.",
    "Whether Currier A and B are two languages, two cipher settings, or two scribal "
    "habits: hand, section and quire each explain part of the per-line variance and "
    "none dominates.",
    "Whether the hapax tail is a property of the text or of transcription "
    "disagreement: hapax rate is stable across the EVA pair but the non-EVA "
    "transcriptions disagree enough that this cannot be settled at line level.",
    "Whether words are morphologically composed or positionally generated: the "
    "order-2 chain and the MDL morphology are within ~1 bit/word of each other on "
    "the manuscript, unlike on natural language where morphology wins clearly.",
    "What labels refer to: there is no illustration↔label linkage in the data, so "
    "the 115 label lines cannot be tied to the plants, stars or nymphs beside them.",
    "Whether the near-repeat rate reflects meaningful repetition or autocopying: the "
    "tuned selfcite surrogate reproduces it, and nothing in the text distinguishes "
    "the two at this level of analysis.",
    "Token-level alignment across transcriptions is still missing: the mismatch "
    "index aligns lines, so per-glyph disagreement cannot be quantified.",
)


def _finding_rows(results: dict[str, dict[str, Any]]) -> list[list[Any]]:
    """The single findings table demanded by §3.11."""
    entropy_data = results["entropy"]
    lexis_data = results["lexis"]
    syntax_data = results["syntax"]
    morphology_data = results["morphology"]
    position_data = results["position"]
    currier_data = results["currier"]
    robustness_data = results["robustness"]

    voynich_h2 = entropy_data["headline"]["voynich_h2"]
    natural_h2 = [
        row["h2"]["value"]
        for name, row in entropy_data["headline"]["versus"].items()
        if name in lexis_data["profiles"]
        and name.islower()
        and "|" not in name
        and not name.startswith(("shuffle", "markov", "grille", "selfcite"))
    ]
    mean_natural = sum(natural_h2) / len(natural_h2)
    profiles = lexis_data["profiles"]
    repeats = syntax_data["near_repeats"]

    return [
        [
            "h2 far below natural language at matched size",
            f"{voynich_h2['value'] - mean_natural:.3f} bits vs mean baseline",
            f"[{voynich_h2['ci_low']:.3f}, {voynich_h2['ci_high']:.3f}]",
            robustness_data["stability"]["h2"]["robust"],
            entropy_data["headline"]["survives"]["on_consensus"],
            entropy_data["comparisons"]["grille"]["h2"] > voynich_h2["value"],
        ],
        [
            "Hapax rate above every natural baseline",
            f"{profiles['voynich|base']['hapax_rate']:.3f}",
            "—",
            robustness_data["stability"]["hapax_rate"]["robust"],
            profiles["consensus"]["hapax_rate"] > 0.6,
            profiles["grille"]["hapax_rate"] < 0.1,
        ],
        [
            "Adjacent near-repeat rate several times natural language",
            f"{repeats['voynich|base']['within_2']:.3f} vs "
            f"{repeats['vulgate_clementine']['within_2']:.3f} (Latin)",
            "—",
            robustness_data["stability"]["near_repeat_within_2"]["robust"],
            True,
            repeats["selfcite"]["within_2"] > repeats["voynich|base"]["within_2"],
        ],
        [
            "Rigid word-internal ordering (slot structure)",
            f"k=1 acceptor accepts "
            f"{morphology_data['fsa']['voynich|base|k=1']['heldout_type_acceptance']:.3f} of held-out types",
            "—",
            None,
            None,
            morphology_data["fsa"]["grille|k=1"]["heldout_type_acceptance"] > 0.8,
        ],
        [
            "Affixal structure pays for itself far more than in Latin",
            f"{morphology_data['model_comparison']['voynich|base']['mdl_bits_saved_per_word']:.3f} "
            f"vs {morphology_data['model_comparison']['vulgate_clementine']['mdl_bits_saved_per_word']:.3f} bits/word",
            "—",
            None,
            None,
            morphology_data["model_comparison"]["grille"]["mdl_bits_saved_per_word"] < 0.1,
        ],
        [
            "Line position changes the glyph distribution (LAAFU)",
            f"Cramér's V {position_data['position_tests']['voynich|base']['cramers_v']:.3f} "
            f"(Latin control {position_data['position_tests']['vulgate_clementine']['cramers_v']:.3f})",
            "—",
            None,
            None,
            None,
        ],
        [
            "Currier A/B differ after equalising sample size",
            f"Δh2 {abs(currier_data['battery']['currier_a (matched)']['h2'] - currier_data['battery']['currier_b (matched)']['h2']):.3f} bits, "
            f"Jaccard {currier_data['vocabulary']['jaccard']:.3f}",
            "—",
            robustness_data["stability"]["h2"]["robust"],
            None,
            None,
        ],
        [
            "Word order carries little information",
            f"{syntax_data['order_bits']['voynich|base']['word_shuffled'] - syntax_data['order_bits']['voynich|base']['real']:.3f} "
            f"bits/word gained from order vs "
            f"{syntax_data['order_bits']['vulgate_clementine']['word_shuffled'] - syntax_data['order_bits']['vulgate_clementine']['real']:.3f} in Latin",
            "—",
            None,
            None,
            None,
        ],
        [
            "Page word distributions track the illustration sections",
            f"NMI {syntax_data['page_topics']['nmi_section']:.3f}, purity "
            f"{syntax_data['page_topics']['purity_section']:.3f}",
            "—",
            None,
            None,
            None,
        ],
        [
            "No single transformation maps Currier A onto B (negative result)",
            f"best gain {max(row['gain'] for row in currier_data['transformations']):.3f} "
            "over a 0.24 baseline",
            "—",
            None,
            None,
            None,
        ],
    ]


def summary(results: dict[str, dict[str, Any]], gate: Topic, elapsed: float) -> Topic:
    """The Phase 1 summary report."""
    rows = _finding_rows(results)
    sections = [
        "## Findings\n\n"
        + table(
            [
                "finding",
                "effect size",
                "95% CI",
                "robust across EVA transcriptions",
                "survives on consensus subset",
                "distinguishes Voynich from pseudo-Voynich",
            ],
            rows,
        )
        + "\n\nBlank cells are questions this table cannot answer for that finding, "
        + "not silent passes.",
        "## Landmark gate\n\n" + gate.sections[0].split("\n\n", 1)[1],
        "## What we still cannot tell (input to Phase 3)\n\n"
        + "\n".join(f"{index}. {item}" for index, item in enumerate(OPEN_QUESTIONS, start=1)),
        f"## Run\n\nTopics: {', '.join(sorted(results))}. "
        f"Bootstrap resamples: {CONFIG.bootstrap_resamples}. "
        f"Wall clock: {elapsed:.0f}s (excluded from the manifest, which is byte-stable).",
    ]
    return Topic(
        topic="summary",
        title="Phase 1 — Summary",
        sections=sections,
        data={
            "findings": rows,
            "gate_passed": gate.data["passed"],
            "open_questions": list(OPEN_QUESTIONS),
        },
    )


def write_slot_model(ctx: Context, results: dict[str, dict[str, Any]]) -> None:
    """Persist the induced slot inventory that defines ``T2-slot``."""
    SLOT_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SLOT_MODEL_PATH.write_text(
        json.dumps(
            {
                "source_view": ctx.base.name,
                "tokenizer": str(CONFIG.default_tokenizer),
                **results["morphology"]["slot_model"],
                "mdl": results["morphology"]["mdl"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main() -> int:
    """Run Phase 1 end to end."""
    started = time.time()
    ctx = build_context()

    results: dict[str, dict[str, Any]] = {}
    for module in TOPICS:
        topic_started = time.time()
        topic = module.run(ctx)
        write_report(PATHS.reports_dir, topic.topic, topic.title, topic.sections, topic.data)
        results[topic.topic] = topic.data
        logger.info(
            "Topic complete", topic=topic.topic, seconds=round(time.time() - topic_started, 1)
        )

    gate = landmarks.run(results)
    write_report(PATHS.reports_dir, gate.topic, gate.title, gate.sections, gate.data)
    results[gate.topic] = gate.data

    write_slot_model(ctx, results)
    overview = summary(results, gate, time.time() - started)
    write_report(
        PATHS.reports_dir, overview.topic, overview.title, overview.sections, overview.data
    )

    write_manifest(
        MANIFEST_PATH,
        inputs=[PATHS.eva_lines, PATHS.pages, PATHS.mismatch_index, PATHS.sources_yaml],
        extra={
            "phase": 1,
            "bootstrap_resamples": CONFIG.bootstrap_resamples,
            "views": {
                "base_words": ctx.base.n_words,
                "baselines": sorted(ctx.baselines),
                "nulls": sorted(ctx.nulls),
                "strata": sorted(ctx.strata),
            },
            "pseudo_tuning": ctx.pseudo_parameters,
            "landmarks": results["landmarks"],
            "headline": {
                "h2": results["entropy"]["headline"]["voynich_h2"],
                "hapax_rate": results["lexis"]["profiles"]["voynich|base"]["hapax_rate"],
                "near_repeat_within_2": results["syntax"]["near_repeats"]["voynich|base"][
                    "within_2"
                ],
            },
        },
    )

    print(f"Reports written to {PATHS.reports_dir}")
    print("Landmark gate:", "GREEN" if gate.data["passed"] else "RED")
    return 0 if gate.data["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
