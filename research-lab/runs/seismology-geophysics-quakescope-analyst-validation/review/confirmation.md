# Confirmation pass: QuakeScope station-level validation, revision 278a772

Reviewer: the same independent reviewer as `review/review.md`, 12 October 2026. Checked: `deviations.md` D5 and its
completion note, `report.md`, `report.html`, `code/review_checks.py`, `code/run_review_checks.sh`, the diffs to
`checks.py`, `figures.py` and `tests/synthetic_test.py`, everything in `results/tables/review/`, the rerun AGHQ
JSONs, the extended `station_reliability.csv`, the new Figure 1, `tiles.json`, and the logs. Every number named below
was recomputed from the stored outputs or from the data with the study's venv; the variant-A station effects were also
compared with my own independent refit from the first pass. Nothing outside `review/` was modified.

## Verdict: PUBLISH WITH EDITS

All 21 issues are resolved or, for issue 11, settled in a way I accept. Every new number in the report reproduces.
Three small edits remain, none of which touches a verdict:

1. **Variant-A convergence sentence** (report.md, zero-output section, "Convergence: as in the primary fit, every VB
   fit carries statsmodels' non-convergence flag"). Not quite: `h1_excl_zero_days.json` has `boot_converged_share
   0.02`, i.e. 4 of the 200 refits did converge (the draws file confirms 4 `True`). Write "the main fit and 196 of the
   200 refits carry the flag".
2. **The quoted phrase "recently integrated"** attributed to Tepp et al. (SSA 2024) in "Related work". The SSA
   listing I can reach says the SCSN "has integrated the deep-learning picker PhaseNet into its event
   post-processing". Either quote the abstract verbatim or drop the quotation marks; the substance is confirmed.
3. **Wherever the one-word tag appears without the verdict line** (the lab index entry in `leads.json` has no
   verdict fields yet), carry the qualifier with it: "Refuted on H2; H1 at its threshold", or a plain-summary sentence
   to that effect. This is the condition under which I accept the tag (see issue 11 below).

## The verdict tag (issue 11)

Accepted. The reasons given in the D5 completion note are sound: the lab's tags describe the lead's joint hypothesis,
the second half fails robustly (upper bound 0.36 as preregistered, 0.42 without zero-output days, both below 0.50),
and the report's first line now quotes both halves, states both H1 outcomes, and says explicitly that the tag is not a
verdict on the catalogue. I no longer consider the tag misleading in the report. The residual risk is the tag read on
its own in an index, which edit 3 covers.

## Issue-by-issue

| # | Issue (from review.md) | Status | Evidence |
|---|---|---|---|
| 1 | `loaded` station-days with zero catalogue output in the denominator | **Resolved** | Variant A with the full 200-refit bootstrap: SD_p 0.0953 (0.0876-0.1048), Inconclusive; percentiles reproduce from `review/excl_zero/h1_bootstrap_draws.csv`; 14% of draws >= 0.10 (28 of 200); draws 0.0829-0.1129. Effects identical to my independent refit (max |Δu| 9e-7). Both verdicts in the verdict line, bullets, plain terms, H1 section, zero-output section, Limitations, tiles. Tails 79%/70%/11.2%/29.8% reproduce. H2 on the same effects 0.357 (0.284-0.419), Refuted. Station table: 6 new columns, original 17 columns byte-identical to d497663 (checked), `zero_pick_day_share` matches my computation for all 1,026 stations, 8 stations flagged. Figure 1 spans 0.1-1.0 with the overlay; the lowest station (BK.BABI, 0.131) is now shown. The reader-defect quotation is verbatim from seisscoped.org. The 26% / 3.5% band-mismatch claim reproduces (25.9% / 3.5%). |
| 2 | AGHQ synthetic-test claim not reproduced | **Resolved** | D4 corrected and explained (the 1.074/1.073 came from S = 1,500); both S = 400 and S = 1,500 runs stored in `review/aghq_test_output.txt` and reported; cross-check now described as ML-VB agreement. |
| 3 | H1 margin: quadrature value, share of draws below 0.10 | **Resolved** | 0.1045, 0.1040-0.1046 over seeds, 19%, draws 0.093-0.119: all in `review/misc.json` and in the H1 section. |
| 4 | Logit-normal sensitivity, direction | **Resolved** | Limitations: 0.115 (949), 0.103 (946, without zero-output days; reproduces as 0.1026), 0.098 (>= 100 picks), skew -0.49. |
| 5 | "Location predicts nothing / not a regional pattern" | **Resolved** | Rewritten; r = 0.25/0.32/0.34 for 1/5/10 neighbours (median 14 km) and plain-CV R² 0.10 / 0.33 / 0.39 reproduce from `review/misc.json`. |
| 6 | Regional boxes undefined | **Resolved** | `review_checks.BOXES` and the text give the boxes and station counts (67, 31, 106); shares 18/13/14/9% reproduce from `station_reliability.csv`. |
| 7 | False-pick proxy caveats | **Resolved** | Thresholds (59/44/24%), confidence quantiles, diurnal profile (1.20-1.27x at 07-13 h, 0.78-0.86x at 00-04 h; 57% vs 48% daytime), neighbours loaded (89% all five, 99% at least four), by network (74/59/53%), "unreferenced" defined, other networks named, validation reframed as a sensitivity check, 0.5 picks/s (0.485; 38.1 M after de-duplication). All reproduce from `review/falsepick_caveats.json` and `falsepick_hour_profile.csv`. |
| 8 | Reference heterogeneity (weight, onset) | **Resolved** | Weight/onset covariate fit: σ_u 1.009, SD_p 0.097 (observed mix) and 0.060 (best picks, typical 96%), log10 d +0.17; recall by weight and onset; mean weight 0.92/0.62 and impulsive share 88%/38% by distance reproduce (0.915/0.622, 87.6%/37.9%). "On impulsive arrivals alone, H1 does not hold" stated. |
| 9 | PhaseNet trained on NCEDC picks | **Resolved** | Stated with the by-period recall (89.9/89.4; 93.2/92.2, reproduce). The added SCSN-PhaseNet-seeding paragraph is a good catch; 92.6/92.6 reproduces (92.56/92.64). See edit 2 for the quotation marks. |
| 10 | Related work; `instance` weights | **Resolved** | Münchmeyer et al. 2022 and the Shimota, Tepp and Biondi preprint (ESS Open Archive, 15 Oct 2025, confirmed by search) cited; the 2025 archive now described as run with `instance` weights, which matches the QuakeScope page verbatim. |
| 11 | One-word tag "Refuted" | **Accepted** (see above) | Verdict line "Refuted on H2; H1 at its threshold" quotes both parts and scopes the tag. Edit 3 asks that the qualifier travel with the tag. |
| 12 | "HH n = 287" | **Resolved** | "H-band stations (n = 287: 278 HH broadband, 9 HN accelerometer)". |
| 13 | Noise covariate plausibility, windows, fallback | **Resolved** | Limitations list 33 above -6, 32 below -8.7, 495 of 927 below 180 windows, 14 below 60, fallback not implemented; `noise_windows` and `flag_noise_implausible` (65 stations) in the table. |
| 14 | S-recall denominator label | **Resolved** | Both rows labelled. |
| 15 | 9 dropped P picks | **Resolved** | Stated in "The data". |
| 16 | Duplicate partition rows | **Resolved** | Stated (0.6-5.7%). |
| 17 | Decomposition of misses | **Resolved** | Table of 45,856 misses: 14/15/6/22/43%, reproduce from `review/misses.json` (13.9/15.2/6.4/21.7/42.8%); no clock or format artefact stated. |
| 18 | NCEDC status A share | **Resolved** | 21% A, 2% I among M >= 1.5 events in the sampled months (`review/misc.json`). |
| 19 | AGHQ mode-convergence flag | **Resolved** | `modes_unconverged_at_optimum` recorded; 0 in all four rerun JSONs (checked). |
| 20 | Reproduce block | **Resolved** | `fetch.py months` and `fetch.py catalogues` added, plus `run_review_checks.sh`. |
| 21 | `synthetic_test.py` writes into results/ | **Resolved** | `A.TAB = Path(tempfile.mkdtemp())` added; `results/tables/h1_bootstrap_draws.csv` is the committed version. |

## Numbers recomputed in this pass

| Quantity | Report | Recomputed | Status |
|---|---:|---:|---|
| Variant A: SD_p, 95% CI, verdict | 0.095 (0.088-0.105), Inconclusive | 0.09526 (0.08755-0.10478) from the 200 draws; verdict by the rule | ok |
| Variant A: share of draws >= 0.10; range | 14%; 0.083-0.113 | 0.14 (28/200); 0.0829-0.1129 | ok |
| Variant A: σ_u; typical recall | 1.087; 93.6% | 1.0872; 93.63% | ok |
| Variant A: refits carrying the VB flag | "every VB fit" | 196 of 200 (4 converged) | **edit 1** |
| Variant A: picks / stations; pooled recall | 503,204 / 1,025; 92.2% | same; 92.16% | ok |
| Variant A tails: 10th, 5th, < 80%, < 90% | 79%, 70%, 11.2%, 29.8% | 79.2%, 70.0%, 11.2%, 29.8% | ok |
| Variant A: empirical SD of recall (946) | 0.103 | 0.1026 (json and table) | ok |
| Variant A: H2 R², linear, + secondary | 0.36 (0.28-0.42); 0.36; 0.40 (0.33-0.46) | 0.357 (0.284-0.419); 0.359; 0.400 (0.331-0.461) | ok |
| Variant A effects vs my independent refit | | max abs. difference 9e-7, correlation 1.000 | ok |
| Variant B: picks, pooled recall, SD_p | 501,463 / 1,026; 92.2%; 0.099 | same; 92.19%; 0.0990 | ok |
| Zero-pick station-days (sampled months); < 5 picks | 7.4%; 17% | 7.45%; 16.8% | ok |
| Picks on zero-pick days; recall by day count | 6,383; 65/82/89/95-96% | 6,383; 64.9/81.8/89.5/94.8-96.0% | ok |
| CI 2017-01-01 share of these picks | 1,169 | 1,169 | ok |
| Analyst band absent from bands read: zero-pick days vs others | 26% vs 3.5% | 25.9% vs 3.5% | ok |
| Bottom-decile overlap; EH in new bottom decile | 83 of 95; 85 of 95 | 83; 85 | ok |
| Regional shares without zero-output days | 18%, 13%, 13%; 9% elsewhere | 17.9, 12.9, 13.2; 8.7% | ok |
| Regional shares as preregistered; station counts | 18/13/14/9%; 67, 31, 106 | 17.9/12.9/14.2/8.6%; 67, 31, 106 | ok |
| Station table: original columns unchanged; new columns; flags | stated | 17 columns identical to d497663; 6 added; 8 zero-pick flags, 65 noise flags | ok |
| `zero_pick_day_share` column | | matches independent computation for all 1,026 stations | ok |
| Quadrature SD_p; MC seeds; draws < 0.10; range | 0.1045; 0.1040-0.1046; 19%; 0.093-0.119 | same | ok |
| Local spatial r (1/5/10 nn); median distance | 0.25/0.32/0.34; 14 km | 0.247/0.318/0.336; 14.0 | ok |
| Plain-CV R²: location; primary; primary + location | 0.10 (0.03-0.16); 0.33; 0.39 | 0.099 (0.034-0.155); 0.334; 0.394 | ok |
| Weight/onset model: σ_u; SD_p mix; SD_p best; typical best; log10 d | 1.01; 0.097; 0.060; 96%; +0.17 | 1.009; 0.0968; 0.0602; 96.1%; +0.169 | ok |
| Mean weight / impulsive share, <= 10 km vs 60-100 km | 0.92 / 0.62; 88% / 38% | 0.915 / 0.622; 87.6% / 37.9% | ok |
| Recall by source and weight; by onset | as listed | match `review/h1_weight_onset_covariates.json` | ok |
| Recall by period: NCEDC, SCEDC; SCEDC 2010-22 vs 2023-24 | 89.9/89.4; 93.2/92.2; 92.6/92.6 | same; 92.56/92.64 | ok |
| NCEDC M >= 1.5 events: A, I shares | 21%, 2% | 21.3%, 1.6% (`review/misc.json`) | ok |
| Misses: 45,856; shares | 14/15/6/22/43% | 13.9/15.2/6.4/21.7/42.8% | ok |
| False-pick: picks/s; shares at 0.5/0.7/0.9; daytime; neighbours; by network; confidence quantiles | 0.5 (38.1 M); 59/44/24%; 57 vs 48%; 89%, 99%; 74/59/53%; 0.65 (0.56-0.78) vs 0.93 | 0.485 (38,141,132); 59.3/44.1/24.4%; 56.6 vs 48.2/48.0%; 89.4%, 98.8%; 74.1/59.4/53.3%; 0.647 (0.561-0.779) vs 0.930 | ok |
| Diurnal profile 07-13 h and 00-04 h | 1.2-1.3x; about 0.8x | 1.199-1.271; 0.784-0.855 | ok |
| AGHQ test S = 400 and S = 1,500 | 1.060 -> 1.006/1.011; 1.074 -> 1.067/1.073 | as stored | ok |
| AGHQ reruns: unconverged modes | 0 in all four | 0, 0, 0, 0 | ok |
| Noise: > -6, < -8.7, < 180 windows, < 60 | 33, 32, 495 of 927, 14 | 33, 32, 495, 14 | ok |
| Figure 1 range and overlay; caption | 0.1-1.0; purple outline | as rendered; lowest bar at 0.13 | ok |
| `tiles.json` H1 note | includes 0.095 Inconclusive | yes | ok |
| `report.html` | mirrors report.md | key strings present ("Refuted on H2", "0.095 (0.088 to 0.105)", "83 of the 95", "85 of the new bottom 95") | ok |
| QuakeScope reader-defect quotation; `instance` weights | quoted | verbatim on seisscoped.org | ok |
| Shimota, Tepp and Biondi preprint; SCSN PhaseNet integration | cited | confirmed by search (15 Oct 2025; SSA abstract) | ok; edit 2 |
| D5 timing | decided before the bootstrap returned | D5 06:40; `review_zero.log` finished 10:33; commit 10:38 | ok |
