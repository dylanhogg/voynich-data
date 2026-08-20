# Phase 3 — Analysis round 2

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## Findings

| finding | effect size | what it means for the translation |
| --- | --- | --- |
| Token-level agreement is far higher than line-level agreement | 0.862 of tokens read identically by ZL and IT, against 0.293 of lines | the line-level mismatch rate overstates transcription noise for anything computed per token |
| Merging buys entropy and pays for it in word length and repetition | 4 of 11 metrics inside the natural-language range against 3 raw; 4 moved toward it, h2, h3, word_length_cv, morph_bits_saved_per_word | H2's converged merge shifts the conditional entropies into the natural region but drives mean word length below every baseline and doubles the near-repeat rate — the signature of a compression, not of a plaintext |
| Reliability filtering leaves the landmarks where they were | 3 of 11 metrics inside the natural range, 3 moved toward it | the landmarks are properties of the text, not artifacts of the tokens the two transcribers disagree about |
| Roots take more distinct suffixes than in either comparison language | 3.76 suffixes per root against 1.90 (Latin) and 1.63 (Finnish) | suffix choice looks freer than inflection allows — positional generation remains the live rival to morphology |
| Section-specific vocabulary is real | mean divergence 0.461 bits against a page-permutation null of 0.165 (max 0.199), p = 0.005 | herbal-only and pharma-only vocabularies exist beyond page-topic frequency; they are the most translatable subsets if anything is |
| Labels are shorter and plainer than running text | mean length 2.37 against 4.92 in a size-matched prose sample; suffix rate 0.242 against 0.895 | consistent with a nomenclature, but with no concordance they still cannot be tied to what they label |
| Re-scoring narrows every gap and changes no verdict | best round-2 result H2 on merged at -0.105 bits/token, p = 0.308, unconverged | the gaps narrow because the baseline is re-based per representation — on the same channel a shuffled-text surrogate gains ten bits — so no row of the eighteen is evidence, and none beat its surrogates |

## What this changes for Phase 4

The translator's configuration is written to `output/translation/phase3_translator_config.json`. It records two things and keeps them apart: `best_scoring`, the top of the ranked table, which is an unconverged wide-codebook variant and is there only so the number is not hidden; and `chosen`, the best *converged* candidate that committed to a key, which is what Phase 4 should actually run. It also carries the per-token reliability weights the renderer must apply, and the anchors it is allowed to use — still none.

Three things Phase 3 makes available that Phase 4 should use: the paragraph blocks (so a rendering unit can be a paragraph rather than a line), the per-token reliability weight (so a gloss can be hedged token by token), and the section-specific vocabulary (so herbal and pharmaceutical pages can be glossed separately from the rest).

## What we still cannot tell (input to Phase 4)

1. What the labels name: no machine-readable illustration↔label concordance could be pinned, so the 115 label lines remain a nomenclature for unknown things.
2. Whether the marginalia say anything usable: their readings are disputed and exist only as prose discussion, so no crib enters the pipeline.
3. Whether Voynichese words are composed or generated: the paradigm probe shows suffix choice is freer than inflection and barely conditioned by context, which weakens the morphology reading without establishing generation.
4. Whether any hypothesis in the registered space is right: every one of them loses to a Markov model of the manuscript's own statistics, on every representation tested. The space may simply not contain the answer.
5. Whether GC and FG agree with the EVA pair at token level: the v101 mapping is unbuilt, so cross-alphabet robustness is still untested.

## Run

Reports regenerated from `output/translation/phase3_manifest.json`; the run cost is recorded there. Topics: distribution, gap_analysis, labels, paradigms, recharacterise, reliability, rescoring.
