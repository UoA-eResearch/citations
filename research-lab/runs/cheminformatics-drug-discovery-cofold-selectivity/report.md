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

TBD

## Reproducing it

TBD
