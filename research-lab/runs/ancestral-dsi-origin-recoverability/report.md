# Countries of origin on sequence samples: the 2023 INSDC rule left the usable-country share unresolved, and most untagged samples have no origin to recover

*Every non-human sample submitted to NCBI BioSample from June 2021 to May 2025 (20.9 million) was classified by its
country field. A regression discontinuity tested the June 2023 INSDC rule. Then a 500-record gold set tested whether
the missing countries can be recovered automatically from the sample's own record, its BioProject and its linked
publication. This version incorporates an independent review (`review/review.md`; changes logged as D10).*

**Verdict: H1 Inconclusive; H2 Refuted.**

- **H1 (the rule raised the usable-country share by less than 10 points): Inconclusive.**
  - The jump at 1 June 2023 is **+2.9 points (95% interval −5.9 to +10.8)**. The upper bound crosses the 10-point
    line.
  - Records after the rule more often carry a placeholder ("missing", "not collected" and so on) where earlier ones
    were blank: placeholders +9.1 points (+1.8 to +18.2), absent fields −12.0 (−16.0 to −8.7).
  - That shift is a trend visible across the rule, not an effect the design can attribute to it. At 55 placebo
    cutoffs, placeholder jumps have a standard deviation of 5.5 points, and 9 of 55 are as large as the real one
    (review).
  - The raw usable share actually fell across the cutoff, from 85.3% to 79.4%. The +2.9 estimate is the local-linear
    extrapolation's.
  - Within submitters active on both sides, the usable share barely moved (+0.6; −4.1 to +8.8).
  - Placebo dates a year and two years earlier show jumps of +17.6 and −15.7 points. The series swings too much for
    this design to measure a 10-point effect precisely.
- **H2 (an automatic method recovers a correct country for at least 40% of untagged samples at 90% precision):
  Refuted.**
  - Only **19 of the 300 test records (6.3%)** have a country that any evidence states, as an explicit sampling site.
    No method could reach 40%.
  - At their tuned thresholds the three methods recover 0%. The upper bounds of their intervals are 1.3%.
- **Why: most untagged samples have no origin to find.**
  - Projected to the 1.66 million untagged samples submitted from June 2023 to May 2025:
    - **61% are laboratory or cultivated material** (lab mice, cell lines, reference strains, cultivars), for which
      no collection origin applies or none is recorded;
    - **32% are natural samples whose origin no evidence states**;
    - **8% (about 127,000; 81,000 to 173,000) have a stated sampling country somewhere in the evidence.** Some of
      these already carry it, under a different field name.
  - Samples whose BioProject links a publication are 92% laboratory material.
- **Correction after review.** Nine gold labels had taken a country from a collector's address or an experimental
  facility. The plan excludes both. Relabelled, the ceiling falls from 8% to 6.3%, and the one method that had
  recovered anything (1.7%) recovers nothing (D10).

## In plain terms

When a scientist deposits a DNA sample from a plant, an animal or a microbe, the record is supposed to say which
country it came from. International rules on sharing the benefits of genetic resources depend on that: you cannot
pay a country back for a resource if nobody recorded where it came from. In 2023 the world's DNA archives made the
country field compulsory.

We checked 20.9 million sample records. Over these years, fewer records left the field blank and more wrote "missing"
or "not collected" instead, but this was a gradual trend we cannot pin on the rule. The share naming a real country did
not clearly rise.

Then we asked whether the missing countries could be filled in automatically, by reading the sample's description
and the paper it belongs to. Mostly they cannot, because there is nothing to find. Six in ten of the samples without
a country were laboratory animals, cell lines, lab strains or crop cultivars, for which no place of collection applies
or none is recorded. Most of the rest never say where they were collected, anywhere. Only about one in thirteen had a
sampling country written down somewhere else in their records. A language model found most of those when allowed to
guess, but it also guessed countries for lab samples, usually the country of the lab. Held to the 90% accuracy the
plan required, no method made any calls.

## What was asked

The lead (`ancestral-dsi-origin-recoverability`) asked two things:
- whether the INSDC's spatiotemporal metadata rule (in force 1 June 2023) put countries of origin on sequence
  samples;
- whether the origins still missing can be recovered at archive scale.

This matters for the Convention on Biological Diversity's arrangements on digital sequence information, including
the Cali Fund: traceability to a provider country starts with a country on the record. The plan (`plan.md`) was
written before the archive was parsed.

## How it was done

1. **Classification** (`parse.py`, `countries.py`). Each BioSample's `geo_loc_name` (or `country`) is:
   - **usable** if its country part resolves to an INSDC country or ocean;
   - **placeholder** if it is an INSDC missing-value term or a common equivalent;
   - **malformed** or **absent** otherwise.

   Human samples and human-host metagenomes are removed (care filter, D3). D4 fixed an apostrophe bug that had
   classed "Cote d'Ivoire" malformed (10,183 samples reclassified).
2. **Limb 1** (`analysis_rd.py`). A local-linear regression discontinuity on daily shares at 1 June 2023:
   - 24 months either side, with a one-month donut;
   - intervals from a cluster bootstrap over 43,055 submitting organisations;
   - secondaries: the 1 January 2025 extension, placebo dates, bandwidths, no donut, package fixed effects, and
     placeholder terms for inapplicable material removed;
   - post hoc (`analysis_rd_posthoc.py`): without SARS-CoV-2, and within submitters.
3. **The gold set** (`goldset.py`). 500 untagged samples from June 2023 to May 2025, half with a linked publication,
   stratified by package; 200 tuning and 300 test.
   - **Evidence:** the sample's attributes, its BioProject title and description, and for a publication its title,
     abstract and up to 12 sampling sentences from the open-access full text.
   - **Never evidence:** submitter institutions.
4. **Labels.** Each record is a country, **inapplicable** (laboratory material) or **not stated** (D2).
   - Two blind passes by the study's AI agent, more than five hours apart, each in its own shuffled order.
   - A blind third pass on the disagreements, under the plan's fixed rule (D5).
   - Three records are excluded by code: two human-host metagenomes, and one whose own country field resolves after
     D4. That leaves 497.
5. **Recovery arms** (`arms.py`), run only after all labels were fixed:
   - a GeoNames gazetteer with reverse geocoding of coordinates;
   - a TF-IDF classifier trained on 196,561 tagged samples from the same period;
   - the locally served open-weight LLM (Nemotron 3 Nano Omni), asked for the collection country or "unknown", with
     its stated probability as confidence (D6: output budget raised before running).

   Each arm's threshold is the lowest giving 90% precision on the tuning split. A call on a record without a
   determinable country counts as wrong.

## Results

### Limb 1: what the rule changed (`results/figures/F1_monthly_shares.png`)

| class | jump at 1 June 2023 (points) | 95% interval |
|---|---|---|
| usable country | +2.9 | −5.9 to +10.8 |
| placeholder | +9.1 | +1.8 to +18.2 |
| absent | −12.0 | −16.0 to −8.7 |
| malformed | −0.0 | −0.0 to +0.0 |

- **Robustness.** The usable-share jump stays small and uncertain under every variant:
  - 12-month bandwidth: −0.0 (−13.7 to +14.2);
  - 36-month bandwidth: +3.1 (−8.3 to +9.7);
  - no donut: +2.6 (−1.3 to +9.9);
  - placeholder terms for inapplicable material removed from the denominator: +2.7 (−5.9 to +10.6);
  - package fixed effects: +6.0;
  - without SARS-CoV-2 samples (41% of the window): +2.9 (−4.3 to +11.1).

  The fall in absent fields holds in every variant. The placeholder rise holds in every variant except the 12- and
  36-month bandwidths, where its interval includes zero (+11.3, −1.8 to +26.3; +3.7, −4.3 to +16.4).
- **Within submitters** (10,149 organisations active on both sides):
  - usable +0.6 (−4.1 to +8.8);
  - placeholder +5.8 (+3.0 to +8.0);
  - absent −6.4 (−14.2 to −2.5).
- **Why H1 stays Inconclusive.** The placebo dates (1 June 2021 and 2022) produce usable-share jumps of +17.6 and
  −15.7, and the 2025 extension gives −11.7 (−22.9 to +2.4). Submission volumes, led by SARS-CoV-2 surveillance in
  2021–22, move the shares by more than the effect H1 is about. The design cannot pin the usable-share change to
  within 10 points.
  - **Not placeholders either.** The independent review ran the same specification at 55 month-start cutoffs
    (`review/reviewer_checks/rd_replicate.json`). The placebo standard deviations are:
    - usable 10.2 points;
    - placeholder 5.5;
    - absent 8.1.

    9 of 55 placebo placeholder jumps are as large as the real +9.1 (placebo-calibrated p ≈ 0.16), and 11 of 55 of
    the absent ones. The yearly shares follow a smooth trend: absent 41% → 0.9% and placeholder 5.5% → 36% from 2019
    to 2025. A jump appears wherever the window is centred.
  - **H1's rule is one-sided**, so a large decrease would also read "Supported". The raw usable share fell across the
    cutoff (85.3% → 79.4%), and the +2.9 estimate comes from the local-linear extrapolation.
- **Where usable countries point.** Among samples with a usable country, the share from upper-middle-income countries
  rose from 9.8% (before) to 24.8% (after), and from CBD Parties from 58.9% to 68.7% (descriptive).

### The gold set (`results/figures/F2_gold_and_recovery.png`)

- **Agreement** (`gold_agreement.json`).
  - The two passes agree with Cohen's κ = 0.93 on the full labels, and κ = 0.94 on what scoring uses (a country
    versus not determinable). That is 17 disagreements, 4 of which change a scoring outcome.
  - One agent made both passes in one working session (D5), so these figures are upper bounds on what independent
    labellers would reach.
  - The third pass gave 3 of the 17 a country.
- **Final labels after D10** (497 records):
  - inapplicable 350 (70%), not stated 119 (24%), country 28 (6%);
  - with a linked publication: 92% inapplicable, 7% not stated, 1% country;
  - without: 49% inapplicable, 41% not stated, 10% country.
  - "Inapplicable" means no collection origin applies or none is recorded for lab-propagated material. 234 of the
    350 are *Mus musculus*. 21 are field, agricultural or genebank material with no stated source (review), so the
    category is not a clean biological partition.
- **The 28 countries:** China 7, USA 6, Japan 2, the Pacific Ocean 2, and one each for 11 others.
  - By the CBD: 64% are Parties, 21% are not (the USA), and 14% are oceans.
  - Where the submitter's country is known (10 records), it equals the sample's country in 7.
- **Labels as first adjudicated** (`*_pre_d10` tables): 37 countries, including 12 USA (6 from a US state code in a
  collector field), Spain (an experimental facility) and China (a germplasm grow-out site).
- **Projected to the 1,657,423 untagged window samples** (stratified by publication link):
  - inapplicable 60.7% (56.1–65.3%);
  - not stated 31.6% (27.1–36.2%);
  - country 7.7% (4.9–10.4%), about 127,000 samples (81,000–173,000). Before D10 this was 9.2%.
- **Some of that 7.7% is already recorded.** Besides `geo_loc_name`, a country can sit under "geographic location,
  country and/or sea" (2,190 window samples, D3) or `geo_location` (a further 4,445, found in review). Two of the 28
  gold countries are of this kind, so part of the share is recorded under another field name rather than
  recoverable by mining.
- **Full-text check (D8).** Each paper contributed at most 12 sampling sentences, and every open-access paper hit
  that cap. The 12 publication-linked "not stated" records were checked against their full texts: none gives a
  single sampling country. Even if every one had, the projected country share would rise by at most 1.3 points.

### Limb 2: recovery (`limb2_primary.json`)

| arm | threshold (tuning) | test calls | correct | recovery (95% CI) | precision |
|---|---|---|---|---|---|
| gazetteer | none reaches 90% | 0 | 0 | 0% (0–1.3%) | – |
| classifier | none reaches 90% | 0 | 0 | 0% (0–1.3%) | – |
| LLM | none reaches 90% | 0 | 0 | 0% (0–1.3%) | – |

- **Before D10** the classifier reached 90% on two tuning calls (threshold 0.971) and recovered 1.7% (0.7–3.8%) at
  100% precision. One of those two tuning calls was R475, a label D10 removes.
- **At any confidence** on the test split:
  - gazetteer: 4.0% correct, at 12.6% precision;
  - classifier: 4.7% correct, at 4.7% precision (it always names a country);
  - LLM: 5.3% correct (16 of 300), at 57.1% precision (16 of 28 calls). It finds 16 of the 19 test records that
    have a country.
- **Two discarded answers.** The LLM arm discarded two confident answers that fell outside the INSDC vocabulary: R357,
  and R401 (a test record whose gold is the Pacific Ocean). Raw answers were not kept, so this slightly understates
  its recall.
- **The ceiling is the binding constraint.** With 19 determinable records in 300, even a perfect arm would recover
  6.3%.
- **Asymmetric error** (secondary).
  - Where an arm names the wrong country and the submitter's country is known, it names the submitter's country in
    (test split, predictions at any confidence, since after D10 no arm has a tuned threshold):
    - 75% of the LLM's errors (6 of 8; 41–93%);
    - 60% of the classifier's (52–67%);
    - 38% of the gazetteer's (25–52%).

    Over all 497 records the shares are 64.7% (11 of 17), 57.7% and 34.2%.
  - Most of these errors are calls on laboratory material, such as naming the lab's country for lab mice. INSDC's own
    vocabulary has "missing: lab stock" for exactly this case.
- **Calibration** (Brier score, all records): gazetteer 0.75, classifier 0.44, LLM 0.50. The LLM states 0.95–1.00 for
  many wrong calls.

### Post hoc: natural samples only (D7; `results/figures/F3_posthoc_natural.png`)

- **The ceiling.** Removing laboratory material leaves 147 gold records, of which 19% (14–26%) have a findable
  country.
- **The LLM** names a country for 35 of them and is right on 23 (66% precision; 49–79%), finding 82% of the
  determinable ones.
- **The gazetteer and classifier** reach 29% and 12% precision.
- So once laboratory material is filtered out, an LLM finds most of what can be found, but still short of 90%
  precision.

### Mirror agreement (plan §5; `mirror_agreement.json`)

A random 10,000 window samples were looked up in the ENA portal; 9,729 were found.
- **Country.** Whether a sample has a usable country agrees in 99.9% of them. Where both mirrors have one (8,079),
  it is the same country every time.
- **Absence.** The mirrors record it differently. Among the found samples, BioSample holds 829 placeholders and
  806 absent fields; ENA holds 525 and 1,111. So part of what limb 1 counts as placeholders appears in ENA as a blank.
- **Conclusion.** The usable-country results do not depend on which mirror is read. The placeholder/absent split
  does: 304 of 829 BioSample placeholders (37%) are plain blanks in ENA. This is another reason not to treat the
  placeholder shift as a measured effect.

## What this does and does not show

- **Neither change can be attributed to the rule.**
  - Over 2019–2025, blanks gave way to placeholders, which the rule asks for when a country cannot be given. But the
    change was gradual, and the design's own placebos produce jumps as large as the one at the rule.
  - Whether the usable share rose by less than 10 points cannot be settled with this design: the series moves by
    more than that in years with no rule change.
- **The traceability gap is mostly not a recovery problem.**
  - About 61% of untagged samples are laboratory material, whose missing country is legitimate.
  - About 32% are natural samples whose origin is recorded nowhere we looked.
  - About one in thirteen states a sampling country somewhere in its evidence, and some of those already carry it
    under another field.
  - Improving traceability for provider countries therefore means recording origin at collection. Mining records
    afterwards cannot supply it.
- **This contrasts with an earlier estimate.**
  - The CBD's traceability study found that 44% of checked untagged GenBank entries state an origin in the linked
    publication. Here, 3 of 250 publication-linked untagged *BioSamples* (1.2%) have a stated sampling country in any
    evidence, because 92% of them are laboratory material.
  - The populations differ (GenBank sequence entries against BioSample records, which are dominated by expression
    studies of lab organisms), and so does the evidence (abstracts and up to 12 sampling sentences of open-access full
    text, not the whole paper).
- **Limits.**
  - All labelling was done by the study's AI agent, in two passes and a third, with no human adjudicator.
  - The evidence is what the archive stores and the open-access literature holds. It excludes closed papers,
    supplementary tables, and attributes past a 600-character cap.
  - Laboratory animals, their housing facilities and experimental sites were not treated as having an origin (D5,
    D10). A different construct, "where was this sample taken", would put a country on many of them, and then the
    arms' "errors" on lab material would count as recoveries.
  - The gold set was drawn from the classification before D3/D4, while the projection counts the population after
    them. The effect is well under a point.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - D1: after the limb-1 results, the failed placebo cutoffs and the post-hoc checks (without SARS-CoV-2, within
    submitters);
  - D2: the two kinds of not-determinable label;
  - D3: the care filter extended to human-host metagenomes, an ENA attribute variant, culture-collection labels;
  - D4: the classifier apostrophe fix and limb 1 re-run;
  - D5: pass-2 conditions, a display truncation in pass 2 (audited; it enters no final label), the shared attribute
    cap, label spelling, and the third pass's readings;
  - D6: the LLM output budget, before running;
  - D7: the post-hoc natural-sample analysis;
  - D8: the full-text check;
  - D9: the mirror check, run late;
  - D10: changes after the review:
    - nine gold labels brought back to the plan's evidence rule;
    - the placeholder claim withdrawn as an effect;
    - the attribute-variant count corrected;
    - the two discarded LLM answers;
    - wording.
- **Independent review:** Fable, 2026-10-23, "publish with edits" (`review/review.md`). Both verdicts stand.

## Reproducing it

- **Limb 1:** `code/parse.py`, `code/reclassify.py`, `code/analysis_rd.py`, `code/analysis_rd_posthoc.py`,
  `code/decomposition.py limb1`.
- **Gold set:** `code/goldset.py`, `code/bioproject.py`, `code/owner_countries.py`. The hand labels are in
  `results/gold/` (pass 1, pass 2 and pass 3, with keys). `code/score.py agree` computes agreement.
- **Limb 2:** `code/arms.py`, `code/score.py score`, `code/decomposition.py limb2`, `code/posthoc_natural.py`,
  `code/mirror.py`, `code/monthly.py`, `code/figures.py`.
- **Tables:** `results/tables/`.
