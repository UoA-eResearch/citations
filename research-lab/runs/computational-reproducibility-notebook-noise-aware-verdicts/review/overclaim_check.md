# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | How much "irreproducibility" in biomedical Jupyter notebooks is run-to-run noise? About a sixth of mismatching notebooks by the preregistered rule, none if the stored value must fall within the replicates' range; masked exact matching overstates irreproducibility about 1.2-fold, byte-exact matching 1.9-fold | primary.json H1 5/30, H1_envelope_only 0/30, overstatement 1.20, overstatement_byte_exact 1.92 | Supported | retitled after review |
| 2 | standfirst | Python notebooks from PubMed Central-linked GitHub repositories, drawn from those that Samuel and Mietchen's large-scale re-execution found to run but not reproduce their stored outputs. | plan.md sample; ledger N2, N5 | Supported |  |
| 3 | standfirst | Environments were rebuilt with uv, pinned to the dependency landscape before publication, inside isolated Docker containers. | plan.md environments | Supported |  |
| 4 | standfirst | Each notebook was executed three times without network access, plus once with current packages. | plan.md execution | Supported |  |
| 5 | standfirst | The plan was committed before any notebook was executed; an execution bug found during validation forced a full re-run (D3). | git: plan before execution; deviations.md D3 | Supported |  |
| 6 | verdict | **Verdict: H1 Inconclusive; H2 Inconclusive.** Both were re-computed after review with a corrected comparator (D4); neither verdict changed. | primary.json H1/H2 Inconclusive; primary_v1.json | Supported |  |
| 7 | verdict | **H1 (in at least 30% of completing-but-mismatching notebooks, every mismatch is run-to-run variability): Inconclusive.** | plan H1 | Supported |  |
| 8 | verdict | **5 of 30** (16.7%; Wilson 95% 7.3% to 33.6%; repository bootstrap 3.7% to 32.0%). | primary.json all_intrinsic 5, exact_mismatch 30, wilson [0.0734, 0.3356], repo bootstrap [0.037, 0.32] | Supported |  |
| 9 | verdict | The point estimate is below the bar, but the interval includes it. | bar 0.30 inside both intervals | Supported |  |
| 10 | verdict | **The preregistered rule is a disjunction, and only one branch is ever met.** A mismatch counts as noise if the three replicates differ among themselves, or if the stored value lies inside their range. | plan.md intrinsic rule; primary.json H1_varies_only_notebooks 5 | Supported |  |
| 11 | verdict | In all 5 notebooks every mismatching cell meets only the first branch: the replicates vary, but the stored value lies outside their range or is an image. | primary.json H1_varies_only_notebooks 5; intrinsic_cells_split envelope_only 0 | Supported |  |
| 12 | verdict | Read strictly, requiring the stored value inside the replicates' range, H1 is 0 of 30 (0% to 11.4%). | primary.json H1_envelope_only 0/30 wilson [0, 0.1135] | Supported |  |
| 13 | verdict | Some cases are convincing, such as Monte-Carlo output, random data, random error bars and tie order in `value_counts`. | review finding 4 (nb18515, nb18687, nb18392, nb7508), all in the 5 | Supported |  |
| 14 | verdict | **H2 (exact-match verdicts overstate irreproducibility by at least 1.4×): Inconclusive.** | plan H2 | Supported |  |
| 15 | verdict | Among the 57 notebooks that ran to completion three times, 52.6% fail **masked** exact matching and 43.9% fail noise-aware matching. | primary.json exact_fail_rate 0.5263, noise_aware_fail_rate 0.4386 | Supported |  |
| 16 | verdict | Masked matching hides volatile tokens and compares numbers at displayed precision. | compare.py mask, num_equal | Supported |  |
| 17 | verdict | The factor is **1.20** (repository bootstrap 1.04 to 1.47). | primary.json overstatement 1.2 ci [1.0385, 1.4707] | Supported |  |
| 18 | verdict | **Against byte-exact matching** on the same re-runs, 84.2% fail and the factor is **1.92**, which would clear the bar. | primary.json rungs byte_exact 48/57; overstatement_byte_exact 1.92 | Supported |  |
| 19 | verdict | The preregistered comparison is the masked one. | plan.md H2 | Supported |  |
| 20 | verdict | **All 57 were irreproducible in the dataset**, so these rates describe that set, not notebooks in general (D1). | D1.4 | Supported |  |
| 21 | verdict | **Three rungs, on the study's own re-runs:** 48 of 57 notebooks differ byte for byte, 30 under masked matching, and 25 under noise-aware matching. | primary.json rungs 48/30/25 of 57 | Supported |  |
| 22 | verdict | So normalisation recovers 18 notebooks and replicates 5 more. | primary.json rungs 48-30, 30-25 | Supported |  |
| 23 | verdict | 9 notebooks match byte for byte here, although the dataset called them irreproducible. | primary.json rungs 57-48 | Supported |  |
| 24 | verdict | For those, its verdict came from its environment or its comparator, not from the notebook. | posthoc_commit.json identical notebook files; byte-exact match | Supported |  |
| 25 | verdict | 31 of the 57 were checked out at a commit other than the dataset's, but the notebook file is identical at both commits in all 31. | posthoc_commit.json read_at_other_commit 31, identical 31 | Supported |  |
| 26 | verdict | The stored outputs compared are the dataset's own. | posthoc_commit.json | Supported |  |
| 27 | verdict | **The comparator, validated blind** (post hoc; `results/tables/validation_blind.json`). | validation_blind.json | Supported |  |
| 28 | verdict | A separate labelling session judged 95 stratified cell pairs without seeing the comparator's verdicts, plus all 17 remaining figure mismatches. | validation_blind.json pairs 95; validation_blind/labels2.json 17 | Supported |  |
| 29 | verdict | Text: the comparator agrees on 29 of 30 flagged mismatches and 20 of 20 matches. | validation_blind.json text_mismatch 29/30, text_match 20/20 | Supported |  |
| 30 | verdict | Figures: it agrees on 14 of 15 matches, but only 20 of the 47 flagged figure mismatches are judged genuinely different. | validation_blind.json figure_match 14/15; posthoc_figures_human.json judged_different 20 of 47 | Supported |  |
| 31 | verdict | The rest differ in fonts, legend placement, tick labels or figure size. | validation_blind/labels*.json reasons | Supported |  |
| 32 | verdict | With the human judgement in place of the comparator for every flagged figure, H1 is 5 of 26 (19.2%, 8.5% to 37.9%) and the H2 factor 1.24. | posthoc_figures_human.json 5/26 (0.0851-0.3788), overstatement 1.2381 | Supported |  |
| 33 | verdict | Neither verdict changes. | posthoc_figures_human.json | Supported |  |
| 34 | verdict | The first draft's 94/100 agreement came from a check whose labeller saw the comparator's verdicts. | review finding 2 (verdict in the sample file; same agent) | Supported |  |
| 35 | verdict | It is withdrawn. | D4 | Supported |  |
| 36 | verdict | **What drives the real mismatches.** | heading | Supported |  |
| 37 | verdict | Missing command-line tools: shell cells calling `qiime`, `wget` or `unzip` fail silently inside Jupyter, so the notebook still "completes". | cell mismatch audit (notebooks.csv; posthoc_no_shell.json) | Supported |  |
| 38 | verdict | Version-dependent output formats, such as pandas `value_counts` naming. | cells inspected in the first draft; review finding 8 (Python 2 reprs at most one notebook, dropped) | Supported | Python 2 removed |
| 39 | verdict | Genuinely stochastic analyses (MCMC, cross-validation). | intrinsic cells 28 of 180 mismatching | Supported |  |
| 40 | verdict | With current packages, 12% of cells that are stable and matching in the AS-OF environment change. | primary.json drift_share_of_stable_cells 0.1183 | Supported |  |
| 41 | plain terms | Scientists increasingly publish the code behind their papers as Jupyter notebooks. | background | Supported |  |
| 42 | plain terms | Studies that re-run them often find the results don't match, and count that as a failure to reproduce. | ledger N1, N2 | Supported |  |
| 43 | plain terms | But some analyses involve randomness, and would give slightly different numbers even on the original computer. | background | Supported |  |
| 44 | plain terms | Is much of the measured "irreproducibility" just that? | question | Supported |  |
| 45 | plain terms | We took about 150 notebooks from biomedical papers that an earlier study had found didn't reproduce. | 149 notebooks kept (How it was done) | Supported |  |
| 46 | plain terms | We rebuilt each one's software environment as it was around publication, in a sealed container, and ran it three times. | plan.md | Supported |  |
| 47 | plain terms | Of the 57 that ran, 9 matched their published outputs byte for byte, and 27 in all matched once trivial differences were ignored, such as memory addresses, timestamps and digits beyond those printed. | primary.json rungs: 9 byte-exact matches, 27 masked matches | Supported |  |
| 48 | plain terms | Of the 30 that still differed, 5 showed run-to-run variation in every mismatching cell. | primary.json all_intrinsic 5 of 30 | Supported |  |
| 49 | plain terms | But in none of them did the published output fall within the spread of our three runs, so randomness is a possible explanation, not a demonstrated one. | primary.json H1_envelope_only 0 | Supported |  |
| 50 | plain terms | Most differences had other causes, such as missing command-line tools and changed software or output formats. | cell mismatch audit: missing tools, version-dependent formats | Supported | was '... or analyses that aren't seeded' (unseeded variation is what the study counts as noise) |
| 51 | plain terms | So how much exact-match counts overstate the problem depends on what "exact" means: by a factor of about 1.2 once trivial differences are masked, and about 1.9 for byte-for-byte comparison. | primary.json overstatement 1.2, overstatement_byte_exact 1.92 | Supported |  |
| 52 | plain terms | Most mismatches are not just noise. | primary.json 25 of 30 masked mismatches not all-intrinsic | Supported |  |
