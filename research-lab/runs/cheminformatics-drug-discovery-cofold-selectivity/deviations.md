# Deviations from the lead and from the plan

## D1 — 2026-10-13 09:43 NZDT — three departures from the lead, all before any panel prediction

Recorded with the preregistration, so that the plan's own text can be read as final.

1. **The panel axes are the other way round.** The lead says "442 inhibitors x 72 kinases". Davis et al.
   2011 profiled 72 inhibitors against 442 kinase assays; DeepDTA packages 68 of the inhibitors, giving a
   complete 68 x 442 Kd matrix. All estimands are defined on the correct axes: "within-ligand across-target"
   means one of 68 ligands ranked across kinases.
2. **The decoy hypothesis is restated.** The lead predicted a predicted-affinity shift of "< 0.5 log units
   for >= 50% of ligands" when the protein is swapped for an unrelated one. Prior work points the other way
   (Koch's LIT-PCBA target-identification benchmark; and the lead's own critic note cites a ChemRxiv
   preprint reporting >100-fold shifts, which I could not locate in any search and therefore record as
   unverified). The decoy arm is demoted to a descriptive secondary and restated as a comparison of the
   decoy-induced shift with the within-kinome spread of the same ligand's predictions. No verdict depends
   on it. Reasons in plan.md §1.2.
3. **Kinase inputs are the annotated kinase domain plus a 20-residue flank, not the full-length sequence.**
   Davis protein entries are full-length (median 707 aa, up to 2549); co-folding those is unaffordable at
   panel scale and is not what the KINOMEscan competition assay reports. Disclosed as a limitation
   (plan.md §9.3), uniform across kinases, and the crop is derived from UniProt domain annotation by a rule
   fixed in `code/panel.py` before any prediction.

Also set in the plan rather than the lead: AutoDock Vina cross-docking is declared out of scope (plan.md
§5.8), and two arms the lead did not ask for are added — an affinity-sampling arm (§5.4, prompted by
BoltzOmics' finding that within-drug correlation moves with sampling) and a training-support gradient
(§5.6, prompted by MIRAGE).

## D2 — 2026-10-13 09:57 NZDT — boltz needs the cuequivariance kernels installed

`pip install boltz` (2.2.1) does not install `cuequivariance_torch`, and the default code path imports it:
the first run died with `ModuleNotFoundError: No module named 'cuequivariance_torch'` before any
prediction. Installed `cuequivariance-torch`, `cuequivariance-ops-torch-cu13` and `cuequivariance-ops-cu13`
(all 0.12.0, the cu13 build matching torch 2.14.1+cu130) rather than passing `--no_kernels`, so the model
runs on its intended fused kernels. Recorded in `results/tables/env.json`. No effect on the design.

## D3 — 2026-10-13 10:01 NZDT — one analysis added beyond the plan, coded before any panel result

`code/geometry.py`: if the affinity head turns out not to track the measured selectivity profile, the plan
has no way to say whether it responds to the protein *at all*. The added analysis builds a kinase-by-kinase
distance matrix from the predictions (after removing each ligand's mean) and correlates it with the same
matrix built from the measurements and with pairwise sequence identity between the kinase-domain crops
(Biopython global alignment, BLOSUM62). A protein-blind head correlates with neither; a protein-aware but
mis-calibrated head correlates with sequence while missing the measurements. Exploratory, no verdict
depends on it, and the code was written and committed before any panel prediction was read.

Also recorded here: per-complex runtime measured at 19 s on the idle A100 (results/tables/timing.csv), so
the whole design — 1,597 complexes — fits in about 8.4 GPU-hours and no arm has to be dropped. The arms run
in three concurrent shards with seeds 20261013 + shard index, and the shard map is released
(results/tables/shards_*.csv) because the diffusion sampling makes each prediction stochastic: a value is
reproducible given the shard layout and seed, not given the pair alone.

## D4 — 2026-10-13 10:32 NZDT — one boltz process per arm, not three; the GPU is already saturated by one

The plan (§5.7, D3) said the arms would run in three concurrent shards. Measured on the decoy arm, three
processes take about 29 s per complex in aggregate while one process takes 19 s — a single boltz process
already holds the A100 at 94-100 % utilisation, so the extra processes only add contention and memory
pressure (49 GB across three). Every arm now runs as a single process with seed 20261013, which also makes
each prediction reproducible from the pair alone rather than from a shard layout.

The 22 decoy complexes computed under the three-shard layout were deleted rather than kept: a process that
sees every third input has a different RNG stream from one that sees all of them, so keeping them would
have meant two provenances in one arm for about seven minutes of saved compute. `results/predictions.jsonl`
was cleared with them; nothing had been analysed.

Revised budget: 1,597 complexes at 19 s is about 8.4 GPU-hours, still well inside the 48-hour cap, so no
arm is dropped.

## D5 — 2026-10-13 11:05 NZDT — two corrections to the lead's literature claims, found while the panel ran

1. The lead's `lit_against` says "the Boltz-2 authors already report ligand-only baselines ... so some
   ligand-bias quantification exists in-house". Reading the preprint (bioRxiv 2025.06.14.659707) I could
   find no ligand-only baseline and no within-ligand across-target evaluation; what is there is the
   *training* construction, where synthetic decoys are made by "shuffling binders identified in hit-to-lead
   screens across different targets, while mitigating low false negative rates by ensuring that each decoy
   has a Tanimoto similarity below 0.3 to all known binders associated with similar proteins". Training on
   cross-target decoys is not the same as measuring ligand bias in evaluation. Stated this way in the
   report.
2. MIRAGE (arXiv 2609.14491) does not report a within-ligand across-target statistic: it varies how much
   historical public support a protein family has and reports stratified correlations — for Boltz-2,
   r = -0.03 at support 1 rising to 0.585 at support 301+, on 373 matched PDBbind-derived complexes, with
   ligand-only and family-disjoint controls staying flat. Complementary to this study rather than
   overlapping: its axis is generalisation to unsupported families, ours is selectivity inside a
   well-supported family.

Neither changes the design. Both are recorded because the report's novelty claim rests on them.

## D6 — 2026-10-13 11:09 NZDT — D4 corrected: two concurrent processes are faster, and the budget is 2x what I said

D4 concluded that one boltz process per arm was fastest. That comparison was not like for like. Boltz runs
**two** passes over an arm — a structure pass and then an affinity pass — and I had compared the probe's
structure-pass rate (19 s per complex) against the three-shard *affinity*-pass rate (60 s per shard), which
made sharding look three times worse than it was.

Measured properly, on the panel arm with and without a second arm running beside it:

| configuration | per complex, each process | aggregate per complex |
| --- | --- | --- |
| one process (panel alone, structure pass) | 15.1 s | 15.1 s |
| two processes (panel + decoy, structure pass), first sample | 17.3 s and 21 s | 9.5 s |
| the same, a few minutes later | 23.6 s and 19.3 s | 10.6 s |
| three processes (decoy, structure pass) | ~28 s | ~9.4 s |

So two concurrent processes give a 1.4-1.6x aggregate speedup (two samples, taken minutes apart, differ by
that much) while the first arm slows by 15-55 %, and a third process adds nothing. The arms now run in two lanes: the panel in one, and decoy, promiscuity, sampling and
post-cutoff one after another in the other (`code/lane2.sh`). Each arm is still a single process with seed
20261013, so a prediction is still reproducible from its arm and pair alone.

Corrected budget: each complex costs about 34 s of single-process GPU time across the two passes, not 19 s,
so the 1,597 complexes are about 15 GPU-hours, or about 9-10 hours of wall clock in two lanes. Still inside
the 48-hour cap in plan.md §5.7, so no arm is dropped, but the figure in D4 and in
results/tables/timing.csv was wrong by a factor of two and is corrected there.

## D7 — 2026-10-14 01:07 NZDT — host crash mid-run; a silent collector bug; corrected checkpoint hashes

The VM stopped hard at about 22:56 NZDT on 13 October, the second such stop in two days (the first is
recorded in the lab's notes for 13 October). Nothing in the guest records a cause. The reboot killed both
boltz lanes and the MSA queue, and brought the owner's vLLM container back up on the GPU, which leaves
about 10 GB of the 80 GB free.

What survived, because every arm writes its outputs per complex as it goes:

| arm | structures | affinity read-outs | state after the crash |
| --- | --- | --- | --- |
| panel | 1024 / 1024 | 582 / 1024 | affinity pass resumed |
| decoy | 128 / 128 | 128 / 128 | complete |
| promiscuity | 256 / 256 | 256 / 256 | complete |
| sampling | 96 / 96 | 96 / 96 | complete |
| post-cutoff | 0 / 93 | 0 / 93 | 33 of 61 MSAs cached, fetching the rest |

Three things changed as a result, none of them in the design or the analysis:

1. **A silent bug in `collect()`, fixed.** It looked for pair directories in `out/<arm>/predictions` and
   in `out/<arm>` itself, but boltz writes them to `out/<arm>/boltz_results_inputs_<arm>/predictions/`.
   It therefore found nothing and printed "collected 0 predictions" for three finished arms without
   failing, which is how `logs/lane2.log` came to report `decoy collected, 0 rows`. It now walks the tree
   for `affinity_<pair_id>.json`. No prediction was lost: all 1062 finished read-outs collected on the
   first attempt after the fix. The lesson is the familiar one — a step that reports zero should be
   treated as a failure, not as a count.
2. **The resumed panel run shares the GPU with vLLM.** Stopping that container is the owner's call, not
   mine, so the affinity pass was restarted into the memory that was left, with
   `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` to reduce the chance of a fragmentation failure in
   the narrower space. Neither the allocator setting nor the sharing changes the computation: the model,
   its weights, the flags and the seed are the preregistered ones, and the 582 read-outs taken before the
   crash are kept rather than recomputed.
3. **`results/tables/env.json` is rebuilt by `code/env_record.py`.** The hand-made first version was
   wrong twice: the affinity checkpoint was still downloading when it was hashed, so its recorded size was
   a partial 508 MB against the true 2,062,139,170 B, and both digests were labelled sha256 but held only
   their first 32 characters. The conformer digest was right as far as it went; the affinity one described
   a file that was never used. Both are now full sha256 of the released checkpoints, and both kernels the
   run executed under are recorded.

## D8 — 2026-10-14 03:33 NZDT — an interval for the hit-rate difference, which the plan only point-estimated

plan.md §7 compares the model with each baseline on P1, by paired ligand bootstrap, and §6 lists the hit
rates (P4) as an estimand without a baseline comparison. That was an oversight, and the results make it
matter: P1 and the hit rates disagree about how much the model adds over the two non-trivial baselines.
On P1 the margin over target promiscuity is +0.058 with an interval spanning zero; on top-1 it is +0.375
with an interval that does not. A difference carrying that much of the conclusion cannot be reported as
two point estimates, so `analysis.py` gained `hit_vectors` and `paired_hit_difference` (the same paired
ligand bootstrap, same seed, same 2000 draws) and `assemble.py` stores a `hit_diff` per baseline.

`hit_rates` now derives its numbers from `hit_vectors` so that the point estimates and the bootstrapped
ones cannot drift apart. The 17 estimator checks still pass and P1-P5 are unchanged to three decimals.

This is an addition to the preregistered comparison, made after seeing P1, and it is reported as such:
the preregistered verdict stands on P1 alone.

## D9 — 2026-10-14 03:38 NZDT — two exploratory additions, and an environment change made mid-run

**The per-ligand floor.** plan.md §6 defines P1 as the median of the within-ligand correlations and says
nothing about their spread. On seeing that Boltz-2 and the promiscuity baseline have nearly the same median
but very different worst cases (+0.029 against -0.387, and 0 against 2 ligands below zero), the spread is
reported descriptively in the results and in F1. It is an observation made after seeing the data, it has no
interval and no test, and the verdict does not rest on it.

**The binary probability head.** Reporting `affinity_probability_binary` alongside the value head was
preregistered (§4), but only as a secondary read-out. That it ranks kinases consistently better than the
value head is an unanticipated finding, and the recommendation drawn from it is practical advice, not a
tested hypothesis.

**matplotlib installed mid-run.** Generating the figures needed matplotlib, which was not in the venv.
Installing it pulled numpy 2.5.4 over the pinned 1.26.4, which boltz forbids (`numpy<2.0`) — while the
post-cutoff arm was running in that same venv. The running process already held numpy in memory and was
unaffected (its outputs continued without a break, 23 structures at the time and 93 complete afterwards),
and numpy 1.26.4 was restored within two minutes along with a compatible matplotlib 3.9.4. No prediction
was made under the wrong numpy: the panel, decoy, promiscuity and sampling arms had all finished before the
install, and the post-cutoff arm's process never reloaded it. `results/tables/env.json` was rebuilt
afterwards and records what the analysis actually ran under. The lesson is the obvious one — do not install
into the environment of a running job; it was luck, not judgement, that this cost nothing.

## D10 — 2026-10-14 04:26 NZDT — a claim tested and withdrawn before review

The geometry arm reported three Mantel-style correlations as point estimates, and the first draft of the
report drew a comparison between two of them: that the model's kinase geometry tracks sequence distance
(0.338) more tightly than the measured geometry does (0.248), and therefore that it "leans on sequence
harder than the measurements justify".

Comparing two correlations needs more than two numbers, so `geometry.py` gained a permutation test for each
Mantel correlation (9,999 permutations of kinase labels, which preserves the dyadic dependence) and a
kinase bootstrap of the difference. Results:

* all three correlations are individually well outside their permutation nulls: pred vs measured 0.434
  (p = 0.0001), pred vs sequence 0.338 (p = 0.0003), measured vs sequence 0.248 (p = 0.0029);
* the difference the report claimed is +0.081 (−0.099, +0.284), positive in 80 % of draws.

The claim is withdrawn, and the withdrawal is stated in the report rather than quietly deleted. A second
check followed it: if the model over-merged close paralogues, the five most similar kinase pairs should be
compressed more than average. Their predicted/measured difference ratios are 0.33 to 0.79, median 0.57,
against 0.50 across all 496 pairs — no worse, if anything slightly better. The surviving finding is uniform
compression: the model halves the distance between any two kinases regardless of their similarity.

This was found by testing my own claim before sending the draft out, which is where it should have been
found; the first draft should not have made a comparison it had no interval for.

## D11 — 2026-10-14 05:16 NZDT — changes made in response to the independent adversarial review

The Fable 5.1 review of draft 04c7f25 returned **fix first** with 19 issues. It re-derived the panel from
the Davis release and UniProt independently (identical to the byte), reproduced every statistic to three
decimals, and confirmed the verdict. Four of its findings changed what the report claims, three of them in
the model's favour, and all four were verified here before being acted on.

**1. The central comparison was reported on one statistic and reverses on the other preregistered one.**
B1's and B2's P2 values were sitting in `results/tables/primary.json` and appeared nowhere in the report.
On P2 — uncensored cells only, preregistered in §6 — the model beats B1 by +0.171 (+0.065, +0.292) and B2
by +0.170 (+0.017, +0.346), both excluding zero, where on P1 neither does. Added to the report, and the
sentence claiming "censoring is not doing the work" is corrected: it is not doing the work for the model's
own score, and it is doing nearly all of it in the comparison.

**2. The mechanism given for the P1 result was wrong.** `analysis.py` gained the rank statistics the review
asked for — concordance among uncensored cells, NDCG, NDCG@3, NDCG@5, and the AUC for separating the
ceiling block from real binders — each with the same paired ligand bootstrap. The model separates from B1
on every one except the ceiling AUC (0.724 against 0.711). So P1's null result is not "the model adds
little in the censored tail"; it is "both are equally good there, and P1 gives that a quarter of its
weight". These statistics were chosen after seeing P1 and are reported as such; the verdict still rests on
P1 alone.

**3. The per-ligand floor claim does not survive the uncensored subset.** Model worst −0.094 with 2 of 32
ligands below zero, against B1's −0.101 with 2 of 32: indistinguishable. The "never below zero" framing was
an all-cells phenomenon, and the recommendation built on it ("that floor matters more than the median") is
withdrawn.

**4. The uniform-compression claim repeated the defect D10 was written about.** The table compared a ratio
of medians with medians of ratios; it is now one estimator throughout (0.52 all pairs, 0.57 for the five
near-identical ones). The dependence is now tested rather than asserted: Spearman(identity, ratio) = −0.068
with a dyadic permutation p = 0.41, and near-minus-rest = +0.051 (−0.223, +0.309). The honest statement is
that no dependence is detectable, not that compression is uniform. "Halves the distance between any two
kinases" is also wrong — per-pair ratios run 0.25 to 1.32, and 6 of 496 pairs are predicted further apart
than they measure.

**Also fixed.** `repro.csv` (plan §4) had never been produced and the omission was not logged; it has now
been run (`code/repro_check.py`): the same seed reproduces the affinity value bit for bit, and a changed
seed moves it 0.156 log units — which gives the sampling arm the reference it lacked, and strengthens it,
since the two sampling settings differ by less (0.128) than a seed change does. The sensitivity bootstraps
were running 500 draws against plan §6's 2,000 and now run 2,000 (intervals essentially unchanged:
kinase 0.367–0.578, dyadic 0.329–0.624). B0 and B3 hit rates were artefacts of the kinase column order and
are now reported as undefined, with `hit_vectors` returning nan for a predictor with no ranking and a test
asserting it under permuted column order. The crop gradient is quantified and its asymmetric direction
stated. The post-cutoff censored share now counts both bounds (8.6 %, not 3.2 %). The promiscuity
sub-rectangle reports n = 16 of 32 ligands, and the 40-kinase union's P3 = 0.379 — below H2's floor — is no
longer omitted. B1 is labelled as using the measured panel, with plan §7's caveat carried into the report.
The post-cutoff shortfall (14 compounds projected, 11 delivered; two filters in `postcutoff.py` that plan
§5.3 does not state) is disclosed, and "the preregistered budget exactly" corrected to 1,597 against ≈1,624
projected. "Seed 20261013 plus the shard index" is corrected — only the deleted shard runs used other
seeds. "Stopped twice by host crashes" is corrected to once, which is all that is evidenced. The plan's
literature table is carried into the report, Koch et al. is cited and reconciled with the decoy arm, the
H4 restatement is disclosed, and Nesso-1 is added. The preregistered HSP90 question is answered. Boltz's
documentation scoping `affinity_pred_value` away from inactives is now stated where the read-out is
defined, since it is the documented explanation for a finding the report had called unanticipated.

Not changed: the geometry section's "removing ligand means" is indeed a no-op for the distance it feeds
(the review measured max |centred − uncentred| = 0), and the wording is corrected rather than the code.

## D12 — 2026-10-14 05:27 NZDT — the confirmation pass: Boltz is not reproducible across run configurations

The reviewer's confirmation pass on the revised draft returned **publish with edits** with five remaining
items. Four were small (listed below). The fifth falsifies a claim made three times in this run's own
records, and nobody had checked it until the reviewer did the obvious thing and compared `repro.csv`
against the stored panel value for the same pair.

| the same complex, the same seed (20261013) | `affinity_pred_value` |
| --- | --- |
| run alone, twice (`repro.csv` a and b) | 0.9130484461784364 both times |
| run inside the 1,024-complex panel job | 0.8504559397697449 |

**0.063 log units apart.** Boltz is exactly deterministic given an identical run configuration, and not
deterministic across configurations: batching moves the answer, through RNG stream position or
non-deterministic kernels. The reviewer ruled out the obvious confounders — this pair's structure and
affinity outputs were both written during the first panel run, well before the crash, the resume, or the
memory-constrained period.

Three consequences, all recorded rather than quietly patched:

1. **"The pipeline is fully deterministic" was false** and is corrected in the report.
2. **D6's "a prediction is still reproducible from its arm and pair alone" is falsified.** It was the stated
   justification for deleting the 22 sharded decoy complexes in D4. The deletion was still the right call —
   one provenance per arm is good hygiene regardless — but it was justified on a premise that does not hold.
3. **The sampling arm's evidence is rebuilt on a better reference.** Comparing 0.128 (between settings) with
   0.156 (a seed change in a single-complex run) was not like for like. The right comparison is 0.128 against
   0.063, the movement with no seed change at all, purely from batching context. The conclusion is unchanged
   — the sampling settings do not matter much — and now rests on a floor measured the same way.

Readers are warned in the reproduction section that re-predicting one complex will not reproduce a released
value exactly, with 0.06 log units as the floor on any single-complex comparison.

**The other four items.** The sensitivity-bootstrap row in the report still showed the old 500-draw
intervals and now shows the 2,000-draw ones. Issue 12 of the review — the per-axis B1 variant switch — had
been fixed in code comments only and is now stated in the report with both numbers (B1 without the
leave-one-out adjustment scores 0.4256 against 0.3856, so the adjustment mildly flatters the model). Two
sentences surviving from the pre-revision draft were removed: the plain-language summary still carried the
"any two kinases ... near-twins or unrelated" wording that D11 retired, and the discussion still credited
the model's floor as an advantage after D11 had withdrawn it. The sixteen post-hoc comparisons now carry a
multiplicity statement, and the five whose lower bound is under +0.025 are no longer typeset as though they
were as solid as the three large ones.

The reviewer also conceded one point to me: it had written that a single kinase pair was predicted further
apart than measured, having read the maximum rather than counted. Six of the 496 pairs are.

## D13 — 2026-10-16 18:51 NZDT — post-publication correction: the report had no figures, and one misled

Found while building the next study's report. The published report.html carried none of its five figures:
the builder embeds an image only where report.md has a markdown image tag, and this report.md had none, so
F1-F5 existed on disk but never reached the page. They are now embedded where the text cites them.

Viewing F2 for the first time in context showed a worse problem. Its two lower heatmaps (measured and
predicted, each ligand's mean removed) used separate colour scales - measured +/-2.5, predicted +/-1.2 - so
they looked equally variable. That hid the report's own finding that the predictions are compressed to about
half the measured spread. Each row now shares one colour scale, set by the measured values, and the paler
predicted panel shows the compression directly. No number in the report changes.
