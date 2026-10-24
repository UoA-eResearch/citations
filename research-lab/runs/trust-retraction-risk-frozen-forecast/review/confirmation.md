# Confirmation pass: trust-retraction-risk-frozen-forecast

Checked commit 6d4c885 against review/review.md, finding by finding, 2026-10-24. New check: `review/reviewer_checks/
c7_confirm_h2_pmc_share.py` (one number the report gives that is not in posthoc_review.json). Nothing outside
review/ was modified; the sealed score file was not opened; `review/reviewer_checks/born_flawed.txt` (my pdftotext
extraction of the preprint, untracked) is deleted so no quoted paper text remains under review/.

## Verdict: publish with edits

The substance is fixed: the degenerate fit is documented from the frozen models' own curves, the PubMed Central host
is named and its exclusion reported, H2's ex-Hindawi range and institution component are in, the post-hoc work is
labelled and kept apart from the frozen results, both preregistered verdicts are unchanged, and the H3 addendum is
keyed by committed hashes that match the files. What remains is one wrong number in a table (my fault originally),
four ambiguities in the H3 addendum, and small omissions.

## Checks requested by the brief

- **Post-hoc numbers in report.md against posthoc_review.json.** All match: exclusions (full 6.6 [4.1–11.5], 4.7
  [1.7–15.2], 7.4 [4.3–12.6]; H2 11.4 [6.1–14.2], 7.4 [5.4–9.3], 7.5 [5.4–9.5]), iid contrast (3.3–4.2, 10.7–12.1),
  fit curves (−0.00323 → −0.00585; H2 32 iterations, −0.00317), composition (90/57, 41/10), host table for the
  full model and for the seven H2 hosts listed, PMC host rate 0.035%, H3 inputs (4,375,482 rows; 822). The review's
  refits and buffer figures quoted in the report match c3/c4. **One exception:** the H2 column's "0.1%" for the
  PubMed Central host is not in posthoc_review.json (its H2 list has eight hosts and PMC is not among them). c7:
  the frozen H2 model puts **1.3%** of its top 1% there (519 of 39,585). The 0.1% came from an unsupported sentence
  in my review (finding 2, "The H2 model puts 0.1% of its top 1% there"), which I had not computed; the error is
  mine, and the report copied it.
- **Labelling.** Every post-hoc result is tied to D3, posthoc_review.json or "the review's refits (not frozen)" in
  Methods and Results. The verdict line and the H1/H2 numbers are unchanged. The opening summary mixes frozen and
  post-hoc numbers under one preamble sentence; see edit 3.
- **H3 addendum and hashes.** `forward_wid_doi.csv` 486a8f59…fde61a and `forward_retracted_at_seal_wids.csv`
  9e9a5e62…685c76 match the files in data/forecast/; `forward_scores.parquet` 973d5968… and `forward_model.pkl`
  2950dd43… are unchanged. Neither key file is tracked by git (`git ls-files data/` is empty). The addendum is
  not yet unambiguous; see new issue 2.
- **Exposure.** No per-paper score and no quoted paper text in any tracked file (grep for work-id and DOI patterns
  over review/, results/, report.md, deviations.md: none). posthoc_review.py reads the sealed score file for its
  `wid` column only, by the author, with the seal hash unchanged; D3 should say so (edit 8).

## Findings

1. Degenerate primary fit: **fixed** (curves from the frozen pickles; diagnosis; title, plain terms and the "venue
   history misleads" paragraph rewritten; refits labelled as the review's and not frozen).
2. PubMed Central host: **fixed** (named audit for both models, mechanism, exclusions). The repository decision is
   deferred to a future forecast, which is the right non-fix for frozen models.
3. Crossref self-update dates: **partly fixed**. Documented as a leak channel with the one-year bound, counted in the
   training positives, and excluded from the H3 rule; not re-run, justified by the freeze. The Born Flawed
   comparison still does not say that Zhang excluded reference-retraction share as inadmissible and that this
   study's inclusion rests on registry dating.
4. H2 robustness and composition: **fixed** (ex-Hindawi 7.4× frozen and 6.7× refit, seed range, "7–11×", institution
   component in the summary, plain terms and ethics).
5. Notices and the OpenAlex check: **partly fixed**. Both reported from c4/c5; notices kept in the cohort with a
   stated 0.02% effect, acceptable. The plan's exclusion counts (§1) are still not reported.
6. H3 addendum: **partly fixed**. Decision rule, registry, cohort key, exclusion list and the 10-iteration admission
   are all present and hashed; four points remain ambiguous (new issue 2).
7. Leave-one-publisher-out partial and fragile: **fixed** (stated).
8. Bootstrap contrast: **fixed** (iid interval shown, labelled as deciding H1's label).
9. Within-publisher completeness and re-typing: **partly fixed**. D3 §7 says the metadata-completeness note was
   added, but the report's D2 section is unchanged and carries neither the within-publisher gaps (Elsevier 3.6% vs
   23.7%, Springer 0.2% vs 7.7%) nor the no-re-typing result (93–94% typed "article" for 2023–2026 retractions).
10. Small plan departures: **fixed** (newcomer, 10 fields, ids; the fetch-date nit is immaterial).
11. Ethics and exposure: **fixed** (institutions, PMC host, Hindawi-era line).

## New issues (edits before publishing)

1. **Host table, H2 column:** change the PubMed Central row from 0.1% to **1.3%** (c7_confirm_h2_pmc_share.json),
   and, if the row is kept in the H2 narrative, note that it is 1.4× its cohort share, not negligible. Optionally
   replace the two dashes in the full-model column with the values in h1_h2.json (Hindawi 1.2%, no host 1.4%).
2. **H3 addendum, four ambiguities:**
   - *Date cut.* "Fetched on or after 2028-12-31" does not bound the retraction dates. Say: retractions dated on or
     before 2028-12-31 (RW date, else notice date), whatever the fetch date.
   - *Undated records.* "Crossref-only self-update dates are not used for anything" leaves open whether a work whose
     only evidence is a Crossref-only self-update counts as retracted in 2028. Say which (e.g. counts if present in a
     fetch made by 2029-03-31, since the fetch date bounds it; or is excluded).
   - *Clusters.* The publisher-clustered bootstrap needs host ids for the forward works; say they are the `host`
     column of the 2026 features for the sealed wids (or add host to the key file and re-hash), not a 2029 snapshot.
   - *Third outcome.* Say "otherwise Inconclusive", as H1/H2 do.
3. **Summary block:** tag the post-hoc bullets ("The frozen full model is a failed fit", "Without that host",
   "Without Hindawi", "Much of it is institution triage") with "(post hoc, D3)" so the preregistered and post-hoc
   numbers are distinguishable without the preamble.
4. **Finding 3's Born Flawed nuance:** one sentence in "What was asked" or "What this does and does not show".
5. **Finding 9:** either add the within-publisher completeness and no-re-typing sentences to the D2 section or drop
   the claim in D3 §7 that they were added.
6. **Exclusion counts** (plan §1): report articles excluded for no DOI, no primary topic, other type, from pass2.log
   or a one-line recount.
7. **My review:** review.md finding 2 states "The H2 model puts 0.1% of its top 1% there" without a check; the
   measured value is 1.3%. I have not edited review.md (the brief says modify only confirmation.md); the correction
   is recorded here.
8. **D3:** add that posthoc_review.py read the sealed score file's `wid` column to build the key file, with the seal
   hash unchanged.
