# Deep Voynich Analysis

```
============================================================
VCAT DEEP ANALYSIS
============================================================

Loading dataset...
Characters: 170,564
Words: 33,625

============================================================
1. COMPRESSION ANALYSIS (Entropy Upper Bounds)
============================================================

Original size: 204,732 bytes

Compression ratios (lower = more structure):
  gzip  : 0.327 (3.14 bits/char)
  bz2   : 0.294 (2.83 bits/char)
  lzma  : 0.302 (2.90 bits/char)

Shuffled text (destroys structure):
  gzip  : 0.578
  bz2   : 0.543
  lzma  : 0.524

→ Lower ratio on real vs shuffled = genuine structure exists

============================================================
2. SHANNON ENTROPY
============================================================

Character entropy (bits/char):
  H0 (max possible): 4.644
  H1 (unigram):      3.865
  h2 (bigram):       2.314  ← KEY METRIC
  h3 (trigram):      2.071
  h4 (4-gram):       1.982

→ Bowern (2021) found h2 ≈ 2.0 for Voynich
→ Natural languages typically h2 ≈ 3.0-4.0
→ Your result: h2 = 2.314

============================================================
3. WORD-POSITION ENTROPY (Novel Analysis)
============================================================

Entropy by character position in word:
(Lower = more constrained/predictable)

  Position 1: H=3.21 bits  (n=33,625)  top: o:20%, c:18%, q:16%
  Position 2: H=3.25 bits  (n=32,489)  top: h:26%, o:20%, a:10%
  Position 3: H=3.48 bits  (n=30,388)  top: e:22%, k:12%, o:10%
  Position 4: H=3.61 bits  (n=27,342)  top: e:20%, i:10%, o:10%
  Position 5: H=3.59 bits  (n=21,368)  top: y:17%, e:12%, d:11%
  Position 6: H=3.37 bits  (n=13,057)  top: y:28%, d:12%, n:10%
  Position 7: H=3.25 bits  (n=6,550)  top: y:33%, n:13%, d:9%
  Position 8: H=3.33 bits  (n=2,750)  top: y:30%, n:14%, i:10%

→ Natural languages: fairly uniform entropy across positions
→ Voynich: rigid positional constraints suggest slot grammar

============================================================
4. CHARACTER TRANSITIONS (What follows what?)
============================================================

Most common bigrams:
  ch:  9973  (observed/expected: 8.9x)
  he:  7558  (observed/expected: 4.5x)
  dy:  6362  (observed/expected: 5.9x)
  ai:  6121  (observed/expected: 7.7x)
  ok:  5620  (observed/expected: 4.4x)
  in:  5576  (observed/expected: 15.5x)
  ol:  5260  (observed/expected: 4.3x)
  qo:  5170  (observed/expected: 7.6x)
  ed:  4759  (observed/expected: 3.9x)
  ee:  4587  (observed/expected: 2.5x)
  ii:  4306  (observed/expected: 6.4x)
  sh:  4218  (observed/expected: 6.9x)
  ho:  3722  (observed/expected: 1.8x)
  ey:  3695  (observed/expected: 2.2x)
  da:  3653  (observed/expected: 4.2x)

Rarest bigrams (that should exist but don't):
  oh: 0 occurrences (expected ~2081)
  eh: 0 occurrences (expected ~1684)
  co: 0 occurrences (expected ~1537)
  ce: 0 occurrences (expected ~1244)
  ah: 0 occurrences (expected ~1193)
  dh: 0 occurrences (expected ~1103)
  ih: 0 occurrences (expected ~1016)
  lh: 0 occurrences (expected ~887)
  ca: 0 occurrences (expected ~881)
  cd: 0 occurrences (expected ~815)

→ Missing expected bigrams suggest phonotactic constraints

============================================================
5. WORD LENGTH DISTRIBUTION
============================================================

Word length frequencies:
   1:  1136 (  3.4%) ███
   2:  2101 (  6.2%) ██████
   3:  3046 (  9.1%) █████████
   4:  5974 ( 17.8%) █████████████████
   5:  8311 ( 24.7%) ████████████████████████
   6:  6507 ( 19.4%) ███████████████████
   7:  3800 ( 11.3%) ███████████
   8:  1549 (  4.6%) ████
   9:   627 (  1.9%) █
  10:   251 (  0.7%) 
  11:   117 (  0.3%) 
  12:    79 (  0.2%) 

Mean length: 5.06
Std dev:     1.94
Coefficient of variation: 0.38

→ Natural language CV typically 0.4-0.6
→ Voynich shows unusually symmetric distribution

============================================================
6. CURRIER A vs B: ENTROPY COMPARISON
============================================================

Metric                 Language A   Language B   Difference
----------------------------------------------------------
Characters                 53,433      114,977
H1 (unigram)                3.831        3.859        0.028
h2 (bigram)                 2.357        2.184        0.173

→ Different entropies suggest different underlying systems
→ Or: same system with different vocabulary/register

============================================================
7. HAPAX LEGOMENA (Single-occurrence words)
============================================================

Total unique words:  7,159
Hapax legomena (1x): 4,994 (69.8%)
Dis legomena (2x):   773 (10.8%)

Hapax ratio: 14.85% of all word tokens

→ Natural language hapax ratio typically 40-60% of vocabulary
→ Very high hapax suggests productive morphology or noise

Sample hapax (longest):
  syoraiinykeeoloctheody
  shdydchdchschsyotchdy
  okeedydchschysotchdy
  chdyolchyykchyykedy
  yteychkeeodypchedpy
  ytyokeeodysyolcheey
  dteodoiinsaroqoches
  lshedarydalshalshy
  octhydarchytotody
  chokeeokychokoran

============================================================
8. LINE POSITION EFFECTS
============================================================

Most common LINE-INITIAL words:
  daiin            153 (3.8%)
  y                 73 (1.8%)
  saiin             57 (1.4%)
  dain              48 (1.2%)
  dar               36 (0.9%)
  sol               34 (0.8%)
  sain              33 (0.8%)
  qokeey            32 (0.8%)
  ol                32 (0.8%)
  o                 32 (0.8%)

Most common LINE-FINAL words:
  daiin            123 (3.1%)
  dy                82 (2.1%)
  dam               52 (1.3%)
  am                50 (1.3%)
  dal               46 (1.2%)
  dar               41 (1.0%)
  oly               39 (1.0%)
  ol                38 (1.0%)
  y                 37 (0.9%)
  aiin              35 (0.9%)

Entropy by line position:
  Initial: 9.72 bits
  Middle:  9.82 bits
  Final:   9.71 bits

→ Lower entropy = more constrained choices
→ Line position affects word choice (unusual for cipher)

============================================================
SUMMARY OF FINDINGS
============================================================

Key metrics:
  • h2 (conditional entropy): 2.314 bits/char
  • Compression ratio (gzip): 0.327
  • Vocabulary richness: 21.3%
  • Hapax ratio: 69.8% of vocabulary
  • Mean word length: 5.06 chars

Structural findings:
  • 53,433 chars in Language A, 114,977 in Language B
  • h2 differs between A (2.357) and B (2.184)
  • Strong positional constraints on characters within words
  • Line position affects word choice
  • Many "expected" bigrams are completely absent

============================================================
Analysis complete.
============================================================
```
