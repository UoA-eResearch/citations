# Independent adversarial review: SAE features, pretraining seeds against SAE seeds (pre-review draft, commit 4928313)

Reviewer: independent of the study agent. 13 October 2026. Scope: the brief in `review/prompt.md`. Everything I
recomputed is in `review/reviewer_checks/` (`recompute_stats.py`, `recompute_match.py`, `procrustes_check.py`, with
their `.json` outputs and logs). Nothing outside `review/` was modified; nothing was committed.

## Recommendation: publish with edits

The verdict stands. I re-derived the primary statistic, its interval and the verdict from the pair tables with my
own implementation (matrix form, independent of `analysis.py`), re-implemented the matching densely over the whole
held-out set for a within pair and a full-seed pair at each layer (independent hookpoint, sparsify's own encoder,
dense fp32 cross-moments), and checked every number in `report.md`, `tiles.json` and the figure captions against the
results files. All agree (table at the end). The edits needed are factual corrections to the McCann comparison and to
one piece of the D6 evidence, and several places where the prose claims more than the data support. None changes a
number or the verdict.

## What I verified and found sound

- **Timing.** `plan.md` and `NOTES_pre_plan.md` exist only in commit 3e34053 (16:13, 12 Oct), before the pilot.
  `match.py` was last changed in 585ca82 (16:22, 12 Oct), `analysis.py` in 1625f36 (16:20, 12 Oct), both before
  main training finished (05:38, 13 Oct) and before matching started (05:39). `figures.py` was committed at 05:42:26;
  the first pair score was written at 05:53 (first encode of 16 models + reference took until 05:48). `pairs.py` and
  `analysis.py` are byte-identical to their first commits. Post-hoc scripts (D5-D7) are labelled post hoc in
  `deviations.md`, each committed before its output (D7 by two seconds: script committed 06:43:13, CSV written
  06:43:15). The primary statistic was not touched by anything post hoc.
- **Hookpoint.** sparsify trains on `model.base_model.get_submodule("layers.L")` and unpacks `outputs[0]`
  (`trainer.py` lines 347-362); the model is loaded with `AutoModel` for `loss_fn="fvu"` (`__main__.py`), so
  `layers.L` is block L of `GPTNeoXModel`, exactly what `match.py` hooks. My check against
  `output_hidden_states` (hidden_states[L+1], 13 states) gives a maximum difference of 0.0 for both models at both
  layers. `exclude_tokens` is empty in `data/sae/*/config.json`, so SAE training included position 0; matching drops
  it, as the plan says. Position 0 is dropped before the Procrustes subset is kept and before the FVU totals.
- **SAE encode.** sparsify 1.3.3 `SparseCoder.encode` subtracts `b_dec`, then `fused_encoder` = ReLU(linear) then
  top-k; the trainer sets `b_dec` to the first batch's mean at step 0 (`trainer.py` line 416). `match.SAE.encode`
  does the same. My re-implementation used sparsify's own `load_from_disk().encode()` and reproduced the stored
  firing counts bit for bit (`fired_*_identical: true` for all SAEs checked).
- **FVU.** `err / (sxx - sx^2/n)` is the sum of squared residuals over the total sum of squares about the
  per-dimension mean, sparsify's definition over the whole of H instead of per batch. My recomputation with
  sparsify's own `decode` agrees to 1e-9.
- **Assessable rule and non-assessable candidates.** Latents with fewer than 20 firings on H are NaN in their own
  arrays and excluded from the candidate set of the other side (`r[:, ~ok_b] = -2`). My re-implementation (masking
  with -inf) reproduced the assessable counts and NaN patterns exactly, and the per-latent best correlations to
  float16 storage precision (max |Δr| 2.5e-4; 0-3 latents per side change side of 0.7 out of 25,000-32,000).
  The pair-row fractions agree to 1e-16.
- **Design.** No cross-model pair shares an SAE seed; 246 pairs per layer; the 45 full-seed model pairs each have
  exactly the combinations (0,1), (1,2), (2,0); within pairs are (0,1), (0,2), (1,2) on one model.
- **Statistic.** W, X, R, the dyadic bootstrap (same seed: identical interval; another seed and B = 20,000: 0.859-0.866
  again) and the verdict reproduce. The 10 per-model pooled ratios lie in 0.855-0.873; a plain t-interval on them is
  0.858-0.867. The interval is narrow because the 10 models agree, not because of a defect. The Limitations section
  states correctly what the interval excludes (SAE recipe, held-out text, layers); I would add that SAE-seed variation
  is averaged out (3 combinations per pair; SD of a model pair's three scores about 0.001-0.002) and that everything
  is conditional on one SAE training stream and one H.
- **Released arrays** (`results/match_arrays_L*.npz`) are identical to `data/match/L*/` (1,080 arrays compared).
- **Lineage.** `lineage_check.csv` reproduces the D6 numbers; the step-1000 and final-checkpoint evidence that the
  weight-seed runs started from the original's initialisation is sound (see issue 2 on the step-1 evidence).
  Issue EleutherAI/pythia#203 says what D6 says it says (opened 21 July 2026; the 3 October comment reports step 1
  bitwise identical to the original's, step-0 branches copied from seed4-6, same apparent first batch).
- **Novelty.** Searches (two extended web searches plus the cited papers) found nothing that decomposes SAE-feature
  reproducibility into SAE-seed and pretraining-seed parts, nothing using PolyPythias for SAEs, and nothing with an
  activation-correlation within-model baseline across pretraining seeds. McCann (2605.24577) is the nearest: nine
  Pythia-70m seeds, decoder cosine and reconstruction, no SAE-seed baseline. Váradi & Kmetty (2607.08499) is a
  method paper on BERT seeds. "Unstable Features, Reproducible Subspaces" (2606.12138) is SAE seeds on fixed models
  (GPT-2, Gemma-2, Pythia). Lan et al. (2410.06981) and SharedSAE (2609.04344) are different models/families. The
  novelty claim holds. Paulo & Belrose is ICLR 2026; the 42% figure is theirs for Pythia-160M (layer-6 MLP output,
  32k latents, 8B tokens, encoder-and-decoder cosine ≥ 0.7). The PolyPythias paper's table does label the variants
  "(only parameters)" and "(only data)", and the Hugging Face card says "only weight initialization varied (data
  order fixed)". The reference SAE's card says 8.2B Pile tokens; its `layers.4`/`layers.8` entries are residual
  SAEs (the card's text mentions MLP outputs, but the repo has both, and FVU 0.11 on the residual stream settles it).

## Issues

Severity: **F** factual error, **O** overstatement or unsupported inference, **D** disclosure/labelling, **m** minor.

1. **[F] The McCann "within 0.025 EV" claim is for his toy model, not Pythia-70m.** `report.md` §"Decoder geometry"
   (third bullet of the McCann summary, and "still 0.27 and 0.18 below the within-model ceiling, not within 0.025").
   McCann's text: "reconstruction recovers to within 0.025 EV of the within-seed self-baseline at every internal toy
   site and to 0.85–0.99 at every internal Pythia site." So for Pythia-70m he reports an absolute post-rotation EV of
   0.85-0.99, not a 0.025 gap. The comparison still goes the same way (this study's 0.59 and 0.70 are below 0.85),
   but the sentence as written misstates his claim. **Fix:** restate his Pythia claim as EV 0.85-0.99 after rotation
   and compare to 0.59/0.70; delete "not within 0.025". While there, add the settings that matter to the comparison
   and are missing from the caveats: his SAEs are ReLU + L1 trained and evaluated on 256 × 256 = 65k tokens, at
   expansion 8× and 32× of d = 512, at seven sites that are mostly layers 0-1 of 6 plus layer-5 resid_post; his 98% is
   Hungarian-matched decoder cosine > 0.5 at intermediate sites and drops to 62% at the final layer. Note also that
   this study's best-match criterion is more lenient than Hungarian, so finding 0.000 is a stronger non-replication,
   not a weaker one.

2. **[F] The step-1 evidence in D6 is vacuous: the step-1 checkpoints are the step-0 checkpoints.** `deviations.md`
   D6 ("Step 1 correlates 1.000"), `report.md` §D6 ("Their weights at step 1 correlate 1.000 with the original's
   step-0 weights, and 0.000 with their own step-0 checkpoints"). I compared the step-1 and step-0 `pytorch_model.bin`
   files on disk: for the original and for weight-seed1-3 and data-seed1, every one of the 172 tensors is bitwise
   identical to the original's step 0 (max |diff| 0; the LR warmup starts at 0, so step 1 applies no update; the
   original's own step 1 equals its step 0 too). So "step 1 correlates 1.000" says only that the released step-1
   file is the original's initialisation; it carries no information about training, and in particular nothing about
   "the same first batch" (the #203 comment's "step 1 bitwise identical" is uninformative for the same reason). The
   conclusion of D6 survives on the step-1000 (0.892-0.893 against the original's step 0, 0.000 against their own)
   and final-checkpoint (0.068-0.069) evidence, which I reproduce. **Fix:** say that the step-1 checkpoint equals
   step 0 and rest the claim on step 1000 and step 143000; attribute the first-batch claim to #203 only and mark it
   as not verified here.

3. **[D] The relabelling is a post-hoc correction, not the plan's contingency.** `deviations.md` D6 ("Plan section
   2's rule applies"), `report.md` headline and Deviations list ("relabelled per plan section 2"). The plan's
   contingency was conditioned on the step-0 comparison, which passed (D2). The relabelling was triggered by a
   pattern in the results (D5's raw decoder cosine across the lineage), then justified by external artifacts and
   #203. That is legitimate, changes no number, and both labellings are reported, but it is outcome-triggered and
   should be called post hoc rather than preregistered. **Fix:** "post-hoc relabelling, justified by step-1000 and
   final checkpoints and by #203; the plan's own check (step 0) had passed".

4. **[O] The decomposition reading overreaches.** `report.md` §D6 "What the decomposition shows", especially "The
   likely reading. Whatever perturbs a pretraining run, its SAE features end up about equally dissimilar. Training
   appears to amplify small differences until the runs are as far apart, feature-wise, as independent seeds", and
   "Near-replicates lose as much", "Sharing the initialisation is worth about one point".
   - The weight-seed runs' perturbation is unidentified. If #203's suggestion of a later data-order change is right,
     they are ordinary data-order variants and the study contains no small-perturbation pair at all; the
     "amplification" story then has no observation behind it. The step-1000 similarity (0.977-0.980, against 0.964
     for data-seed1) shows they had already diverged substantially by step 1000; no trajectory of amplification is
     measured.
   - The kinds are at the resolution limit: init 0.871 (0.862-0.879) contains the full point estimate 0.862; the
     model-pair scores overlap (layer 4: lineage pairs 0.419-0.426 inside full's 0.410-0.432; layer 8: lineage
     0.325-0.355 against full 0.329-0.347). "About one point" should be "at most about one point, not resolvable
     with 6-9 pairs".
   - "Near-replicate" is itself an interpretation; "same initialisation, perturbation unidentified" is what the
     artifacts show.
   **Fix:** replace "The likely reading" with what can be said: every lineage pair, whatever its actual perturbation,
   loses about as much matching as independent seeds; the study cannot tell whether that is because training
   amplifies any perturbation or because the weight-seed runs are data-order variants after their first batch.

5. **[F/D] "16 independently pretrained versions" is no longer accurate.** Subtitle of `report.md`; "In plain
   terms" ("trained several times from different random starting points"). After D6, seven of the 16 share the
   original's initialisation and three are of unidentified provenance. **Fix:** "16 pretraining runs: the original,
   nine independent seeds, and six variants of the original" (and credit PolyPythias / van der Wal et al. rather
   than "EleutherAI trained several times").

6. **[O] The plain-language verdict needs its scope.** "In plain terms": "The prediction is refuted" and "Most of
   the irreproducibility ... comes from the SAE". By the preregistered rule the verdict is right (lower bound 0.859
   ≥ 0.8), but the summary should say in one sentence that it holds at the preregistered criterion (r ≥ 0.7, layers 4
   and 8 pooled), that at r ≥ 0.9 the ratio is 0.725 and the prediction would have held, and that layer 8 alone is
   0.817, two points above the line. The headline bullets mention 0.725 but not that it flips the verdict. Also
   "That is the noise of SAE training itself" treats every within-model non-match as noise; some are alternative
   valid decompositions (feature splitting). "The irreproducibility of SAE training itself" is accurate.

7. **[O] The reference-SAE inference about the training budget is not supported as stated.** `report.md` §"SAE
   quality" ("So the shorter training budget does not appear to depress within-model reproducibility") and
   Limitations ("The reference SAE suggests the budget does not limit within-model matching"). The comparison is
   ours-vs-reference (0.476, 0.417) against ours-vs-ours (0.463, 0.416). That shows the 200M-token SAEs are no
   further from an 8.2B-token SAE than from each other. It does not measure what two 8.2B-token SAE seeds would
   share, which is the within-model ceiling that a larger budget could raise. **Fix:** state the weaker claim only.

8. **[F] The outlier-dimension caveat on the rotation is wrong in direction.** `report.md` §"Decoder geometry",
   Caveats: "The rotation was fitted on raw activations, where a few outlier dimensions carry 30-50% of the variance;
   a standardised fit might do better." I tested it (`procrustes_check.py`, same fit/eval split as `exploratory.py`,
   full pair p160m → seed5 and data pair p160m → data-seed1). For the full pair at layer 4: raw Procrustes map FVU
   0.71, per-dimension standardised Procrustes 0.88, Procrustes with the union of the two models' top-10 dimensions
   zeroed in the fit 1.13, least squares 0.48; B's SAE on the mapped stream: 0.53, 0.50, 2.03, (0.91). Layer 8:
   0.92, 0.96, 1.21, 0.53. The raw rotation fails equally on outlier and non-outlier dimensions (layer 4 FVU 0.71
   on the top-10 union, 0.70 on the rest; least squares 0.46 on the rest). About 44% (layer 4) and 33% (layer 8) of
   the Procrustes objective does come from the top-10 dimensions, but removing them does not help: the two residual
   streams are not well related by any linear map, orthogonal or not. **Fix:** replace the caveat with this finding
   (or cite the reviewer check). Two things worth adding from the same check: ||R − I||_F is 39.17 (layer 4) and
   39.13 (layer 8) for the full pair against the Haar prediction √(2·768) = 39.19, so McCann's Haar diagnostic
   replicates at 160M; for the shared-initialisation data pair it is 26.2 and 24.6, i.e. not a random rotation,
   which is a cleaner statement of the "shared initialisation leaves a trace" point than the top-10 lists. Also, the
   Procrustes solution here is over O(768) and has det −1 for the full pairs (a reflection); "orthogonal map" is the
   accurate term where the text says "rotation".

9. **[m] The outlier-dimension sentence is overstated.** `deviations.md` D6 and `report.md` §"Decoder geometry":
   "dimensions 393, 684, 411, 625 and 634 head the list at layer 4 in all seven". From `exploratory_outliers.csv`,
   data-seed2's layer-4 top 10 (684 512 212 634 290 593 29 625 429 692) contains neither 393 nor 411, and data-seed1
   has 411 and 625 only at ranks 8-9. Accurate: 684 and 634 are in all seven top-10 lists, 393 in six, 411 in five;
   each full seed's list is disjoint from the lineage's. **Fix:** wording.

10. **[D] Two small disclosure gaps.** (a) `figures.py` was edited after the results (06:41:57: D6 labels, two
    captions, the `tiles()` function) and committed in b7c45a6; the report says "the figure code [was] committed
    before any pair score existed", which is true of the first version only. Add a line to D6 or D7 saying the
    figure labels and captions were changed after the results (cosmetic; the plotted quantities are unchanged, which
    I confirmed by diff). (b) `lineage_check.py` was committed together with its outputs (138e1a5), which is fine for
    a post-hoc check but should be said. (c) D5 says the analysis ran at 06:09; the files are stamped 06:07:54. Trivial.

11. **[O/m] D7: the result is sound, the framing should be tightened.** `report.md` §"Latents that replicate within
    a model replicate across models". I recomputed the table from the released arrays (shares 46/15/39%, cross
    rates 5.8/41.6/84.7% at layer 4; 51/16/34% and 4.3/34.3/78.4% at layer 8) and stratified it by the source
    latent's firing-frequency tercile. The pattern holds inside every tercile (layer 4, "both": 0.86/0.89/0.79 for
    rarest/middle/most frequent; "neither": 0.08/0.06/0.04; layer 8: 0.84/0.84/0.64 and 0.07/0.04/0.02), so it is
    not a frequency-selection artefact, and regression to the mean would attenuate the contrast, not create it.
    What should be said: (i) the rule is a precision filter that keeps 34-39% of latents and discards the "one"
    group (15-16% of latents with a 34-42% cross rate); (ii) 85%/78% is pooled over latents and over nine partner
    models, not "four of every five runs" for each latent; (iii) "match" is best-match ≥ 0.7, many-to-one. Adding
    the tercile-stratified table would strengthen the section.

12. **[m] Paulo & Belrose comparison.** `report.md` §"SAE quality", "Prior work": their 42% is for the layer-6 MLP
    output with a one-to-one-style criterion (encoder and decoder cosine ≥ 0.7); this study's 42-46% is the
    residual stream with best activation correlation (many-to-one). The numerical agreement is across different
    metrics and sites; say so rather than "close to".

13. **[m] Frequency-tercile table mixes model sets.** `report.md` §"The most frequent latents": the within row pools
    all 16 models while the full row uses the 10 full seeds (disclosed in a footnote line). For a ratio table it
    would be cleaner to use the 10 full seeds in both rows; my recomputation reproduces the published numbers, so
    this is presentation only.

## Answers to the brief's specific questions

- **Post hoc presented as confirmatory?** No. D5-D7 are labelled exploratory in the report; the relabelling (D6) is
  the one place where the wording ("per plan section 2") suggests more preregistration than there was (issue 3).
- **Anything done but not disclosed?** Nothing substantive. The post-result edit of `figures.py` is disclosed in a
  commit message but not in `deviations.md` (issue 10). The pilot and dry-run outputs are accounted for.
- **Is "Refuted" right by the rule, with the right scope?** Yes by the rule (0.859 ≥ 0.8). The scope belongs in the
  plain summary (issue 6): r ≥ 0.7, layers 4 and 8 pooled; r ≥ 0.9 would read Supported; layer 8 alone is 0.817.
- **"The binding constraint is the SAE, not the language model"?** Supported at the preregistered criterion in the
  sense the report gives it: 54-58% of latents lack a match at r ≥ 0.7 in another SAE seed on the same model,
  against a further 4-8 points lost across runs, and D7 shows latents unstable across SAE seeds are almost never
  found across runs. It is conditional on this SAE recipe and budget (issue 7), on best-match ≥ 0.7, and it weakens
  at r ≥ 0.9 and at layer 8. The report's qualifiers in "What this means" cover this; the plain summary does not.
- **Is the interval honest; is its narrowness a problem?** Honest as stated in Limitations. Narrow because every
  model's own ratio is within 0.855-0.873; not a problem, but it is a model-sampling interval only.
- **Lineage claims and #203.** Verified, except that the step-1 evidence is vacuous (issue 2).
- **McCann.** His claims are misstated on one point (issue 1); the Procrustes implementation is sound (SVD of the
  centred cross-covariance, fit tokens held out from the evaluation in D5, decoder rows mapped by `W_dec @ R`); the
  comparison is fair once the setting differences are all stated (issue 1); outlier dominance is real but is not
  what limits the fit (issue 8).
- **D7 as selection or regression artefact?** Not by frequency (stratified check), and regression to the mean works
  against the reported contrast. The advice is sound as a precision filter (issue 11).
- **Numbers.** Every number in `report.md`, `tiles.json` and the figure captions matches the results files (table
  below). The figures show the published quantities with D6 labels.
- **Plain-language summary.** Accurate on the numbers; needs the scope sentence and the two wording changes in
  issues 5 and 6.

## Numbers recomputed (reviewer value against the report's)

| Quantity | Reviewer | Report / tables | Source of my value |
|---|---:|---:|---|
| R (pooled, r ≥ 0.7) | 0.8621 | 0.862 | `recompute_stats.py` |
| 95% interval (seed 20261012, B = 2000) | 0.8588-0.8658 | 0.859-0.866 | same |
| 95% interval (seed 1; seed 7 with B = 20000) | 0.8588-0.8658; 0.8588-0.8659 | - | same |
| t-interval on the 10 per-model pooled ratios | 0.858-0.867 | - | same |
| Verdict | Refuted | Refuted | rule |
| W₄, W₈ | 0.4629, 0.4160 | 0.463, 0.416 | same |
| X₄, X₈ | 0.4177, 0.3400 | 0.418, 0.340 | same |
| R₄ (interval) | 0.9023 (0.8980-0.9070) | 0.902 (0.898-0.907) | same |
| R₈ (interval) | 0.8173 (0.8129-0.8216) | 0.817 (0.813-0.822) | same |
| R at r ≥ 0.5 | 0.9293 (0.9271-0.9317), Refuted | 0.929 (0.927-0.932) | same |
| R at r ≥ 0.9 | 0.7253 (0.7193-0.7314), Supported | 0.725 (0.719-0.731) | same |
| Per-model ratio range, layer 4 / 8 | 0.888-0.915 / 0.810-0.827 | 0.888-0.915 / 0.810-0.827 | same |
| Separation, layer 4: cross / within | 0.410-0.432 / 0.453-0.474 | same | same |
| Separation, layer 8: cross / within | 0.329-0.347 / 0.404-0.421 | same | same |
| Decomposition init / data / both_dc / full | 0.871 (0.862-0.879) / 0.871 (0.867-0.875) / 0.869 (0.862-0.876) / 0.862 (0.859-0.864) | same | own bootstrap (4000 draws) |
| Decomposition by layer (init, data, both_dc, full) | L4 0.908, 0.911, 0.907, 0.897; L8 0.828, 0.827, 0.826, 0.822 | same | same |
| Lineage within mean | 0.4397 | 0.440 | same |
| D7 shares (neither/one/both), layer 4 / 8 | 46/15/39% / 51/16/34% | same | own implementation on released arrays |
| D7 cross rates, layer 4 / 8 | 5.8/41.6/84.7% / 4.3/34.3/78.4% | 6/42/85% / 4/34/78% | same |
| D7 "both" cross rate by tercile, layer 4 / 8 | 0.86/0.89/0.79 / 0.84/0.84/0.64 | not reported | same |
| Tercile match rates (within; full), layer 4 | 0.449/0.510/0.433; 0.431/0.481/0.342 | same | same |
| Tercile match rates (within; full), layer 8 | 0.448/0.448/0.349; 0.407/0.390/0.223 | same | same |
| Best-correlation modes within / full, layer 4 | 0.915 / 0.815 | "near 0.92 / 0.82" | same |
| Best-correlation modes within / full, layer 8 | 0.975 / 0.665 | "0.97 / 0.66" | same |
| Assessable range, layer 4 / 8 | 31,486-32,174 / 25,335-29,343 | "about 31,700" / 25,300-29,300 | `sae_quality_L*.csv` |
| Not-assessable share, layer 4 / 8 | 1.8-3.9% / 10.5-22.7% | 2-4% / 11-23% | same |
| Dead max | 0.191 (seed5, layer 8) | 19% | same |
| FVU median (range), layer 4 / 8 | 0.153 (0.122-0.159) / 0.133 (0.092-0.177) | same | same |
| Flagged SAEs | 0 | none | plan rule |
| Spearman score-FVU, L4 full/within; L8 full/within | 0.267 / 0.211; −0.133 / −0.291 | 0.27 / 0.21; −0.13 / −0.29 | same |
| Reference FVU, layer 4 / 8; match with ours | 0.110 / 0.114; 0.476 / 0.417 | same | `reference_L*.csv` |
| Decoder cosine ≥ 0.5, within / full raw / full rotated | L4 0.541 / 0.000 / 0.113; L8 0.561 / 0.000 / 0.143 | same | `pairs_L*.csv` |
| Reconstruction means over 45 full pairs (own, raw, orth; map orth, lin) | L4 0.146, 2.53, 0.413; 0.60, 0.40. L8 0.128, 2.04, 0.304; 0.90, 0.48 | same | `exploratory_reconstruction.csv` |
| Training wall time | 16:18:39 → 05:38:44 = 13.3 h; 48-52 min per model | 13.3 GPU-hours, about 50 min | `train_main.log` |
| Tiles | 0.862; 0.859-0.866; 46%·42%; 42%·34% | same | `tiles.json` |
| **Matching re-implementation (dense, full H)** | | | `recompute_match.py` |
| L4 within (pair 0): f0.7 ab/ba | 0.46661 / 0.46750 | 0.46661 / 0.46750 | max |Δr| 2.4e-4; 2 and 3 latents cross 0.7 |
| L4 full (pair 61, p160m s1 vs seed5 s2): f0.7 ab/ba | 0.41286 / 0.41923 | 0.41286 / 0.41923 | max |Δr| 2.5e-4; 1 and 1 |
| L8 within (pair 0): f0.7 ab/ba | 0.41694 / 0.41723 | 0.41694 / 0.41723 | max |Δr| 2.5e-4; 1 and 0 |
| L8 full (pair 61): f0.7 ab/ba | 0.31912 / 0.33838 | 0.31912 / 0.33838 | max |Δr| 2.4e-4; 2 and 3 |
| Assessable counts, all four pairs | identical | identical | NaN patterns identical |
| Firing counts (6 SAEs) | identical | identical | sparsify's own encoder |
| FVU (6 SAEs) | agree to 1e-9 | | sparsify's own decoder |
| Rotated decoder cosine ≥ 0.5, full pair L4 / L8 | 0.1083 / 0.1398 | 0.1082 / 0.1398 | own Procrustes fit |
| Hookpoint: sparsify hook vs hidden_states[L+1] | max diff 0.0 | | both models, both layers |
| ‖R − I‖_F full pair L4 / L8 (Haar √1536 = 39.19) | 39.17 / 39.13 | not reported | |
| ‖R − I‖_F data pair L4 / L8 | 26.2 / 24.6 | not reported | |
| Step-1 vs step-0 checkpoints (original, weight-seed1-3, data-seed1) | 172/172 tensors identical, max diff 0 | "step 1 correlates 1.000" | issue 2 |
