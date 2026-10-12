# Preregistration — Does co-folding affinity know its target? A kinase-panel selectivity test of Boltz-2

Lead: `cheminformatics-drug-discovery-cofold-selectivity` (domain: cheminformatics / drug discovery).
Written 2026-10-13 NZDT, before any affinity prediction on the panel was run. Committed before outcomes.

## 1. The question

Boltz-2's affinity head is the headline open claim of 2025–2026: free-energy-perturbation-like accuracy at
a thousandth of the cost. Practitioners are starting to use it for *selectivity* triage — asking which of
many proteins a compound will hit. That use requires the model to respond to the protein, not merely to the
ligand. Published audits test the axis the authors emphasised (rank ligands against one target) and
agreement with physics-based free energies on a handful of systems. The axis that would demonstrate
target-specific learning — hold the ligand fixed, vary the protein, and compare with measured values — has
not been tested on a complete profiling panel.

### 1.1 Hypotheses, as preregistered here

The lead's hypothesis text states the panel as "442 inhibitors x 72 kinases". The data are the other way
round: Davis et al. 2011 profiled 72 inhibitors against 442 kinase assays, and DeepDTA packages 68 of those
inhibitors as a complete 68 x 442 Kd matrix. The hypothesis is restated on the correct axes, and the decoy
clause is revised (§1.2):

* **H1 (selectivity axis).** On a preregistered rectangle of the Davis panel, the median across ligands of
  the within-ligand across-kinase Spearman correlation between Boltz-2's predicted affinity and the
  measured pKd is **≤ 0.25**.
* **H2 (conventional axis).** The median across kinases of the within-kinase across-ligand Spearman is
  **≥ 0.4** — i.e. the model is not simply broken; it ranks ligands for a fixed target.
* **H3 (chemistry-free comparison).** H1's correlation is not better than a *target-promiscuity* baseline
  that uses no chemistry at all, and is statistically indistinguishable from the zero that a target-agnostic
  ligand-only predictor achieves by construction.
* **H4 (decoy proteins, secondary and descriptive).** Re-scoring the same ligands against unrelated
  non-kinase proteins moves the predicted affinity by less than the within-kinome spread of the same
  ligand's predictions.

### 1.2 Why the decoy clause is revised

The lead predicted "< 0.5 log units for ≥ 50% of ligands" when the protein is swapped for an unrelated one.
Two pieces of prior evidence conflict with that specific threshold: the lead's own `critic_note` reports a
ChemRxiv preprint ("Pose-to-Affinity Information Flow in Boltz-2", Aug 2026) finding > 100-fold shifts from
decoy crops and pocket substitutions, and Koch's benchmark (§2) reports Boltz-2 affinity values that fail to
*rank* the true target above decoys — which is a statement about ordering, not magnitude. I could not locate
the Pose-to-Affinity preprint in any search; its claim is therefore recorded as unverified. Rather than
preregister a threshold the literature already disputes, H4 is stated as a comparison of two spreads
(decoy-induced versus within-kinome) and reported descriptively. The verdict does not depend on it.

## 2. What is already known (novelty check, run 2026-10-13)

| Work | What it tests | Why it does not answer this question |
| --- | --- | --- |
| Boltz-2 preprint (bioRxiv 2025.06.14.659707) | FEP benchmarks, hit discovery, in-house ligand-only probes, synthetic cross-target decoys in training | No panel-complete within-ligand test against measured values |
| Koch, "A new benchmark … inter-protein scoring noise problem" (ChemRxiv 10.26434/chemrxiv-2025-sf3cs, v2 Jan 2026) | **Closest prior work.** Target identification on LIT-PCBA: can a model pick the true target for an active among decoy targets? Reports Boltz-2 cannot, by either affinity value or binary probability | Binary target identification among unrelated decoy pockets, not quantitative selectivity ranking inside one protein family against measured Kd; no profiling panel |
| MIRAGE (arXiv 2609.14491, Sep 2026) | Family-support axis: accuracy versus historical public support for the protein family, with ligand-only and family-disjoint controls; Boltz-2 included | Across-target *generalisation* to unsupported families; our panel is deliberately all high-support, inside the training distribution |
| BoltzOmics (Cell Rep. Phys. Sci. / PMC13401010, 2026) | Within-drug ranking across *variants of one protein* (CYP3A4), mean-centred; r = 0.30 / 0.19 / 0.66 for affinity sampling settings (200,5) / (300,7) / (400,9) | Mutants of a single target, two drugs; motivates our sampling arm (§5.4) |
| ChEMBL-derived benchmark (Chem-Bio Inform. J. 26, Mar 2026) | 15,465 post-ChEMBL-34 pairs, 356 targets; global and per-target metrics, mean MAE ≈ 0.9 | Pooled and per-target axes only |
| Reliability audit (arXiv 2603.05532 / JCTC 2026) | Boltz-2 versus physics-based free energies; affinity largely pose-independent | A few targets, within-target axis |
| DAVIS-complete (arXiv 2512.00708; Harvard Dataverse DVN/RTQGP1) | A curated, modification-aware DAVIS with 4,032 extra mutant/phospho pairs; benchmarks DTA models and *fine-tunes* the Boltz-2 affinity module on DAVIS | Supervised benchmark with train/test splits, not a zero-shot audit of the released model |
| KinConfBench (bioRxiv 2026.04.07.716788) and related | Kinase conformational-state accuracy of co-folding models | Structure, not affinity |

Novelty position: the selectivity axis — within-ligand, across-target, against a complete measured panel,
with chemistry-free and label-using baselines and a variance decomposition — is untested. Koch's result
makes a null *more likely a priori* and pre-empts the decoy-target framing, so the decoy arm is demoted to a
descriptive secondary and the study's contribution is the quantitative, in-distribution selectivity measure.

## 3. Data (all open, no credentials)

1. **Davis panel**, as packaged by DeepDTA (`github.com/hkmztrk/DeepDTA/tree/master/data/davis`):
   `Y` (68 ligands x 442 kinase assays, Kd in nM, complete), `proteins.txt` (sequences), `ligands_iso.txt`
   (PubChem CID → isomeric SMILES). Non-binders are reported at the 10 µM assay ceiling
   (Kd = 10000 nM, pKd = 5) — 69.6 % of all cells. pKd = 9 − log10(Kd[nM]).
2. **UniProt** reviewed human entries carrying a "Protein kinase" domain (496 rows, REST, retrieved
   2026-10-13) for sequence identity checks, domain boundaries and the Manning group implied by the
   SIMILARITY annotation.
3. **ChEMBL 37** (local copy at
   `runs/cheminformatics-drug-discovery-cliff-noise-ceiling/data/chembl_37/chembl_37_sqlite/chembl_37.db`)
   for the post-cutoff replication arm and the training-support proxy. Boltz-2's affinity data are ChEMBL
   v34 (March 2024) plus BindingDB, PubChem HTS, CeMM fragments and MIDAS.
4. **PubChem PUG REST** to re-fetch canonical SMILES for the 68 CIDs as a data-integrity check on the
   DeepDTA packaging.
5. **Boltz-2** code and weights (`pip install boltz`, MIT; weights auto-download), MSAs from the public
   ColabFold MSA server.

No raw data are redistributed beyond what their licences allow; derived per-pair predictions are released.

## 4. Model and settings (fixed before any panel run)

* `boltz predict` in affinity mode: YAML per complex with `properties: [{affinity: {binder: B}}]`, protein
  chain A = kinase-domain crop, chain B = ligand SMILES.
* Primary settings: defaults — `--recycling_steps 3 --diffusion_samples 1 --sampling_steps 200
  --diffusion_samples_affinity 5 --sampling_steps_affinity 200`, no `--affinity_mw_correction`,
  `--seed 20261013`, `--output_format mmcif`, one MSA per kinase computed once and reused.
* Primary read-out: `affinity_pred_value` = log10(IC50 in µM), lower = stronger. Converted to a
  pIC50-like scale `pred = 6 − affinity_pred_value` so that higher means stronger, matching pKd.
  `affinity_probability_binary` is the secondary read-out (the quantity intended for hit/decoy separation).
* Note recorded in advance: the molecular-weight correction cannot change any within-ligand statistic,
  because it is a constant for a fixed ligand. It can only affect across-ligand statistics.
* Reproducibility check before the panel: one complex predicted twice with the same seed must give
  identical affinity values; a seed change gives an idea of run-to-run spread. Recorded in
  `results/tables/repro.csv`.

### 4.1 Kinase input construction

Davis protein entries are full-length sequences (median 707 aa, up to 2549). Co-folding full-length
multi-domain kinases is neither affordable nor what the KINOMEscan competition assay reports, so the model
input is the **annotated protein-kinase domain plus a 20-residue flank each side**. Eligibility, in order:

1. the Davis name contains no "(" and does not end in "p" (wild-type, non-phosphorylated entry);
2. the Davis sequence matches a reviewed human UniProt sequence **exactly** (312 of 366 do);
3. that entry has **exactly one** annotated "Protein kinase" domain, of length 220–350 aa;
4. one Davis name per UniProt accession (more uncensored cells wins, then alphabetical).

303 kinases qualify. This is implemented in `code/panel.py`, written and committed before the run.

Every complex is one protein chain plus one ligand chain: no ATP, no cofactors, ions or waters, no
multimers. That is how Boltz-2's affinity head is trained and used, and it is uniform across the panel.

## 5. Design

### 5.1 Primary rectangle

K kinases x L ligands, every cell predicted. Kinases are allocated across the eight Manning groups by
largest remainder with a floor of one per non-empty group, and chosen inside a group by the number of
uncensored Davis cells (ties → alphabetical). Ligands must be RDKit-parseable, single-fragment, MW ≤ 700 and
have at least 8 uncensored cells among the chosen kinases; L are taken by uncensored count (ties → CID).

K = 32 and L = 32 (1024 complexes). Rationale: selecting on uncensored counts gives the rectangle a real
dynamic range — 72.9 % of its cells are uncensored, against 30.4 % of the whole panel, and the median ligand
has 22 uncensored cells out of 32 — so the within-ligand correlation measures quantitative ranking rather
than binder/non-binder detection. The cost is a sample of relatively promiscuous kinases and ligands;
§5.5 adds an arm that probes that bias, and the bias is stated as a limitation in the report.

### 5.2 Decoy-protein arm (secondary, descriptive)

Each of the L ligands against four non-kinase proteins of comparable size, as UniProt residue ranges:
carbonic anhydrase 2 (P00918, 1–260), trypsin-1 (P07477, 24–247, the mature chain), glutathione
S-transferase P (P09211, 1–210) and the N-terminal ATP-binding domain of HSP90-alpha (P07900, 9–236,
the geldanamycin/ADP site). HSP90 is included deliberately as a
*nucleotide-binding* non-kinase: if the affinity head is responding to generic ATP-pocket character rather
than kinase identity, HSP90 should score like a kinase. 4 x L complexes.

### 5.3 Post-cutoff replication arm (secondary)

Compounds whose **earliest** ChEMBL document year is ≥ 2025 (Boltz-2's affinity training used ChEMBL v34,
released March 2024) with ≥ 6 distinct eligible human kinases measured in documents dated ≥ 2025
(`standard_type` in Kd/Ki/IC50, `standard_units` = nM, `standard_relation` in = < >, single protein,
assay confidence ≥ 8). A scoping query on 2026-10-13 found 14 such compounds with 6–13 kinases each
(~120 pairs), which is the ceiling of what public post-cutoff profiling supports; the arm is therefore
small, ragged and explicitly underpowered for anything but a coarse comparison. Ligands additionally need
≥ 4 distinct measured values spanning ≥ 1 log unit. Mixed assay types are a disclosed limitation.

### 5.4 Affinity-sampling arm (secondary)

BoltzOmics reports that the within-drug correlation across protein variants rose from 0.30 to 0.66 when
affinity sampling went from (200 steps, 5 samples) to (400 steps, 9 samples), on two drugs. If low sampling
is what hides target sensitivity, the primary null would be an artefact of the default setting. A
preregistered sub-rectangle of 8 ligands x 12 kinases (96 complexes; the 8 ligands and 12 kinases with the
most uncensored cells in the primary rectangle) is re-run at `--sampling_steps_affinity 400
--diffusion_samples_affinity 9`, and the same within-ligand statistic is recomputed on that sub-rectangle at
both settings.

### 5.5 Promiscuity-bias probe (secondary, no extra GPU time beyond its own cells)

Eight further kinases — the *least* promiscuous eligible kinase in each Manning group, subject to ≥ 5
uncensored cells among the L ligands — are added as a ninth column block (8 x L complexes) and the primary
statistic is recomputed on the 40-kinase union. This tests whether the headline number is an artefact of
choosing well-measured, promiscuous kinases.

### 5.6 Training-support gradient (analysis only, no GPU)

For each panel kinase, count distinct compounds with Kd/Ki/IC50 in ChEMBL documents dated **before 2024**
as a proxy for training support, and regress the per-kinase within-kinase Spearman and the per-kinase
contribution to the within-ligand statistic on log support. A MIRAGE-style check on the selectivity axis.

### 5.7 Compute budget

Measured per-complex wall time on the idle A100 is recorded in `results/tables/timing.csv` before the panel
runs. Total complexes: 1024 (primary) + 128 (decoys) + 96 (sampling, re-run) + 256 (promiscuity probe)
+ ~120 (post-cutoff) ≈ 1624. The arms are run in the order 5.1, 5.2, 5.3, 5.4, 5.5; if the measured rate
implies more than 48 GPU-hours for the whole set, arms are dropped from the end of that list and the
deviation is logged. The primary rectangle is never reduced below 24 x 24 without logging a deviation.

### 5.8 Docking baseline (declared, not scheduled)

The lead proposes AutoDock Vina cross-docking as a physics comparator. It requires pocket definitions and
receptor preparation for 32 kinases and adds a day of plumbing for a comparator that is not needed by any
decision rule. It is **not** part of this preregistration; if it is added later it will appear as a logged
deviation and be reported as exploratory.

## 6. Estimands and decision rules

Write `p̂(i,j)` for the prediction (pIC50 scale) on ligand i, kinase j, and `y(i,j)` for measured pKd.

* **P1 (primary).** `median_i ρ_i`, where `ρ_i = Spearman(p̂(i,·), y(i,·))` over the K kinases, all cells,
  censored cells entering as ties at pKd = 5.
* **P2.** The same restricted to uncensored cells, for ligands with ≥ 5 uncensored cells.
* **P3.** `median_j Spearman(p̂(·,j), y(·,j))` over the L ligands — the conventional axis (H2).
* **P4.** Per-ligand top-1 hit rate and precision@3: does the model's top-ranked kinase for a ligand belong
  to the ligand's true top-3 measured kinases?
* **P5.** Two-way decomposition of the predictions: fit `p̂(i,j) = µ + a_i + b_j + e_ij` by least squares and
  report the variance shares of the ligand term, the kinase term and the interaction, with the same
  decomposition for `y`. A protein-blind predictor has a kinase-term share near zero.
* **P6 (decoys).** For each ligand, the gap between its mean predicted pIC50 over the 4 decoy proteins and
  its mean over the K kinases, alongside the within-kinome standard deviation of its predictions.

**Decision rule (verdict).** All intervals are 95 % percentile intervals from 2000 cluster bootstrap draws
over ligands (the primary clustering), with a kinase-resampling and a two-way (ligand x kinase) dyadic
bootstrap as sensitivity checks; seed 20261013.

* **Supported** if the upper bound of P1 < 0.25 **and** the point estimate of P3 ≥ 0.4.
* **Refuted** if the lower bound of P1 ≥ 0.25.
* **Inconclusive** if the interval for P1 straddles 0.25, or if P1's upper bound < 0.25 but P3 < 0.4 (the
  model is target-blind *and* ligand-blind, in which case the result says nothing specific about targets).
* **Protein-blind (a separate, stronger label)** if the interval for P1 includes 0.
* H3 is tested by a paired bootstrap on `P1(Boltz-2) − P1(baseline)` for each baseline in §7.

The verdict is read off these rules before any narrative is written, and the decisive numbers are quoted
from the stored tables.

## 7. Baselines

| Baseline | What it knows | Why it is here |
| --- | --- | --- |
| **B0 ligand-only** | one value per ligand | Its within-ligand ρ is 0 by construction: the null of H3 |
| **B1 target promiscuity** | measured mean pKd of each kinase over the other 67 Davis ligands (leave-the-ranked-ligand-out) | Uses *no chemistry*. If Boltz-2 does not beat it, the selectivity signal is "some kinases bind everything" |
| **B2 chemical neighbour** | measured pKd of the most ECFP4-similar other Davis ligand on the same kinase (leave-one-out) | A label-using transfer baseline: how much of the panel is predictable from chemistry alone |
| **B3 molecular weight** | ligand MW only | A trivial control for the across-ligand axis P3 |

B1 and B2 use the measured panel, so they are references for *how much signal is extractable*, not fair
competitors to a zero-shot model; Boltz-2's probable exposure to Davis-derived data through BindingDB is the
reason this comparison is still informative rather than unfair.

## 8. Power and minimum detectable effect

For a single ligand, the standard error of a Spearman correlation over K = 32 kinases is
≈ (1 − ρ²)/√(K − 1) ≈ 0.17 at ρ = 0.2. Ligand-level correlations share the same kinase columns, so they are
positively dependent; the cluster bootstrap over ligands is the inferential instrument and the analytic
figure below is a guide, not the reported interval. Treating the L = 32 ligand correlations as exchangeable,
the standard error of their median is ≈ 1.253 × 0.17/√32 ≈ 0.038, so:

* the MDE against the H1 threshold of 0.25 (one-sided, 80 % power) is ≈ 0.095 — i.e. a true median of 0.35
  or more would be detected as "not ≤ 0.25", and a true median of 0.15 or less as "≤ 0.25";
* P1 = 0 is distinguishable from P1 = 0.25 with a wide margin, so the "protein-blind" label is well powered;
* the inter-arm comparison in §5.4 (96 cells) has a standard error roughly 2.5 x larger and can only detect
  a change of ≈ 0.25 in the median correlation — enough for the BoltzOmics-sized effect (0.30 → 0.66), not
  for a subtle one. Stated as such.

If the realised ligand-level correlations are much more dependent than assumed, the bootstrap interval will
be wider than this and the verdict may land on Inconclusive; that is the honest outcome and no post-hoc
re-specification will be used to avoid it.

## 9. Threats to validity, declared in advance

1. **Censoring.** 10 µM ceilings become ties at pKd 5. P1 uses them (binder/non-binder discrimination is
   part of selectivity); P2 removes them. Both are reported, and the verdict follows P1.
2. **Panel selection bias.** Choosing well-measured kinases and ligands makes the rectangle more
   informative but more promiscuous than the kinome; §5.5 probes it.
3. **Kinase-domain crop.** Removing accessory domains could remove information the model needs. Uniform
   across kinases, disclosed; crop length and the model's own confidence scores are reported per complex,
   and the primary statistic is recomputed on the subset with high structural confidence.
4. **Training exposure.** Davis is almost certainly inside the training distribution, which makes a null
   result *harder* to explain away and a positive result uninterpretable as generalisation; §5.3 and §5.6
   bound it.
5. **Assay type.** Davis is Kd from a competition binding assay; Boltz-2's value head mixes Kd/Ki/IC50.
   This matters for calibration, not for rank correlation within a ligand.
6. **Mutant and phospho entries excluded**, so the panel is wild-type only; DAVIS-complete exists for the
   modification-aware question and is cited, not used.
7. **Failed predictions.** Any complex that fails (OOM, RDKit, MSA) is retried once; the pair is then
   dropped and the count reported. More than 5 % failures in any arm is reported in the abstract.

## 10. Process commitments

* Code is committed before the outcomes it produces.
* Every departure from this plan is appended to `deviations.md` with a timestamp from `date`, before or
  immediately after the change, including anything dropped for compute reasons.
* Intermediate per-complex outputs are written to disk as they are produced (`results/predictions.jsonl`),
  so a crash loses at most one complex.
* An independent adversarial review (Fable 5.1) runs on the pre-review draft; its prompt, review and any
  confirmation pass are committed under `review/`.
* Released with the report: the panel definition, per-pair predictions with confidence scores, the MSA
  manifest (hashes, not the alignments), all analysis code, and the decoy protocol so the same test can be
  rerun on the next co-folding release.
