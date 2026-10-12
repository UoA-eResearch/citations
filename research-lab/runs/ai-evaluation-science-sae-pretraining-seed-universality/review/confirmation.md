# Confirmation pass: revised draft (commits 6f4102e and f8501c0) against the 13 review issues, plus D9

Reviewer: the same independent reviewer as `review/review.md`. 13 October 2026. Checked: `report.md`, `report.html`,
`deviations.md` (D8, D9), `code/review_fixes.py`, `code/token_identity.py`, `results/tables/review_*.csv`,
`token_identity.csv`, `token_identity_primary.json`, `token_purity_L*.npz`, the figures and captions. My checks are in
`review/reviewer_checks/d9_check.py` (+ `.json`, `.log`); the earlier scripts are unchanged. Nothing outside `review/`
was modified; nothing committed.

## Recommendation: publish with edits (small ones)

All 13 issues are addressed: 12 resolved, one (issue 4) resolved in the text with two loose ends. The D9 numbers
reproduce exactly and the check is sound; its report section is fair on the pooled result but states the layer-8
qualification more firmly than one purity cut supports (D9 point 1 below). Seven new points, all small; none
changes a number or the preregistered verdict. Unresolved or new: 2 loose ends from issue 4 + 7 new = 9 small items,
of which three matter for accuracy (4a, D9-1, D9-2) and the rest are consistency or wording.

## The 13 issues

| # | Status | Check |
|---|---|---|
| 1 McCann misstated | **resolved** | §Decoder geometry gives his Pythia-70m numbers (≥ 99% at intermediate sites, 62% final layer; EV 0.85-0.99 after the fit; the 0.025 gap attributed to the toy model; √(2d) distance) and his setting (ReLU + L1, 256 × 256 tokens, seven residual sites). Checked against the paper text. Leaving out 8×/32× is right: the paper states it in the toy section. Nit: the abstract's headline is 98%; "98-99%" would match abstract and body. |
| 2 Step-1 evidence | **resolved** | Withdrawn in §D6 and D8 item 2; the step-1 = step-0 fact is stated with its cause; the conclusion rests on step 1000 and the final checkpoints, which I reproduced. #203's further claims are attributed and marked unverified. D6's original text is kept as a log under a corrected heading, which is right. |
| 3 Relabelling framing | **resolved** | "The relabelling is post hoc. The plan's own check (step 0) had passed …" in §D6; headline and Deviations list agree. |
| 4 Decomposition overreach | **partly** | The "amplification" reading is replaced by the two-explanations statement; "near-replicate" is gone from the text; "at most about one point, not resolvable" is right. Loose ends: (a) "the model-pair scores of the lineage kinds lie inside the full-seed range at both layers" is true at layer 4 (lineage 0.419-0.426 inside full 0.410-0.432) and false at layer 8 (lineage 0.325-0.355 against full 0.329-0.347): say "overlap the full-seed range at both layers, inside it at layer 4". (b) Three figures and one caption still say "near-replicate": `figures.py` KINDS label in `scores.png`, `decoder.png`, `ratios.png`, the `ratios()` row label and `ratios.txt`. Relabel (e.g. "weight-seed (same init, perturbation unidentified)") and regenerate. |
| 5 "16 independently pretrained" | **resolved** | Subtitle and plain terms corrected. The two remaining "independently pretrained" refer to the 10 full seeds and are correct. |
| 6 Verdict scope | **resolved** | Headline "The scope" bullet; plain terms carry the criterion, the r ≥ 0.9 reversal and layer 8; "noise" became "irreproducibility". |
| 7 Reference-SAE inference | **resolved** | Weakened to what the comparison shows; Limitations updated. |
| 8 Outlier caveat / rotation | **resolved** | Caveat replaced by the test's numbers, which match `procrustes_check.json`. ‖R − I‖_F and det(R) for all 66 cross pairs per layer (`review_rotations.csv`): full pairs 39.12-39.28 (L4), 39.13-39.24 (L8) against 39.19; lineage 22.9-26.6; reflections in 28 and 25 of 45 full pairs (and 12 of 21 lineage pairs at each layer). My "det −1 for the full pairs" came from two pairs; "about half" is the right general statement. "Rotation" → "orthogonal map" in text, table headers, figure legend and caption. Nit: the CSV stores \|det\| ≈ 1.10 (1.095-1.112) because the SVD is float32; only the sign is meaningful. One line in the script docstring would prevent a reader from thinking R is not orthogonal. |
| 9 Outlier-dimension counts | **resolved** | `review_outliers.csv`: 684, 625, 634 in all seven lineage lists at layer 4, 393 in six, 411 in five, no full-seed overlap at layer 4; layer 8: 684 in seven, 393 and 429 in six. The agent's count including 625 is right; mine was incomplete (625 sits at ranks 8-9 in data-seed1/2). The "no overlap" claim is correctly scoped to layer 4 (at layer 8 five full seeds share 1-2 dimensions with the lineage union). |
| 10 Disclosure gaps | **resolved** | Report §Checks before any outcome and D8 disclose the post-result `figures.py` edits, the lineage_check timing and the 06:07/06:09 stamp. `review_fixes.py` committed (6ead963, 07:20:48) before its outputs (07:20:51-07:23:21); `token_identity.py` committed (b062b1b, 07:26:33) before it ran (purities 07:32-07:38). |
| 11 D7 framing | **resolved** | Precision-filter framing, kept share, pooled-rate definition, many-to-one note, the "one" group's cost. The tercile table matches `review_conditional_by_tercile.csv` and my stratification. |
| 12 Paulo & Belrose | **resolved** | Site and criterion stated; "loose comparison only". |
| 13 Frequency table | **resolved** | Table from `review_frequency_full_seeds.csv`; every cell and ratio recomputed and matches; 16-model figure kept with a caption note; "at most 0.006" is right (max 0.0059). |

## New numbers against the tables

| Report statement | Table / my check |
|---|---|
| Frequency table, L4 within 0.450 / 0.511 / 0.428; ratios 0.96 / 0.94 / 0.80 | 0.4500 / 0.5115 / 0.4275; 0.957 / 0.940 / 0.799 |
| Frequency table, L8 within 0.447 / 0.451 / 0.350; ratios 0.91 / 0.86 / 0.64 | 0.4472 / 0.4509 / 0.3503; 0.910 / 0.865 / 0.637 |
| D7 by tercile, 18 cells | match `review_conditional_by_tercile.csv` and my stratification |
| ‖R − I‖_F full 39.12-39.28; lineage 22.9-26.6; √1536 = 39.19 | 39.119-39.276 (L4), 39.133-39.244 (L8); 24.34-26.61 (L4), 22.89-24.88 (L8) |
| Reflections 28 and 25 of 45 | 28 (L4), 25 (L8) |
| Outlier counts | as in `review_outliers.csv` |
| SAE-seed SD median 0.0013 / 0.0017, max 0.004 | consistent with the per-pair spreads I saw; not independently recomputed |
| Standardised / dropped-outlier fits | `procrustes_check.json` (mine) |
| D9: token share 28.5% / 23.5% | `token_identity.csv`; my recomputation identical (max diff 6e-17) |
| D9: rates within 0.645, 0.391 / 0.594, 0.362; cross 0.606, 0.343 / 0.524, 0.283 | identical |
| D9: ratios 0.94, 0.88 / 0.88, 0.78 | 0.940, 0.878 / 0.882, 0.784 |
| D9: R without token sources 0.833 (0.829-0.837); L4 0.878 (0.872-0.884); L8 0.784 (0.779-0.790) | identical (own matrix-form bootstrap, same seed) |
| D9: purity of p160m L4 seed 0, recomputed from scratch (hidden_states + sparsify encoder) | max \|Δ\| 0.0; NaN pattern and firing counts identical; share ≥ 0.5 = 0.2845 both |

## D9: token-identity latents

**Code.** Sound. The token at kept position t is `tokens[:, 1:]`, which lines up with the activations after position
0 is dropped (my from-scratch recomputation of one SAE's purities, using `hidden_states[5]` and sparsify's encoder,
matches the stored array exactly). The key `latent × 65536 + token` is collision-free (vocabulary 50,304).
`scatter_reduce_("amax")` over the unique (latent, token) counts gives each latent's top-token count; purity = that
over firings; never-fired latents are NaN and fall outside both groups. The restricted statistic goes through
`analysis.primary_block(recomputed, col="f0.7_nontoken")` on the within and full pairs of the 10 full seeds, so the
preregistered bootstrap and rule are reused; I reproduce R, both bounds and the per-layer values to all printed digits.
Sources only are restricted; candidates are unchanged, and the report and D9 say so. The per-layer block added after
the pooled print is disclosed in D9 and the pooled numbers did not change.

**The reading.** The pooled statement is fair: token-identity latents (purity ≥ 0.5) are 24-28% of assessable latents,
match better everywhere, lose least across runs, and without them as sources R falls from 0.862 to 0.833, still
Refuted. The lead's risk note was right and the report now says so prominently (headline bullet, its own section,
What this means, Limitations, plain terms). Three points:

1. **The layer-8 "below the line" result depends on the purity cut, and the report does not show that.** At purity
   ≥ 0.8 (11% / 8% of latents are token-identity), the restricted ratios are pooled 0.855 (0.852-0.859), layer 4 0.897
   (0.892-0.902), layer 8 0.810 (0.805-0.814), Refuted at both layers (`d9_check.json`, `cut0.8`). So layer 8 is
   "at or just below the line depending on the cut", not simply "below the line". The section's own caveat ("the
   purity threshold of 0.5 is a choice") should be backed by this second cut, and the headline bullet and plain terms
   should say "at or just below" or give both cuts. The direction of the effect (1-3 points off the ratio at either
   cut) is robust; the layer-8 Supported/Refuted flip is not.
2. **"Context-dependent" overstates what purity < 0.5 means** (headline bullet, §D9 "Its context-dependent latents",
   What this means "context-dependent rather than token-identity"). A latent with purity 0.3 may fire on three tokens;
   it is "not token-identity", not "context-dependent". Likewise "just track one particular word" in plain terms
   should be "mostly track one word". Keep the operational label.
3. **"The pretraining run matters about as much as the hypothesis said"** (end of §D9) is right for layer 8 at cut
   0.5 (0.784 against "< 0.8") and wrong at cut 0.8 (0.810); with point 1 fixed it should read "about as much as the
   hypothesis said, at the 0.5 cut".

Otherwise the section is accurate, and the D9 note, the Deviations list and the Limitations entry are consistent with
the tables.

## New points (all small; none affects a number or the preregistered verdict)

1. **Layer-8 range sentence** (issue 4a): false at layer 8; reword to "overlap … inside it at layer 4".
2. **Figures and `ratios.txt` still say "near-replicate"** (issue 4b): three figures and one caption; the text no
   longer does. Relabel and regenerate; rebuild `report.html` (it carries one "near-replicate" from the caption).
3. **D9 cut sensitivity** (D9 point 1): add the purity ≥ 0.8 numbers and soften "below the line" to "at or just
   below, depending on the cut".
4. **"Context-dependent" / "just track"** (D9 point 2): use the operational label.
5. **Plain-terms length.** 300 words (302 tokens counting the two bullet dashes), at the limit; trim a few words,
   especially if point 3's wording is added.
6. **Standardised fit on the SAE metric.** §Decoder geometry cites only the map FVU for "does not help". On B's SAE
   reconstruction the standardised fit gives 0.50 against 0.53 (layer 4) and 0.38 against 0.36 (layer 8): no material
   change; half a sentence saying so pre-empts the objection.
7. (nits) `review_rotations.csv` \|det\| ≈ 1.10 is float32 round-off: note it. "At least 99%" against the abstract's
   "98%": write "98-99%". `report.html` status line now reads "revised after independent review" and contains the D9
   section; rebuild once more after the edits above.
