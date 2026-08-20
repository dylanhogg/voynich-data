"""§5.2.1 — the Phase 1 battery, re-run on the Phase 3 representations.

The make-or-break diagnostic. If verbose encipherment is real, the merged
representation is closer to the plaintext's unit stream than the raw glyphs are,
and the landmarks that make Voynichese strange — conditional entropy far below
natural language, symmetric word lengths, an odd Zipf tail, shallow MI decay —
should move *towards* the natural-language region. If they do not move, the
merge is a compression trick and nothing more.

The same question is asked of the reliability-filtered representation: a
landmark that is really an artifact of transcription noise should weaken once
the tokens the two transcribers disagree about are gone.
"""

from __future__ import annotations

from typing import Any

from translations.analysis.common import View
from translations.analysis.context import Context
from translations.analysis.entropy import conditional_entropies
from translations.analysis.lexis import frequency_profile, word_length_profile
from translations.analysis.morphology import model_comparison
from translations.analysis.syntax import mi_curve, near_repeats
from translations.report import Topic, table
from translations.represent import Representation

# The metrics the plan names, plus the two Phase 1 landmarks that bear on them.
METRICS: tuple[str, ...] = (
    "h1",
    "h2",
    "h3",
    "word_length_mean",
    "word_length_cv",
    "zipf_alpha",
    "hapax_rate",
    "mi_excess_d1",
    "mi_excess_d5",
    "near_repeat_within_2",
    "morph_bits_saved_per_word",
)


def profile(view: View) -> dict[str, float]:
    """One comparable row: the metrics §5.2.1 names, for any view."""
    entropies = conditional_entropies(view)
    lengths = word_length_profile(view)
    frequencies = frequency_profile(view)
    curve = mi_curve(view, within_lines=True)
    repeats = near_repeats(view)
    morphology = model_comparison(view)
    return {
        "h1": entropies["h1"],
        "h2": entropies["h2"],
        "h3": entropies["h3"],
        "word_length_mean": float(lengths.get("mean", 0.0)),  # type: ignore[arg-type]
        "word_length_cv": float(lengths.get("cv", 0.0)),  # type: ignore[arg-type]
        "zipf_alpha": frequencies["zipf_alpha"],
        "hapax_rate": frequencies["hapax_rate"],
        "mi_excess_d1": curve.get(1, {}).get("excess", 0.0),
        "mi_excess_d5": curve.get(5, {}).get("excess", 0.0),
        "near_repeat_within_2": repeats["within_2"],
        "morph_bits_saved_per_word": morphology["mdl_bits_saved_per_word"],
    }


def natural_band(
    profiles: dict[str, dict[str, float]], names: list[str]
) -> dict[str, tuple[float, float]]:
    """Min and max of each metric across the natural-language baselines."""
    return {
        metric: (
            min(profiles[name][metric] for name in names),
            max(profiles[name][metric] for name in names),
        )
        for metric in METRICS
    }


def verdicts(
    voynich: dict[str, dict[str, float]], band: dict[str, tuple[float, float]]
) -> list[dict[str, Any]]:
    """Per metric: where each representation sits relative to natural language."""
    rows = []
    for metric in METRICS:
        low, high = band[metric]
        raw = voynich["raw"][metric]
        row: dict[str, Any] = {
            "metric": metric,
            "natural_low": low,
            "natural_high": high,
            "raw": raw,
            "raw_inside": low <= raw <= high,
        }
        for name, values in voynich.items():
            if name == "raw":
                continue
            value = values[metric]
            distance_before = 0.0 if low <= raw <= high else min(abs(raw - low), abs(raw - high))
            distance_after = (
                0.0 if low <= value <= high else min(abs(value - low), abs(value - high))
            )
            row[name] = value
            row[f"{name}_inside"] = low <= value <= high
            row[f"{name}_moved_toward"] = distance_after < distance_before
        rows.append(row)
    return rows


def run(
    ctx: Context,
    representations: list[Representation],
    views: dict[str, View],
) -> Topic:
    """Compare each representation against the natural-language region."""
    profiles: dict[str, dict[str, float]] = {name: profile(view) for name, view in views.items()}
    natural = sorted(ctx.baselines)
    for name in natural:
        profiles[name] = profile(ctx.baselines[name])
    for name, view in ctx.pseudo.items():
        profiles[name] = profile(view)

    band = natural_band(profiles, natural)
    voynich = {name: profiles[name] for name in views}
    rows = verdicts(voynich, band)

    moved = {
        name: sum(1 for row in rows if row.get(f"{name}_moved_toward"))
        for name in views
        if name != "raw"
    }
    inside = {
        name: sum(1 for row in rows if row.get(f"{name}_inside", row.get("raw_inside")))
        for name in views
    }

    sections = [
        "## Where each representation sits\n\n"
        + table(
            ["metric", "natural range", *views, "moved toward natural"],
            [
                [
                    row["metric"],
                    f"{row['natural_low']:.3f} … {row['natural_high']:.3f}",
                    *[
                        f"{row[name]:.3f}{'*' if row.get(f'{name}_inside', row['raw_inside']) else ''}"
                        for name in views
                    ],
                    ", ".join(
                        name for name in views if name != "raw" and row.get(f"{name}_moved_toward")
                    )
                    or "—",
                ]
                for row in rows
            ],
        )
        + "\n\n`*` marks a value inside the natural-language range (min–max over "
        + f"{len(natural)} sample-size-matched reference corpora). "
        + "The range is a *region*, not a test: sitting inside it is necessary for a "
        + "natural-language reading, never sufficient.",
        "## Did the merge help?\n\n"
        + table(
            ["representation", "metrics inside natural range", "metrics moved toward it", "origin"],
            [
                [
                    representation.name,
                    f"{inside[representation.name]} / {len(METRICS)}",
                    (
                        f"{moved[representation.name]} / {len(METRICS)}"
                        if representation.name in moved
                        else "—"
                    ),
                    representation.origin,
                ]
                for representation in representations
            ],
        ),
        "## Pseudo-Voynich controls on the same metrics\n\n"
        + table(
            ["view", *METRICS],
            [
                [name, *[f"{profiles[name][metric]:.3f}" for metric in METRICS]]
                for name in ctx.pseudo
            ],
        )
        + "\n\nThe controls are here because a representation that moves Voynichese "
        + "toward natural language moves the pseudo-Voynich too if the movement is an "
        + "artifact of the transform rather than a property of the text.",
    ]
    return Topic(
        topic="recharacterise",
        title="Phase 3 — Post-merge re-characterisation",
        sections=sections,
        data={
            "profiles": profiles,
            "natural_band": {metric: list(values) for metric, values in band.items()},
            "verdicts": rows,
            "inside_counts": inside,
            "moved_counts": moved,
        },
    )
