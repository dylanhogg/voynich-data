# Phase 5 — Strengths and weaknesses of the automated translation

> **SPECULATIVE OUTPUT — unvalidated rendering under a hypothesis that FAILED VALIDATION: the identical pipeline renders pseudo-Voynich, which encodes nothing, at least as well as it renders the manuscript (plan §7.4). This is model output, not a reading of the manuscript.**

## Bottom line

**What this is:** a complete English rendering of all 4,072 lines under a stated hypothesis, with 61.1% of tokens surviving the confidence gate.

**What it is not:** a reading of the Voynich Manuscript. 4 of the 5 kill criteria the plan agreed in advance are met — chief among them the decisive one, that the identical pipeline renders pseudo-Voynich which encodes nothing at 123% of the rate it renders the manuscript. Under §7.4 the decipherment attempt is declared **unsuccessful**, and that is the finding this programme publishes. The Phase 4 artifacts are not withdrawn; they are re-framed, and every one of them carries the failed-validation banner.

## The decisive control (read this before any sample rendering)

| corpus | gated coverage | mean confidence |
| --- | --- | --- |
| real | 0.611 | 0.494 |
| grille | 0.751 | 0.524 |
| selfcite | 0.045 | 0.045 |

`grille` is a Rugg-style table generator and `selfcite` a Timm-style autocopier, both tuned to the manuscript's own hapax rate and word length and matched to it in token count. Neither encodes anything. The identical pipeline, key, calibration map and lexicon produced all three rows, and the numbers above are the ones the committed artifacts carry.

| corpus | gated coverage over 5 random-key draws | min | max |
| --- | --- | --- | --- |
| real | 0.611 | 0.603 | 0.617 |
| grille | 0.700 | 0.624 | 0.751 |
| selfcite | 0.046 | 0.040 | 0.058 |

The confidence column depends on a draw of twenty permuted keys, and the controls are markedly more sensitive to that draw than the manuscript is. Across 5 independent draws the best control reaches 103%–122% of the manuscript's gated coverage, mean 114%. The magnitude is unstable; the direction is not — the control is at or above the manuscript in every draw.

## Kill criteria, agreed in advance (§7.4)

| criterion | measured | met |
| --- | --- | --- |
| Comparable fluency and confidence on pseudo-Voynich | control renders at 123% of the manuscript's rate | yes |
| Held-out performance indistinguishable from the null distribution | permutation p = 0.162 | yes |
| Cross-transcription gloss agreement no better than transcription identity | gloss agreement 0.909 against a 0.293 line-identity baseline | no |
| Multiple unrelated plaintext languages score equivalently | gated coverage spread 0.149 across 4 language models | yes |
| Illustration congruence shows no signal above the permutation null | rendering 0.0902 bits at p = 0.001; untranslated types 0.2108 at p = 0.001 | yes |

## Gated coverage by stratum

### section

| stratum | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| astronomical | 31 | 198 | 0.556 | 0.460 |
| biological | 722 | 6,141 | 0.686 | 0.564 |
| cosmological | 48 | 296 | 0.557 | 0.445 |
| herbal | 1,612 | 10,840 | 0.552 | 0.447 |
| pharmaceutical | 223 | 2,304 | 0.530 | 0.431 |
| stars | 1,159 | 11,619 | 0.641 | 0.513 |
| text_only | 277 | 2,330 | 0.630 | 0.500 |

### currier_language

| stratum | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| A | 1,562 | 10,774 | 0.531 | 0.433 |
| B | 2,437 | 22,521 | 0.650 | 0.523 |
| None | 73 | 433 | 0.550 | 0.445 |

### line_type

| stratum | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| label | 115 | 124 | 0.210 | 0.193 |
| paragraph | 3,957 | 33,604 | 0.612 | 0.495 |

### hand

| stratum | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| 1 | 1,488 | 10,029 | 0.526 | 0.430 |
| 2 | 1,156 | 10,262 | 0.658 | 0.533 |
| 3 | 1,180 | 11,712 | 0.644 | 0.515 |
| 4 | 62 | 389 | 0.553 | 0.451 |
| 5 | 141 | 875 | 0.622 | 0.494 |
| @ | 45 | 461 | 0.610 | 0.502 |

## Strength evidence (§7.1)

| test | metric | value | null / comparison | verdict |
| --- | --- | --- | --- | --- |
| §7.1.1 synthetic recovery | H1 gloss accuracy on ciphertext we built | 0.909 | key accuracy 1.000 | neutral |
| §7.1.2 held-out generalisation | train − holdout gated coverage | 0.023 | permutation p = 0.162 | undermines |
| §7.1.3 cross-transcription stability | gloss agreement on tokens whose ZL and IT surfaces differ | 0.168 | surface agreement 0.890; line identity 0.293 | undermines |
| §7.1.4 internal consistency | Voynich types per distinct English word (gated view) | 4.742 | 1.0 would be a one-to-one reading | vacuous |
| §7.1.5 illustration congruence | gloss-profile divergence across illustration types | 0.090 | permutation p = 0.001 | supports |
| §7.1.6 syntactic plausibility | bits/word of the rendering under a douay_rheims bigram model | 12.752 | shuffled 12.74; real English 9.25 | undermines |
| §7.1.7 anchor agreement | catalogued anchors | 0 | — | not run |

### §7.1.1 synthetic recovery

| hypothesis | corpus | scheme | synthetic tokens | key accuracy | gloss accuracy |
| --- | --- | --- | --- | --- | --- |
| H1 | clusius_rariorum | substitution | 11,600 | 1.000 | 0.909 |
| H2 | austen_pride_prejudice | verbose | 20,000 | 1.000 | 0.716 |
| H3 | vulgate_clementine | abjad | 19,787 | 1.000 | 0.733 |
| H4 | clusius_rariorum | substitution | 11,600 | 1.000 | 0.887 |
| H7 | austen_pride_prejudice | substitution | 19,673 | 0.491 | 0.122 |

These are the numbers from `make calibrate`: a reference corpus in the language each hypothesis assumes, enciphered under its own scheme, attacked blind. They bound what this pipeline could achieve *if* the manuscript were the system the hypothesis describes. They say nothing about whether it is.

### §7.1.2 held-out generalisation

| split | pages | gated coverage |
| --- | --- | --- |
| train | 165 | 0.575 |
| holdout | 41 | 0.552 |
| difference |  | 0.023 |

The held-out pages were never seen by any key search. Permuting the held-out label across the 206 pages 1,000 times puts the observed difference at p = 0.162. A pipeline that had learned something specific to the training pages would degrade on the held-out ones; a pipeline matching a Latin dictionary against short strings has nothing page-specific to lose.

### §7.1.3 cross-transcription stability

| comparison | tokens | agreement |
| --- | --- | --- |
| surface forms identical (ZL vs IT) | 32,661 | 0.890 |
| glosses identical, all aligned tokens | 32,661 | 0.909 |
| glosses identical, tokens whose surfaces differ | 3,582 | 0.168 |
| published line-level identity baseline |  | 0.293 |

The headline agreement (90.9%) is not a measure of stability: it is carried almost entirely by the 89.0% of tokens the two transcribers already write identically, plus the tokens that gloss to nothing under either reading.

On the tokens they actually disagree about, the glosses agree only 16.8% of the time. Which English word a line receives is therefore decided by which transcriber's reading you happen to load — and only 29.3% of lines are identical between the two. A rendering this sensitive to transcription noise cannot be a property of the manuscript.

### §7.1.4 internal consistency

| measure | value |
| --- | --- |
| types glossed identically everywhere | 1.000 |
| distinct Voynich types printed by the gated view | 4,111 |
| distinct English words they print | 867 |
| Voynich types per English word | 4.742 |

The first row is 1.000 **by construction**: glossing is a pure function of the type, so consistency across sections, paradigms and repeated phrases cannot come out any other way. The test as written is vacuous, and the honest number beside it is the collapse ratio: 4,111 distinct Voynich types print only 867 distinct English words, 4.7 to one.

| English word | distinct Voynich types rendered as it |
| --- | --- |
| by | 119 |
| but | 80 |
| go | 72 |
| out of | 67 |
| love | 62 |
| money | 51 |
| whether | 51 |
| altar | 50 |
| to | 49 |
| big toe | 38 |

### §7.1.5 illustration congruence

| illustration type | pages | glossed tokens |
| --- | --- | --- |
| A | 5 | 110 |
| B | 19 | 4,214 |
| C | 6 | 165 |
| H | 128 | 5,984 |
| P | 16 | 1,221 |
| S | 25 | 7,442 |
| T | 6 | 1,469 |

Statistic: token-weighted mean Jensen–Shannon divergence between each illustration type's gloss distribution and the pooled one. Observed 0.0902 bits; permuting the page labels 1,000 times gives p = 0.001.

| corpus scored | divergence | permutation p |
| --- | --- | --- |
| glossed rendering | 0.090 | 0.001 |
| glossed rendering, permuted within Currier language | 0.090 | 0.001 |
| untranslated Voynich types | 0.211 | 0.001 |
| pseudo-Voynich, same page labels | 0.000 | 0.954 |

The third row is what settles this test, and it settles it against the rendering. The untranslated Voynich types score 0.2108 bits at p = 0.001: the manuscript's *own vocabulary* already varies with what is drawn on the page, which Phase 1 established and which needs no translation to observe. Glossing is a deterministic many-to-one map of the surface form, so by the data-processing inequality it cannot manufacture page structure the surface types do not already have — and it does not: 0.0902 bits against 0.2108. The rendering inherits this signal; it does not supply it.

The other two rows rule out the cheaper explanations. `grille` encodes nothing yet inherits the manuscript's line and page structure, so it shows what page layout alone produces (p = 0.954). And illustration type is heavily confounded with Currier language, whose two halves differ in word length; permuting labels only among pages of the same Currier language still gives p = 0.001, so the effect is not purely that confound.

The label-level variant — the sharper test, matching an individual label to the thing it is drawn beside — needs the illustration↔label concordance that plan §5.1 lists as an **open gap**. It is not run, and no hand-built plant or body-part word list stands in for it: that list would be the answer smuggled into the question.

### §7.1.6 syntactic plausibility

| English model | text scored | words | bits/char | bits/word (bigram) |
| --- | --- | --- | --- | --- |
| douay_rheims | manuscript rendering | 20,605 | 3.506 | 12.752 |
| douay_rheims | same glosses, shuffled order | 20,605 | 3.506 | 12.739 |
| douay_rheims | pseudo-Voynich rendering | 25,338 | 4.121 | 12.832 |
| douay_rheims | the reference corpus itself | 64,000 | 2.453 | 9.255 |
| austen_pride_prejudice | manuscript rendering | 20,605 | 3.543 | 12.558 |
| austen_pride_prejudice | same glosses, shuffled order | 20,605 | 3.542 | 12.549 |
| austen_pride_prejudice | pseudo-Voynich rendering | 25,338 | 4.074 | 12.648 |
| austen_pride_prejudice | the reference corpus itself | 25,712 | 2.565 | 10.511 |

Two models per corpus, because the character model is nearly blind to word order — it reads a shuffled rendering almost as happily as the original, which is why the plan's shuffle comparator needs the word-bigram column beside it to have any power at all. The reference row is the same corpus scoring unseen text from itself: the floor a genuinely English rendering would approach.

### §7.1.7 anchor agreement

The anchor catalogue in `translations/decipher/anchors.py` is empty, and deliberately so: an anchor enters it only with a checksummed source behind it. Plan §5.1 lists the three sources that would fill it — the zodiac month-name marginalia, the f116v marginalia, and the v101 mapping — as **still open** after Phase 3. Entering them by hand would put an unsourced answer into the audit that is supposed to test the answer.

## Weakness evidence (§7.2)

| test | metric | value | null / comparison | verdict |
| --- | --- | --- | --- | --- |
| §7.2.1 pseudo-Voynich control | `grille` gated coverage as a share of the manuscript's | 1.230 | 1.00 means gibberish renders as well; 5 draws span 103%–122% | undermines |
| §7.2.2 shuffled-input control | character-shuffled Voynichese, gated coverage as a share of the manuscript's | 0.419 | word-order shuffle scores 0.978 — a tautology, not a test | neutral |
| §7.2.3 rival-language ambiguity | spread in gated coverage across plaintext languages | 0.149 | gain spread 1.318 bits/token | undermines |
| §7.2.4 key instability | mean token-level gloss agreement across independent re-searches | 0.293 | 1.00 would mean the key is identified | undermines |
| §7.2.5 ablations | largest swing in gated coverage across analysis choices | 0.140 | committed run reads 0.641 | undermines |
| §7.2.6 known-weak zones | weakest zone: tokens containing a unit the key never saw | 0.138 | whole manuscript 0.611 | neutral |
| §7.2.7 coverage honesty | gated coverage, whole manuscript | 0.611 | — | neutral |

### §7.2.2 shuffled-input control

| surrogate | gated coverage | mean confidence | same glosses as the manuscript |
| --- | --- | --- | --- |
| shuffle_chars | 0.274 | 0.226 | no |
| shuffle_within_word | 0.361 | 0.295 | no |
| shuffle_word_order | 0.640 | 0.524 | yes |
| manuscript (no reliability weighting) | 0.654 | — | yes |

The reliability weight is switched off for all four rows: it is defined by a ZL/IT token alignment that a surrogate has no counterpart for, so leaving it on would penalise the manuscript alone.

The last column is the finding. `shuffle_word_order` produces the *identical multiset of glosses* as the manuscript — glossing is context-free, so reordering the words cannot change what any token becomes. Its gated coverage differs only because each rendering draws its own twenty permuted null keys, by about the same margin §7.2.1 measured between draws. Destroying the manuscript's word order costs this pipeline nothing, because no stage of it reads a sequence.

### §7.2.3 rival-language ambiguity

| language model | variant | gain/token | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| clusius_rariorum | clusius_rariorum-o3\|plain | -5.771 | 0.643 | 0.537 |
| dante_commedia | dante_commedia-o3\|plain | -5.927 | 0.494 | 0.401 |
| vulgate_clementine | vulgate_clementine-o3\|plain | -6.835 | 0.628 | 0.503 |
| austen_pride_prejudice | austen_pride_prejudice-o3\|plain | -7.090 | 0.546 | 0.447 |

Every key here was searched under the same scheme and the same representation, differing only in which reference corpus supplied the language model — Latin, Italian and English among them. Each resulting key is then glossed against the *same Latin* lexicon.

The gain spread across languages is 1.318 bits/token and the gated-coverage spread is 0.149. A method that had identified the plaintext language would separate them sharply; a key found under an English model should not produce Latin dictionary hits at a comparable rate.

### §7.2.4 key instability

| hypothesis | re-searches | mean key agreement | mean gloss agreement | worst gloss agreement |
| --- | --- | --- | --- | --- |
| H1 | 9 | 0.527 | 0.430 | 0.038 |
| H2 | 9 | 0.174 | 0.344 | 0.037 |
| H3 | 9 | 0.427 | 0.416 | 0.159 |
| H4 | 9 | 0.285 | 0.191 | 0.044 |
| H7 | 9 | 0.045 | 0.082 | 0.070 |

Each hypothesis was searched again from scratch: 6 fresh seeds on the full training pages, and 3 searches on random 80% subsets of them. Every re-found key was then used to gloss the whole manuscript, and compared token by token against the committed rendering.

Agreement here is not accuracy. Two keys can agree because both are right or because both fail the same way — a token that glosses to nothing under either key counts as agreement, which is why the number is an upper bound on stability, not a measure of it.

H7 is searched here by simulated annealing like the rest, but its *committed* key came from an exact assignment under an order-1 model, which has no seed. Its row therefore measures how close annealing lands to a known optimum, not how unstable H7 is.

### §7.2.5 ablations

| ablation | tokens | gated coverage | mean confidence | mean key coverage |
| --- | --- | --- | --- | --- |
| committed (T1-glyph, CB=break, ZL, all lines) | 33,728 | 0.641 | 0.516 | 0.999 |
| tokenizer T0-char | 33,728 | 0.501 | 0.410 | 0.820 |
| comma policy CB=join | 31,311 | 0.666 | 0.540 | 0.998 |
| transcription IT | 33,176 | 0.649 | 0.530 | 0.998 |
| uncertainty-flagged lines dropped | 28,119 | 0.652 | 0.536 | 0.999 |
| Currier A only | 10,774 | 0.563 | 0.462 | 0.997 |
| Currier B only | 22,521 | 0.682 | 0.560 | 0.999 |
| consensus subset only | 28,359 | 0.648 | 0.539 | 1.000 |

The committed row differs from `coverage.md` because reliability weighting is switched off here, so that the ablations that change the transcription are comparable with the ones that do not.

`T0-char` is the informative failure: the committed key is defined over merged glyph units, so a character tokenization presents it with units it has never seen, its key coverage collapses, and the rendering goes with it. A key is only meaningful together with the tokenization it was searched on.

Largest swing in gated coverage: 0.140.

### §7.2.6 known-weak zones

| known-weak zone | lines | tokens | gated coverage | mean confidence |
| --- | --- | --- | --- | --- |
| labels | 115 | 124 | 0.210 | 0.193 |
| circular / radial pages (illustration A or C) | 79 | 494 | 0.557 | 0.451 |
| lines flagged uncertain | 84 | 933 | 0.476 | 0.342 |
| lines flagged illegible | 0 | 0 | — | — |
| lines with transcriber alternatives | 584 | 5,182 | 0.558 | 0.405 |
| lines with high-ASCII tokens | 115 | 956 | 0.510 | 0.418 |
| Currier language unknown | 73 | 433 | 0.550 | 0.445 |
| outside the consensus subset (transcribers disagree) | 658 | 5,369 | 0.511 | 0.412 |
| lines at least half hapax | 236 | 1,160 | 0.537 | 0.423 |
| tokens containing a unit the key never saw | — | 123 | 0.138 | 0.162 |

Whole-manuscript gated coverage is 0.611. Zones with no rows were checked and are listed empty rather than omitted. A zone above that line is not better understood — the pipeline has no notion of understanding — it simply contains shorter or commoner strings that hit the Latin lexicon more often.

### §7.2.7 coverage honesty

| section | tokens | high | medium | low | none |
| --- | --- | --- | --- | --- | --- |
| astronomical | 198 | 0.333 | 0.222 | 0.182 | 0.263 |
| biological | 6,141 | 0.451 | 0.236 | 0.120 | 0.194 |
| cosmological | 296 | 0.287 | 0.270 | 0.152 | 0.291 |
| herbal | 10,840 | 0.283 | 0.269 | 0.159 | 0.289 |
| pharmaceutical | 2,304 | 0.268 | 0.262 | 0.181 | 0.289 |
| stars | 11,619 | 0.376 | 0.265 | 0.121 | 0.238 |
| text_only | 2,330 | 0.342 | 0.288 | 0.122 | 0.247 |

The gated view prints the high and medium bands only: 61.1% of tokens across the manuscript. The remaining tokens appear in `english_speculative` marked `?word?` or `⟨surface⟩(≈guess)`, and appear in the gated view as `UNKNOWN`. Neither number is a measure of correctness — both are measures of how often a Latin lexicon matched a short string.

## Falsification conditions

**What would retire the current hypothesis** — beyond the criteria already met:

- A pseudo-Voynich control that renders *less* than the manuscript would remove the decisive objection, but only removes it; it is a necessary condition, not evidence.
- A key that survives re-searching from a different seed with near-total gloss agreement, where the current keys do not.
- Ablations that leave the headline coverage unmoved, where changing the tokenization currently collapses it.

**What would raise confidence** — none of these is available from the manuscript alone, and all are automatable once their source is:

- The illustration↔label concordance that plan §5.1 still lists as an open gap, turning §7.1.5 into a label-level test rather than a page-level one.
- A sourced anchor catalogue (zodiac month names, f116v marginalia, the v101 mapping), which would let §7.1.7 run at all.
- A hypothesis whose gain per token beats an order-2 Markov model of the manuscript's own statistics on held-out pages. No hypothesis in this programme does; until one does, every rendering downstream is decoration on a losing model.

## Decision log

| decision | title | where |
| --- | --- | --- |
| Decision 1 | Primary Source Selection | `docs/decisions.md` — Decision 1 |
| Decision 2 | Stolfi Interlinear Usage | `docs/decisions.md` — Decision 2 |
| Decision 3 | Line Numbering Policy | `docs/decisions.md` — Decision 3 |
| Decision 4 | Text Cleaning Algorithm | `docs/decisions.md` — Decision 4 |
| Decision 5 | Schema Versioning (Pre-1.0) | `docs/decisions.md` — Decision 5 |
| Decision 6 | Line-Level Granularity First | `docs/decisions.md` — Decision 6 |
| Decision 7 | IVTFF Locus Type Preservation | `docs/decisions.md` — Decision 7 |
| Decision 8 | Tokenization Contract for Analysis (T0/T1 + comma policy) | `docs/decisions.md` — Decision 8 |
| Decision 9 | Reference Corpora Are Fetched, Not Vendored | `docs/decisions.md` — Decision 9 |
| Decision 10 | Frozen Held-Out Page Split | `docs/decisions.md` — Decision 10 |
| Decision 11 | Entropy Estimation and Bootstrap Protocol | `docs/decisions.md` — Decision 11 |
| Decision 12 | Definition of the "Running Prose" Subset | `docs/decisions.md` — Decision 12 |
| Decision 13 | Cross-Transcription Stability Is Judged on the EVA Pair Only | `docs/decisions.md` — Decision 13 |
| Decision 14 | Currier B Is Not Reachable from A by a Single Systematic Transformation | `docs/decisions.md` — Decision 14 |
| Decision 15 | `[a:b]` Alternative Selection Is a Parameter, Not a Hard-Coded Convention | `docs/decisions.md` — Decision 15 |
| Decision 16 | One Description-Length Scale for Every Hypothesis | `docs/decisions.md` — Decision 16 |
| Decision 17 | Annealing with Restarts Instead of Gibbs Decipherment | `docs/decisions.md` — Decision 17 |
| Decision 18 | The H4 Abbreviation Transform Is a Crude Proxy | `docs/decisions.md` — Decision 18 |
| Decision 19 | H5 Is Registered Unfunded, Not Falsified | `docs/decisions.md` — Decision 19 |
| Decision 20 | Every Funded Phase 2 Hypothesis Was Falsified by Its Own Criterion | `docs/decisions.md` — Decision 20 |
| Decision 21 | Paragraph Blocks Come from the IVTFF Markers, Not from Heuristics | `docs/decisions.md` — Decision 21 |
| Decision 22 | Token Alignment Is EVA-Only and the Reliability Weight Is Declared, Not Fitted | `docs/decisions.md` — Decision 22 |
| Decision 23 | A Multi-Part Corpus Entry, and What `herbal_latin` Is Not | `docs/decisions.md` — Decision 23 |
| Decision 24 | Three Phase 3 Gaps Stay Open, With Their Pre-Committed Fallbacks | `docs/decisions.md` — Decision 24 |
| Decision 25 | Round-2 Re-Scoring Narrows Every Gap and Changes No Verdict | `docs/decisions.md` — Decision 25 |
| Decision 26 | Confidence Is the Calibrated Score Times a Random-Key Null, Not the Calibrated Score Alone | `docs/decisions.md` — Decision 26 |
| Decision 27 | The Distributional Gloss Fallback Is Not Implemented | `docs/decisions.md` — Decision 27 |
| Decision 28 | No Word Reordering and No Inserted Function Words | `docs/decisions.md` — Decision 28 |
| Decision 29 | The Pseudo-Voynich Control Renders More Than the Manuscript Does | `docs/decisions.md` — Decision 29 |
| Decision 30 | The Decipherment Attempt Is Declared Unsuccessful | `docs/decisions.md` — Decision 30 |
| Decision 31 | The Artifact Banner Is Chosen by the Run's Own Control Result | `docs/decisions.md` — Decision 31 |
| Decision 32 | Illustration Congruence Is Measured Against the Untranslated Text | `docs/decisions.md` — Decision 32 |
| Decision 33 | The Key Is Not Identified — Re-Searching Changes Most of the Reading | `docs/decisions.md` — Decision 33 |
| Decision 34 | The Glosses Inherit Transcription Disagreement Rather Than Surviving It | `docs/decisions.md` — Decision 34 |

Every negative result in this programme is written up there, as `AGENTS.md` requires: a cleanly falsified hypothesis is a deliverable.

## Run

`make audit` · 6 seeds and 3 training subsets per keyed hypothesis · 1,000 permutations per null · ceiling 7200 s. No wall-clock figure is recorded here or in the manifest, so the report is byte-identical across runs.

**One caveat about this audit itself.** Plan §9 asked for the Phase 5 tests to be written before any Phase 4 output was read, so that the pipeline could not be tuned against its own audit. That ordering was not followed: Phase 4 was completed and its reports read first. Nothing in Phase 4 was changed in response to an audit result — the only edit this phase made to it was the banner, which the audit's verdict requires — but the tests were chosen by someone who already knew what the pipeline produced, and a reader should weigh them accordingly. Three of them (§7.1.5's untranslated-type baseline, §7.2.1's five-draw range, §7.2.2's gloss-multiset assertion) were added *because* a first result looked better than it was, which cuts in the honest direction but is exactly the freedom the ordering rule exists to remove.
