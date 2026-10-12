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
