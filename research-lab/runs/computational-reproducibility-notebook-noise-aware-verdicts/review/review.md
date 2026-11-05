# Review: computational-reproducibility-notebook-noise-aware-verdicts

Reviewer: independent adversarial review (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.py`–`checks4.py` with `.txt` outputs, `recompare.csv`, `cells_recomputed.csv`, `png_dists.csv`,
`img/` contact sheets: stored | asof_1 | asof_2 | asof_3). All checks used `venv/bin/python -I` with `code/` on
`sys.path`, reading only stored notebooks and run outputs; nothing was executed.

## Verdict: fix first

The pipeline is sound where it matters most: the selection fields match the dataset's schema (340 eligible, one
execution each), no failed run is scored as a match (57 completed = 57 with three "ok" status files), the D3
timeline is as described (first comparison 06:38:27, re-runs from 06:38:41, verdicts moved from Refuted/Refuted
to Inconclusive/Inconclusive), and both verdicts survive my re-computations. But: (1) one of the seven H1
numerator notebooks is a comparator artefact (stream chunking), so the primary table is wrong by one in both
numerator and denominator; (2) the comparator validation is hollow (the labeller saw the comparator's verdict in
the sample file, the 100 labels were written in 68 s, and in a fresh sample 5 of 6 flagged figure mismatches are
cosmetic); (3) the "40% now match … once trivial differences are ignored" attribution is not supported by the
data (byte-exact matching on the study's own reruns already passes 9 of the 23, and 31 of 57 notebooks were read
from a different commit than the dataset used); (4) "every mismatch explained by run-to-run variability" is
true only under the disjunctive definition: in all seven H1 notebooks the stored value lies outside the
replicates' range or is an image, and under the envelope-only reading H1 is 1 of 31.

## Findings

### 1. (Major) nb16791 is counted all-intrinsic because stdout was split into chunks; coalesced, it matches exactly

Evidence: `checks3.txt` §1, `checks4.txt` §1. The cell prints 4,366 numbers; the stored notebook holds one
stdout chunk, each rerun three chunks split at different positions. `cell_equal` (`compare.py:101`) compares
item by item, so the chunk count makes it a mismatch and the chunk boundaries make the replicates "vary". After
concatenating consecutive stdout items, stored = asof_1 and the three replicates are identical. With coalescing:
exact mismatches 33, all-intrinsic 6, H1 = 18.2% (Wilson 8.6–34.4%), H2 factor 1.22. Chunking also defeats the
envelope test for nb4750 (stored "MSE: 6.5371" against replicates 6.3254/6.4102/6.5668 — inside the range, but
`in_envelope` returns False because the rerun has two text items; `compare.py:107`). The report's missing-tool
and format explanations are unaffected.

Fix: coalesce consecutive stream outputs of the same name before comparison (nbformat semantics); re-run
`compare.py run`; update primary.json, the table, the title's "about a fifth" (18%) and overclaim rows 8, 28.

### 2. (Major, G7/G1) The 94/100 validation is not a blind check, and figure verdicts are mostly wrong when flagged

Evidence: `checks1.txt`/`checks3.txt` §B; file times. `compare.py sample` writes `comparator_mismatch` into the
pair file handed to the labeller (`compare.py:237`), the sample was written at 07:15:23 and `validation.json` at
07:16:31, and the labeller is the agent that wrote the comparator. 55 of the 100 pairs were comparator mismatches;
all 6 disagreements are figures the comparator flagged. In my fresh sample of 30 cells (seed 2026; 18 text
mismatches, 6 figure mismatches, 6 matches; contact sheets in `img/`): text mismatches 16 of 18 correct (nb16791 is
finding 1; nb17727 differs in the 17th significant digit, finding 6); figure mismatches 1 of 6 real (nb5344 PR
curves with different areas), 5 cosmetic (fonts, legend placement, axis labels: nb17648, nb2176, nb17652, nb21804
×2); matches 6 of 6. Across all 143 stored-vs-rerun figure pairs, 38 exceed 6 bits and 25 of those sit at 7–12
bits (`png_dists.csv`). So the 94% figure is dominated by easy text cases and the flagged-figure precision is
around 1 in 6 to 1 in 2.

Fix: redo the validation blind (strip the verdict field, label before looking at it, second labeller or at least
a different session), report agreement separately for flagged mismatches and for figures, and adopt the 12-bit
threshold (post hoc phash12) or a pixel-level test as primary with justification. Overclaim row 19 is Overstated.

### 3. (Moderate) "23 of 57 now match once trivial differences are ignored" misattributes the cause

Evidence: `checks2.txt` §C and the commit check. Byte-exact comparison of stored vs asof_1 on the study's own
reruns fails 48 of 57 notebooks, the masked comparator 34. So normalisation accounts for 14 notebooks (25%), and 9
(16%) match byte-for-byte: for those the dataset's verdict differed because of its environment, its comparator,
or the notebook version. On the last point, 31 of the 57 completed notebooks were read at an AS-OF commit that is
not the dataset's `commit`; the stored outputs the study compared against were never shown to be the ones the
dataset compared against. The plain-terms sentence and the "Normalisation matters as much as replicates" bullet
state the 40% as a normalisation effect.

Fix: report the byte-exact 48/57, the masked 34/57 and the noise-aware 27/57 as three rungs; count notebooks at a
different commit and, for them, check whether the notebook file differs from the dataset's version.

### 4. (Moderate) "Explained by run-to-run variability" rests entirely on the "varies" branch; the stored value is never inside the envelope

Evidence: `checks2.txt` §A, `checks3.txt` §2, `checks4.txt`. Of 28 intrinsic cells, 24 are "varies only"
(replicates differ and the stored value lies outside their min–max), 3 varies-and-envelope, 1 envelope-only. All
seven all-intrinsic notebooks are varies-only (five involve images, where no envelope test exists). Under the
envelope-only reading of "explained by noise" (coalesced, text items, finding 1 applied) H1 is 1 of 31 (3.2%,
Wilson 0.6–16.2%, which would be Refuted) and the H2 factor 1.03. The preregistered disjunction stands as the
verdict rule, but "differed solely because of run-to-run randomness" (plain terms) and "every mismatch is
explained by run-to-run variability" are stronger than what three replicates show. Some cases are convincing
(nb18515 Monte-Carlo, nb18687 random data, nb18392 random error bars, nb7508 tie order in `value_counts`); nb19758's
mismatch is an unmasked timing token ("elapsed_time:0.05[sec]" escapes the duration regex) plus a figure.

Fix: state the varies/envelope split in the verdict bullet and give the envelope-only number as a sensitivity;
soften the plain-terms sentence to "showed run-to-run variation in every mismatching cell".

### 5. (Moderate) H2's "exact-match verdicts" are the study's masked comparator, not exact matching

Evidence: plan §3, `checks2.txt` §C. The title and H2 bullet say "exact matching overstates … about 1.3-fold". The
numerator is the masked, precision-aware, 6-bit-phash comparator (34/57); against byte-exact matching on the same
reruns (48/57) the factor is 48/27 = 1.78, which clears the 1.4 bar. D1.4 states the within-sample base (all 57
were dataset-irreproducible) in deviations.md but the report's H2 bullet and the "What this does not show" list do
not. Readers will take "exact" literally.

Fix: say "masked exact matching" in the title/verdict, report the byte-exact factor beside it, and repeat the
within-sample caveat in the verdict.

### 6. (Minor) Comparator strictness at full double precision, and a few masking gaps

Evidence: `checks4.txt` §2: 6 mismatching cells in 4 notebooks differ only in numbers printed to ≥ 10 significant
digits by < 1e-9 relative (e.g. nb17727 `pearsonr` −0.17749533260329886 vs …892); with a tolerance for such
numbers two more notebooks (nb17727, nb19008) become exact matches (H1 6/31, H2 1.24). `\d+ ... [sec]` and "Oct 24
18:11" listings (`!ls -l`, nb23220 cell 11, labelled intrinsic) are not masked. None changes a verdict.

Fix: treat full-precision floats with a relative tolerance (say 1e-9) and extend the duration/timestamp masks;
report the effect.

### 7. (Minor) The completing set is not what the report implies about environments

Evidence: `checks1.txt`, the requirements check. Of 149 notebooks, 11 had a requirements file (2 built, 0
completed), 110 were resolved from the import map (49 completed) and 28 had no mapped imports (8 completed, built
with ipykernel only). Every completed notebook therefore ran in an import-map environment resolved AS-OF, never in
an author-declared one. The report says "uv installs the repository's requirements, or the notebook's imports";
it should say the former never completed. D2 (full image retry) is fair but recovered only 10 builds, and its
LATEST arm stayed slim (8 LATEST builds failed), which the drift secondary should note. Repository-size filtering
dropped 36 of 192 (19%), 25 on GitHub size before cloning.

### 8. (Minor) Process and numbers

- One execution (nb19053, `asof_1` status "error") finished at 07:47, after `primary.json` (07:19:45) and the draft
  commit (07:21). It is excluded either way, but results were tabulated while a run was still live; say so or
  wait for the queue.
- Shell "not found" messages are on stdout in 6 notebooks and stderr in 2 (`checks3.txt` §3), so they are
  compared in 6 and ignored in 2; the post hoc no-shell exclusion (6) is the stdout set. State the rule.
- The 7 notebooks named in the H1 numerator cluster in 7 repositories, fine; 1 of 57 completed notebooks is
  Python 2 (it matches), so the "Python 2 reprs" cause is at most one notebook — nb21804's `u'...'` text reprs
  are from that one.
- All other numbers in the report match `primary.json`, `validation.json` and the post hoc tables; the Wilson
  interval for 7/34 recomputes to 10.35–36.80%.

## Gate checks

- **G1 (labeller blind):** fails (finding 2). **G7:** single labeller, 68 s for 100 pairs; hollow.
- **G2:** the flow figure counts 149 → 71 built → 57 completed; no failure is scored as a match (verified from the
  status JSONs). The 36 too-large, 6 missing and 1 clone-failed are in `sample_all.csv` but the report's "Kept: 149
  with repositories of at most 500 MB" should list the three reasons.
- **G5:** `review/overclaim_check.md` present; the gate edits were honest, but rows 8, 13, 19, 27, 28 and 30 need
  relabelling after findings 1–5.
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (5 claims)".
