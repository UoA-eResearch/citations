# Review: bioinformatics-sc-disease-de-negative-control

Reviewer: independent adversarial review, 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.txt`). Checks used `venv/bin/python -I` on the stored tables; no DE job was re-run and no container was
started.

## Verdict: publish with edits

The study is carefully built and the arithmetic holds: every figure in the report reproduces from `contrasts.csv`
and `primary.json` (74% / 82%, the by-disease shares, the practitioner bands 12 / 42 / 64%, the Open Targets 9.91%
raw with none surviving BH, the 11.8% and 5.5% matching fallbacks, 8.9% of nulls above 100 DE genes), coverage is
complete with no failed fits in 420,274, D2 is correctly timed (power check 00:58, H1 tables 01:02), and the
positive control behaves as a working test should. The headline needs one correction. "Indistinguishable from the
matched null" is, for most of the 74%, not a case of the disease result resembling healthy variation: it is a case
of both sides finding nothing at all. 53% of all contrasts return zero DE genes in the real comparison at matched
size, and those zero-signal contrasts make up 72% of the indistinguishable group, against a null whose median is
also zero in 96.5% of contrasts. That is a finding about power at 13 donors per group, and the report should say so
in the title and plain-terms section rather than only in the size caveat.

## Findings

### 1. (Major) Most "indistinguishable" contrasts produce no DE genes at all, so the comparison is nothing against nothing

Evidence: `checks1.txt` §A. At the matched size the real comparison's median DE-gene count over the 25 subsamples is
exactly 0 for 424 of 799 contrasts (53.1%). Of the 590 contrasts called indistinguishable on the DE-gene count, 424
(71.9%) are these. The matched null's median is 0 in 96.5% of contrasts, and its 95th percentile is 0 in 27.9%. So
for the bulk of the headline share the empirical p is 1 by construction: neither the disease comparison nor any of
its 500 healthy comparisons found a single gene.

This does not break H1 as preregistered, and the direction of the conclusion is unchanged. But the report's framing
("the disease result is no more striking than what you get by splitting healthy people into two arbitrary groups",
"cannot be told apart from comparing healthy donors with each other") invites the reading that disease signatures
look like donor noise. For three quarters of the indistinguishable group the correct statement is that at 13 donors
a side the analysis is empty on both sides. The interesting, defensible claim is the one in the practitioner
section: contrasts that yield 0 or 1–10 DE genes at full size never exceed their null (0 of 347), and even those
yielding 11–100 exceed only 12% of the time.

Fix: give the zero-DE share in the verdict and the plain-terms section; retitle along the lines of "at matched group
sizes most atlas contrasts produce no differential expression at all, and of those that do, most do not exceed a
healthy-vs-healthy null"; keep the existing size caveat.

### 2. (Moderate) The sex-matching fallback undermines the exceedances, not the indistinguishable share, and the gradient is much stronger than the report conveys

Evidence: `checks1.txt` §F. Splitting contrasts by the sex imbalance between their disease and normal groups:

| quartile | median sex imbalance | share exceeding the null | median null 95th percentile (DE genes) |
|---|---|---|---|
| lowest | 0.03 | 12.0% | 1.00 |
| second | 0.10 | 25.0% | 1.00 |
| third | 0.18 | 20.6% | 1.00 |
| highest | 0.36 | 47.0% | 1.05 |

The correlation between sex imbalance and exceeding is 0.29. The null's 95th percentile is flat across quartiles, so
the 5.5% of null slots that could not match sex do **not** inflate the null; the association sits entirely on the
real side. This answers the brief's question: the fallback weakens the exceedance cases and leaves the
indistinguishable ones alone, which means the true share of contrasts carrying disease signal is lower than 26%,
not higher. The report states the direction but gives only the regression coefficient; the fourfold gradient is the
more telling number and belongs in the Results.

### 3. (Moderate) The empirical p and BH together impose a floor that favours H1, unstated

Evidence: `checks1.txt` §B. With 500 null draws the smallest attainable p is 1/501 = 0.0020. Under BH across 799
contrasts, a contrast can only reach q < 0.05 if at least 32 contrasts tie at that minimum. Here 129 do, so the
constraint does not bind and the reported 26% exceedance is sound. But the design cannot ever report a small number
of distinguishable contrasts: had only, say, 20 contrasts carried real signal, S1 would have come out at 100%. The
test is structurally conservative in the direction of H1, and that should be on the record beside the verdict.

Fix: one sentence stating the minimum detectable count; optionally raise B for the contrasts near the boundary.

### 4. (Minor) D2 is defensible, but the power check does not establish sensitivity to realistic effects

Evidence: `power_check.json`; `deviations.md` D2. The switch of emphasis to the DE-gene count is justified, properly
timed (power check written 00:58, H1 tables 01:02) and made from null draws and synthetic injections alone, with the
one incidental sighting disclosed. The π1 result is still reported with its 8% power, which is the honest treatment.
The caveat is that the injection is large: a twofold change in one gene in twenty. Power of 87% against that says
little about power against a disease effect of a few tens of percent in a handful of genes, which is what most of
these contrasts would plausibly carry. The report already says it does not estimate per-contrast power against a
biological effect size; given finding 1, that limitation deserves more prominence than a bullet under "Not shown",
because it is the main alternative explanation for the headline.

### 5. (Confirmatory) Checks that passed

- All reported numbers reproduce: by-disease shares (COVID-19 45.3%, schizophrenia 0/37, tauopathy 0/35,
  interstitial lung disease 62.5%, pulmonary fibrosis 63.0%), practitioner bands (11.8 / 42.3 / 64.3%), Open Targets
  (575 contrasts, 9.91% at raw p, 0 after BH), m median 13 against 100 donors at full size, 106 median cells.
- H2: 335 pairs, 94 groups, 9 diseases, median ρ 0.19, β_d 0.061 (0.021–0.095), β_d − β_c 0.030 (−0.032 to 0.084);
  the disease-level bootstrap widens everything to include zero, as the report says. The null-pair baseline (0.03
  against 0.30) is computed on the same 33 pairs with both sides' null draws, and 0.30 is that subset's own real
  median rather than the headline 0.19, so the comparison is like for like. "Inconclusive" is the right call.
- Coverage: 43 of 43 datasets pseudobulked, 420,274 of 420,274 fits succeeded, 5 replication pairs dropped for
  fewer than 500 shared genes, donor drops reasoned (21,073 under the 10-cell rule, 116 multi-disease).
- Timeline: plan 05:16 before any expression value, D1 05:37, analysis code 05:46, results 01:06 the next day.

## Gate checks

- **G1:** the audit in plan §6 is real. Null draws see disease labels only to copy composition, nothing is tuned on
  results, and the Open Targets caveat about shared underlying studies is stated. The label-correlated field it did
  not anticipate is sex through the matching fallback, which finding 2 quantifies; the plan does flag sex matching
  as a limit.
- **G2:** `coverage.json` present and complete; no unplanned fallback entered a statistic; the matching fallbacks
  are counted and reported.
- **G3:** `plausibility.md` has the positive control (219 DE genes, p = 0.005 against 200 permutations, with π1
  missing it at p = 0.25), the power check, and three traced contrasts; the invariants hold.
- **G4:** `age_map.csv` lists 194 distinct development-stage strings with parsed years and bins; the donor-exclusion
  reasons are in coverage.
- **G5:** `review/overclaim_check.md` is consistent with the tables; the title row and the plain-terms rows need
  relabelling after finding 1.
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (7 claims)". The Open Targets row's
  corrected DOI resolves to the right paper, and the self-reported near-miss (a resolvable but unrelated identifier
  caught by the title check) is the sort of disclosure the gate exists for.
- **G7:** does not apply; there are no human labels. Confirmed.

## Confirmation pass

Reviewer: Opus 5.5, 2026-11-05 (first review by Fable 5.1). Second-round check of the D3 edits against the four
findings above. Scripts and outputs in `review/reviewer_checks/`: `confirm_findings.py` -> `confirm_findings.txt`
(independent recomputation from `results/tables/contrasts.csv`, compared field by field with
`results/tables/posthoc_review.json`) and `confirm_gates.py` -> `confirm_gates.txt` (report text against each D3 edit,
the G5 table against the sentences the tool extracts from `report.md`, `tools/overclaim_check.py --verify`, and
`tools/attribution.py check --show`). All Python ran as `venv/bin/python -I` with paths as arguments; nothing outside
`review/` was modified. I also read `deviations.md` D3, `code/posthoc_review.py`, `code/analyse.py` (empirical p and
BH) and `code/draws.py` (null matching).

What I checked:
- **Zero-DE share.** 424 of 799 (53.07%) have a matched-size median of zero DE genes; all 424 are indistinguishable
  (empirical p = 1 for every one, by construction), making 71.86% of the 590. Null median zero in 96.5% of contrasts.
  375 contrasts find at least one DE gene; 166 (44.3%) of them are indistinguishable and 209 (55.7%) exceed, so the
  report's departure from the first review's suggested wording is correct and the plain-terms "a little over half"
  is right. All 799 contrasts have 500 null and 25 real fits, so the p denominator is 501 throughout. The power
  reading is further supported: the zero-DE share falls from 61% at m = 8-10 to 36% at m > 22.
- **Sex-imbalance quartiles.** The table reproduces exactly (12.0 / 25.0 / 20.6 / 47.0%; median null q95 1.0 / 1.0 /
  1.0 / 1.05; r = 0.285). But two further cuts change what it can support (`confirm_findings.txt` §2): the association
  is entirely between datasets (within-dataset r = -0.010; dataset-level r = 0.61 over 25 datasets; 57% of the
  imbalance variance is between datasets), and only the *median* null q95 is flat: the share of contrasts whose null
  q95 exceeds 10 DE genes rises 9.5% -> 14.5% -> 25.6% -> 25.0%, and the mean from 12 to 60-173. The gradient also
  largely tracks the zero-DE share (70% in the lowest quartile, 24% in the highest); among contrasts with any DE genes
  it is non-monotone (39 / 65 / 49 / 61%).
- **p floor.** 1/501 = 0.001996; ceil(0.001996 x 799 / 0.05) = 32 (exact 31.9); 129 contrasts sit at the minimum,
  giving q = 0.0124 there. My BH recomputation matches `n_de_q` exactly and gives 209 distinguishable.
- **Power caveat.** Now the second bullet of "What this does and does not show" ("Power is the main alternative
  explanation"), with the injection size stated; the "Not shown" bullet is kept.
- **Report text.** Title, verdict bullets ("Most of the 74% is nothing against nothing", 424/799, 96.5%, 72%, 166 of
  375, "mainly reflects power", the 1/501 floor) and the reframed plain terms are all present.
- **G5.** The tool extracts 51 sentences; the table has the same 51, in order, with correct section labels, none stale
  or missing, all labelled Supported with backing; `--verify` -> "G5 passed (51 rows)". G5's scope does not include
  Results, so it does not cover the sex-imbalance conclusion below.
- **G6.** `attribution.py check --show` -> "G6 passed (7 claims)"; every resolved title is the work its claim names.

### Final verdict: publish with edits

- **Finding 1 (zero-DE share): fixed.** Every number reproduces (`confirm_findings.txt` §1), the title, verdict and
  plain terms are reframed around power, and the 166-of-375 departure is the correct reading of the data. One small
  wording point remains (issue 3 below).
- **Finding 2 (sex-imbalance gradient): partly fixed.** The quartile table is in Results and is correct. The
  conclusion attached to it, "the true share of contrasts carrying disease signal is likely below 26%", does not
  follow. The first review proposed it, and this pass withdraws it. With a within-dataset correlation of -0.01, the
  table cannot tell cohort-level confounding (which would lower the true share) from dataset or disease differences in
  signal and power (which would not). "Flat" holds only for the median of the null q95; its upper tail rises with
  imbalance (`confirm_findings.txt` §2).
- **Finding 3 (p floor): fixed.** The arithmetic is right and it sits beside the verdict. The wording of the
  condition is slightly off (issue 2 below), but the substance holds: the design cannot report fewer than 32
  distinguishable contrasts (4% of 799) other than none.
- **Finding 4 (power caveat): fixed.** It is moved into "What this does and does not show" and says the injection is
  large and realistic-effect power was not estimated.

Remaining issues:
1. (Moderate) Results, sex-imbalance bullets: replace "the true share of contrasts carrying disease signal is likely
   below 26%, not above it" with a statement that the association is between datasets (within-dataset r = -0.01), so
   it is consistent with cohort-level confounding but cannot establish it. Qualify "the null's 95th percentile is
   flat" to the median, noting that the share of contrasts with null q95 > 10 DE genes rises from 9.5% to 25%.
2. (Minor) Verdict, p-floor bullet: "only if at least 32 contrasts reach that minimum" should read "only if at least
   32 contrasts are called distinguishable". Under BH step-up, 70 contrasts at p = 2/501 with none at the minimum
   would all pass (`confirm_findings.txt` §3).
3. (Minor) Plain terms: "neither the disease comparison nor its healthy fakes found any differences at all"
   overstates the null side. For the 424 zero-DE contrasts the null median is zero in 99.3%, but the null q95 is zero
   in only 32%. Suggest "nor the typical healthy fake".
4. (Minor, record) `deviations.md` D3 is dated 2026-11-06, but the file was written 2026-11-05 22:12 NZDT, before this
   pass (2026-11-05 23:37 NZDT). Correct the date.
