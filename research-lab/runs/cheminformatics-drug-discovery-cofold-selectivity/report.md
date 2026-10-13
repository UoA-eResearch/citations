# Does co-folding affinity know its target?

*A kinase-panel selectivity test of Boltz-2: hold each ligand fixed, vary the protein, and compare with
measured binding constants.*

**Verdict: Refuted.** The preregistered hypothesis — that Boltz-2's affinity head cannot rank proteins for
a fixed ligand — does not hold. It ranks them with a median correlation of 0.44, puts a true top-3 kinase
first for 56 % of compounds, and never falls below zero on any of them. It also does not demonstrably beat
a baseline that ignores the compound entirely on the primary statistic, captures barely a third of the
compound-by-kinase interaction that selectivity consists of, and over-trusts sequence similarity between
close paralogues.

## In plain terms

Drug companies need to know not just whether a compound hits its target, but what else it hits. A drug that
blocks the intended enzyme and thirty others causes side effects. So the practical question for any new
affinity predictor is: given a compound, can it tell you which proteins that compound will bind?

Boltz-2 is an open model that predicts binding affinity roughly a thousand times faster than the physics
calculations it aims to replace. We tested it the way a drug project would: take 32 known kinase
inhibitors, ask the model to rank 32 human kinases for each one, and compare with laboratory measurements
of all 1,024 combinations.

We expected it to fail, and preregistered that prediction. It didn't. The model's rankings correlate about
0.44 with the measurements, well above the threshold we had set for failure.

But a correlation on its own means little without something to compare it against, so we also wrote down,
before running the model, what some deliberately stupid methods achieve. One of them ignores the compound
entirely and simply ranks kinases by how many drugs bind them in general. That scores 0.39 — statistically
indistinguishable from the model.

The resolution is that the two methods fail differently. The stupid baseline is excellent for promiscuous
compounds and actively wrong for selective ones, dropping as low as −0.42. The model is never actively
wrong on any of the 32 compounds, and when asked to name a compound's single best target it gets one right
56 % of the time, against 19 % for the baseline.

Where it falls short is the thing selectivity actually consists of. Most of what varies in real
measurements is the specific pairing of compound and kinase; the model captures only about a third of that,
leaning instead on how potent a compound is overall and on how similar two kinases look in sequence — more
heavily than the real biology warrants. It predicts two near-identical kinases to be three times more alike
than they measure.

Useful for triage, then, and better than nothing by a clear margin at the top of the list. Not yet a
substitute for the experiment when two close relatives have to be told apart.

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

All 1,024 panel complexes predicted, no failures, no missing cells. The secondary arms add 573 more, for
1,597 in total — the preregistered budget exactly.

### The preregistered verdict: Refuted

The hypothesis was that the model fails this test, with a median within-ligand Spearman of 0.25 or below.
It does not fail it.

| | point | 95 % interval | |
| --- | --- | --- | --- |
| **P1** median within-ligand Spearman, 32 kinases | **0.444** | 0.418 – 0.532 | ligand cluster bootstrap |
| P2 the same, uncensored cells only | 0.464 | 0.429 – 0.487 | |
| P1, resampling kinases instead of ligands | — | 0.368 – 0.569 | sensitivity |
| P1, dyadic bootstrap | — | 0.331 – 0.619 | sensitivity |
| P1 on the high-confidence half | 0.537 | 0.391 – 0.637 | |
| P1 using the binary binder probability | 0.596 | 0.519 – 0.665 | |
| P3 median within-kinase Spearman, 32 ligands | 0.453 | — | H2's floor was 0.4 |
| P4 top-1 in the true top-3 | 0.562 | — | chance 0.094 |
| P4 precision@3 | 0.375 | — | chance 0.094 |

The lower end of every interval sits above 0.25, so by the rule in plan.md §6 the hypothesis is **refuted**:
the affinity head is not protein-blind, and its rankings are not noise. Censoring is not doing the work —
dropping the ceiling cells moves P1 from 0.444 to 0.464 — and neither is structural quality, since the
high-confidence half scores slightly higher than the whole.

### But the threshold was in the wrong place, which the baselines show

This was foreseeable and was written down before any prediction: 0.25 is *below* what a baseline with no
chemistry in it achieves. Ranking kinases purely by how many compounds they bind — a single column vector
reused for every ligand — scores 0.386.

| | P1, selectivity axis | top-1 | precision@3 |
| --- | --- | --- | --- |
| **Boltz-2 affinity** | **0.444** (0.418 – 0.532) | **0.562** | **0.375** |
| B1 target promiscuity, no chemistry | 0.386 (0.310 – 0.522) | 0.188 | 0.229 |
| B2 nearest chemical neighbour (uses labels) | 0.394 (0.268 – 0.503) | 0.312 | 0.240 |
| B0 ligand-only | 0.000 | 0.062 | 0.042 |
| B3 molecular weight | 0.000 | 0.062 | 0.042 |

Paired ligand bootstraps of the difference, model minus baseline:

| vs | P1 | top-1 | precision@3 |
| --- | --- | --- | --- |
| B1 promiscuity | +0.058 (−0.071, +0.166) | **+0.375 (+0.188, +0.562)** | **+0.146 (+0.021, +0.250)** |
| B2 neighbour | +0.050 (−0.065, +0.195) | **+0.250 (+0.031, +0.469)** | **+0.135 (+0.010, +0.260)** |

The two statistics disagree, and the disagreement is the result. On the preregistered primary statistic —
the median rank correlation over the whole 32-kinase profile — Boltz-2 is within noise of a baseline that
never looks at the compound. On finding the right targets it is not: it puts a genuine top-3 kinase first
for 56 % of ligands, against 19 % for the promiscuity baseline and 9 % for chance. The hit-rate comparison
was not preregistered with an interval; that was added on seeing the gap, and is reported as the addition
it is (D8).

Two things explain the gap. The profile contains a 27 % block of cells tied at the assay ceiling plus a
long tail of weak binders, where ordering carries little information and the model adds little; the median
Spearman weights all of that equally with the top. And the per-ligand floor differs sharply, which is
visible in F1 and is an exploratory observation (D9):

| | worst ligand | ligands below 0 | ligands below 0.25 |
| --- | --- | --- | --- |
| Boltz-2 | +0.029 | 0 of 32 | 3 of 32 |
| B1 promiscuity | −0.387 | 2 of 32 | 7 of 32 |
| B2 neighbour | −0.419 | 3 of 32 | 11 of 32 |

The baselines reach their median by being excellent for promiscuous compounds and actively misleading for
selective ones. Boltz-2 is never actively misleading on this panel. For a tool meant to nominate a
handful of targets, that floor matters more than the median.

### What the model gets wrong: it hears the ligand, and over-trusts sequence similarity

The two-way decomposition says where the error lives (F3). In the measurements, 60 % of the variance is
the ligand-by-kinase interaction — which is exactly what selectivity *is*. In the predictions it is 35 %,
while the ligand main effect swells from 25 % to 53 %.

| share of variance | measured | predicted |
| --- | --- | --- |
| ligand (which compound is potent in general) | 25.5 % | 53.4 % |
| kinase (which kinase binds most things) | 14.6 % | 11.4 % |
| ligand × kinase interaction (selectivity itself) | 59.9 % | 35.2 % |

The predictions are also compressed: the spread of a ligand's profile is half the measured spread (SD 0.52
against 1.00), and across the whole panel 0.76 against 1.19. So differences are in the right direction more
often than not, but systematically too small.

The geometry arm (exploratory, D3) says what the model is listening to. Taking each kinase's 32-ligand
prediction vector, removing ligand means and comparing the resulting kinase-by-kinase distance matrices:

| Mantel-style comparison | ρ |
| --- | --- |
| predicted distances vs measured distances | 0.434 |
| predicted distances vs kinase-domain sequence distance | 0.338 |
| **measured** distances vs sequence distance | **0.248** |
| binary-probability distances vs measured distances | 0.520 |

The model's picture of which kinases resemble each other tracks sequence identity *more tightly than the
real pharmacology does*. The four near-identical pairs in the panel show the same thing from the other
side: CSNK1D and CSNK1E share 97 % of their kinase-domain sequence and really differ by 0.35 log units on
average across these ligands, but are predicted to differ by 0.12; AURKB and AURKC differ by 0.37 measured
and 0.15 predicted. Across all 496 kinase pairs the median measured difference is 1.12 log units and the
median predicted difference 0.56. Sequence similarity is a good prior for binding similarity, and the model
leans on it harder than the measurements justify — which is precisely the failure mode that matters when a
project needs to separate two close paralogues.

### The secondary arms

**Decoys (128 complexes).** For every one of the four non-kinase proteins, the median prediction sits 1.1
to 1.3 log units below the same ligand's mean across the 32 kinases — 2.0 to 2.4 within-kinome standard
deviations. No decoy ever outscored a ligand's best kinase (0 of 128), and only 2 of 128 outscored a
ligand's kinase *mean*. The binary probability separates them further still (median 0.07 – 0.29 against
0.44 for kinases). Kinase inhibitors are recognised as kinase binders; this is the easy discrimination, and
the model passes it cleanly.

**Promiscuity probe (256 complexes).** Adding the eight least-promiscuous eligible kinases to the panel
leaves the result where it was: P1 = 0.475 (0.359 – 0.573) over the 40-kinase union. The eight on their own
give 0.284 (0.192 – 0.577), but with an average of 1.4 uncensored cells per ligand that sub-rectangle is
too censored to carry any weight, and it is reported rather than relied on.

**Affinity sampling (96 complexes re-predicted).** Doubling the affinity sampling steps and running nine
diffusion samples instead of five changes nothing: predictions correlate 0.979 between settings, move 0.13
log units on average, and P1 shifts by −0.029 (−0.206, +0.091). The result is not a sampling artefact.

**Post-cutoff compounds (93 complexes).** The eleven compounds whose earliest ChEMBL document is 2025 or
later, profiled against 6 to 12 kinases each (61 kinases in all, 3 % of records censored), give P1 = 0.543
(0.371 – 0.657) — if anything above the Davis panel's 0.444, with intervals that overlap heavily. Whatever
the model is doing, it is not reciting Davis.

Three caveats keep this a check rather than a replication. The measurements are ChEMBL pActivity pooled
over mixed assay types rather than one laboratory's Kd, so some of the within-compound variation is
between-assay noise. Six to twelve kinases make a per-compound correlation noisy. And this arm admits no
baseline: the promiscuity analogue needs kinases measured across several compounds, but only 8 of the 61
appear in three or more, leaving the baseline defined for 4 compounds over 3 to 6 kinases each — two of
which share all six, so their "mean over other compounds" is essentially each other and both score exactly
1.0. That is an artefact of the overlap, and it is reported as not computable rather than as a comparison.
Ninety-three pairs is the ceiling of what public post-cutoff kinase profiling currently offers.

**Training support (no GPU).** Across the panel's kinases, pre-2024 ChEMBL compound counts span 91 to
5,205, and accuracy barely tracks them: Spearman 0.147 against the within-kinase correlation, 0.251 against
pairwise concordance, −0.041 against absolute error. On this panel the model is not simply reciting the
best-measured targets.

### The other head is better

One practical finding worth stating separately. Boltz-2 emits a binary binder probability alongside the
affinity value, and on this axis the probability is consistently the better ranker: P1 = 0.596 against
0.444, within-kinase 0.614 against 0.453, and a Mantel correlation of 0.520 against 0.434. Anyone using
Boltz-2 for selectivity triage should be ranking by `affinity_probability_binary`, not by
`affinity_pred_value`. That comparison was preregistered as a secondary read-out, so it is not a fishing
expedition, but the size of the gap was not anticipated.

## What this does and does not show

The headline is easy to misread in either direction, so stated plainly: on this panel Boltz-2's affinity
head carries real protein-side signal — it is not ranking kinases at random, and it clears the
preregistered threshold comfortably — but on the preregistered primary statistic it does not demonstrably
beat a baseline that never looks at the compound, and its advantage is concentrated at the top of the
ranking and in its floor rather than spread across the profile. The hypothesis this study set out to test
was refuted, and the threshold it set was, as the preregistration itself anticipated, too low to be the
interesting comparison. The interesting comparison is the baseline table, and it was fixed before any
prediction was made.

A reader should not take "Refuted" to mean the model is good at selectivity. It means the specific claim
that it is *useless* at selectivity is wrong. The limitations below were written from the design, before
the predictions were analysed.

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
