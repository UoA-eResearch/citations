# Review: ecology-biodiversity-globi-temporal-link-holdout

Reviewer: Fable (independent, adversarial), 2026-10-26. Checks and outputs are in `review/reviewer_checks/`
(`quick_stats.py`, `raw_extract.py`, `reresolution.py`, `reresolution2.py`, `recheck.py`, `post_scores.py`,
`genus_neighbour.py`, `misc_checks.py`, each with a `.json` of the same name).

## Verdict: fix first

The preregistered verdict (H1 Refuted) reproduces and survives every correction I could apply: my re-run gives
temporal AUROC 0.880 / 0.946 (study 0.880 / 0.948) and random 0.950 / 0.991; removing re-resolved names, removing the
citation-count leak and removing the dominant dataset each leave the temporal advantage well above half the random
one (lowest ρ ≈ 1.4). But two things in the verdict block are not publishable as written: 45% of the "future
records" come from one dataset whose species-level links are mostly *inferred by taxonomic expansion* (finding 1), and
the "degree-matched negatives" are not degree-matched (finding 2). Both need a fix and a rewrite before the title's
"grows, not shrinks" can stand.

## Findings

### 1. Major — 45% of the temporal positives are trophiCH links, ~70% of which are taxonomic inferences, not observations; undisclosed

- **Evidence.** `quick_stats.json` temporal_positives_namespaces: trophiCH introduces 164,003 of 213,620 trophic
  positives (77%) and 19,113 of 72,106 pollination positives; 183,892 of 411,702 positives overall (44.7%). The top
  three datasets (trophiCH, usda-fungus-host 71,121, iNaturalist 48,986) are 74% of all positives.
- trophiCH (Reji Chacko et al. 2025, *Scientific Data*; EnviDat) is a national metaweb for Switzerland. Paraphrasing
  its methods: about 30% of its species-level links are documented in a source; the rest are inferred, mainly by
  extending a record of a species feeding on a genus to every Swiss species in that genus, with family-level
  extension for generalists trimmed by habitat and stratum, guild nodes, and habitat co-occurrence filters. GloBI's
  indexing config for the dataset (`globalbioticinteractions/trophiCH`, `globi.json`) declares the `Inference` column
  but applies no filter, so GloBI v0.11 carries the inferred links (2,460,745 records). The inferred links carry
  their original source's citation, so they cannot be separated in GloBI's export (`post_scores.json`
  trophiCH_citation_split: all but 4 of the 183,892 carry a non-metaweb citation). 413,555 trophiCH records cite
  GloBI's own data products: 51,465 positives (12.5% of all) are, at one remove, derived from GloBI itself.
- **Why it matters.** The study's headline is that a taxonomy-aware model beats effort on "future records". For
  nearly half of those records the ground truth was itself produced by a taxonomic-expansion rule, so the test is
  partly "does our taxonomic model agree with their taxonomic inference", not "does it predict observed
  interactions". That is exactly the dataset-level artefact the brief asked about. The report does not mention
  trophiCH or inference anywhere.
- **Quantified.** `post_scores.json`: A_temporal (taxgb − effort, pooled percentile ranks, my re-run) is 0.0662 on all
  positives, 0.0585 without trophiCH (227,810 positives; effort 0.907, taxgb 0.966), 0.0572 without trophiCH and
  usda-fungus-host; per class without trophiCH: trophic 0.0765 (vs 0.080), pollination 0.025 (vs 0.026), host
  0.064 (vs 0.066). Per dataset A ranges from 0.013 (mangal) to 0.128 (NHM interactions bank). Against A_random =
  0.040, ρ without trophiCH is about 1.46 (bootstrap interval: see the addendum at the end). So H1 stays Refuted, but
  "grows" rests on the inferred dataset: without it, ρ's interval is what decides between "grows" and "holds".
- A mechanical check (`genus_neighbour.json`) shows trophiCH positives are *not* disproportionately genus-neighbours
  of v0.6 edges (16.8% have s already linked to t's genus or vice versa, against 28–81% for other trophic datasets
  and 65% for random-holdout positives), so the inflation is not a simple copy of GloBI edges expanded by genus; the
  concern is conceptual (inferred truth) and compositional, not a leak of G6 into the labels.
- **Fix.** (a) Report trophiCH's nature and share in the verdict block and plain terms. (b) Report the
  leave-one-dataset-out table and the without-trophiCH ρ with its cluster-bootstrap interval as the robustness result
  the verdict leans on. (c) Retitle: "holds" unless the without-trophiCH interval for ρ excludes 1. (d) Add the GloBI
  self-citation share (51,465 positives) to the circularity caveat.

### 2. Major — the degree-matched negatives are not degree-matched; the "grows when degree is matched" claim is unsupported as stated

- **Evidence.** `code/model.py:44-57`. The sampler draws 20·n uniform candidates and then fills each positive decile
  from that pool. Line 55, `rng.choice(len(pool), min(len(pool), need), replace=len(pool) < need)`, draws only
  `len(pool)` items when the pool is short — and draws them *with replacement*, so it returns fewer than `need`
  negatives and duplicates among them. Uniform candidates are rare in the top degree deciles, so those deciles are
  starved. Reproduced with the study's function on the study's positives (`quick_stats.json`
  churn_and_sampler.matched_sampler):
  - host: 921,408 negatives returned of 1,259,760 needed (860,377 distinct); the top three positive deciles get
    5.1%, 2.2% and 0.8% of negatives against 10% each of positives; mean log degree product 4.17 for negatives vs
    5.20 for positives;
  - pollination: 646,981 of 721,060; top two deciles 7.6% and 3.3%;
  - trophic: 2,116,511 of 2,136,200, nearly matched (top decile 9.2%).
- **Consequence.** Effort's 0.568 (report, verdict bullet "It grows with degree-matched negatives"; F2 title,
  `code/figures.py:65`) still contains degree signal, and so does taxgb's 0.850; A = 0.28 on these negatives is not
  the degree-free advantage the sentence claims. The random-holdout "matched" effort AUROC of 0.682 says the same. G5
  row 18 labels the sentence Supported on the strength of numbers from a broken sampler.
- **Fix.** Sample each decile until filled (rejection sampling within strata, or draw candidates proportional to the
  positives' degree distribution), without replacement, report the achieved negative decile shares, rerun secondary
  2, and reword the bullet and the F2 title to whatever the corrected numbers support.

### 3. Moderate (G1) — citation counts leak the hidden and inner-label edges into the random holdout; measured effect nil

- **Evidence.** `code/build.py:72-78` builds `species_v0.6.n_citations` over all v0.6 records; `code/model.py:67`
  uses it unchanged for the 90% training graph and for the inner 81% graph (`fit_models`, line 116), so every
  hidden positive's citation is counted in its endpoints' effort feature. Measured on the study's own split logic
  (`recheck.json` citation_leak_size): the summed log-citation feature of random-holdout positives is inflated for
  70% of host positives (mean +0.20) and 77% of pollination positives (+0.12), against 20–37% of negatives
  (+0.03–0.04).
- **Effect.** Recomputing citations from the training records only (hidden and label edges removed), same split and
  models: A_random 0.0409 → 0.0407; effort 0.9501 → 0.9497; ρ 1.62 → 1.63. Degree already carries the signal.
- **Fix.** Record it as a D-entry with these numbers (the plan has no leakage-audit section, G1), and note in the
  report that the random-holdout effort baseline is marginally optimistic.

### 4. Minor (G1, checked and cleared) — name re-resolution does not manufacture the positives; the turnover caveat can be made quantitative

- **Evidence.** For every v0.11 record behind a positive I asked whether v0.6 had a record with the same verbatim
  source and target names in the class, or the same resolved taxon IDs (`reresolution2.json`; the stricter key with
  namespace and citation is in `reresolution.json`). 1.12% of positives have any such v0.6 record behind them
  (0.99% by verbatim name, 0.15% by ID); 0.96% are made only of such records; in 2,077 of 2,077 verbatim matches the
  v0.6 resolution was the genus (e.g. verbatim "Cytospora kunzei" resolved to *Cytospora* in v0.6 and to the species
  in v0.11), i.e. newly resolved to species level rather than renamed. Existing-dataset positives: 3.4%; new-dataset:
  0.26%. Dropping all of them changes A_temporal from 0.0662 to 0.0658 (`recheck.json`).
- The 26–42% turnover is mostly pairs *leaving*: mycoportal alone loses 48,077 host pairs; 13,115 v0.6 pairs are in
  v0.11's refuted set (38,229 pairs, 523,687 rows from the EOL refuted list, `misc_checks.json`); 45,560 of 210,384
  v0.6 species names are absent from v0.11; and interaction types were remapped (v0.6 has 13.26M `hasHost` records,
  v0.11 7.13M, while v0.11 has 2.34M `hasArbuscularMycorrhizalHost` and 1.84M `symbiontOf` records that the class
  mapping excludes; `hemiparasiteOf` falls from 96,440 to under 3,000). None of this creates positives.
- **Fix.** Replace "some new pairs may be re-resolved old ones" with the measured 1.1% and the A without them; say
  the turnover is dominated by pairs removed, refuted or re-typed.

### 5. Minor — the temporal holdout is three datasets; the interval should be read that way

- 74% of positives come from three datasets (finding 1). The cluster bootstrap over datasets is the right tool and is
  implemented correctly (`code/model.py:208-218`; weighted AUROC equals sklearn's to 1e-15, `quick_stats.json`
  auroc_check), but with one cluster holding 45% of positives the interval is close to a three-point distribution
  (trophiCH drawn 0, 1 or 2+ times). Report the number of clusters and the share of the largest, and the per-dataset
  A table.

### 6. Minor — two small design points, both checked, both negligible

- Inner-split negatives are drawn from non-edges of the *training* graph (`model.py:118`), so evaluation positives
  can be labelled negative in training: expected tens of pairs in the random holdout and a few hundred in the
  temporal one, out of 0.4–0.9M training negatives. Conservative and negligible.
- Temporal negatives exclude v0.11 edges (`model.py:161`), as the plan says; this uses future information to clean
  the negatives. For uniform negatives the excluded mass is ~0.02–0.04% of the pair space; immaterial, but it is not
  what a truly prospective user could do. One sentence in the limits.

### 7. Gates

- **G5** passes mechanically and the edits were honest, but row 18 (degree-matched) is backed by a broken sampler
  (finding 2) and row 1 (title, "grows") depends on the inferred dataset (finding 1). Re-run after the fixes.
- **G6** passes; L1–L8 spot-checked (L3's condition that the study's RDPG lacks phylogenetic transfer is correct;
  L5's limitation is stated). Add a ledger row for trophiCH (dataset, its inference method, GloBI's config).
- **G1**: no leakage-audit section in `plan.md` (the study predates the gate); finding 3 is a leak it would have
  caught. Add the section retrospectively with findings 3, 4 and 6.
- **G2 missing**: no `coverage.json`. The species-name, self-loop and refuted filters drop 19.8% of v0.6 study-type
  rows (17,050,034 → 13,668,469) and 48.1% of v0.11's (15,678,150 → 8,142,528; `raw_v*_counts.json`,
  `logs/build_*.log`) with no accounting of which filter, and the planned `graph_summary.json` and
  `eval_sets_summary.json` (plan section 7; `model.py:4` still claims to write the latter) were never written.
- **G3 missing**: no `results/plausibility.md`; the turnover table at the pre-review gate covers one number.
- **G4, G7**: not applicable (no pipeline validation metric, no agent labelling).

### 8. Report checks

- Every number in the report matches `primary.json`, `per_class.csv` and `turnover.json` (verdict block, both tables,
  growth, eligibility 26–36%, turnover, captions). The pooled AUROC equals the positive-weighted mean of the
  per-class AUROCs, so the percentile-rank pooling is a legitimate summary (`model.py:187-194`).
- Graph construction is sound: type mapping and direction are right for all 20 types (`build.py:18-22`), refuted
  pairs are oriented the same way before removal, and the DuckDB options lose nothing — rows read equal the line
  counts minus the header for both files (19,981,541 and 24,453,954) with `store_rejects` reporting 0 rejects.
- Plan and code preceded the data (plan 01:48, code 02:06, edges 03:57 and 07:04, `primary.json` 08:32 NZDT on
  2026-10-24; `build.py` and `model.py` unchanged since commit 0aac991).
- Presentation: F2's legend covers the first bar group; move it.
- Title and plain terms: fair on the preregistered question (Refuted is robust); unfair by omission on what the
  "future records" are (finding 1) and overstated on degree matching (finding 2). "Grows" should wait for the
  without-trophiCH interval.

## Addendum: cluster-bootstrap interval for A_temporal without trophiCH

`post_scores.json` (B = 500, clusters = introducing dataset, negatives iid, same weighted-AUROC estimator as
`model.auroc`, on my re-run's scores):

- all positives: A_temporal 0.0662, 95% interval 0.054 to 0.073 (266 clusters), matching the study's 0.053 to 0.075;
- without trophiCH: A_temporal 0.0585, 95% interval 0.050 to 0.066 (265 clusters).

Against the study's A_random of 0.040 (0.029 to 0.054), ρ without trophiCH is about 1.46, and combining the two
intervals bound-by-bound gives roughly 0.92 to 2.3. So:

- **H1 Refuted is robust**: every bootstrap draw, with or without trophiCH, has ρ > 0.5 (the worst corner, 0.050 /
  0.054, is 0.92).
- **"Grows" is not established without trophiCH**: the lower bound falls below 1. The title and verdict should say
  the advantage *holds* out of time, and may grow, with the growth resting on the inferred-link dataset.
