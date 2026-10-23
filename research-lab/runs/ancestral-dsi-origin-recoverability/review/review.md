# Independent review: `ancestral-dsi-origin-recoverability`

Reviewer: Fable, 2026-10-23. Adversarial review against `review/prompt.md`. All checks are reproducible from
`review/reviewer_checks/` (scripts, their stdout, and two JSON outputs). Nothing outside `review/` was modified.

## Verdict: **publish with edits** — the title and the limb-1 placeholder claim must change (F1), and the
## PulseNet gold labels must be disclosed with a sensitivity (F2). Neither preregistered verdict changes:
## H1 Inconclusive is right and my own placebo sweep strengthens it; H2 Refuted holds under every sensitivity I ran.

**What replicated.** The limb-1 point estimates reproduce exactly from the parsed samples (usable +2.903,
placeholder +9.133, malformed −0.007, absent −12.029 pp; placebos +17.609 and −15.749; 20,863,614 window samples) —
`reviewer_checks/rd_replicate.out`. `code/gold_cut_audit.py` re-run is byte-identical to the stored audit
(`diff` clean, 58 records) — `data/review_evidence/cut_audit_rerun.txt`. Every number I checked in `report.md` traces to
the tables (κ 0.925/0.942, 17/4 disagreements, label counts 350/110/37, strata 92/5/4 and 49/40/11, the 16 gold
countries, arm recoveries and Wilson intervals, Brier 0.75/0.43/0.42, asymmetric-error shares, D7's 147/25%/77%/73%,
the projection 60.7/30.1/9.2% with CI, D8's +1.3 points, the mirror figures, the decomposition's 9.8→24.8% and
58.9→68.7%); I recomputed the stratified projection by hand and it matches to rounding. Git provenance checks all
pass: `plan.md` 01:46 precedes `parse.py` 01:49 and the parse log 04:23; the pass-1 seal's sha256 matches
`pass1_labels.csv` today; pass 2 began 15:00, 5 h 15 m after pass 1 sealed at 09:45; `score.py` was committed 09:48
(before pass 2) and `arms.py`'s final form 15:33, with D5 (15:27) and D6 (15:33) both before the arms ran at 15:44.
The LLM budget (D6) was adequate — 500 calls, zero timeouts, zero parse failures. No sample in the window has an
empty `Owner`, so the cluster bootstrap has no degenerate cluster. The classifier's training pool (`country_class ==
usable`) and the gold set (`!= usable`) are disjoint by construction, and R497 — which D4 moved to usable — is
excluded from scoring; I found no gold-label leakage.

**My own re-labelling.** I re-labelled 40 records drawn at random (seed 20261023) blind to the study's labels
(`reviewer_checks/reviewer_labels.csv`, evidence in `data/review_evidence/blind40_evidence.txt`), then compared:
**39/40 agree, and 0 of the differences change the scoring label** (`relabel_compare.out`). The single difference is
R190 (*Ciona robusta* embryos: I read a wild-caught marine ascidian with no stated site as "not stated"; the study
read a model organism as "inapplicable"). I also read all 37 country records and all 8 judgement-call rows
individually; those reads produce F2, F3 and F4 below. On the prompt's first question: "inapplicable" is applied
*consistently between the passes*, but not on a consistent principle (F3, F4). I found no "not stated" record that is
determinable from the stored evidence.

---

### F1. High — the report's headline causal claim about placeholders is not supported by its own design

`report.md:1` (title) "the 2023 INSDC rule turned blanks into placeholders"; `report.md:12-13` "What the rule did
clearly change is the *kind* of missing value"; `report.md:120-121` "The design can say the rule produced
placeholders. It cannot pin the usable-share change to within 10 points."

I ran the study's exact specification at every month-start cutoff from 2020-06-01 to 2025-01-01 — 55 placebo dates
(`reviewer_checks/rd_replicate.py`, output `rd_replicate.json`/`.out`):

| class | jump at 2023-06-01 | placebo sd | placebo range | placebo dates with \|jump\| ≥ real |
|---|---|---|---|---|
| usable | +2.90 | 10.22 | −17.23 to +17.77 | 46 of 55 (84%) |
| placeholder | +9.13 | 5.53 | −13.72 to +10.48 | 9 of 55 (16%) |
| absent | −12.03 | 8.13 | −13.18 to +14.89 | 11 of 55 (20%) |

A placebo-calibrated test of the placeholder jump therefore gives p ≈ 0.16, not the bootstrap interval's
"+1.8 to +18.2": the design produces placeholder jumps of −13.7 and +10.5 pp at dates with no rule change, and the
sweep's shape is a smooth wave (usable swinging +17.8 in mid-2021 to −17.2 in mid-2022 and back), which is the
signature of local-linear fitting over strong curvature and composition shifts, not of discrete events. Three
further strands point the same way, two of them the study's own: (i) `rd_posthoc.json` gives a *significant*
within-owner placeholder rise at the 2022 placebo (+4.09, 2.63 to 7.49) and a significant usable rise at the 2021
placebo (+14.36, 1.09 to 23.15); (ii) `rd_secondary.json`'s yearly shares are a smooth monotone trend (absent
41%→0.9%, placeholder 5.5%→36% over 2019–2025), so a "jump" appears wherever the window is centred; (iii) the mirror
check shows **304 of 829 (37%) BioSample placeholders are plain blanks in ENA** while all 806 BioSample-absent
records are absent in ENA too (`reviewer_checks/mirror_crosstab.out`) — so the placeholder/absent distinction, the
entire substance of the claim, is itself one-sidedly mirror-dependent. `report.md:191` concludes "The usable-country
results do not depend on which mirror is read", which is true but sidesteps that the headline claim does.

The report applies a falsification test to the usable share, finds it fails, and correctly declines a causal reading
— then asserts a 9-pp placeholder effect from the same series without applying the same test. **Fix:** retitle
(e.g. "…the 2023 INSDC rule left the usable-country share unresolved, and most untagged samples have no origin to
recover"); replace "clearly change" and "The design can say the rule produced placeholders" with the
placebo-calibrated statement (largest at the real cutoff, but within the design's own placebo spread); report the
placebo sd beside every bootstrap CI. The descriptive statement — that post-rule records carry placeholders where
earlier ones were blank — is well supported and can stay, as a description, not as an effect of the rule.

### F2. High — the PulseNet gold labels use evidence the plan excludes, and the one non-zero preregistered recovery depends on a single such label

`plan.md:68` "The submitter's institution is **not** evidence of origin"; `plan.md:72-73` the fixed adjudication rule
gives a country only where there is "an explicit sampling-site statement".

For R240, R241, R242, R243, R244 and R475 the only origin cue in the whole evidence is a US state postal code in
`collected_by`/`sequenced_by` (NJ, GA, NY, GA, MA, MN) plus the programme name "PulseNet"; the only literal "USA" in
the text is a substring inside the PulseNet strain identifiers themselves, and the only country *words* are
reagent-supplier addresses in the methods — which is exactly why the gazetteer answered "Germany", a supplier's
city, on all five. R477's "China" comes from a named provincial CDC in `collected_by`; pass 2 flagged it itself as
"JUDGEMENT CALL … (collector field; no site field)". Under the plan's own rule all seven are "not stated". (The
other five USA records are fine: R470/R472/R473/R474 name PulseNet USA surveillance in the BioProject description
and R496 carries a `geo_location` value that resolves to the USA.)
Evidence dumps (record and publication text, kept out of git): `data/review_evidence/gold_sensitivity.out`.

Consequences (`reviewer_checks/gold_sensitivity.json`, `tuning_fragility.out`):

- **R475 alone decides the classifier arm.** It is one of only two tuning records above the tuned threshold
  (0.9712; the other is R425/China). Relabel R475 and no threshold reaches 90% precision, so the classifier makes
  no test calls: the preregistered row becomes **0% / 0% / 0%** instead of 0% / 1.7% / 0%. The reported "1.7%
  (0.7–3.8%), precision 100%" rests on one label inferred from a state postal code.
- Relabelling all seven: gold countries 37→30; test ceiling 24/300→21/300 (8.0%→7.0%); projected country share
  9.2%→**8.1%** (5.3–10.9%); D7's LLM precision 77% (61–88) → **71% (55–84)**, test-natural 83%→78%.
- H2 stays Refuted throughout (recovery upper bounds 1.3–3.8% ≪ 40%), and more firmly.

**Fix:** either (a) state plainly that collector/centre fields were admitted as origin evidence — a deviation from
plan §3 — and publish the sensitivity above, including the "all three arms recover 0%" variant; or (b) relabel the
seven and rerun `score.py score`, `posthoc_natural.py`, `decomposition.py limb2` and the figures.

### F3. Medium — "inapplicable" tracks evidence availability, so "61% laboratory material" is not the category the report describes

`report.md:26-27` "61% are laboratory material (lab mice, cell lines, reference strains, cultivars), for which a
collection country does not apply"; `report.md:43-44` "laboratory animals, cell lines or lab strains, which have no
country of origin in the relevant sense".

Lab-propagated organisms receive a country whenever their source happens to be stated, and "inapplicable" when it is
not: R450 (*Arabidopsis halleri* lab stock, own country field `missing: lab stock`, whose comment names a Japanese
river as the stock's origin) → Japan; R234 (cold-acclimated *D. ananassae* isofemale lines, whose paper names the
Thai city the source population was collected from) → Thailand; while R317 (soybean cultivar), R335 (wheat cultivar), R457
(Dendrobium hybrid cultivar), R341, R371, R456, R460, R466 (breeding/mapping populations) → inapplicable.
`data/review_evidence/construct_check.out` lists 21 of the 350 "inapplicable" records whose own recorded basis is field,
agricultural or genebank material. The bulk of the category is genuine (234 of 350 are *Mus musculus*), so this is a
wording and reporting fix, not a reclassification: the category is "material whose collection origin is inapplicable
**or unstated**", and the 61%/30% split is therefore not a clean biological partition. On the prompt's construct
question: treating laboratory material as having no country does **not** make H2 unreachable by definition — the
ceiling is an empirical finding (8% of test records determinable), the plan's wording ("recovery over all 300 test
records") is applied exactly as written, and `score.py:260` implements the preregistered Refuted rule. "Refuted" is
the right tag provided the report keeps saying, as it does at `report.md:23` and `:159`, that the binding constraint
is the ceiling and not arm performance. **Fix:** rename the category in prose, and report the agricultural/genebank
count inside it.

### F4. Medium — two of the three pass-3 readings in D5 §5 contradict D5 §5's own principles

`deviations.md:85-90`. Both affected records are in the test split, so both enter the 24-record ceiling
(`data/review_evidence/construct_check.out`).

- **R054 → Spain** ("livestock sampled at a named farm facility … as a national herd survey does"). The paper's
  methods state that the work was carried out at a named Spanish animal-research facility — a maternal-diet
  experiment at a research facility, not a herd survey. D5 §5's own next sentence excludes it: "A laboratory
  animal's housing facility is not a sampling site." It is the same design as R297 (chicken diet trial),
  R414 (bass feeding trial) and R440 (sheep heat-stress trial), all labelled inapplicable in the same pass.
- **R461 → China.** The record is a USDA Plant Introduction accession (a PI number in `cultivar`) at seedling stage,
  from a BioProject assembling a lettuce germplasm collection, and its `isolation_source` names the Chinese city it
  was grown in — the grow-out site, not the accession's origin. D5 §5's third reading ("genebank accessions with no
  stated origin are 'not stated'") was applied to R449 and R451 and inverted here.
- **R001 → Czechia** (F1 crosses from stated broodstock) is defensible but strained: the sampled fish were
  hatchery-bred and aquarium-reared, and the stated site is the parents' capture site. It is harmless only because
  the hatchery and the reservoir are both in Czechia.

**Fix:** apply one principle (my reading: a controlled experiment's facility is not a sampling site, in which case
R054 and R461 are not determinable), or keep the labels and record them as judgement calls with the ceiling
sensitivity (24→22).

### F5. Medium — the comparison with the CBD's 44% is not like-for-like

`report.md:206-209`: "The CBD's traceability study found that 44% of checked untagged GenBank entries state an
origin in the linked publication. Here, 4% of publication-linked untagged *BioSamples* do." The 9/250 behind that
4% includes the five R240–R244 records whose country came from `collected_by` state codes, not from any publication.
The like-for-like quantity — origin stated in the linked publication — is **4/250 = 1.6%** (R001, R054, R129, R234).
This sharpens the report's own conclusion, but as written the figure does not measure what the sentence says.

### F6. Medium — the plain-terms section misstates the lab-material share

`report.md:42-44` "Seven in ten of the samples without a country were laboratory animals…". Seven in ten is the
unweighted gold-set share (350/497); the population-weighted estimate used everywhere else, including
`report.md:26`, is 60.7% (56.1–65.3%). The plain-terms sentence is about the untagged population, so it should read
"six in ten". While there: the same section says the language model "found most of those" without noting that at the
preregistered threshold it makes no calls at all — worth one clause.

### F7. Low-medium — a second country-bearing attribute variant was missed, and part of the "findable" bucket is "already recorded under another field name"

`deviations.md:42-43` (D3 §2) discloses 2,190 window samples carrying a country only under the ENA attribute
"geographic location, country and/or sea". I reproduce that count exactly, and find a **further 4,445** untagged
window samples whose `geo_location=` holds a resolvable country ("USA: MO", "USA: missing", …) that D3 did not count
— 6,635 in total, 0.18% of untagged window samples and 0.032% of the window
(`reviewer_checks/attr_variant_scan.py`, `attr_variant_scan.json`). Limb 1 is unaffected at that magnitude, but two
of the 37 gold countries are exactly these cases (R339 France via the ENA attribute, R496 USA via `geo_location`),
both in the test split, and R496 is one of the classifier's five correct calls. So part of the 9.2% is not
"recoverable by mining" but "already recorded in the sample, outside `geo_loc_name`". **Fix:** correct D3's count,
and say this where the 9.2% is reported (`report.md:28`, `:144`).

### F8. Low-medium — threshold tuned on two predictions; the LLM arm's raw answers were not retained

`score.py:150-159`: `tune()` returns the lowest threshold reaching 90% precision with no minimum support, so the
classifier's 0.9712 comes from two tuning calls at precision 1.0. That is `plan.md:86` applied as written and the
Wilson bound (57%) is honestly reported, so no verdict is affected — but it is the mechanism behind F2's fragility
(`reviewer_checks/arms_tuning_check.out` prints the full precision-by-threshold curves: the gazetteer never exceeds
10% and the LLM never exceeds 45% on tuning, so both are zeroed out).

Separately, `arms.py:191` stores only `insdc(...)`'s resolved name, so an answer naming a place outside the INSDC
vocabulary is indistinguishable from "unknown": two records (R357, and **R401, a test record whose gold is Pacific
Ocean**) carry `llm=null` with `llm_conf=0.99` — the model answered confidently and the answer was discarded
(`reviewer_checks/pass1_limit_check.out`). The raw text was not kept, so the 450 "unknown" answers cannot be
separated from unresolvable ones. The direction understates the LLM's recall. **Fix:** report the two dropped
answers; keep raw outputs in future runs.

### F9. Low — H1's preregistered rule is one-sided, and the sign of the headline estimate comes from extrapolation

`plan.md:46-49`: Supported if the interval's *upper* bound is below 10 pp. A large decrease therefore reads as
"Supported" — the January-2025 cutoff estimate (−11.7, −22.9 to +2.4) would qualify. Execution is correct and
Inconclusive is the right call, but the rule does not test what H1's prose says. Worth pairing with a fact the
report omits: the raw usable share *fell* across the cutoff (85.3% → 79.4%, `rd_primary.json`), so the +2.9 pp
estimate is entirely the local-linear extrapolation's.

### F10. Low — frame mismatch between the gold draw and the projection population (no action needed)

The gold set was drawn at 09:33 from the pre-D4 classification and without D3's human-host filter, while
`population()` (`score.py:173-190`) counts the post-D3/D4 untagged population. Removing the three affected drawn
records is the right first-order correction and the magnitudes are small (D4 moved 10,183 of 34.3M samples; D3
excluded 180,191, 0.86%), so the projection is affected well below one point. The stratum definitions do match
between `goldset.py` and `population()` (first BioProject, non-empty `pubmed_ids`), and I verified the projection
arithmetic and intervals independently. Worth one sentence in the limits.

---

## On the prompt's specific questions

1. **Gold labels.** 39/40 blind agreement, no scoring-label differences; the pass-2 display cut (D5 §6) is audited
   convincingly — my re-run is byte-identical, all 56 non-escalated records were records the two passes *agreed* on,
   and I verified independently that pass 1's own reading aid hid nothing: **0 of 500** records have a location value
   past the aid's 500-char attribute / 300-char comment limits (`pass1_limit_check.out`), which is what D5 §2 claims.
   Consistency problems are F3 and F4, not pass-to-pass noise.
2. **The construct.** Defensible and not self-fulfilling; the ceiling is empirical and "Refuted" is the preregistered
   rule correctly applied to the plan's wording. The category label overstates (F3).
3. **Arms.** No gold-label leakage; the classifier's training pool is disjoint from the gold set. Institution text
   *is* inside the evidence for 108 of 500 records (`insdc center name`, `collected_by`, `sequenced_by`,
   `biomaterial_provider`), which the plan said would never be evidence — but it shows no measurable inflation of
   owner-country errors (classifier: 6/10 of such errors name the owner country vs 156/271 elsewhere, on the D10
   labels; 4/8 vs 156/271 as first adjudicated,
   `leakage_check.out`). The damage is to the gold labels, not the arms (F2). LLM budget fair (F8 caveat).
   Thresholds computed as the plan says (F8).
4. **Limb 1.** Replicated exactly. Kernel, donut, owner clustering and the multinomial cluster bootstrap are all
   implemented as preregistered, and there is no degenerate owner cluster. The placebos do mean the design cannot
   support a causal reading **of either class** — including placeholders, which is F1.
5. **Projection.** Arithmetic, weights and intervals verified. Wording needs F2, F6 and F7.
6. **D5 display truncation.** Convincing; re-run reproduces byte-for-byte, and I verified the pass-1 premise it rests
   on.
7. **The report.** Every table number checks out; the errors are the title and `:12-13`/`:120-121` (F1), the 4%
   comparison (F5), and "seven in ten" (F6).
