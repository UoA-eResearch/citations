# Deviations from the preregistration

## D1 — 2026-10-22 04:32 NZDT — after the limb-1 results: the placebo cutoffs fail; post hoc checks

The preregistered RD gives a usable-share jump of +2.8 pp (−6.3 to +10.5) at 1 June 2023, so H1 is Inconclusive by
its rule. Placeholders rose by 9.0 pp (1.7 to 18.7) and absent fields fell by 11.9 pp (−16.0 to −8.5). But the
placebo cutoffs give jumps larger than the threshold in both directions: +17.3 pp at 1 June 2021 and −15.7 pp at 1
June 2022. The pooled daily series is dominated by shifts in who submits, most visibly pandemic-era SARS-CoV-2
surveillance, so a jump at any date mostly measures composition. Two checks, written after seeing this
(`code/analysis_rd_posthoc.py`):

1. the preregistered RD with SARS-CoV-2 samples (taxonomy 2697049) excluded, at the real and placebo cutoffs;
2. a within-submitter comparison: for organisations submitting in both windows, the change in their own shares,
   weighted by their samples, with an organisation-cluster bootstrap, at the real and placebo cutoffs.

H1's verdict stays the preregistered estimate's. The checks describe how far that estimate can be trusted.

## D2 — 2026-10-22 09:34 NZDT — gold-set labels (before any record was labelled)

The gold set was drawn as planned: 500 records, 250 with a linked publication, all of whose texts were retrieved. A
first look at six records showed that many untagged samples are laboratory organisms: mice, a medaka strain, grafted
tomato plants, a mouse-brain atlas. For these a country of collection is legitimately inapplicable. The plan's
"not determinable" label is therefore recorded in two kinds:
- **inapplicable**: laboratory stock, model organism raised in a lab, cell line, synthetic or engineered material;
- **not stated**: a country could exist, but the evidence does not give it.

Scoring is unchanged: both count as "not determinable", so a prediction on either counts as wrong. The split is
reported, because it shows how much of the missing metadata is legitimately missing.

**Pass 1** labels every record in sheet order and writes `data/gold/pass1_labels.csv` (sheet id, label, basis).
**Pass 2** follows at least five hours later, from `pass2.md` (its own order and ids), without reading pass 1's
labels. The arms are not run until both passes are complete.

## D3 — 2026-10-22 09:40 NZDT — care filter extended; an attribute variant; culture-collection labels

1. **Human-host metagenomes.** A gold record (a human colon-tissue microbiome carrying per-person attributes) showed
   that the first filter misses metagenomes whose organism is just "metagenome" but whose host is *Homo sapiens*.
   There are 180,191 of these in the analysis window (0.86%). They are now excluded everywhere, consistent with the
   plan's care rule. Limb 1 is re-run with the extended filter; the earlier tables are kept in
   `results/tables/pre_d3/`. The gold record is excluded, leaving 499 records.
2. **An ENA attribute variant.** 2,190 window samples (0.01%) give their country only under an ENA-style attribute
   ("geographic location, country and/or sea") rather than `geo_loc_name`, and are classified absent. This is
   negligible and is disclosed rather than corrected, to keep the preregistered classifier unchanged.
3. **Culture-collection strains.** In the gold set, natural isolates held in culture collections are labelled "not
   stated", since they have a real origin that is not given. Laboratory lineages (inbred mice, reference yeast and
   *E. coli* strains, cell lines) are "inapplicable". Scoring is unaffected.

## D4 — 2026-10-22 09:44 NZDT — classifier fix: apostrophes and accents

During gold-set labelling, a sample whose own country field reads "Cote d'Ivoire: Lamto" turned out to have been
classed malformed. The vocabulary file, copied from the INSDC page, spells it with a curly apostrophe ("Cote
d’Ivoire"), so a straight apostrophe, or the accented "Côte", failed to match, and the "Ivory Coast" variant pointed to
the same mis-spelling. `countries.norm()` now straightens apostrophes and strips accents on both sides of the match;
every vocabulary entry still resolves to itself. `code/reclassify.py` re-applies the classifier to the stored field
of every parsed sample and logs every class change. Limb 1 is then re-run with the D3 filter. The interrupted D3
re-run is superseded, and `results/tables/pre_d3/` keeps the original tables. Gold records whose own field now
resolves are no longer untagged; they are labelled and then excluded from scoring, and the exclusion is reported.

## D5 — 2026-10-22 15:26 NZDT — pass 2 conditions, a display truncation, and label spelling (before `score.py agree`)

1. **Pass 2 was done in the same working session as pass 1.** It began more than five hours after pass 1 was sealed,
   from its own sheet and order, and pass 1's labels file was not opened. But the labeller is the same agent, with the
   same rules in mind, and its working notes from pass 1 were in context. Agreement between the passes is therefore an
   upper bound on what two independent labellers would reach, and is reported as such.
2. **A display truncation in pass 2.** For P2-000 to P2-416 the reading aid's output was further cut to 280–420
   characters per line; pass 1 used the aid without that cut (session log). The cut hid text in attribute, comment
   and publication-cue lines. One record (an ENA plastisphere sample whose country sits under "geographic location,
   country and/or sea") was caught while labelling and labelled from the full record. An audit of the 417 cut
   records (`results/tables/gold_pass2_cut_audit.txt`) finds a location cue past the cut in 58. Two hid a real
   sampling site: an Iberian-pig farm in Spain and a Czech reservoir supplying fish broodstock. Both disagree with
   pass 1 and go to pass 3, which read them in full. The other 56 are supplier addresses, laboratory methods or the
   mislinked yak paper. Where the cut hid evidence that pass 1 used, the result is a disagreement, so the cut lowers
   agreement but does not enter a final label. No pass-1 record has a location value past the reading aid's own
   limits (500 characters of attributes, 300 of comment).
3. **A cap that gold and arms share.** `parse.py` stores at most 600 characters of a sample's other attributes. The
   gold sheets and all three arms read the same stored fields, so they are scored on the same evidence; but a
   location written past that cap is invisible to both. Recoverability is therefore measured on the stored evidence,
   which can understate what the full BioSample record holds. Three gold records end inside a "geographic location"
   attribute at the cap. A sensitivity count from the raw records is reported if the raw XML is still available.
4. **Label spelling.** `score.py` compared labels as raw strings. Country labels are now mapped to their INSDC
   spelling through `countries.resolve`, the function the arms use for their predictions, and a label outside the
   vocabulary stops the script. This changes no label's meaning; it only stops "Cote d'Ivoire" with a straight
   apostrophe from differing from the vocabulary's curly one.
5. **Pass 3 (17 records, blind to both earlier labels).** It applied the plan's fixed rule, reading "sampling site"
   as the place where the organism was taken from its source population. Three readings are recorded:
   - livestock sampled at a named farm facility take that country (as a national herd survey does);
   - experimental first-generation crosses from broodstock caught at a stated site take that site's country;
   - genebank accessions with no stated origin are "not stated", by analogy with culture-collection isolates (D3).
   A laboratory animal's housing facility is not a sampling site. Of the 17, three end as a country (Spain, Czechia,
   China); the rest are not determinable.

## D6 — 2026-10-22 15:32 NZDT — LLM arm output budget (before any arm is run)

The locally served model (nemotron_3_nano_omni) writes its reasoning before its answer. Two earlier studies in this
lab found that small output budgets truncate its replies before the answer (FAERS recalibration, D1–D2; the
Schedule-LLM study used 16,384 tokens). `arms.py` had a 400-token budget, which would have scored most truncated
replies as "unknown". The budget is now 16,384 tokens and the request timeout 900 s; requests run eight at a time.
The prompt, temperature (0), evidence and parsing are unchanged. No arm had been run.

## D7 — 2026-10-22 15:45 NZDT — post-hoc analysis (after limb-2 results were read)

Only 24 of the 300 test records turned out to have a determinable country, so H2's 40% recovery bar was out of reach
for any arm. To show what recovery looks like where it is possible, `code/posthoc_natural.py` repeats the arm
evaluation among *natural* samples only, with records labelled "inapplicable" (laboratory material) removed. It uses
every arm's predictions at any confidence. This analysis was not preregistered and is reported as exploratory. It
changes no preregistered verdict.

A note on reading `limb2_secondary.json`: for an arm with no tuned threshold (gazetteer, LLM), the
"test_at_threshold" asymmetric-error row counts every prediction, so it is an any-confidence row.

## D8 — 2026-10-22 15:50 NZDT — full-text check of the publication cap (post hoc)

The evidence keeps, from each open-access paper, the first 12 sentences with a sampling cue (at most 2,500
characters). All 186 gold records with full text reached that cap, so a sampling statement later in a paper could
have been missed. Only records labelled "not stated" can be affected (laboratory material is inapplicable whatever
the text says), and only those with a publication: 12 records. Their full texts were searched for any sentence naming
a country with a sampling cue, and every hit was read (`results/tables/fulltext_check.json`). Nine are open access;
none states a single sampling country; three are not open access. No label changes. Had all 12 been countries, the
projected country share would rise by at most 1.3 points.

## D9 — 2026-10-22 15:51 NZDT — mirror agreement run late

The plan's mirror check (§5: 10,000 random accessions against the ENA portal) had not been run with limb 1. It was
run now (`code/mirror.py`), after both limbs' results were read. It is descriptive, with no decision rule, and it
does not bear on any verdict: usable-country status agrees in 99.9% of the 9,729 samples found.
