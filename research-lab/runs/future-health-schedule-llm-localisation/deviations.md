# Deviations from plan.md

Timestamps are Pacific/Auckland, from `date`.

## D1 — 2026-10-18 16:50 NZDT — generator details fixed before any item was generated

- **Stability editions.** The PBS API's earliest schedule is 1 November 2025, so the NZ stability edition is also
  November 2025, not the plan's October 2025. Both jurisdictions then use 11 months.
- **Families (a) and (b)** are restricted to single-ingredient tablets and capsules. Each item is keyed by its
  normalised chemical, its strength (first number and unit, with mcg/µg unified) and a modified-release flag.
  - Questions are rendered in the same generic form in both jurisdictions, for example "budesonide 3 mg capsule
    (modified release)", so the wording does not reveal the source.
  - Other dose forms cannot be matched reliably across the two documents' formulation vocabularies.
- **AU scope.** The General Schedule program only (`program_code` GE), comparable to the NZ Community section (B).
- **AU "authority required"** means benefit type A or S (Streamlined Authority).
- **NZ "Special Authority required"** means a Rule of Type "Special" with Attribute "Subsidy", on the formulation,
  its chemical or an ATC ancestor.
- **Mixed items are excluded from (b):** formulations whose packs or brands carry different flags, in either
  jurisdiction.
- **Grouping for counterfactual criteria (d).** Groups use the matched chemical's ATC level 2 from the NZ Schedule,
  in both jurisdictions (the PBS item table carries no ATC code).
- **The criteria themselves:**
  - NZ: the MathML criterion texts in the chemical's Special Authority request forms;
  - AU: the prescribing texts linked to the chemical's GE items through their restrictions.

## D2 — 2026-10-18 17:43 NZDT — family (a) balanced within each jurisdiction (after generation, before any model output)

**Shortfall.** Under the 3-per-chemical cap and the stability rule, the generator found fewer valid negatives than
planned: 100 for NZ and 66 for AU, against the plan's 150. With 150 positives each, a yes-leaning model would score
higher on AU purely from the base rate.

**Change.** Positives are therefore capped at the number of negatives found: NZ 100/100, AU 66/66. Families (b)
(NZ 97 yes, 100 no; AU 100/100) and (d) (100/100 each) are unchanged. No model had been queried.

## D3 — 2026-10-18 17:45 NZDT — evidence used for the answer-key check (before any model output)

**AU.** The PBS website's item pages and its printed-Schedule archive are rendered by JavaScript and cannot be
fetched as documents. The AU half of the 200-item check is therefore made against the raw PBS API JSON records, read
directly:
- every General Schedule item for the drug, with its form and benefit type;
- the full restriction texts.

This checks the generator's parsing, keying and flag logic. It does not check the API against the printed Schedule.

**NZ.** The NZ half uses the October 2026 Schedule PDF text, a rendering independent of the XML the generator parsed.

## D4 — 2026-10-18 17:49 NZDT — the answer-key check found generator bugs; one fix, then a fresh check (before any model output)

**Round 1** (`results/tables/key_validation_round1.csv`): 9 of 200 keys are wrong (4.5%), under the 5% bar
overall. But 7 of the 9 are among the 29 family (a) negatives (24%), from three generator bugs:
- **Units and separators.** NZ "Tab 1,000 mg" was read as 0 mg. PBS "500 micrograms" was not matched to 0.5 mg.
- **Release labelling.** Release type is labelled inconsistently: NZ "Cap 75 mg" is Enlafax XR, and PBS "Tablet
  15 mg" is Rinvoq (modified release).
- **Form vocabulary.** An NZ "Wafer" is an orally disintegrating tablet.

The other two errors:
- a malformed name from salt stripping ("ferrous");
- a generic renewal phrase ("No evidence of disease progression") used as a counterfactual for a chemical whose
  renewal criterion means the same thing.

**Using the plan's one allowed fix** (§5):
- separators removed, and strengths converted to mg;
- no release-type flag in the key or the rendering;
- wafers counted as tablets;
- ion-only names (ferrous, ferric) excluded;
- counterfactual criteria barred if they contain generic progression, response, benefit, stability, tolerance or
  continuation language.

**Re-check.** The items are regenerated, and a fresh 200 (seed 20261020) are checked by hand. The fresh sample
excludes any question already checked in round 1. Errors are now also reported per family, and the round-2 bar
applies both overall (≤ 5%) and to family (a) negatives. The v1 items are kept in `data/items_v1.jsonl`.

## D5 — 2026-10-18 17:56 NZDT — round 2 passes overall but fails the family (a) bar; consequences fixed before any model output

**Round 2** (`results/tables/key_validation_round2.{csv,json}`): 4 of 200 keys are wrong (2.0%). This passes the
plan's overall bar (§5). Per cell:
- family (a) negatives: 2 of 24 (8.3%). This **fails** the bar D4 added for this cell;
- family (d) negatives: 2 of 31 (6.5%). No per-family bar was set for this cell;
- every other cell: 0 errors (a yes 0/26, b no 0/44, b yes 0/31, d yes 0/44).

The four errors:
- **Two parser misses, family (a).** NZ "Sprinkle cap 15 mg" (topiramate) was not read as a capsule. PBS "Tablet
  containing desmopressin acetate 200 micrograms" was filtered out as a combination, because of the word "containing".
- **Two near-duplicate counterfactuals, family (d).**
  - "Patient remains at moderate to high risk of invasive fungal infection" for voriconazole, whose own prophylaxis
    criteria say "The patient is at risk of invasive fungal infection".
  - "The treatment must be the sole PBS-subsidised therapy for this condition" for erlotinib, whose restrictions say
    "The treatment must be as monotherapy".

The plan allows one fix, and D4 used it. So these consequences are fixed now, before any model output exists:

1. **Family (a)** is reported as not constructible from these data at the bar set in D4. Its items are still run.
   Its accuracy is reported descriptively, next to its key-error rate.
2. **H1 and H2.** The confirmatory verdicts use family (b) alone. The preregistered pooled (a)+(b) analysis is
   reported alongside, flagged as resting on a family whose key failed its bar. If the two disagree, the report says
   so, and the verdict follows family (b).
3. **H3.** Near-duplicate counterfactuals inflate the fabrication rate. Before any model output is opened, all 100
   NZ counterfactual items are screened by hand against the chemical's own Special Authority text
   (`results/tables/nz_counterfactual_screen.csv`).
   - H3 is tested on all 100, as preregistered, and on the items that pass the screen.
   - It gets a Supported or Refuted verdict only if both tests agree. Otherwise it is Inconclusive.
4. Nothing else changes: conditions, prompts, the bootstrap and the thresholds stay as written.

**D5 addendum — 2026-10-18 18:13 NZDT — the NZ counterfactual screen (done while the runs were in progress, before any output was opened).**
- 17 of the 100 NZ counterfactual items overlap the chemical's own criteria (`results/tables/nz_counterfactual_screen.csv`):
  - 12 are equivalent. Two differ from an own criterion only by "the"; others restate ECOG 0–2, "at risk of invasive
    fungal infection" or "immunocompromised";
  - 5 overlap: the counterfactual is implied by, or is a narrower or broader form of, an own criterion.
- The round-2 sample drew 17 of these 100 items and caught only one of the 17. The cell's true key-error rate is far
  above that sample's 1/17.
- H3's screened test uses the 83 distinct items. Both overlap tiers are excluded, so the screened set holds only
  clearly distinct counterfactuals.
- The AU counterfactuals are not screened; AU family (d) results are descriptive only.

## D6 — 2026-10-18 19:56 NZDT — after the independent review (fix first): retrieval diagnostics, a data snapshot, corrected descriptions

The review (`review/review.md`) reproduced every reported number and confirmed all three verdicts. The changes below
come after the results were seen, and none of them alters a verdict.

1. **Reproducibility.** `generate.py` builds the family (d) pools from Python sets, so their order depends on
   string-hash randomisation and the seed does not fix the (d) sample. Families (a) and (b) regenerate exactly.
   - The items, passages and model answers actually used are committed as a snapshot (`results/snapshot/`, with
     SHA-256 sums). The snapshot, not a re-run of the generator, defines the benchmark.
   - The generator is left as it ran.
2. **Retrieval diagnostics** (`code/retrieval_diagnostics.py`, exploratory). For each item, these record whether the
   item's own chemical passage was in the BM25 top 3. For counterfactuals, they also record whether the passage of the
   chemical the sentence was taken from was retrieved. Retrieval accuracy is reported conditional on the own passage
   being retrieved.
3. **Response bias.** Youden's J (yes-rate on true "yes" minus yes-rate on true "no") with the same chemical-cluster
   bootstrap, as a bias-free companion to H1.
4. **The Australian counterfactuals.** The reviewer blind-screened them. The AU fabrication rate on the items it
   judged distinct is reported beside the unscreened rate. The reviewer's NZ re-screen (98/100 agreement with D5's
   screen) is reported as a sensitivity for H3.
5. **Descriptions corrected in the report:**
   - **The AU half of the key check.** It checked the generator's parsing of the API records, not the API against the
     printed Schedule.
   - **Key-error rates.** The (d)-negative key-error rate is about one in six by full screens. The AU (a)-negative
     rate is at least 10.6% (5 of 47, from the "containing" filter, which also removes 272 AU single-ingredient
     presentations from the universe).
   - **Sampling.** The cap is 3 per chemical per family and answer.
   - **Family (d)'s mix.** It is dominated by cancer medicines.
   - **The H1 wording asymmetry.** The AU restriction question names Streamlined Authority.
   - **D2's counts.** They predate D4: the final family (a) counts are NZ 80/80 and AU 47/47.
   - **The NZ inheritance code.** Its ATC and brand inheritance branches are never exercised on this XML.
