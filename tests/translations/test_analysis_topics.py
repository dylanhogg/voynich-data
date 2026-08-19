"""Topic modules run end to end on a small synthetic context.

The real Phase 1 run takes minutes; these tests check that each module produces
a well-formed report from a corpus small enough to be instant, so the shapes and
the report contract are covered without the compute.
"""

from __future__ import annotations

import random

import pytest

from translations.analysis import currier, entropy, landmarks, lexis, morphology, position, syntax
from translations.analysis.common import View
from translations.analysis.context import Context
from translations.report import Topic
from translations.strata import StratumRow

ALPHABET = "qokedycshlainrt"


def _row(index: int, line_number: int, page: str) -> StratumRow:
    return StratumRow(
        line_id=f"{page}:{line_number}",
        page_id=page,
        folio_id=page[:2],
        quire_id="qA" if index % 2 else "qB",
        side="recto",
        line_number=line_number,
        section="herbal" if index % 2 else "stars",
        page_section="herbal",
        page_section_disputed=False,
        currier_language="A" if index % 2 else "B",
        hand="1" if index % 3 else "2",
        line_type="paragraph",
        illustration_type="H",
        position="+",
        is_first_line_of_page=line_number == 1,
        is_last_line_of_page=line_number == 4,
        has_uncertain=False,
        has_illegible=False,
        has_alternatives=False,
        has_high_ascii=False,
        mismatch_status="exact_match",
        in_consensus=True,
        is_holdout=False,
    )


def _view(name: str, seed: int, lines: int = 60) -> View:
    rng = random.Random(seed)
    content = []
    rows = []
    for index in range(lines):
        line = [
            [rng.choice(ALPHABET) for _ in range(rng.randint(2, 7))]
            for _ in range(rng.randint(3, 8))
        ]
        content.append(line)
        rows.append(_row(index, index % 4 + 1, f"f{index // 4 + 1}r"))
    return View(name=name, lines=content, rows=rows)


@pytest.fixture(scope="module")
def context() -> Context:
    base = _view("voynich|base", 1)
    strata = {
        key: _view(f"voynich|{key}", index + 2)
        for index, key in enumerate(
            (
                "currier_a",
                "currier_b",
                "consensus",
                "prose",
                "labels",
                "section_herbal",
                "section_stars",
            )
        )
    }
    baselines = {
        key: _view(f"baseline|{key}", index + 20)
        for index, key in enumerate(
            ("vulgate_clementine", "austen_pride_prejudice", "finnish_bible")
        )
    }
    nulls = {
        key: _view(f"null|{key}", index + 40)
        for index, key in enumerate(
            ("shuffle_within_word", "shuffle_word_order", "markov_words|n=1")
        )
    }
    pseudo = {
        key: _view(f"pseudo|{key}", index + 60) for index, key in enumerate(("grille", "selfcite"))
    }
    return Context(
        base=base,
        grid={"T1-glyph|CB=break|zl": base, "T1-glyph|CB=break|it": strata["consensus"]},
        strata=strata,
        baselines=baselines,
        nulls=nulls,
        pseudo=pseudo,
    )


@pytest.mark.parametrize("module", [entropy, lexis, morphology, syntax, position, currier])
def test_topic_modules_produce_reports(module, context: Context) -> None:  # type: ignore[no-untyped-def]
    topic = module.run(context)
    assert isinstance(topic, Topic)
    assert topic.sections and all(section.startswith("## ") for section in topic.sections)
    assert topic.data


def test_landmark_gate_reads_topic_results(context: Context) -> None:
    results = {
        module.__name__.rsplit(".", 1)[-1]: module.run(context).data
        for module in (entropy, lexis, morphology, syntax, position, currier)
    }
    gate = landmarks.run(results)
    assert set(gate.data["landmarks"]) and isinstance(gate.data["passed"], bool)
    # Random text must not reproduce the manuscript's landmarks.
    assert not gate.data["passed"]
