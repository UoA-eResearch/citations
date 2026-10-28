# Review: metascience-retraction-citer-contagion

Reviewer: Claude (Fable 5.1), 2026-10-28. Independent, adversarial. Scripts and outputs in `review/reviewer_checks/`
(`check_construction.py`, `check_reason_classes.py`, `check_estimation.py` -> `estimation_out.json`,
`estimation_log.txt`, `pairs_*.parquet`; `check_levels.py` -> `levels_log.txt`). All three designs were re-matched
from `data/interim/` and reproduce the published numbers exactly (preregistered +0.0678, 4,355 retractions, 38,134
pairs; A +0.0680, 5,513; B +0.0031, 3,203, 10,955 pairs; depth 2 likewise).

## Verdict: publish with edits

The headline holds up: against not-yet-treated controls there is no detectable citation penalty to innocent citers
(depth 1 −1.5% to +2.1%), and the positive preregistered and design-A estimates are artefacts of the control group.
The strongest evidence for that last claim is a check the report does not contain: on the same 12,326 exposed works,
clean controls give +0.085 (0.063 to 0.108) and not-yet-treated controls give +0.008 (−0.015 to +0.031). Design B's
null also survives removing the 1–2% of controls in r's author or institution cluster (G1), splitting by the control's
retraction horizon, and dropping multiply exposed works.

What must change before publication: the report explains the artefact with the wrong mechanism (findings 1–2), it
never states that 56% of depth-1 exposed works (87% in design B) have no match and that the matched ones are the
less-cited, younger ones (finding 3), its standfirst and plain-terms sample sizes are overstated (findings 3–4), and
the H2 verdict line replaces the rule's output rather than reporting it (finding 11). The rest is documentation of
limits and undocumented deviations. No number needs recomputing.

## Findings

### 1. Major (interpretation). The "pre-trend" is a regression-to-the-mean step at the first unmatched year, not a trend, and the report's mechanism ("already pulling ahead", "faster-growing communities", "kink") misdescribes it

Evidence (`levels_log.txt`, retraction-weighted mean log1p citations, depth 1):
- Preregistered design, analysis sample (year ≤ T−3): exposed − control is +0.005 (T−4), +0.013 (T−3), +0.001
  (T−2, the anchor), then +0.083 at T−1, +0.087 at T, +0.079, +0.073, +0.076, +0.055 through T+4. There is no
  divergence before the anchor. The whole "pre-trend" is a single step in the first year the match does not pin, and
  the gap then decays. That is the signature of regression to the mean when units are matched on a noisy level and
  the two pools have different latent means (controls that happened to equal the exposed work at T−2 fall back to
  their lower mean: 1.282 → 1.226 in the balanced panel while the exposed stay at 1.28). The preregistered DiD is
  therefore (post ≈ +0.07) − (pre containing the anchor ≈ 0): the estimate *is* the artefact.
- Design A pins T−1, T−2 and the cumulative to T−1, so every pre-year is matched by construction and the step
  lands on T. Its size falls with how much the matched levels say about the latent mean: pairs published at T−2
  (16,666 of 38,536 pairs, 4,562 of 5,513 retractions) step +0.116; published at T−3, +0.047; published at or before
  T−4, +0.036, fading to +0.006 by T+4. Among those older pairs the "+8% effect" is gone within three years. A
  growth-rate difference would open a widening gap; this opens a step and closes.
- Design B is flat at every age (balanced panel within ±0.02 at all nine event years; pairs published at T−2 drift
  to −0.026 by T+3), consistent with the two pools sharing a latent level, so there is nothing to revert to.
- Pre-T growth from T−3 to T−1 on balanced pairs (`estimation_out.json` → `growth_*`): preregistered design
  exposed +0.073 vs control +0.045 (reversion already under way at T−1); designs A and B 0.086 vs 0.098 and 0.074
  vs 0.081, i.e. no faster exposed growth once the latent level is matched.

Where the report is wrong or misleading: report.md verdict bullet 1 ("exposed works were already pulling ahead
before the retraction"), "Why the naive comparisons mislead" ("grow faster", "kink at that year"), plain terms
("belong to faster-growing research communities"), deviations.md D1.1 ("outgrow their controls between T−2 and
T−1"), and the figure caption ("exposed works rise faster before T"). The data show a *higher level*, not faster
growth, among citers of later-retracted work.

Fix: rewrite those passages around regression to the mean under level matching with a latent-level difference
between the pools; add the age decomposition above and the same-works A-vs-B comparison (+0.085 vs +0.008) as the
evidence; drop "pulling ahead", "outgrow" and "faster-growing" (say "more cited over their lifetime than same-venue
papers that cite no retracted work"). The methodological lesson is sharper this way: single- or two-year level
matching cannot remove a pool-level difference, and the artefact moves to whichever year is left free.

### 2. Major (report accuracy). "Pre-trends … Designs A and B: within ±0.015 at T−2 to T−3" is both false and vacuous

- False: `event_profile_nyt.csv` depth 2, k = −3 is −0.030; `event_profile_t1.csv` depth 1, k = −3 is +0.016.
- Vacuous: in A and B the T−1 and T−2 levels and the cumulative to T−1 are inside the caliper by construction, so a
  flat pre-profile cannot validate parallel trends (the report presents it as if it did). Report this as a
  property of the design, and point to the balanced-panel levels for the only informative pre-period evidence.

### 3. Major (G2, coverage). The report never states how many exposed works are analysed or that the drop is selective

- Preregistered: 86,463 depth-1 exposed → 84,837 with a candidate → 38,134 matched pairs (44%; 56% dropped at the
  caliper, not at the pool; 97.9% of exposed works had 20 candidates). Depth 2: 69,865 → 22,506 (32%). Design A
  matches 44.6% of depth-1 exposed works; design B 12.7% (49,254 have a not-yet-treated candidate; median 3
  candidates; 10,955 pairs).
- The drop is not random (`estimation_out.json` → `selection_*`): mean log1p cumulative citations to T−1 are 1.91
  matched vs 2.66 unmatched (preregistered), 1.65 vs 2.51 (A), 1.78 vs 2.18 (B); matched works are also younger at T.
  Every estimate in the report describes the less-cited end of the citer population. If a penalty exists mainly
  for prominent citers, no design here could see it.
- `primary.json` holds the pair counts, but report.md gives only retraction counts, the standfirst leads with
  86,463 / 69,865, and plain terms says "We followed about 86,000 such papers, and 70,000 papers one step further
  removed".

Fix: a coverage table in the report (exposed → with candidates → matched, per design and depth, with the matched vs
unmatched citation means); write `results/tables/coverage.json`; rewrite the standfirst and plain terms to the
analysed numbers ("about 38,000 of 86,000 such papers could be matched…; the decisive comparison uses about 11,000");
add the restriction to the limits.

### 4. Moderate (report accuracy). The standfirst's "Retraction Watch retractions 2000–2021, matched to 61,527 OpenAlex works" is the all-years count

The chain is 61,848 DOIs → 61,527 matched (all years) → 27,802 retractions 2000–2021 with good date order (other
14,245; misconduct 10,754; honest 2,803) → 6,222 with at least one depth-1 exposed work → 4,355 in the preregistered
analysis, 3,203 in design B. Give the chain, or at least the 27,802 and 6,222.

### 5. Moderate (construction, both control pools). Retractions invisible to Retraction Watch leak into the "clean" and the not-yet-treated pools

7,778 article/review works 1994–2019 are flagged `is_retracted` by OpenAlex but are not in the Retraction Watch match
(27% of OpenAlex's flagged set in that range; conversely 399 RW matches carry `is_retracted` false). Citers of
those works count as citing no retracted paper, so they can be controls in every design, and `first_ret` in
design B (posthoc_b.py:33) cannot see their retraction dates. The direction is unknown. State it as a limit; an
optional sensitivity would add OpenAlex-flagged works to the retracted set when building `cites_any_retracted` and
`first_ret` (one further snapshot pass).

### 6. Minor (construction). The plan's reason-class list has a dead label and omits several misconduct labels

`check_reason_classes.py`: the plan's "Plagiarism of Article" does not occur in the file (the label is
"Plagiarism of/in Article", 2,671 records), and "Falsification/Fabrication of Results" (111), "Manipulation of
Data" (27), "Manipulation of Results" (41), "Euphemisms for Misconduct", "Misconduct by Third Party",
"Misconduct by Company/Institution", "Taken via Peer Review" and "Concerns/Issues about Peer Review" (11,451, mostly
post-2021) are absent from the list. Effect within 2000–2021: 1,011 usable retractions classed "other" would be
misconduct under a fuller list (184 of the 1,427 depth-1 "other" retractions; 1,127 exposed works). The honest-error
class is unaffected (0 of 782 depth-1 honest retractions reclassify), so H2 and the design-B honest estimate do not
move, and the misconduct estimate would change at the third decimal. Document it in deviations.md; the plan says
the reason codes were seen before it was written, so this is a construction slip, not a data surprise.

### 7. Minor (undocumented deviations from plan.md)

- Exposed works that OpenAlex flags retracted are not excluded (plan §1 "Works"): 137 depth-1 and 57 depth-2 works
  (`select1` never reads `oaret`).
- Depth-2 "not citing r" is implemented as "citing no Retraction Watch-retracted work at all" (build.py:233–238),
  stricter than the plan; fine, but say so.
- Self-citations are included in citations per year (plan is silent; say so).
- Citing works with a null publication year are counted into the cumulative pre-period metric (7,996 citations of
  139.9 million; negligible).
- `R.T` → `R["T"]` in analyse.py after the data existed is a crash fix with no analytic content (verified by diff);
  mention it in the provenance line rather than claiming the file was untouched.

### 8. Minor (construction). The author/institution overlap exclusion has a small loophole, and the multiply exposed are a small contamination

- 3.9% of usable retracted works have no OpenAlex author ids and 8.5% no institution ids (682 neither); 0.7% and
  2.3% of depth-1 exposed works attach to them, and 6.1% of depth-1 works have no institution ids themselves. For
  those pairs "no overlap" is untestable. State the shares.
- 18.4% of depth-1 works cite more than one RW-retracted paper; 5.3% cite one retracted before T (the earliest
  no-overlap in-window exposure is not the earliest retraction they cite), 3.8% in T−4..T−1 and 7.5% another in
  T+1..T+4. Estimates are unchanged on single-exposure works (A +0.068; B +0.009, −0.009 to +0.027). Report the check.

### 9. Minor (design B, depth 2). The not-yet-treated logic is weaker at depth 2

Depth-2 exposed works cite no retracted paper by construction, but their design-B controls are citers of
later-retracted papers (the same pool as depth 1). The "same community" argument therefore compares a citer-of-citer
with a direct citer. State it, or build depth-2-type controls (citers of citers of papers retracted after T+4).

### 10. Minor (design B, inference). Thin pools and shared controls

Median 3 candidates per exposed work (16% have 20); 13,932 distinct controls serve 20,753 pairs, one control up to
26 times; 52% of matches are exact (vs 59% in A, 72% preregistered), mean distance 0.105. The bootstrap resamples
retractions only, so shared controls are treated as independent. Likely a small understatement of the interval;
state it or add a control-side cluster.

### 11. Moderate (verdict wording). H2: report the rule's output as the preregistered verdict, then reinterpret

The preregistered rule produced "Supported" (C = 0.116, 0.026 to 0.205). Declaring H2 "not testable" after seeing
that both groups gain is a reasonable reading, but the verdict line should carry the rule's output
("Supported by the letter of the rule, vacuously: both penalties are negative; not interpretable") so that the
post hoc re-labelling is visible. Note also that under design B the only interval excluding zero is the honest-error
*gain* (+0.054, +0.006 to +0.105, 406 retractions) against −0.000 for misconduct, i.e. the point estimates run
opposite to H2; the report's "should not be over-read" is fair, but say the direction. The plain-terms sentence
"This held for misconduct retractions too" is fine.

### 12. Minor (verdict wording). H1 and H3 lines

"H1 … Inconclusive by the preregistered rule, and there is no penalty" reads as if the preregistered estimate
established the absence; it cannot, since it is the artefact of finding 1. Say "Inconclusive (preregistered);
no penalty detectable in post hoc design B (−1.5% to +2.1%)". Same for H3 ("Refuted as preregistered; design B
+0.010, −0.005 to +0.026"). The title is long but fair now that it names the post hoc design; "the wrong controls"
is supported once the same-works comparison is in the report.

### 13. Gates

- **G5** passes and is honest about the post hoc status. Rows 8, 19 and 27 are labelled Supported on the
  mischaracterised mechanism (finding 1) and need relabelling after the rewrite; row 25 (sample sizes) is
  Overstated per finding 3.
- **G6** passes; each identifier resolves to the named work (Lu et al. 2013 Sci Rep; Jin et al. 2019 RESTAT;
  Azoulay et al. 2015 RESTAT "Retractions"; Hsiao & Schneider 2021 QSS; RealSpill Zenodo). R5 ("Cor and Sood
  2022") is correctly marked not found and removed from the report. R7 (no prior estimate for unrelated citers):
  an OpenAlex semantic search returned nothing that estimates a citer penalty, but Madlock-Brown & Eichmann 2014
  (Sci Eng Ethics, OpenAlex W1999506146; keywords include citation networks and citation counts) should be read
  and either cited as the nearest prior work or ruled out in the ledger's conditions.
- **G1** passes by test: 0.9% of design-B controls cite a later-retracted paper by r's authors and 1.9% by r's
  institutions; excluding them gives +0.002 (−0.015 to +0.020); controls whose first retraction is > T+8 give
  +0.000 (−0.029 to +0.030) and T+5..T+8 give +0.001. Record this in the report.
- **G2** fails as a report: the drops exist in `primary.json` but are not in report.md and there is no
  `coverage.json` (finding 3).
- **G3** is absent (the study predates the gate). One sentence placing the preregistered +7% and design B's ±2%
  against Azoulay et al.'s 5–10% field-level decline would do.
- Provenance verified: plan.md committed 01:39:52 before any build output (rw.parquet 01:41); analyse.py
  committed 01:44:28 before citers1 (01:49); D1 with the design-B text committed 02:29:21 before posthoc_b.py
  (02:29:51) and its outputs (02:31–02:39).

### 14. Numbers checked

Every figure in report.md was checked against `primary.json`, `posthoc.json`, `posthoc_b.json` and the event
profiles; all match except the two in findings 2 and 4. The figure matches the tables; its caption needs the
finding-1 wording and a note that A/B pre-years are matched by construction.

## Summary of required edits

1. Rewrite the mechanism (finding 1), including deviations.md D1.1 and the figure caption; add the age
   decomposition and the same-works A-vs-B comparison.
2. Correct the pre-trend sentence (finding 2) and the standfirst counts (finding 4).
3. Add coverage and selection (finding 3) and rewrite the standfirst and plain terms to the analysed sample.
4. H2 verdict wording (finding 11); H1/H3 lines (finding 12).
5. Limits: invisible retractions (5), reason-class gaps (6), undocumented deviations (7), overlap loophole and
   multiple exposure (8), depth-2 asymmetry (9), shared controls (10); G1 result and the Madlock-Brown check (13).
