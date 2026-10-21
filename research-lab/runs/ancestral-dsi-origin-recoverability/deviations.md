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
