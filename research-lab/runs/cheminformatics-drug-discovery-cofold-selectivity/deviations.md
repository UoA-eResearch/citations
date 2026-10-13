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
