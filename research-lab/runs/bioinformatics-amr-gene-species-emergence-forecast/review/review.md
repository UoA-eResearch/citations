# Independent review — bioinformatics-amr-gene-species-emergence-forecast

Reviewer: independent adversarial review (Fable), 2026-11-03. Read-only on the study; my scripts, outputs and logs
are in `review/reviewer_checks/`.

## Verdict: **fix first**

The study's substantive conclusion survives everything I threw at it: under the preregistered first-appearance
rule, neither model places a single emerging pair in its top 100 at any of six random seeds, while a correctly
computed sampling-effort null reaches 0.07–0.10, and a null built only from pre-cutoff effort does nearly as well
(0.06), so the baseline is not smuggling in foreknowledge. The data build reproduces exactly, the three plausibility
traces re-trace to the digit, the primary and secondary tables reproduce bit-for-bit from the committed code, and
the preregistration demonstrably precedes the first download.

What cannot be published as written is the mechanics around that conclusion. Four of the report's load-bearing
numbers are artefacts of implementation choices rather than of the model: the null's 0.08 is decided by the order
rows happen to sit in the candidate table (F1); the model's 0.00 is one draw of a statistic that ranges 0.00–0.19
over seeds (F2); the "embedding breaks the model" diagnosis reverses sign at six of eight seeds (F3); and the
"83% were already observed" diagnosis halves to 40% once the deposit dates already present in the metadata are
used (F6). Two reported labels do not follow their own rules: H1 flips to Inconclusive if the 22 discarded
bootstrap draws that favour the model are reinstated (F5), and H2's preregistered rule as written in plan.md gives
Inconclusive, not Refuted (F4). Fixing F1–F3 and F5–F6 is a few hours of compute and a rewrite of the verdict
block and plain-terms section; none of it requires new data.

---

## 1. The null's precision@100 — the comparator in the title, verdict and plain terms — is set by row order, not by the null. Severity: major

As coded, `1 − Binomial(≤1; n, f)` reaches exactly 1.0 in float for **4,727 of 472,779 candidates**, and the whole
top 1,000 of the null's ranking holds **one distinct score** (`check_null_ties.json`, `check_nulls_boot.json`).
`analyse.py:47-49` ranks with a stable argsort, so "the null's top 100" is the first 100 rows of that tie block;
because `candidates.py:82` emits rows species by species in alphabetical order, all 100 are *Acinetobacter
baumannii*, which happens to hold 8 positives → the reported 0.08.

- The tie block's own base rate is 132/4,727 = 2.8%. Under random tie order the null's precision@100 is **0.028
  (95% 0.00–0.06)**, and 5.9% of orderings give 0.00. The reported 0.08 sits above the upper tail.
- The same holds for the variant: 4,191 tied at 1.0, reported 0.10, random-order 0.039 (0.01–0.08).
- The bootstrap confirms it: across 2,000 gene resamples (which reshuffle row order) the null's precision@100 has
  mean **0.0279** and is 0.00 in 10.5% of draws (`check_nulls_boot.json`). The reported point estimate and the
  interval built around it are therefore not the same statistic.
- Corroboration from the study's own tables: `secondary.json` gives the `effort_only` **model** — trained on the
  three effort features, one of which is the null's own probability — a precision@100 of 0.00, where the raw null
  gets 0.08. A real effort signal would not vanish like that.

This is the row-order packaging leak that the lab's G1 exists to catch, and it decides the headline comparator.

**Fix** (cheap, and it does not change H1's direction): rank the null by a non-saturating monotone transform of the
same probability. Computing log P(≤1 carrier) in log space gives 988 distinct scores in the top 1,000, a sensible
top-100 mix (*Salmonella enterica* 29, *Campylobacter jejuni* 29, *E. coli* 9), **precision@100 = 0.07**,
precision@500 = 0.06, AP = 0.021 (above the as-coded null's 0.0153 — saturation costs the null ranking information
too), and a bootstrap mean of 0.068 (0.03–0.11) with no zero draws. Expected carriers (n·f) gives 0.06. Report that
number, and recompute the derived claims: the lift over the base rate becomes 39-fold, not 44-fold, and the full
model's AP advantage becomes 3.7x, not 5x.

## 2. The model's 0.00 is a property of one fit, not of the model. Severity: major

Refitting the preregistered feature set with the chosen hyperparameters at eight `random_state` values
(`seed_sweep.json`) gives precision@100 of **0.00, 0.19, 0.10, 0.18, 0.19, 0.12, 0.17, 0.12** — mean 0.134. The
preregistered seed is the only zero and the minimum of the eight. (`HistGradientBoosting` subsamples 200k of the
386k training rows to pick bin thresholds, so the seed changes the binning, and the top 100 of this list sits inside
a near-saturated score region where tiny logit differences decide the order.)

Consequences:
- "Not one of the model's 100 most confident predictions emerged" is a one-draw statement presented as a model
  property.
- Against the null's 0.08, four of the eight seeds give a ratio ≥ 2, so the H1 **label** is seed-dependent.
- The diagnosis is seed-specific too: the 118 saturated scores and the 93-of-100 concentration in *Edwardsiella
  piscicida* and *Pluralibacter gergoviae* hold at the preregistered seed only. Other seeds give 1 to 139 saturated
  candidates and completely different top-100 species (*S. aureus*, *Klebsiella planticola*, *Vibrio cholerae*,
  *Klebsiella terrigena*).

**Fix:** report precision@100 as a seed ensemble (mean and range) alongside the preregistered seed's value, and say
plainly that the preregistered statistic is one draw from that spread. Answering the brief's question directly:
precision@100 on 472,779 candidates with 847 positives is **not** a stable statistic for a single fit here, and the
report should treat p@500 and AP (which move much less: 0.11–0.17 and 0.075–0.090) as the informative ones.

## 3. "The embedding is what breaks the model" is not established. Severity: major

Three checks contradict it:
- **Seeds.** Full-model p@100 spans 0.00–0.19 (mean 0.134); no-embedding spans 0.06–0.23 (mean 0.163). The reported
  0.00-vs-0.18 gap is the extreme of both distributions, not a typical difference.
- **Sign reversal on the H2 statistic.** AP(full) − AP(no embedding) by seed: −0.0046, +0.0070, +0.0146, +0.0064,
  +0.0056, +0.0036, +0.0025, −0.0004. The embedding **adds** average precision at six of eight seeds (mean
  +0.0043), and the preregistered seed is the most negative of the eight.
- **The ablation is not specific.** `secondary.json` shows `no_taxonomy` — which *keeps* the embedding — also
  recovers the top of the list (0.16). "Remove a feature family and precision@100 jumps" is a property of this
  unstable statistic, not of the embedding.

The mechanism the report describes is real and I verified it (median nearest-neighbour cosine 0.9706 across
candidates, 0.9953 among positives, `check_labels.json`) — but a near-saturated feature cannot be shown to "break"
a model by an ablation whose effect is smaller than fit noise and reproducible by ablating something else.

**Fix:** delete the three sentences that assert the embedding causes the failure (the verdict block's claim that it
breaks the model, and the plain-terms claims that one ingredient actively hurt and that dropping it turned the model
from worse than the baseline to better). Keep the saturation measurement as a plausible
mechanism, labelled as a conjecture, and report the seed spread for both arms. H2 then reads: the embedding's effect
on average precision is within fit noise, direction unresolved.

## 4. H2's label does not follow the preregistered rule. Severity: moderate

plan.md:57-58 sets three outcomes: Supported when the interval sits above zero; **Refuted when it sits below zero
or lies entirely inside a band of ±0.005 around zero**; Inconclusive otherwise. The interval is −0.0128 to +0.0009. It does not lie above 0, does not lie below 0, and does
not lie within ±0.005 of 0 (it reaches −0.0128). By the written rule the label is **Inconclusive**.
`analyse.py:101` instead refutes whenever the upper bound alone falls below +0.005, a different and easier test,
and `deviations.md` does not record the substitution. The report therefore states a stronger negative than the
preregistration licenses — and with F3, Inconclusive is also the substantively right label.

**Fix:** either relabel H2 Inconclusive, or add a D-entry that states the rule was reinterpreted as a test for the
absence of a meaningful positive effect, explains why, and reports both labels. The former is cleaner.

## 5. The bootstrap discards 22 draws that favour the model, and reinstating them moves H1 to the decision threshold. Severity: moderate

`primary.json` reports 210 of 2,000 draws undefined. I reproduced the resampling (`boot_undefined.json`): **188 are
genuinely uninformative** (null and model both scored 0, ratio 0/0) and **22 have the model scoring above 0 while
the null scored 0** — i.e. ratio +∞, the draws most favourable to the model. `analyse.py:82` drops all 210 via
`nanpercentile`, giving the reported interval 0.00–1.27. Dropping only the 188 uninformative draws and keeping the
22 as +∞ gives **0.00–2.00**, and the preregistered rule refutes only when the upper bound falls below 2. It does not,
so H1 becomes **Inconclusive**. 2.98% of the kept draws have a ratio ≥ 2, just over the 2.5% the upper percentile
tracks: the Refuted label rests on the convention for the discarded draws, not on the data.

Two further honesty points about this interval: with the null's denominator being a tie-order lottery (F1), most of
its width is implementation noise rather than gene-sampling uncertainty; and the paired H2 interval resamples genes
around a *single pair of fits*, so it cannot see the fit noise that F3 shows dominates.

**Fix:** state the composition of the undefined draws, report the interval under both conventions, and set H1's
label from the convention declared in advance — or, since neither convention supports a clean "Refuted", report H1
as Inconclusive on the primary rule and let the first-appearance variant (where every seed gives 0.00 against a null
of 0.10) carry the negative conclusion. That is the robust result and it deserves the weight.

## 6. The 2022 cutoff is not the information frontier: the metadata's deposit dates were never audited, and using them halves the report's central diagnosis. Severity: moderate

The downloaded metadata carries `target_creation_date` and `sra_release_date`. Neither appears in `build.py`, in the
feature code, or in the plan's G1 audit; everything is dated by `collection_date` alone. Measured over the kept
corpus (`check_hindsight.json`):

- **498,031 of the 1,271,989 isolates collected by 2022 (39%) were only deposited after 2022.** The features,
  frequencies, co-occurrence matrix and candidate exclusions at the "2022 cutoff" therefore use a third more data
  than existed then, so the evaluation is retrospective-with-hindsight rather than the strictly prospective,
  calendar-time evaluation the report presents as its contribution.
- The report's central label diagnosis does not survive the correction. Of the **705** positives it calls "already
  observed at least once before 2023", only **341 had a pre-2023-collected carrier that was actually deposited by
  the end of 2022**; the other 364 were invisible at the cutoff. So a forecaster standing at the end of 2022 would
  have seen 341 of 847 positives (40%) as already-observed pairs, not 705 of 847 (83%), and 506 would have looked
  like genuine first appearances. The claim that the two-BioProject rule turns most emergences into confirmations
  is roughly half as strong as stated.
- The same issue cuts into the variant: pairs whose first carrier was collected before 2022 but deposited later are
  excluded from the variant's candidate set although a real-time forecaster would have had them as candidates.

G1 is incomplete in two further ways worth naming: it does not mention row order (F1), which the lab's own G1 text
names as the canonical packaging leak; and it does not address the overlap of units across splits that METHODS G1
explicitly asks about — 384,730 of the 472,779 test candidates (81%) are the same (gene, species) pairs the model
trained on (`posthoc.json`). The post hoc carried-over split partly covers this and is a good check; it belongs in
the audit, not only in the diagnosis.

**Fix:** recut features and labels on `min(collection year, deposit year)` — the column is already downloaded — or,
if that is out of scope, report the 39% and the 341-vs-705 figures, correct the "83% are confirmations" sentence
wherever it appears (report.md verdict block, plausibility.md, overclaim row 19), and add deposit lag to the limits
and to G1.

## 7. A preregistered sensitivity and four preregistered secondary analyses were never run, and nothing records that. Severity: moderate

- `deviations.md:24` promises that the genes D1 excludes are reported and that a sensitivity keeps them.
  `candidates.py:23` carries the `KEEP_ALL_GENES` switch, but no such task table, result or gene list exists
  anywhere in `results/` or `data/`. The D1 restriction is the one design choice made after looking at outcome data
  (see F11), so its sensitivity is the one most worth having.
- plan.md:76-82 promised four more secondary analyses that are absent from code, tables and report: the
  **at-least-three-isolates** outcome variant, **gene × country** first appearances, **recall at matched list
  sizes**, and the **Europe PMC literature check** of the top 20 hits. `deviations.md` records no decision to drop
  them. The ≥3 variant matters most: it is the rule that would separate "a confirmation" from "an outbreak clone",
  which is precisely the tension the report is about.

**Fix:** run the D1 sensitivity and the ≥3 variant (both are one command each), or add a D-entry that drops the
others explicitly and says why.

## 8. G4 is missing; what the report calls G4 is G3's work. Severity: minor

plan.md:104-105 promised a check of 30 random first-observation dates and BioProjects recomputed from the raw metadata
by an independent script. No such script or output exists, and report.md:143-145 relabels the three plausibility traces
as G4. METHODS G4 also asks that every validation metric come with an error audit on a judgeable denominator; for
precision@100 = 0.00 that audit is one query, and I ran it (`check_labels.json`): all 100 of the model's top
predictions are pairs **never observed in the corpus at any date** — none is an artefact of the outcome rule, none
is an 'any'-rule positive that the two-BioProject rule hid, so the metric as measured (0.00) equals the metric on
the judgeable denominator (0.00, denominator 100). That is a clean result that strengthens the paper; its absence
left the obvious "were the top 100 really wrong?" question unanswered.

## 9. G3's promised null calibration is missing, and it points straight at F1. Severity: minor

plan.md:102-103 lists the null's calibration under G3; `plausibility.md` calibrates nothing (the decile table in
`secondary.json` is the model's). Computed (`check_traces.json`): the null's top decile has mean predicted
probability **0.467 against an observed emergence rate of 0.0112**, a 42-fold overprediction, and its top 1,000
scores hold one distinct value. The planned check would have exposed the saturation before the headline was written.

G3's other duties are sound. I re-traced all three pairs from `isolates.parquet` and every figure in the table
matches (genus counts 14/0/2, Jaccard 0.44/0.98/0.83, frequencies 0.002/0.200/0.200, horizon isolates 20/738/47,
carriers and BioProjects as described), including the honest observation that two of the three reach two BioProjects
only because of a pre-2023 isolate — one of them a pair carried by 15 isolates in 2016–2018.

## 10. G2: a silent zero fallback, a double-counted denominator, no Coverage line. Severity: minor

- `candidates.py:76-77` substitutes a zero vector for any gene without an ESM-2 embedding, so `emb_cos_max` becomes
  0 — a silent default entering the H2 statistic, which METHODS G2 forbids. It affects one gene (dfrA51), 156 test
  rows and 2 positives (`check_emb_fallback.json`), so the effect is negligible, but it is unrecorded in
  `coverage.json` and should be either a declared fallback or a drop.
- `coverage.json`'s `attempted` (2,943,943) exceeds the rows actually read (2,943,808) because "no species binomial"
  and "no collection year" both count the 135 rows that fail both (`check_build.json`). The drop categories do not
  partition the input.
- METHODS G2 requires the report to carry a Coverage line; report.md names the file but prints no line. The line is
  available from `tools/coverage.py`.

Otherwise G2 is in good order, and one worry I checked out clean: all 106 group files do carry the
`AMR_genotypes_core` column, so the 721,790 "no AMR call field" drops are genuinely per-isolate missing values, not
whole organism groups lost to a header difference.

## 11. D1 was decided using test-period labels. Severity: minor

`deviations.md:14-16` justifies the catalog restriction with the enrichment of late-catalogued genes among
**2023–2025 emergent pairs** (8.5% against 3.1%) — outcome data that the plan's leakage audit (plan.md:86) reserves, promising that no horizon-period
record reaches training or model choice. The restriction is conservative and small (I verified 4,250 of 4,417 symbols and
1,116 of 1,160 emergent pairs are kept), so the harm is minor, but the peek should be named in D1 and in the G1
audit, and it is a second reason the missing sensitivity (F7) matters.

## 12. One plausibility number does not reproduce; everything else does. Severity: minor

`plausibility.md` compares 349,205 dated isolates in 2023–2025 with **416,410** in 2020–2022. The kept table holds
**386,839** for 2020–2022 (349,205 for 2023–2025 is exact); raw rows in that window are 586,875, and rows with a
species and an AMR field are 386,843 (`check_2020_count.json`, `check_numbers.json`). I cannot reconstruct 416,410.
The comparison's direction survives either way.

Everything else I checked reproduces exactly, including by rerunning the pipeline's own fits
(`refit.json` matches `primary.json` and `secondary.json` to the last digit): 1,621,194 isolates / 264 species /
4,417 symbols / 19,436 observed pairs; 472,779 candidates with 847 positives and 386,001 with 1,271; p@100
0.00/0.08; AP 0.076283/0.080920, difference −0.004637 (−0.0128 to +0.0009); p@500 0.126/0.040; ablations
0.00/0.16/0.00/0.18; 118 scores above 0.999; 989 distinct scores in the top 1,000; top-100 median 24 horizon
isolates against 414 for emergent pairs; 93 of 100 in two species; cosine 0.9706/0.9953; 705 of 847 and 979 of
1,271 already observed, median 2019; D1 keeping 4,250/4,417 and 1,116/1,160; drops of 598,704 and 721,790;
within-period 0.06; carried-over 0.00 and newly-eligible 0.07; variant 0.00/0.00 against 0.10.

---

## Answers to the brief's specific questions

- **The two-BioProject rule (brief 1).** Not defensible as "emergence", and the study says so — but for a different
  reason than it thinks. By collection date 83% of its positives were seen before; by what was actually public at
  the cutoff, 40% were (F6). Either way the rule measures confirmation, not first appearance. The variant is
  handled honestly: it was preregistered, it is reported, and the verdict block concedes that the no-embedding
  repair dies under it. Given F2 and F5, the variant is also the only leg of the argument that is stable, so it
  should be promoted to carry the conclusion, with the primary rule reported as the preregistered-but-fragile
  statistic.
- **The null (brief 2).** The functional form is defensible but the implementation is not (F1); fix the saturation
  and it becomes a well-defined 0.07. Handing both sides the realised horizon count does **not** hand the null the
  answer: a null that uses only pre-cutoff effort scores 0.06 against the realised-effort null's 0.07
  (`check_cutoff_null.json`), so the baseline encodes surveillance intensity in general, not foreknowledge of the
  horizon. A stronger null (expected carriers, 0.06) and a weaker one (isolate count alone, 0.02) both leave H1's
  direction unchanged at the preregistered seed.
- **The candidate set (brief 3).** The ≥20-isolate and gene-established rules are reasonable and their cost is
  reported honestly in `coverage.json` (269 of 1,116 emergent pairs, 24%, fall outside the test candidate set). D1
  does little analytic work — 97.9% of symbols and 96% of emergent pairs survive it — but it was chosen with a look
  at outcome data (F11) and its promised sensitivity was never run (F7).
- **The model (brief 4).** Features and cutoffs are respected as the plan describes, with the deposit-date caveat
  (F6) and the unaudited 81% unit overlap across splits. Hyperparameter selection by gene-grouped CV inside the
  training task is sound and all three ablation arms select the same setting, so the report's "selection noise"
  caveat is more conservative than needed — the real instability is the random seed (F2). precision@100 is not a
  stable statistic here for a single fit.
- **The embedding diagnosis (brief 5).** Not established; it is an artefact of one ablation at one seed, as F3
  shows. The saturation measurement itself is correct, and the top-100 characterisation is correct for that fit.
- **Inference (brief 6).** The gene bootstrap is the right idea, but as reported it is not honest about the
  discarded draws (F5), it mixes tie-order noise into the null's denominator (F1), and it cannot see the fit noise
  that dominates both headline comparisons (F2, F3).
- **G7.** Confirmed not applicable: no unit in this study is labelled by an agent or a person. (The one planned
  agent-adjacent step, the Europe PMC check, was not run — F7.)
- **G6.** `tools/attribution.py check` passes (5 claims). I verified both DOIs by title, not just resolution:
  10.1038/s41598-021-91456-0 is the Feldgarden et al. 2021 AMRFinderPlus / Reference Gene Catalog paper in
  *Scientific Reports*, and 10.1038/s41467-021-22757-1 is Ellabaan et al. 2021 on forecasting resistance-gene
  dissemination in *Nature Communications*; both support the claims made of them, and A2's recorded condition
  (retrospective, static snapshots) is accurate — that paper confirms 34 of 94 predicted mobilisations in a separate
  genome collection. One gap: the NCBI taxonomy dump supplies the genus and family features and appears in the
  report's data line but has no ledger row.
- **Git (brief).** Verified. plan.md was committed at 2026-10-28 17:57:57 (f076a49) and the first metadata file
  landed at 18:00:21 — two and a half minutes later. The pipeline including `analyse.py` was committed at 22:52:08
  (95520db); the first candidate table was written at 2026-10-29 00:16. The only post-run change to `analyse.py` is
  a comment renaming D1 to D2 (`git diff 95520db`), with no change to any computation; `candidates.py` gained the
  D1 catalog filter and the RULE switch, the latter defaulting to the primary rule.

## G5 re-labels

`review/overclaim_check.md` is complete in form and its backings point to real numbers, but it labels 11 sentences
Supported that a reader cannot rely on. Re-labelled:

| row | sentence (abbreviated) | my label | why |
|---|---|---|---|
| 1 | title: nothing forecasts better than sequencing effort | Partially supported | True and robust under the first-appearance rule; under the primary rule the model averages 0.134 against a correctly computed null of 0.07 (F1, F2) |
| 7, 8 | precision@100 is 0.00 / not one of the top 100 emerged | Partially supported | One fit; 0.00–0.19 over eight seeds, preregistered seed the minimum (F2) |
| 9 | ratio interval 0.00–1.27 | Partially supported | 22 of the 210 discarded draws favour the model; reinstating them gives 0.00–2.00 (F5) |
| 10 | the null is strong: 44-fold lift | Partially supported | 0.08 is a row-order slice of a 4,727-way tie; tie-free value 0.07, 39-fold, and the bootstrap's own central value is 0.028 (F1) |
| 12, 13 | H2 Refuted; AP difference −0.005 | Partially supported | Point values correct for that fit; sign reverses at six of eight seeds, and the preregistered rule as written gives Inconclusive (F3, F4) |
| 14, 15 | the embedding does not merely fail to help; it is what breaks the model | **Overstated** | Within fit noise, and reproducible by ablating taxonomy instead (F3) |
| 19, 20 | 705 of 847 (83%) were already observed; they are confirmations | **Overstated** | 341 of 847 (40%) were observable at the cutoff; 364 of the 705 were deposited later (F6) |
| 26 | the simple calculation got one in ten | Partially supported | Tie-order artefact; 0.039 under random order in the variant (F1) |
| 27 | one ingredient actively hurt | **Overstated** | Same as 14/15 |
| 29 | it predicted in barely-sequenced species | Partially supported | True of the preregistered fit; other seeds nominate heavily-sequenced species (F2) |
| 30 | dropping it turned the model from worse than the baseline to better | **Overstated** | Same as 14/15 |

Rows 2–6, 11, 16–18, 21–25, 28 and 31 I agree with as labelled. Row 23's recorded fix (dropping an unverified
superlative) is the right call.

## What to do

1. Fix the null's saturation and recompute every null-derived number (F1).
2. Report both headline precision@100 figures as seed ensembles, and state the preregistered values as single draws
   (F2, F3).
3. Relabel H2 Inconclusive, or record the rule substitution as a deviation (F4); report the undefined-draw
   composition and H1 under both conventions (F5).
4. Correct the "83% are confirmations" diagnosis using the deposit dates, and add deposit lag to G1 and the limits
   (F6).
5. Run the D1 sensitivity and the ≥3-isolate variant, or record their abandonment (F7).
6. Supply G4 (the 30-unit audit, plus the top-100 error audit I computed above), the null calibration under G3, the
   Coverage line, and the coverage fix for the zero-vector fallback (F8–F10).
7. Rewrite the verdict block and plain-terms section around the first-appearance result, which is what the evidence
   supports.

## In plain terms

The study's answer is probably right: nothing it tried can say which resistance gene will show up in which new
species next, better than just knowing where people are sequencing most. That part held up under every re-run I
did.

But the numbers it uses to tell that story are shakier than the write-up admits. The "simple calculation" it
compares against scores well only because of the order the rows happened to be stored in; computed properly it is
a slightly different number that happens to be close. The model's famous zero — none of its hundred best guesses
came true — is one roll of the dice: re-running the same model with a different random start gets between ten and
nineteen right, and the version the plan locked in was the worst of eight. The claim that the protein language
model is what broke the model does not hold: at six of eight starts that feature helps rather than hurts, and
removing a different feature instead does the same apparent good. And the striking statistic that 83% of the
"new appearances" had actually been seen before falls to about 40% once you account for the fact that many of those
earlier samples were not yet in the public database at the time the forecast was supposed to be made — a date the
study downloaded but never used.

So: keep the conclusion, rebuild the scaffolding around it, and lead with the strict definition of "first
appearance", which is the part that does not wobble.
