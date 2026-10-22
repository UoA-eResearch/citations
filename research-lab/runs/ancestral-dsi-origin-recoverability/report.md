# Countries of origin on sequence samples: the 2023 INSDC rule turned blanks into placeholders, and most untagged samples have no origin to recover

*Every non-human sample submitted to NCBI BioSample from June 2021 to May 2025 (20.9 million) was classified by its
country field. A regression discontinuity tested the June 2023 INSDC rule. Then a 500-record gold set tested whether
the missing countries can be recovered automatically from the sample's own record, its BioProject and its linked
publication.*

**Verdict: H1 Inconclusive; H2 Refuted.**

- **H1 (the rule raised the usable-country share by less than 10 points): Inconclusive.**
  - The jump at 1 June 2023 is **+2.9 points (95% interval −5.9 to +10.8)**. The upper bound crosses the 10-point
    line.
  - What the rule did clearly change is the *kind* of missing value. Placeholders ("missing", "not collected" and so
    on) rose **+9.1 points (+1.8 to +18.2)**, and absent fields fell **−12.0 points (−16.0 to −8.7)**.
  - Within submitters active on both sides, the usable share barely moved (+0.6; −4.1 to +8.8).
  - Placebo dates a year and two years earlier show jumps of +17.6 and −15.7 points. The series swings too much for
    this design to measure a 10-point effect precisely.
- **H2 (an automatic method recovers a correct country for at least 40% of untagged samples at 90% precision):
  Refuted.**
  - Only **24 of the 300 test records (8%)** have a country that any evidence states. No method could reach 40%.
  - At their tuned thresholds the three methods recover 0%, 1.7% and 0%. The upper bounds of their intervals are all
    below 4%.
- **Why: most untagged samples have no origin to find.**
  - Projected to the 1.66 million untagged samples submitted from June 2023 to May 2025:
    - **61% are laboratory material** (lab mice, cell lines, reference strains, cultivars), for which a collection
      country does not apply;
    - **30% are natural samples whose origin no evidence states**;
    - **9% (about 153,000; 104,000 to 201,000) have a country somewhere in the evidence.**
  - Samples whose BioProject links a publication are 92% laboratory material.

## In plain terms

When a scientist deposits a DNA sample from a plant, an animal or a microbe, the record is supposed to say which
country it came from. International rules on sharing the benefits of genetic resources depend on that: you cannot
pay a country back for a resource if nobody recorded where it came from. In 2023 the world's DNA archives made the
country field compulsory.

We checked 20.9 million sample records. After the rule, fewer records left the field blank. But most of them filled
it with "missing" or "not collected" rather than a country, and the share naming a real country did not clearly rise.

Then we asked whether the missing countries could be filled in automatically, by reading the sample's description
and the paper it belongs to. Mostly they cannot, because there is nothing to find. Seven in ten of the samples
without a country were laboratory animals, cell lines or lab strains, which have no country of origin in the
relevant sense. Most of the rest never say where they were collected, anywhere. Only about one in eleven had a
country written down somewhere else in their records. The best automatic method, a language model, found most of
those, but it also guessed countries for lab samples, usually the country of the lab.

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
  2021–22, move the shares by more than the effect H1 is about. The design can say the rule produced placeholders. It
  cannot pin the usable-share change to within 10 points.
- **Where usable countries point.** Among samples with a usable country, the share from upper-middle-income countries
  rose from 9.8% (before) to 24.8% (after), and from CBD Parties from 58.9% to 68.7% (descriptive).

### The gold set (`results/figures/F2_gold_and_recovery.png`)

- **Agreement** (`gold_agreement.json`).
  - The two passes agree with Cohen's κ = 0.93 on the full labels, and κ = 0.94 on what scoring uses (a country
    versus not determinable). That is 17 disagreements, 4 of which change a scoring outcome.
  - One agent made both passes in one working session (D5), so these figures are upper bounds on what independent
    labellers would reach.
  - The third pass gave 3 of the 17 a country.
- **Final labels** (497 records):
  - inapplicable 350 (70%), not stated 110 (22%), country 37 (7%);
  - with a linked publication: 92% inapplicable, 5% not stated, 4% country;
  - without: 49% inapplicable, 40% not stated, 11% country.
- **The 37 countries:** USA 12 (mostly PulseNet foodborne-pathogen surveillance), China 9, Japan 2, the Pacific
  Ocean 2, and one each for 12 others.
  - By the CBD: 57% are Parties, 32% are not (the USA), and 11% are oceans.
  - Where the submitter's country is known (12 records), it equals the sample's country in 9.
- **Projected to the 1,657,423 untagged window samples** (stratified by publication link):
  - inapplicable 60.7% (56.1–65.3%);
  - not stated 30.1% (25.6–34.6%);
  - country 9.2% (6.3–12.1%), about 152,600 samples (104,000–201,300).
- **Full-text check (D8).** Each paper contributed at most 12 sampling sentences, and every open-access paper hit
  that cap. The 12 publication-linked "not stated" records were checked against their full texts: none gives a
  single sampling country. Even if every one had, the projected country share would rise by at most 1.3 points.

### Limb 2: recovery (`limb2_primary.json`)

| arm | threshold (tuning) | test calls | correct | recovery (95% CI) | precision |
|---|---|---|---|---|---|
| gazetteer | none reaches 90% | 0 | 0 | 0% (0–1.3%) | – |
| classifier | 0.971 | 5 | 5 | 1.7% (0.7–3.8%) | 100% (57–100%) |
| LLM | none reaches 90% | 0 | 0 | 0% (0–1.3%) | – |

- **At any confidence** on the test split:
  - gazetteer: 4.3% correct, at 13.7% precision;
  - classifier: 6.0% correct, at 6.0% precision (it always names a country);
  - LLM: 6.3% correct (19 of 300), at 67.9% precision (19 of 28 calls). It finds 19 of the 24 test records that have
    a country.
- **The ceiling is the binding constraint.** With 24 determinable records in 300, even a perfect arm would recover
  8%.
- **Asymmetric error** (secondary).
  - Where an arm names the wrong country and the submitter's country is known, it names the submitter's country in:
    - 60% of the LLM's errors (9 of 15; 36–80%);
    - 57% of the classifier's (51–63%);
    - 33% of the gazetteer's (24–44%).
  - Most of these errors are calls on laboratory material, such as naming the lab's country for lab mice. INSDC's own
    vocabulary has "missing: lab stock" for exactly this case.
- **Calibration** (Brier score, all records): gazetteer 0.75, classifier 0.43, LLM 0.42. The LLM states 0.95–1.00 for
  many wrong calls.

### Post hoc: natural samples only (D7; `results/figures/F3_posthoc_natural.png`)

- **The ceiling.** Removing laboratory material leaves 147 gold records, of which 25% (19–33%) have a findable
  country.
- **The LLM** names a country for 35 of them and is right on 27 (77% precision; 61–88%), finding 73% of the
  determinable ones.
- **The gazetteer and classifier** reach 31% and 18% precision.
- So once laboratory material is filtered out, an LLM finds most of what can be found, but still short of 90%
  precision.

### Mirror agreement (plan §5; `mirror_agreement.json`)

A random 10,000 window samples were looked up in the ENA portal; 9,729 were found.
- **Country.** Whether a sample has a usable country agrees in 99.9% of them. Where both mirrors have one (8,079),
  it is the same country every time.
- **Absence.** The mirrors record it differently. Among the found samples, BioSample holds 829 placeholders and
  806 absent fields; ENA holds 525 and 1,111. So part of what limb 1 counts as placeholders appears in ENA as a blank.
- **Conclusion.** The usable-country results do not depend on which mirror is read.

## What this does and does not show

- **The rule changed how absence is recorded, not clearly how often a country is given.**
  - Blanks became placeholders, which the rule asks for when a country cannot be given.
  - Whether the usable share rose by less than 10 points cannot be settled with this design: the series moves by
    more than that in years with no rule change.
- **The traceability gap is mostly not a recovery problem.**
  - About 61% of untagged samples are laboratory material, whose missing country is legitimate.
  - About 30% are natural samples whose origin is recorded nowhere we looked.
  - Under one in ten could be filled in from existing evidence, and those are concentrated in surveillance isolates
    from the USA and China.
  - Improving traceability for provider countries therefore means recording origin at collection. Mining records
    afterwards cannot supply it.
- **This contrasts with an earlier estimate.**
  - The CBD's traceability study found that 44% of checked untagged GenBank entries state an origin in the linked
    publication. Here, 4% of publication-linked untagged *BioSamples* do, because 92% of them are laboratory
    material.
  - The populations differ (GenBank sequence entries against BioSample records, which are dominated by expression
    studies of lab organisms), and so does the evidence (abstracts and up to 12 sampling sentences of open-access full
    text, not the whole paper).
- **Limits.**
  - All labelling was done by the study's AI agent, in two passes and a third, with no human adjudicator.
  - The evidence is what the archive stores and the open-access literature holds. It excludes closed papers,
    supplementary tables, and attributes past a 600-character cap.
  - Laboratory animals and their housing facility were not treated as having an origin (D5). A different
    construct, "where was this sample taken", would put a country on many of them, and then the arms' "errors" on lab
    material would count as recoveries.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - D1: parsing;
  - D2: the two kinds of not-determinable label;
  - D3: the care filter extended to human-host metagenomes, an ENA attribute variant, culture-collection labels;
  - D4: the classifier apostrophe fix and limb 1 re-run;
  - D5: pass-2 conditions, a display truncation in pass 2 (audited; it enters no final label), the shared attribute
    cap, label spelling, and the third pass's readings;
  - D6: the LLM output budget, before running;
  - D7: the post-hoc natural-sample analysis;
  - D8: the full-text check;
  - D9: the mirror check, run late.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

- **Limb 1:** `code/parse.py`, `code/reclassify.py`, `code/analysis_rd.py`, `code/analysis_rd_posthoc.py`,
  `code/decomposition.py limb1`.
- **Gold set:** `code/goldset.py`, `code/bioproject.py`, `code/owner_countries.py`. The hand labels are in
  `results/gold/` (pass 1, pass 2 and pass 3, with keys). `code/score.py agree` computes agreement.
- **Limb 2:** `code/arms.py`, `code/score.py score`, `code/decomposition.py limb2`, `code/posthoc_natural.py`,
  `code/mirror.py`, `code/monthly.py`, `code/figures.py`.
- **Tables:** `results/tables/`.
