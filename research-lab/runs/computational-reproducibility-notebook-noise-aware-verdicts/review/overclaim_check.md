# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | How much "irreproducibility" in biomedical Jupyter notebooks is run-to-run noise? About a fifth of mismatching notebooks, and exact matching overstates irreproducibility about 1.3-fold; neither clears nor clearly misses the preregistered bars | H1_share 0.206 (0.104-0.368); overstatement 1.26 (1.09-1.58); both Inconclusive | Supported | was 'too few to call exact-match verdicts badly inflated' (both intervals reach their bars) |
| 2 | standfirst | Python notebooks from PubMed Central-linked GitHub repositories, drawn from those that Samuel and Mietchen's large-scale re-execution found to run but not reproduce their stored outputs. | plan.md sample; ledger N2, N5 | Supported |  |
| 3 | standfirst | Environments were rebuilt with uv, pinned to the dependency landscape before publication, inside isolated Docker containers. | plan.md environments | Supported |  |
| 4 | standfirst | Each notebook was executed three times without network access, plus once with current packages. | plan.md execution | Supported |  |
| 5 | standfirst | The plan was committed before any notebook was executed; an execution bug found during validation forced a full re-run (D3). | git: plan before execution; deviations.md D3 | Supported |  |
| 6 | verdict | **Verdict: H1 Inconclusive; H2 Inconclusive.** | primary H1, H2 Inconclusive | Supported |  |
| 7 | verdict | **H1 (in at least 30% of completing-but-mismatching notebooks, every mismatch is run-to-run variability): Inconclusive.** | plan H1 | Supported |  |
| 8 | verdict | **7 of 34** (20.6%; Wilson 95% 10.4% to 36.8%; repository bootstrap 7.9% to 36.7%). | all_intrinsic 7 / exact_mismatch 34; Wilson 0.104-0.368; repo bootstrap 0.079-0.367 | Supported |  |
| 9 | verdict | The point estimate is below the bar, but the interval includes it. | bar 0.30 inside both intervals | Supported |  |
| 10 | verdict | **H2 (exact-match verdicts overstate irreproducibility by at least 1.4×): Inconclusive.** | plan H2 | Supported |  |
| 11 | verdict | Among the 57 notebooks that ran to completion three times, 59.6% fail exact matching and 47.4% fail noise-aware matching. | completed_with_3_reps 57; exact 0.5965, noise-aware 0.4737 | Supported |  |
| 12 | verdict | The factor is **1.26** (repository bootstrap 1.09 to 1.58). | overstatement 1.259 (1.086-1.579) | Supported |  |
| 13 | verdict | **Notebooks the dataset called irreproducible now match.** 23 of the 57 match their stored outputs exactly under this comparator, which masks volatile tokens and compares numbers at displayed precision. | 57 - 34 exact mismatches = 23 match | Supported |  |
| 14 | verdict | **What drives the real mismatches.** | heading | Supported |  |
| 15 | verdict | Missing command-line tools: shell cells calling `qiime`, `wget` or `unzip` fail silently inside Jupyter, so the notebook still "completes". | cell mismatch audit (notebooks.csv; posthoc_no_shell.json) | Supported |  |
| 16 | verdict | Version-dependent output formats, such as pandas `value_counts` naming and Python 2 reprs. | cell mismatch audit | Supported |  |
| 17 | verdict | Genuinely stochastic analyses (MCMC, cross-validation). | intrinsic cells 28 of 180 mismatching | Supported |  |
| 18 | verdict | With current packages, 11% of cells that are stable and matching in the AS-OF environment change. | drift_share_of_stable_cells 0.111 | Supported |  |
| 19 | verdict | **The comparator agrees with hand labels on 94 of 100 cell pairs.** All six disagreements are figures flagged as different that differ only cosmetically (fonts and title weights across matplotlib versions). | validation.json 94/100; six disagreements are cosmetic figure differences (G4 audit; single labeller, G7 not applied) | Supported |  |
| 20 | verdict | A looser image tolerance moves H1 only to 21.9% (post hoc). | posthoc_phash12.json H1 0.219 (post hoc) | Supported |  |
| 21 | plain terms | Scientists increasingly publish the code behind their papers as Jupyter notebooks. | background | Supported |  |
| 22 | plain terms | Studies that re-run them often find the results don't match, and count that as a failure to reproduce. | ledger N1, N2 | Supported |  |
| 23 | plain terms | But some analyses involve randomness, and would give slightly different numbers even on the original computer. | background | Supported |  |
| 24 | plain terms | Is much of the measured "irreproducibility" just that? | question | Supported |  |
| 25 | plain terms | We took about 150 notebooks from biomedical papers that an earlier study had found didn't reproduce. | 149 notebooks kept (How it was done) | Supported |  |
| 26 | plain terms | We rebuilt each one's software environment as it was around publication, in a sealed container, and ran it three times. | plan.md | Supported |  |
| 27 | plain terms | About 40% of the notebooks that ran turned out to match their published outputs after all, once trivial differences such as memory addresses and timestamps were ignored. | 23 of 57 match (40%) under the masked comparator | Supported |  |
| 28 | plain terms | Of those that still differed, only about one in five differed solely because of run-to-run randomness. | H1 share 20.6% | Supported |  |
| 29 | plain terms | Most differences had other causes, such as missing command-line tools and changed software or output formats. | cell mismatch audit: missing tools, version-dependent formats | Supported | was '... or analyses that aren't seeded' (unseeded variation is what the study counts as noise) |
| 30 | plain terms | So exact-match counts somewhat overstate the problem, by a factor of about 1.3 here, but most mismatches are not just noise. | overstatement 1.26; H1 20.6% (upper 36.8% < 50%) | Supported |  |
