# Phase 2 — Approach to cracking

> **SPECULATIVE OUTPUT — no verified decipherment of the Voynich Manuscript exists. This is model output under a stated hypothesis, not a reading of the manuscript.**

## The question, made scoreable

Every hypothesis is treated as a *code* for the manuscript, and scored by the number of bits it needs to reconstruct the observed glyph stream exactly: the model (key, merge partition, syllable table, grammar) plus the data under that model. This is what puts 'enciphered Latin' and 'meaningless table-generated text' on one scale, and it is the MDL penalty of §4.1 — a key elaborate enough to fit anything has to pay for itself first.

Two costs are charged that are easy to omit. Writing down the key costs `(units − 1) · log2 27` bits. And if a key maps several glyphs onto one letter, the plaintext no longer reconstructs the manuscript, so each occurrence is charged `log2(glyphs sharing that letter)`. Without that second term every search collapses the key onto `e`.

## What a score is measured against

The reference is an order-2 Markov model of the glyph stream itself, with its parameters priced at ½·log2(N) bits each. It knows nothing about language — only the manuscript's own local statistics — so a hypothesis that cannot beat it is not explaining anything. Reported **gain** is bits per token saved against that baseline.

A raw score is not evidence, so every funded hypothesis is re-run, unchanged, on four null corpora: the two tuned pseudo-Voynich generators from Phase 1 (grille, autocopy), a glyph shuffle, and an order-2 Markov surrogate. Significance is the real score's position in that null distribution, Benjamini–Hochberg corrected across the grid.

## Search

Keys are found by simulated annealing with multi-restart, seeded, iteration-counted, and started from a frequency-matched assignment. Scoring is vectorised over *distinct* cipher n-grams rather than positions, which is what makes a million key evaluations affordable on CPU. For the order-1 case (H7) the optimal key is an exact linear assignment, so no search is needed.

The verbose hypothesis (H2) is searched two ways: fixed-width segmentation (every plaintext letter written with exactly 2 or 3 glyphs) and a content-based merge search over partitions, seeded with the morphs Phase 1 induced. The merge search is stochastic steepest descent — plain hill-climbing wanders in this space, which the synthetic verbose cipher makes visible.

Not implemented: Bayesian/Gibbs decipherment. At a 25-symbol cipher alphabet the annealer reaches the same optimum well inside budget; Gibbs earns its keep on key spaces an order of magnitude larger, which is H5, and H5 is registered unfunded.

## Discipline

All 10 hypotheses were registered as YAML records — prediction, falsifier, prior, Phase 1 evidence for and against, search grid and budget share — and committed before any run. Searches see the training pages only; the held-out pages (41 of 206, frozen in Phase 0) are scored once, at the end, with the key the search already committed to. Every candidate is written to `output/decipher/candidates.parquet`, losers and null runs included, each row carrying its budget, convergence and truncation flags.

Anchors (zodiac month names, marginalia) are **not** used: the catalogue is empty until Phase 3 can source them with checksums. The protocol is implemented so that when they arrive they can only rank finished candidates, never enter the models.

## Does the search work at all?

Known-answer tests, on ciphers built here and then broken blind: substitution 100%, verbose 100%, abjad 100% token accuracy. The engine recovers keys it invented itself under substitution, fixed-width verbose and abjad schemes, which is the precondition for its verdict on the manuscript meaning anything. See `synthetic_validation.md`.

## Funded this run

| id | hypothesis | family | budget share | search |
| --- | --- | --- | --- | --- |
| H1 | Monoalphabetic substitution of a natural language | substitution | 0.060 | substitution |
| H2 | Verbose cipher - one plaintext letter written as several glyphs | substitution | 0.450 | merge |
| H3 | Abjad / vowel-suppressed script | substitution | 0.080 | substitution |
| H4 | Medieval Latin scribal abbreviation | substitution | 0.060 | substitution |
| H6a | Table and grille generated meaningless text (Rugg) | generative | 0.050 | grille |
| H6b | Autocopying / self-citation generation (Timm and Schinner) | generative | 0.050 | selfcite |
| H7 | Transposition or anagrammed plaintext | substitution | 0.020 | assignment |
| H8 | Natural language with heavy affixal morphology, lightly encoded | generative | 0.050 | morphology |
| H9 | Constructed language or ars combinatoria | generative | 0.050 | slot_grammar |
