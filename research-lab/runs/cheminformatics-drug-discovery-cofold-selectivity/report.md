# Does co-folding affinity know its target?

*A kinase-panel selectivity test of Boltz-2: hold each ligand fixed, vary the protein, and compare with
measured binding constants.*

> Draft in progress — the panel is still running. Sections marked TBD are filled from the stored tables
> once every arm has finished.

## In plain terms

TBD

## What was asked

Boltz-2 predicts a binding affinity for a protein–ligand pair at a thousandth of the cost of a
free-energy calculation, and its affinity head is the headline open claim of 2025–2026. People are
beginning to use it for *selectivity*: given a compound, which of many proteins will it hit? That use
needs the model to respond to the protein, not only to the chemistry of the ligand.

The published audits test the axis the authors emphasised — rank a series of ligands against one target —
and agreement with physics-based free energies on a handful of systems. This study tests the other axis.
On a complete kinase profiling panel (Davis et al. 2011, as packaged by DeepDTA: 68 inhibitors against 442
kinase assays, every cell measured), it holds each ligand fixed and asks the model to rank kinases, then
compares that ranking with the measured dissociation constants.

The preregistered hypothesis, in plan.md, was that the model fails this test: median within-ligand
across-kinase Spearman ≤ 0.25, while still clearing 0.4 on the conventional axis.

## How it was done

**The panel.** A 32 × 32 rectangle of the Davis panel, every cell predicted. Kinases had to be wild-type,
non-phosphorylated Davis entries whose sequence matches a reviewed human UniProt entry exactly, with
exactly one annotated protein-kinase domain of 220–350 residues; 303 of 442 qualified, and 32 were taken by
largest-remainder allocation across the eight Manning groups, choosing inside a group by the number of
uncensored Davis cells. The model input is that kinase domain plus a 20-residue flank — full-length
multi-domain kinases are neither affordable at panel scale nor what the competition binding assay reports.
Ligands had to be RDKit-parseable, single-fragment, MW ≤ 700 and have at least 8 uncensored cells among the
chosen kinases; the 32 taken are recognisable kinase drugs (pazopanib, crizotinib, gefitinib, erlotinib,
sorafenib, sunitinib, bosutinib, axitinib, neratinib, vandetanib, fedratinib, staurosporine and the rest).

Selecting on uncensored counts matters: 69.6 % of the whole Davis matrix sits at the 10 µM assay ceiling,
but only 27.1 % of this rectangle does, and the median ligand has 22 uncensored cells out of 32. The
selectivity question is therefore asked where there is a real dynamic range to rank. The cost is a sample
of relatively promiscuous kinases and ligands, which a separate arm probes.

**The model.** Boltz-2 2.2.1 with its released weights, in affinity mode, one protein chain plus one ligand
chain, one MSA per protein from the public ColabFold server, reused across every complex that protein
appears in. Settings are the defaults, passed explicitly: 3 recycling steps, 200 sampling steps, 1
diffusion sample, 5 affinity diffusion samples, 200 affinity sampling steps, no molecular-weight
correction, seed 20261013 plus the shard index. The read-out is `affinity_pred_value`, which is
log10(IC50 in µM), converted to a pIC50-like scale (6 − value) so that higher means stronger, matching pKd;
`affinity_probability_binary` is reported alongside. Note that the molecular-weight correction cannot
change any within-ligand statistic, because for a fixed ligand it is a constant.

**What the measurements say before the model is consulted.** Three numbers fix the scale, and all three
come from Davis alone:

| Reference, from measured data only | Selectivity axis (within-ligand, 32 kinases) | Conventional axis (within-kinase, 32 ligands) | Top-1 hit |
| --- | --- | --- | --- |
| Ligand-only (one value per ligand) | 0.000 by construction | **0.489** | 0.062 |
| Target promiscuity, no chemistry at all | **0.386** (0.310–0.522) | 0.000 by construction | 0.188 |
| Nearest chemical neighbour (uses labels) | 0.394 (0.268–0.503) | 0.264 | 0.312 |
| Molecular weight only | 0.000 | 0.061 | 0.062 |
| Chance | — | — | 0.094 |

Two consequences for reading the hypothesis. The threshold it set on the selectivity axis, 0.25, is *below*
what a baseline with no chemistry in it achieves (0.386): knowing only which kinases bind most compounds
gets you a correlation of 0.39 with a given compound's real selectivity profile. And the floor it set on
the conventional axis, 0.4, is below what a baseline with no protein in it achieves (0.489): ranking
ligands within a target is mostly ranking ligands by overall potency. The verdict below follows the
preregistered rules, but the baselines are the more informative comparison, which is why they were
preregistered too.

The measured panel's variance splits 25.5 % to the ligand, 14.6 % to the kinase and 59.9 % to the
ligand-by-kinase interaction — so most of what a selectivity predictor has to get right is the interaction,
not either main effect.

## Results

TBD

## What this does and does not show

TBD — the outcome-specific paragraph goes here once the arms are in. The limitations below were written
from the design, before the predictions were analysed.

**It tests one axis, not the model.** The question is whether a fixed ligand's predicted ranking of
proteins tracks the measured one. That is the axis selectivity work needs, and it is not the axis Boltz-2
was tuned or benchmarked on. A model can be genuinely useful for ranking a congeneric series against one
target — the published audits say it is — and carry no usable protein-side signal. Nothing here speaks to
pose accuracy, to the structure module, or to the conventional axis beyond the one within-kinase number
reported for scale.

**One model version, one read-out.** Boltz-2 2.2.1 released weights, the `affinity_pred_value` head, the
default settings passed explicitly. The binary binder probability is reported alongside because it is a
differently-trained head on the same features; the sampling arm varies the diffusion budget. A later
release could behave differently, which is why the decoy protocol and panel definition are released with
the report rather than only the numbers.

**The crop is a real assumption.** The model sees the annotated kinase domain plus 20 residues, not the
full-length protein. That matches what the competition binding assay reports and makes a panel affordable,
but accessory domains, linkers and partners that shape selectivity in the cell are absent. If removing
them is what removes the signal, that is a finding about the input the model can be given at scale, not
about the kinome. Crop length and Boltz's own confidence scores are reported per complex, and the primary
statistic is recomputed on the high-confidence half, so a reader can check whether the failures are the
poorly-folded inputs.

**Training exposure cuts one way.** Davis is from 2011 and is almost certainly inside the training
distribution. That makes a null result harder to explain away — the model is not being asked to
extrapolate — and it makes a positive result uninterpretable as generalisation. The post-cutoff arm (11
compounds first published in 2025, 93 pairs) and the training-support gradient bound this, but 93 pairs is
the ceiling of what public post-cutoff profiling offers, so that arm is a check, not a replication.

**Censoring is handled two ways and both are reported.** 27.1 % of the rectangle sits at the 10 µM assay
ceiling. P1 keeps those cells as ties at pKd 5, because telling binders from non-binders is part of
selectivity; P2 drops them and asks only about ordering among real numbers. The verdict follows P1, as
preregistered.

**The panel is deliberately the easy case.** Kinases and ligands were chosen for having many uncensored
measurements, which buys dynamic range to rank but samples the more promiscuous end of both. The
promiscuity probe adds the eight least-promiscuous eligible kinases to test whether the picture changes
where binding is rare. A panel chosen for difficulty would be a harder test, not an easier one.

**Rank, not calibration.** Davis reports Kd from a competition binding assay; the model's head mixes
Kd/Ki/IC50. Every primary statistic is a rank correlation within a fixed ligand, which is invariant to any
monotone recalibration — including the molecular-weight correction, which for a fixed ligand is a
constant and cannot change a within-ligand statistic at all. Absolute agreement in log units is reported
descriptively and should not be read as a calibration claim.

**No docking comparison.** A Vina or Glide baseline would answer "is this better than the cheap physical
alternative?", which is a different and larger study; it was declared out of scope in the plan (§5.8)
rather than dropped quietly. The baselines here are deliberately trivial — target promiscuity, nearest
chemical neighbour, ligand-only, molecular weight — because the point of the comparison is what a model
must beat to be worth running at all.

## Reproducing it

Everything needed is in the run directory, and nothing in it requires a credential: the Davis panel comes
from the DeepDTA release, the kinase sequences from UniProt, the alignments from the public ColabFold
server, and the model weights from the Boltz release.

```
code/panel.py                  select the 32 x 32 rectangle   -> data/panel.json
code/validate_data.py          check the matrix against the paper and PubChem
code/build_inputs.py <arm>     write one YAML per complex     -> data/inputs_<arm>/
code/boltzrun.py msa <seqs>    fetch one MSA per protein      -> data/msa/
code/boltzrun.py run <in> <out>  boltz predict, resumable
code/boltzrun.py collect <out> <arm> results/predictions.jsonl
code/assemble.py tidy          per-pair tables                -> results/tables/pairs_<arm>.csv
code/assemble.py primary       P1-P5, baselines, verdict      -> results/tables/primary.json
code/secondary.py              decoy, promiscuity, sampling, support
code/geometry.py               sequence-vs-prediction geometry
code/figures.py                F1-F5
code/test_analysis.py          17 checks on the estimators
```

The estimator checks are worth running first: they assert that a perfect predictor scores 1, that a
ligand-only predictor scores exactly 0 on the selectivity axis, that the sign convention is right, that a
pure-noise predictor's interval covers 0, and that each of the four verdict branches fires on data built to
trigger it. They take a second and they caught two real bugs in this analysis.

Seeds and settings are fixed in `code/boltzrun.py` (`SEED = 20261013`, the explicit flag dictionary) and
`code/analysis.py` (`SEED`, `NBOOT = 2000`). `results/tables/env.json` carries the package versions and the
sha256 of both released checkpoints, so a rerun can confirm it used the same weights. The per-complex
read-outs, with Boltz's own confidence scores, are released as `results/predictions.jsonl`; the alignments
themselves are not redistributed, only the manifest of which sequence was aligned.

One operational note for anyone repeating this at panel scale. A thousand complexes is about fifteen
GPU-hours, which is long enough that the machine will probably interrupt you: this run was stopped twice by
host crashes. Boltz writes each complex's outputs as it finishes and skips on restart any complex that
already has them, so both interruptions cost one complex each. Fetch the alignments once per protein and
cache them, rather than letting the predictor fetch per complex — the same 32 proteins appear in every
column of the rectangle, and the public server is the slowest step in the whole pipeline by an order of
magnitude.
