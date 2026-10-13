# Adversarial review — "Does co-folding affinity know its target?"

Reviewer: independent adversarial pass (Fable 5.1), 2026-10-14, against draft `04c7f25`.
Scripts: `review/reviewer_checks/{repanel,restat,mechanism,geom_check}.py`; outputs `recomputed.json`, `mechanism.json`.

## Recommendation: **fix first** — 19 issues

The measurement work is the cleanest I have audited in this lab. The panel re-derives **exactly** from the Davis
release and UniProt — every eligibility rule, the largest-remainder allocation, all 32 ligands, all 32 crops
byte-identical, and the censoring arithmetic to four decimals. The pipeline verifies end to end, 1024/1024, with no
silent loss. Every number I recomputed from `pairs_panel.csv` matches the report to three decimals. The verdict
(**Refuted**) is correct, robustly so: all five intervals clear 0.25, including the most conservative (dyadic)
one, and the tight lower bound is genuine rather than an order-statistic artefact.

The reason this is *fix first* rather than *publish with edits* is the framing, not the science. Four issues
(1–4) sit in the abstract and the plain-language summary, and three of them (1–3) **systematically understate the
model** in a way that makes the report's central narrative wrong: the claim "does not demonstrably beat a baseline
that ignores the compound entirely" is true of exactly one statistic, P1, and reverses on P2 — which was
preregistered, was computed, is sitting in `primary.json`, and is not in the report. Issue 4 asserts a comparison
with no interval, which is precisely the defect D10 had just withdrawn another claim for. The fixes are textual and
tabular; no re-run is needed, and the verdict does not move.

---

## A. Issues that must be fixed

### 1. MAJOR — The central claim holds only on P1 and reverses on the preregistered P2, whose baseline values the report computed and omitted

**Location:** abstract (l. 8–11), "In plain terms" (l. 29–30), baseline tables (l. 91–97, 144–157), discussion (l. 283–286).

The baselines' P2 values are already stored in `results/tables/primary.json`
(`baselines.B1_promiscuity.P2.point` = 0.2926, `baselines.B2_neighbour.P2.point` = 0.2937). They appear nowhere in
the report. Recomputed, with the same paired ligand bootstrap:

| statistic | model | B1 | model − B1 | model − B2 |
| --- | --- | --- | --- | --- |
| P1 (all cells) | 0.4435 | 0.3856 | +0.0579 (−0.0711, +0.1656) | +0.0496 (−0.0654, +0.1946) |
| **P2 (uncensored, preregistered)** | **0.4638** | **0.2926** | **+0.1712 (+0.0647, +0.2917)** | **+0.1701 (+0.0173, +0.3460)** |

Both P2 intervals exclude zero. The report reports the model's own P2 (0.464) and says "Censoring is not doing the
work — dropping the ceiling cells moves P1 from 0.444 to 0.464". That is true of the model and false of the
comparison: dropping the ceiling cells moves B1 from 0.386 to 0.293. Censoring is doing nearly all the work in the
one place the report rests its headline.

**Fix:** add a P2 column to both baseline tables and the P2 row to the paired-difference table; change every
statement of the central claim to name the statistic ("on the all-cells statistic P1 the model is within noise of
B1; on the uncensored-only statistic P2 it beats it by +0.17, interval excluding zero"); correct the "censoring is
not doing the work" sentence to say it is not doing the work *for the model*.

### 2. MAJOR — "The two statistics disagree" is really P1 against every other statistic, and the stated explanation is the wrong mechanism

**Location:** l. 159–168.

I computed every rank statistic a selectivity user would plausibly ask for (`mechanism.py`). Paired ligand
bootstrap, model − B1:

| statistic | model | B1 | difference | excludes 0 |
| --- | --- | --- | --- | --- |
| P1 (median within-ligand ρ, all cells) | 0.4435 | 0.3856 | +0.0579 (−0.0711, +0.1656) | no |
| **AUC, ceiling block vs real binders** | **0.7332** | **0.7331** | **+0.0001 (−0.0832, +0.0810)** | **no** |
| P2 (uncensored only) | 0.4638 | 0.2926 | +0.1712 (+0.0647, +0.2917) | yes |
| concordance among uncensored cells | 0.6688 | 0.6055 | +0.0633 (+0.0269, +0.1140) | yes |
| NDCG (gain = pKd − 5) | 0.8638 | 0.8022 | +0.0615 (+0.0209, +0.1064) | yes |
| NDCG@3 | 0.6927 | 0.4968 | +0.1959 (+0.0965, +0.2956) | yes |
| NDCG@5 | 0.7088 | 0.5664 | +0.1424 (+0.0527, +0.2360) | yes |
| top-1 in true top-3 | 0.5625 | 0.1875 | +0.3750 (+0.1875, +0.5625) | yes |

The pattern is not a disagreement between two statistics. It is that **the model and B1 are in a dead heat on one
thing only — telling the 27 % ceiling block from real binders (AUC 0.7332 vs 0.7331) — and P1 gives that shared
competence 27 % of its weight.** Everything that asks about ordering real affinities, or about the top of the
profile, separates them with an interval excluding zero. Exact McNemar on the top-1 indicators confirms the
hit-rate result independently: 13 model-only hits against 1 baseline-only, p = 0.0018 vs B1 (vs B2: 11 against 3,
p = 0.057 — so the B2 top-1 margin is weaker than the bootstrap interval alone suggests, and should be reported as
borderline).

The report's explanation — "a 27 % block of cells tied at the assay ceiling plus a long tail of weak binders,
where ordering carries little information and **the model adds little**" — misattributes the cause. Ordering
carries plenty of information there (AUC 0.73); what happens is that the *baseline is just as good at it*.

**Fix:** restate as "P1 is the one statistic on which the model does not separate from B1, because both are
equally good at spotting the ceiling block and P1 weights that block equally with the top"; report at least one
rank-weighted statistic (NDCG@3 is the natural one for a triage tool); report the B2 top-1 margin as borderline.

### 3. MAJOR — The "never below zero" floor claim does not survive the uncensored-only subset, and the abstract states it unqualified

**Location:** abstract (l. 8), "In plain terms" (l. 33–34), l. 171–179.

| predictor | P1 worst | P1 ligands < 0 | P2 worst | P2 ligands < 0 |
| --- | --- | --- | --- | --- |
| Boltz-2 value head | +0.0292 | 0 of 32 | **−0.0944** | **2 of 32** |
| B1 promiscuity | −0.3873 | 2 of 32 | **−0.1008** | **2 of 32** |
| B2 neighbour | −0.4194 | 3 of 32 | −0.1233 | 6 of 32 |

On uncensored cells the model's floor (−0.094, 2 ligands below zero) is **indistinguishable from B1's** (−0.101,
2 ligands below zero). The dramatic floor gap is entirely a censored-block phenomenon. The same holds on
concordance (2 ligands below 0.5 for both). And the property does not even belong to the head the report
recommends: the binary probability head has 1 ligand below zero on P1 (worst −0.0329).

The report builds a recommendation on this: "For a tool meant to nominate a handful of targets, that floor matters
more than the median." D9 marks it exploratory, but the abstract ("never falls below zero on any of them") and the
plain-language summary ("The model is never actively wrong on any of the 32 compounds") state it flatly.

**Fix:** qualify to "on the all-cells statistic"; add the P2 floors to the table; drop or heavily soften the
"floor matters more than the median" recommendation, since the floor advantage does not survive the subset the
report itself calls the one that "asks only about ordering among real numbers".

### 4. MAJOR — The "uniform compression" replacement claim repeats the exact defect D10 withdrew a claim for

**Location:** l. 215–232, D10.

Three problems.

(a) **The table compares incommensurable quantities.** The five near-pair rows are per-pair ratios; the
`all 496 pairs` row (0.50) is a *ratio of medians* (1.1205 / 0.5620). Like for like, the median of per-pair ratios
over all 496 pairs is **0.5222**, and over the five near pairs 0.5725 — so the comparison is 0.57 vs 0.52, not
0.57 vs 0.50.

(b) **"Uniform" is asserted with no interval** — the same error D10 says "should not have made a comparison it had
no interval for". I supplied the tests:

| test of whether compression depends on similarity | result |
| --- | --- |
| Spearman(crop identity, per-pair ratio), 496 pairs | −0.0682 |
| dyadic permutation p (9999 label permutations) | 0.4123 |
| kinase bootstrap, median(ratio \| near) − median(ratio \| rest) | +0.0485 (−0.2228, +0.3086) |
| Mann-Whitney, 5 near pairs vs 491 | p = 0.8409 |

There is **no detectable dependence** on identity — consistent with the report's direction — but the interval is
far too wide to *establish* uniformity. It cannot rule out near pairs being compressed substantially more or less
than average.

(c) **"The model halves the distance between any two kinases" is false as stated.** Per-pair ratios range
0.2504–1.3187 (SD 0.159, IQR 0.429–0.639). One pair is *expanded*, not compressed.

**Fix:** make the last table row a median-of-per-pair-ratios (0.52) so the column is one estimator; replace "the
compression is uniform" with "no dependence of compression on sequence identity is detectable (ρ = −0.07,
permutation p = 0.41), though with five near-identical pairs the interval admits a large effect either way";
change "any two kinases" to "the typical pair of kinases".

---

## B. Moderate issues

### 5. The crop is measurably suppressing accuracy, and the high-confidence recomputation does not test it

**Location:** plan §9.3, report l. 127/136 and l. 308–314.

The crop is the threat the plan flagged as most likely to do hidden work, and it is doing some:

| | |
| --- | --- |
| Spearman(fraction of full protein retained, within-kinase ρ) | **+0.389 (p = 0.028)** |
| Spearman(log full length, within-kinase ρ) | −0.356 (p = 0.045) |
| P1 on the 16 least-cropped kinases | **0.5235** |
| P1 on the 16 most-cropped kinases | **0.3886** |
| median crop fraction / range | 0.555 (0.150–0.929) |

The confidence filter cannot address this, and I can show it does not: 6 of 32 kinases retain **zero** cells at the
median cut, cells kept per kinase range 0–32 and per ligand 8–23, the retained half is *more* censored (31.6 % vs
22.7 % dropped), and mean confidence correlates **−0.278 (p = 0.124)** with within-kinase accuracy. So "the
high-confidence half" is close to a non-random kinase subset with a different effective panel per ligand, not a
fold-quality filter — which makes "P1 on the high-confidence half = 0.537" a confounded comparison, not evidence
that "neither is structural quality doing the work" (l. 136).

The report also never states the direction of the crop bias, which is its strongest available defence and its
sharpest vulnerability at once: the crop biases the model **downward**, so it cannot explain away "Refuted" (it
makes the refutation conservative) — but it **does** weaken the "doesn't beat the baseline" claim, because B1 and
B2 read measured labels and are crop-immune.

**Fix:** report the crop gradient as a quantified limitation; state the asymmetric direction of the bias for the
two headline claims; stop presenting the confidence filter as the crop diagnostic and describe what it actually
is.

### 6. B1 is labelled "no chemistry at all" without the equally important fact that it consumes the measured panel

**Location:** l. 94, 147, abstract l. 9–10, plain terms l. 28–30.

B2 carries a "(uses labels)" marker. B1 does not — yet B1 is built from the measured Kd of 67 other compounds
against the same 32 kinases. plan §7 is explicit: "B1 and B2 use the measured panel, so they are references for
*how much signal is extractable*, not fair competitors to a zero-shot model." That sentence does not survive into
the report. "A baseline that never looks at the compound" is accurate about chemistry and silent about the fact
that B1 is unavailable without the profiling experiment the model is meant to replace.

**Fix:** label B1 "(uses the measured panel)" alongside B2; carry plan §7's caveat into the report; add one clause
noting B1 cannot be computed prospectively for a new kinase set.

### 7. `repro.csv`, a preregistered check, was never produced, and the omission is not logged

**Location:** plan §4 ("Recorded in `results/tables/repro.csv`"); `results/tables/` contains no such file; no
deviation mentions it.

plan §4 committed to predicting one complex twice at the same seed ("must give identical affinity values") and once
at a changed seed ("gives an idea of run-to-run spread"). Neither was done. In an otherwise meticulous deviations
file this is the one silently dropped commitment.

It has a substantive consequence. The sampling arm's headline evidence is "predictions correlate 0.979 between
settings" — but with no same-setting replicate there is no reference for what 0.979 means. It cannot distinguish
"the setting does not matter" from "0.979 is the noise floor". That is exactly what the missing seed-change
measurement would have bounded.

I attempted to supply it and could not: the GPU showed 9.8 GB nominally free but OOM'd during allocation (vLLM has
grown since D7). Worth recording as a positive finding, though — boltz fails **loudly** on OOM
(`WARNING: ran out of memory, skipping batch`, then a `FileNotFoundError` for the missing intermediate), so an OOM
yields a *missing* complex, never a wrong value. Combined with my count of 1024/1024 affinity JSONs, that rules out
silent loss during the memory-constrained resume.

**Fix:** run it (two complexes, ~70 s) or log the omission as a deviation; either way soften "The result is not a
sampling artefact" to note that one setting pair on 9 % of the panel, with no replicate reference, is weak evidence
— as plan §8 itself said it would be.

### 8. Undisclosed post-cutoff shortfall; "the preregistered budget exactly" is wrong

**Location:** l. 114–115; plan §5.3, §5.7.

plan §5.3 projected 14 compounds and ~120 pairs; §5.7 totalled ≈ 1,624 complexes. The arm delivered 11 compounds
and 93 pairs, so the total is 1,597 — not "the preregistered budget exactly". `git show
bc1a623:…/postcut_pairs.csv` has 93 pairs and was committed at **09:54 on 13 Oct, ten minutes after plan.md**, so
the shortfall was known immediately and never logged. `postcutoff.py` also applies two filters plan §5.3 does not
state: MW ≤ 700 and ≤ 128 heavy atoms.

**Fix:** log a deviation for the 14 → 11 shortfall and the two extra filters; change the sentence to "1,597 in
total, against the ≈ 1,624 the plan projected — the post-cutoff arm yielded 93 pairs rather than ~120".

### 9. "Seed 20261013 plus the shard index" contradicts D4/D6

**Location:** l. 83.

I extracted every `boltz predict` invocation from the logs. All nine retained runs used `--seed 20261013` as a
single process; only the *deleted* three-shard decoy runs used 20261014/20261015. The report's phrase describes the
layout D4 and D6 abandoned, and contradicts D6's "a prediction is still reproducible from its arm and pair alone".

**Fix:** delete "plus the shard index".

### 10. "Stopped twice by host crashes" is unsupported

**Location:** l. 379–381.

Only one interruption of this run is documented (D7) or evidenced. `panel_run.log` has no `exit` line (killed
mid-run); `panel_run2.log` has `exit 0 after 8416s`; that is the single resume, and `lane2.log` shows decoy
(13:15), promiscuity (17:50) and sampling (21:35) all finished before the 22:56 crash.

The *harmless* part of the claim is verified: 1024 YAMLs, 1024 output directories, 1024 affinity JSONs, no
directory with more than one, and `predictions.jsonl` has 1,597 rows with 1,597 unique `(arm, pair_id)` keys, zero
duplicates and zero value conflicts.

**Fix:** "stopped once", or document the second interruption.

---

## C. Minor issues

### 11. B0 and B3 hit rates are artefacts of the kinase column order, not estimates

**Location:** l. 93, 96, 149, 150.

A constant predictor has no ranking, so `np.argsort(-p)` returns columns 0, 1, 2 — the first three kinases in
Manning-group-then-alphabetical order. Over 200 random column permutations the same statistic averages **0.1042**
(range 0.000–0.344) for B0 and 0.0927 for B3, against the 0.0625 reported. Both reported values sit *below* the
0.094 chance line, which is the tell. `test_analysis.py`'s "ligand-only top1 is chance-like" passes only because
the synthetic test's column order is random relative to the truth. **Fix:** report these cells as "undefined
(no ranking)" rather than as numbers.

### 12. The per-axis B1 switch is defensible but undisclosed, and it slightly flatters the model

`base_promiscuity` (leave-one-out) is used for P1/P2 and `base_promiscuity_full` for P3. The switch is legitimate —
I confirmed the LOO version gives **exactly −1.000000** on the within-kinase axis (a pure artefact of subtracting
the ranked ligand from its own kinase mean) and the no-LOO version exactly 0.0 — and it was committed at
`bdd795d` (10:04), before the panel started (10:33). But it lives only in a code docstring. Note also that B1
*without* LOO scores **higher** on P1 (0.4256 vs 0.3856), so the LOO choice shrinks the margin the report quotes
from +0.018 to +0.058 — i.e. it flatters the model on the central comparison, though the qualitative conclusion is
unchanged. **Fix:** one disclosing sentence, with both numbers.

### 13. The promiscuity probe's 0.284 rests on 16 of 32 ligands

`secondary.json` records `extra_only.P1.n_ligands = 16` — with 1.4 uncensored cells per ligand the other 16 have
no defined correlation. The report calls the sub-rectangle "too censored to carry any weight", which is right, but
should give n = 16. Separately, the 40-kinase union's P3 = 0.3789 falls below H2's 0.4 floor and is not mentioned.

### 14. The preregistered HSP90 question is set up and never answered

plan §5.2: "HSP90 is included deliberately as a *nucleotide-binding* non-kinase: if the affinity head is
responding to generic ATP-pocket character rather than kinase identity, HSP90 should score like a kinase." The
answer is in the data and is mildly interesting: HSP90α is the **most kinase-like of the four decoys on both
read-outs** — median probability 0.290 against 0.070/0.183/0.190 for the others (kinases 0.436), and the smallest
gap at −2.04 kinome SD against −2.22/−2.33/−2.37. The report gives only the ranges. **Fix:** one sentence
answering it.

### 15. "Chance 0.094" is 3/32; ties make it 0.0957

Measured true-top-3 set sizes average 3.06 (max 4) because kinases tying the third-best pKd are counted in. Immaterial
to any conclusion, but the report quotes the number to three decimals in two tables.

### 16. Sensitivity bootstraps used 500 draws, not the 2,000 plan §6 specifies

`kinase_boot.nboot = 500`, `dyadic_boot.nboot = 500` (`nboot // 4` in `analysis.py`). Recorded in `primary.json`,
not disclosed in the report, and a deviation from plan §6's "2000 cluster bootstrap draws".

### 17. The post-cutoff censored share counts only one direction

3 pairs carry `>` and are treated as censored (the reported 3 %); 5 further pairs carry `<` and are treated as
exact, though they are equally bounds. Both directions give 8/93 = 8.6 %.

### 18. The geometry section's "removing ligand means" is a provable no-op

Subtracting a per-ligand constant cancels in `c[:,i] − c[:,j]`. I measured `max |centred − uncentred| = 0.000e+00`
over all 496 pairs, and the Mantel correlation is identical to six decimals either way. Harmless, but it is
described (l. 197–198, and `geometry.py`'s docstring) as though it controlled for the ligand main effect — which is
the report's own diagnosis of the model's central weakness, so a reader may credit the geometry analysis with a
safeguard it does not contain. **Fix:** drop the clause or note it is immaterial.

### 19. The report cites none of the prior work the plan catalogued, and omits one relevant paper

plan §2 has a careful eight-row literature table. The report cites none of it, and asserts novelty on l. 53–54
with no reference. Two specific consequences:

- **Koch et al. is not cited and the H4 restatement is not disclosed.** I verified the ChemRxiv abstract
  (10.26434/chemrxiv-2025-sf3cs): Boltz-2 "is still not able to identify the correct protein target by correctly
  predicting a higher binding affinity in comparison to the decoy targets" — the study's characterisation is
  accurate. But the report presents its decoy arm passing "cleanly" (l. 240–241) without citing the closest prior
  work that reports Boltz-2 *failing* a related test, and without disclosing that H4 was restated because of it
  (D1, plan §1.2). A reader of the report alone cannot know H4 changed. The tension is explicable — Koch ranks
  among plausible decoy targets drawn from LIT-PCBA, this arm uses four unrelated non-kinases and potent kinase
  drugs — and that explanation is worth a paragraph, not an omission.
- **Nesso-1 (doi 10.64898/2026.08.01.742196) is missing from plan §2.** It reports matching or surpassing Boltz-2
  "over the same benchmarks adopted in their study — which we show reflect in-distribution scenarios". That is
  directly relevant to this study's framing of its panel as "deliberately all high-support, inside the training
  distribution", and MIRAGE benchmarks the two models against each other.

I otherwise found no prior in-kinome within-ligand selectivity audit of a co-folding affinity head against a
complete measured Kd panel. The nearest neighbours are all distinct: MIRAGE (family-support generalisation —
abstract confirms the plan's characterisation, and note MIRAGE's own recommendation to report "excess over a
support-insensitive baseline" is exactly what this study does), BoltzOmics (variants of one protein),
DeepKinome/DeepKinomeWeb and MMCLKin (kinome-wide selectivity prediction, not Boltz-2 audits), and the JCTC/arXiv
2603.05532 reliability audit (within-target). **The novelty claim stands.** A second paper makes the
pose-independence point the plan attributes to 2603.05532 alone (JCIM, pmid 41592323, "affinity predictions seem to
be relatively independent of pose quality").

**Fix:** carry plan §2 into the report, disclose the H4 restatement and reconcile the decoy arm with Koch, add
Nesso-1 to the table.

### A documentation point worth adding rather than an issue

Boltz's own `docs/prediction.md` says `affinity_pred_value` "should only be used when comparing different active
molecules, **not inactives**", and that `affinity_probability_binary` "should be used to detect binders from
decoys". P1 includes a 27 % block of inactives, so the primary estimand uses the value head outside its documented
domain. This is worth stating in the read-out section, because it is the *documented* explanation for the finding
the report calls unanticipated ("the size of the gap was not anticipated", l. 277–278) and it is an independent
argument for P2 being the more appropriate primary for the value head. It also strengthens, rather than weakens,
the report's practical recommendation.

---

## D. What I verified as sound

**Timing and disclosure.** `plan.md` committed `c9fa258` 09:44, the panel arm started 10:33 — the plan predates every
panel prediction. `analysis.py`, `assemble.py` and `baselines_only.json` were all committed before any model output
existed (`bdd795d`, 10:04). Critically, the two estimator choices that could have been outcome-driven both predate
the run: the `rho` → 0.0 convention at `bc1a623` (09:54) and `base_promiscuity_full` at `bdd795d` (10:04). The only
post-outcome `analysis.py` change is D8's `hit_vectors`/`paired_hit_difference`, which is disclosed, and I confirmed
it did not disturb P1–P5. `geometry.py` (D3) was committed 10:01, before any panel result. D10's withdrawal is
complete — the claim survives nowhere as an active claim, and the withdrawal is stated in the text rather than
quietly deleted. The abandoned three-shard decoy run is traceable (`decoy_s2.log: exit -9`).

**The panel re-derives exactly** (`repanel.py`, independent of `panel.py`): rule 1 → 366/442, rule 2 → 312/366
(plan says 312), rule 3 → 304, rule 4 → **303 candidates** (plan says 303), the same per-group counts, the same
largest-remainder allocation `{AGC 3, CAMK 5, CK1 2, CMGC 4, OTHER 5, STE 5, TK 5, TKL 3}`, the identical 32
kinases *in the same order*, the identical 32 ligands, and **all 32 crops reproduce byte-identically** against the
UniProt domain annotation. Censoring: rectangle 72.85 % uncensored vs 30.36 % panel-wide (report: 72.9 / 69.6 %
censored — correct); per-ligand uncensored min 17, median 22.

**The read-out is right.** Boltz's docs and the NVIDIA NIM reference both confirm `affinity_pred_value` =
log10(IC50 in µM), lower = stronger, so `6 − value` is correct in direction and scale; the observed range
(−2.90 to +1.60 → pIC50 4.40–8.90) is sane and the strongest measured cells carry the most negative values. I also
confirmed from `boltz2.py` that the MW correction is affine with positive slope (1.035), so the plan's claim that it
cannot change any within-ligand statistic is exactly right.

**The pipeline is clean.** Three complexes verified end to end (YAML → stored boltz JSON → `pairs_panel.csv` →
analysis matrix → raw Davis pickle), 11/11 checks each, including the censored flag. 1024 YAMLs, 1024 output
directories, 1024 affinity JSONs, none duplicated, every YAML with exactly one output. `predictions.jsonl`: 1,597
rows, 1,597 unique `(arm, pair_id)`, zero duplicates, zero value conflicts. The D7 collector fix collects every
read-out exactly once; the 1,062 figure in D7 reconciles (582 + 128 + 256 + 96). The `(arm, pair_id)` dedup cannot
mix the sampling arm with the panel: they share all 96 `pair_id`s but are separated by `arm`, and `preds()` is
always called with an explicit arm.

**The estimators and the verdict.** 17/17 checks in `test_analysis.py` pass. The verdict branch fires correctly
(`lo` = 0.4182 ≥ 0.25 → Refuted), "protein-blind" is correctly *not* applied, H2's floor is met (P3 = 0.4529 ≥ 0.4),
and "the lower end of every interval sits above 0.25" is true of all five. The ligand cluster bootstrap's tight
lower bound is **genuine, not an artefact**: the per-ligand values immediately below the median are tightly packed
(ranks 12–16 span 0.420–0.441) while those above spread to 0.776. Reporting all three bootstraps, including the
much wider dyadic one, is good practice and the verdict survives the most conservative.

**The 0.0-for-a-flat-predictor convention is defensible** and does not touch the model anywhere: the model's rows
and columns always vary, so it fires only for B0, B3 and B1-on-P3. Assigning 0 (no rank information) rather than
nan is the right call — nan would make the median undefined. Its only cost is issue 11.

**The post-cutoff year query is sound.** All 11 compounds appear in **exactly one** ChEMBL document each, dated
2025, confirmed both via `activities` and independently via `compound_records`, with no NULL-year documents and no
approvals. Nothing predates 2025 by either route. The `min(year) >= 2025` subquery does identify first ChEMBL
publication. (ChEMBL 37 holds only 1,281 docs from 2025, which corroborates "the ceiling of what public
post-cutoff profiling offers".) One caveat worth a line: a 2025-published compound is typically an analogue of
pre-cutoff series, so the arm tests exact-compound rather than chemotype novelty — but the report's actual claim,
"it is not reciting Davis", is narrower than that and holds.

**Figures.** Regenerated byte-identical to the committed PNGs, so nothing is stale and the string-vs-int ligand-id
ordering bug is genuinely fixed (`figures.py` looks up `per_ligand` by position in `primary.json`'s `cids`, which I
confirmed matches `panel.json` order; my independently-built matrices reproduce `per_ligand` to 5e-7). Figures do
not read `geometry.json`, so the 04:25 D10 rewrite could not stale them. `report.html` matches `report.md` on
every key number.

**Numbers.** Every figure I recomputed matched. The decoy arm (gaps 1.1–1.3 log units, 2.0–2.4 kinome SD, 0/128
above a ligand's best kinase, 2/128 above its mean, probabilities 0.07–0.29 vs 0.44), the promiscuity union
(0.475), the sampling arm (0.979, 0.128, −0.029), the post-cutoff arm (0.543, 93 pairs, 61 kinases, 3 % censored),
the support gradient (0.147 / 0.251 / −0.041, span 91–5,205), all four geometry correlations with their permutation
p-values, the withdrawn claim's +0.081 (−0.099, +0.284) at 80 % of draws, the near-pair table, the compression
SDs (0.52/1.00, 0.76/1.19) and the variance decomposition all reproduce.

## E. On the post-cutoff number specifically

The prompt asks whether P1 = 0.543 (0.371, 0.657) is leaned on too hard. **No — this is one place the report is
appropriately careful.** It calls the arm "a check, not a replication", gives three caveats, declines to compute a
baseline rather than reporting the artefactual 1.0s, and frames the comparison as "if anything above the Davis
panel's 0.444, with intervals that overlap heavily". Eleven compounds is very few and the report says so four
times. The only additions I would make are the chemotype-novelty caveat above and the `<`-relation point (issue 17).

## F. Table of recomputed numbers

All recomputed independently of `analysis.py` from `results/tables/pairs_panel.csv`, the raw Davis pickle and
UniProt. "report" is the value in `report.md`.

| quantity | report | recomputed | verdict |
| --- | --- | --- | --- |
| P1 median within-ligand ρ | 0.444 (0.418–0.532) | 0.4435 (0.4182, 0.5324) | match |
| P2 uncensored only | 0.464 (0.429–0.487) | 0.4638 (0.4286, 0.4869) | match |
| P1 kinase bootstrap | 0.368–0.569 | 0.3684, 0.5689 | match |
| P1 dyadic bootstrap | 0.331–0.619 | 0.3308, 0.6191 | match |
| P1 high-confidence half | 0.537 (0.391–0.637) | 0.5366 (0.3907, 0.6369) | match (but see issue 5) |
| P1 binary probability | 0.596 (0.519–0.665) | 0.5958 (0.5188, 0.6652) | match |
| P3 median within-kinase ρ | 0.453 | 0.4529 | match |
| P4 top-1 | 0.562 | 0.5625 | match |
| P4 precision@3 | 0.375 | 0.3750 | match |
| P5 measured ligand/kinase/interaction | 25.5 / 14.6 / 59.9 % | 25.49 / 14.63 / 59.88 % | match |
| P5 predicted ligand/kinase/interaction | 53.4 / 11.4 / 35.2 % | 53.45 / 11.38 / 35.17 % | match |
| B0 ligand-only P1 | 0.000 | 0.0000 | match |
| B0 P3 | 0.489 | 0.4891 | match |
| B1 promiscuity P1 | 0.386 (0.310–0.522) | 0.3856 (0.3100, 0.5216) | match |
| B1 P3 | 0.000 | 0.0000 (no-LOO); **−1.000000** (LOO) | match; issue 12 |
| B1 top-1 / precision@3 | 0.188 / 0.229 | 0.1875 / 0.2292 | match |
| B2 neighbour P1 | 0.394 (0.268–0.503) | 0.3939 (0.2679, 0.5026) | match |
| B2 P3 / top-1 / p@3 | 0.264 / 0.312 / 0.240 | 0.2636 / 0.3125 / 0.2396 | match |
| B3 MW P1 / P3 | 0.000 / 0.061 | 0.0000 / 0.0613 | match |
| model − B1 on P1 | +0.058 (−0.071, +0.166) | +0.0579 (−0.0711, +0.1656) | match |
| model − B2 on P1 | +0.050 (−0.065, +0.195) | +0.0496 (−0.0654, +0.1946) | match |
| model − B1 top-1 | +0.375 (+0.188, +0.562) | +0.3750 (+0.1875, +0.5625) | match |
| model − B2 top-1 | +0.250 (+0.031, +0.469) | +0.2500 (+0.0312, +0.4688) | match |
| model − B1 precision@3 | +0.146 (+0.021, +0.250) | +0.1458 (+0.0208, +0.2500) | match |
| **B1 P2** | **not reported** | **0.2926** | **issue 1** |
| **B2 P2** | **not reported** | **0.2937** | **issue 1** |
| **model − B1 on P2** | **not reported** | **+0.1712 (+0.0647, +0.2917)** | **issue 1** |
| **model − B2 on P2** | **not reported** | **+0.1701 (+0.0173, +0.3460)** | **issue 1** |
| **AUC ceiling block: model vs B1** | **not reported** | **0.7332 vs 0.7331 (+0.0001)** | **issue 2** |
| **NDCG@3: model vs B1** | **not reported** | **0.6927 vs 0.4968 (+0.1959, excl. 0)** | **issue 2** |
| **concordance (uncens.): model vs B1** | **not reported** | **0.6688 vs 0.6055 (+0.0633, excl. 0)** | **issue 2** |
| **McNemar top-1 vs B1 / vs B2** | **not reported** | **p = 0.00183 / p = 0.05737** | **issue 2** |
| model worst ligand ρ, P1 | +0.029 | +0.0292 | match |
| **model worst ligand ρ, P2** | **not reported** | **−0.0944 (2 of 32 below 0)** | **issue 3** |
| **B1 worst ligand ρ, P2** | **not reported** | **−0.1008 (2 of 32 below 0)** | **issue 3** |
| B1/B2 worst, P1; ligands below 0 | −0.387 / −0.419; 2 / 3 | −0.3873 / −0.4194; 2 / 3 | match |
| ligands below 0.25 (model/B1/B2) | 3 / 7 / 11 | 3 / 7 / 11 | match |
| censored share of rectangle | 27.1 % | 27.1484 % | match |
| whole-matrix censored share | 69.6 % | 69.64 % | match |
| rectangle uncensored (plan) | 72.9 % | 72.85 % | match |
| candidate kinases | 303 | 303 | match |
| Davis↔UniProt exact matches (plan) | 312 of 366 | 312 of 366 | match |
| all 32 crops vs UniProt annotation | — | identical | match |
| median pairwise crop identity | 23 % | 23.32 % | match |
| Mantel pred–meas / pred–seq / meas–seq | 0.434 / 0.338 / 0.248 | 0.4340 / 0.3381 / 0.2484 | match |
| Mantel prob–meas | 0.520 | 0.5201 | match |
| withdrawn seq-reliance difference | +0.081 (−0.099, +0.284), 80 % | +0.0812 (−0.0988, +0.2838), 80.25 % | match |
| all-496-pair compression ratio | 0.50 | 0.5016 (ratio of medians); **0.5222 (median of ratios)** | issue 4a |
| five near pairs, median ratio | 0.57 | 0.5725 | match |
| **Spearman(identity, per-pair ratio)** | **not reported** | **−0.0682, perm p = 0.4123** | **issue 4b** |
| **per-pair ratio range** | **"halves any two"** | **0.2504–1.3187** | **issue 4c** |
| within-ligand SD pred/meas | 0.52 / 1.00 | 0.5215 / 0.9987 | match |
| whole-panel SD pred/meas | 0.76 / 1.19 | 0.7577 / 1.1857 | match |
| **Spearman(crop fraction, within-kinase ρ)** | **not reported** | **+0.389 (p = 0.028)** | **issue 5** |
| **P1, 16 least- vs most-cropped kinases** | **not reported** | **0.5235 vs 0.3886** | **issue 5** |
| **kinases retaining 0 cells at the conf. cut** | **not reported** | **6 of 32** | **issue 5** |
| **censored share, kept vs dropped half** | **not reported** | **31.6 % vs 22.7 %** | **issue 5** |
| **B1 P1 without the LOO adjustment** | **not reported** | **0.4256 (vs 0.3856 with)** | **issue 12** |
| **B0/B3 top-1 over random column orders** | **0.062** | **mean 0.1042, range 0.000–0.344** | **issue 11** |
| true top-3 set size (ties) | "chance 0.094" | mean 3.06 → chance 0.0957 | issue 15 |
| decoy gaps (4 proteins) | 1.1–1.3 log; 2.0–2.4 SD | 1.134–1.261; 2.042–2.371 | match |
| decoy probabilities / kinase | 0.07–0.29 / 0.44 | 0.0695–0.2897 / 0.4363 | match |
| decoys above a ligand's best / mean kinase | 0 / 2 of 128 | 0 / 2 | match |
| promiscuity union P1 | 0.475 (0.359–0.573) | 0.4750 (0.3586, 0.5734) | match |
| promiscuity 8-alone P1 | 0.284 (0.192–0.577) | 0.2836 (0.1919, 0.5774), **n = 16 ligands** | match; issue 13 |
| sampling: r, mean shift, ΔP1 | 0.979, 0.13, −0.029 | 0.9795, 0.1284, −0.0294 | match |
| post-cutoff P1 | 0.543 (0.371–0.657) | 0.5429 (0.3713, 0.6573) | match |
| post-cutoff pairs / kinases / censored | 93 / 61 / 3 % | 93 / 61 / 3.23 % (8.6 % both directions) | match; issue 17 |
| support gradient (ρ, conc, MAE) | 0.147 / 0.251 / −0.041 | 0.1474 / 0.2511 / −0.0407 | match |
| support range | 91–5,205 | 91–5,205 | match |
| total complexes | 1,597 "budget exactly" | 1,597; plan projected ≈ 1,624 | issue 8 |

## G. On the plain-language summary

It is well written and mostly accurate, and it correctly refuses both overstatement and false modesty in its last
two paragraphs. Three fixes follow from the issues above, all in the part most people will read:

1. "That scores 0.39 — statistically indistinguishable from the model" (l. 30) is true of P1 only. On the
   uncensored cells the model beats it by +0.17 with an interval excluding zero. Add the qualifier.
2. "The model is never actively wrong on any of the 32 compounds" (l. 33–34) does not survive the uncensored-only
   subset (2 of 32 below zero, floor −0.094, same as the baseline). Qualify it.
3. "the difference it reports between any two kinases is about half the real one, whether they are near-twins or
   unrelated" (l. 40–41) overstates issue 4: per-pair ratios run 0.25–1.32 and the near-twin comparison rests on
   five pairs with no interval. "About half on average, with no detectable dependence on how similar the two
   kinases are" is what the data support.

One more: "deliberately stupid methods" (l. 27–28) should acknowledge that the stupid method needs the complete
measured panel — it is not available to someone who has not already run the experiment.
