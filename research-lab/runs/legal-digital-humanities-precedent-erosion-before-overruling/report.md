# Do Supreme Court precedents die before they are overruled? Not in lower-court citations: in a post hoc check of clean windows, overruled precedents were cited more, not less, in the years before

*71 explicitly overruled US Supreme Court decisions (overruled 1960–2024), each against 10 matched never-overruled
Supreme Court decisions. The data are lower-court citations from CourtListener's citation map (2026-09-30 snapshot;
10.6 million lower-court citing–cited pairs to Supreme Court decisions), in a stacked PPML event study. The plan was
committed before any citation was counted.*

**Verdict: H1 not testable** (the preregistered post-overruling decline is not detectable). Post hoc, in windows
before a 2019 coverage break, the evidence runs against erosion.

- **H1 (at least a third of the five-year post-overruling decline has happened by the year before overruling): not
  testable by the preregistered rule.**
  - Five years after overruling, the overruled precedents' lower-court citations are 27% below their matched
    controls', but the interval includes zero (−13% to +49%). The pre-share (0.68) is therefore undefined.
  - The year before overruling the gap is 18% (−65% to +54%).
  - Overruled cases keep being cited, often in opinions that discuss the overruling itself.
- **Without opinions that also cite the overruling decision,** the post-overruling decline is clear: 65% (37% to
  83%) at five years. The pre-share is 0.31 (−1.43 to 0.81), under the one-third bar but with an interval that
  cannot exclude it.
- **A coverage break distorts the recent stacks (D1, found after the primary result).**
  - CourtListener's federal lower-court citations to the Supreme Court triple from 2018 to 2020 (127,000 to 385,000
    a year), while state citations stay near 45,000.
  - Stacks whose windows cross 2019 mix that coverage change into the treated–control contrast. Chevron's path shows
    it: a sudden 55% "decline" in exactly 2019.
- **Post hoc, windows before the break** (57 overrulings up to 2013, citations up to 2018):
  - overruled precedents are cited **55% more** than their controls the year before overruling (21% to 96%);
  - they peak at 74% more in the year of overruling;
  - they are back to control levels by five years after (+1%, −34% to +44%).

  That is the opposite of fading: citations rise as a precedent heads for the Court.

## In plain terms

When the US Supreme Court overrules one of its own past decisions, was that decision already dying? A recent essay argues that precedents "die before they are overruled", as the Supreme Court narrows and criticises them while lower courts often keep applying them. We asked the lower-court version: do lower courts stop relying on a precedent years before it is overruled? We tested
this on the full record of lower-court citations in the open CourtListener database. We compared 71 overruled
decisions with similar decisions from the same era and subject that were never overruled.

The best evidence we have says no, though it comes from a check we added after seeing the first result. In the years before an overruling, the doomed decisions were cited
more than comparable ones, not less, presumably because they were being fought over. After overruling, citations
fell back. Lower courts kept citing overruled cases for years, often to explain that they had been overruled.

One caution changed how we read our own first result. The database's coverage of federal courts tripled after 2018,
and that distorts comparisons for recent cases, such as the 2024 overruling of Chevron. Our planned test could not
reach a verdict, and the clearest evidence comes from the cases decided before that change.

## What was asked

The lead (`legal-digital-humanities-precedent-erosion-before-overruling`) asked whether lower-court reliance on a
precedent erodes before the Supreme Court overrules it.
- **Feldman (SCOTUSblog, 16 June 2026)** argues from six case studies that the Supreme Court erodes precedents by
  narrowing, distinguishing and criticising them before it overrules them. In his account lower courts often keep
  applying the precedent meanwhile. He reports citation and negative-treatment counts but no population estimate.
  The lead's question, whether *lower-court* reliance erodes first, is a different and testable version of the
  claim. (The lead attributed the lower-court version to Feldman; G6 corrected this.)
- **Broughman & Widiss (2017, J. Legal Stud.)** found, in a difference-in-differences design, that citations fall
  far more after judicial overrulings than after congressional overrides.

This study uses open lower-court citation data, the full list of explicit overrulings, matched controls and a
20-year pre-window.

## How it was done

- **Citations.** CourtListener's opinions, clusters and dockets were streamed once to map opinions to clusters and to
  courts. Citing–cited cluster pairs are kept where the cited cluster is a Supreme Court decision and the citing
  court is not, counted once per pair and dated by the citing opinion's filing year.
- **Treated.** Wikipedia's list of explicitly overruled decisions (132 pairs, each linked to CourtListener by U.S.
  Reports citation), with overrulings from 1960 to 2024. A decision qualifies if it is at least 20 years old at
  overruling and has at least 50 lower-court citations before it: 71 decisions. 50 were excluded as too young and 4
  for too few citations.
  - **Coverage.** SCDB flags 174 precedent alterations in 1960–2024, and 88 of them are not on the list.
- **Controls.** For each treated decision, 10 never-overruled Supreme Court decisions with at least 50 prior
  lower-court citations:
  - decided within 2 years of it, in the same SCDB issue area where known;
  - nearest by Mahalanobis distance on log citations in event years −20 to −11.

  The mean standardised difference on pre-period log citations is 0.28.
- **Model.** Stacked PPML with case × stack and calendar-year × stack fixed effects, and treated × event dummies for
  −10 to +10 (reference −20 to −11).
  - D(e) = 1 − exp(β_e).
  - The pre-share is D(−1)/D(+5), with a stack bootstrap (B = 1,000).

## Results

### H1 and the event paths (`results/figures/F1_event_paths.png`)

![Event paths](results/figures/F1_event_paths.png)

| analysis | stacks | D(−1) | D(+5) | pre-share |
|---|---|---|---|---|
| **preregistered** | 71 | 0.18 (−0.65 to 0.54) | **0.27 (−0.13 to 0.49)** | 0.68 (−14.6 to 7.7): not testable |
| excluding opinions that cite the overruling decision | 71 | 0.20 (−0.63 to 0.55) | 0.65 (0.37 to 0.83) | 0.31 (−1.43 to 0.81) |
| post hoc: windows before the 2019 break (D1) | 57 | **−0.55 (−0.96 to −0.21)** | −0.01 (−0.44 to 0.34) | undefined |

- **Subsets, preregistered and point estimates only.** All of these subsets include stacks that cross the 2019 break.
  - federal courts: D(−1) 0.44, D(+5) 0.42;
  - state courts: −0.59, −0.15;
  - constitutional (51): −0.53, 0.04;
  - statutory (18): 0.63, 0.60;
  - after 1990 (29): 0.44, 0.55.
- **Pooled ratio** (secondary 7): mean D(−3..−1) ÷ mean D(+3..+5) is 0.96 (−14.0 to 10.5).

### The coverage break (`results/figures/F2_coverage.png`)

![Coverage](results/figures/F2_coverage.png)

- **Chevron** (overruled by Loper Bright, 2024; in sample). Against its controls, its citations are flat to 2018, then
  "decline" by 55% in 2019 and about 75–80% in 2020–2025, with intervals of a few points. The step lands exactly on
  the coverage change, five years before Loper Bright.
- **Humphrey's Executor** (overruled 2026, out of sample) is cited more than its controls in most pre-years, with wide
  intervals. Its controls match poorly (standardised difference 1.05).

## What this does and does not show

- **No support for lower-court reliance eroding before overruling.** The preregistered test cannot reach a
  verdict, and the post hoc evidence runs the other way. This is consistent with Feldman's account, in which erosion
  happens at the Supreme Court while lower courts keep applying the precedent.
- **The cleanest comparison** (overrulings up to 2013) shows overruled precedents gaining citations relative to
  similar decisions in the five years before overruling. That is consistent with litigation and salience building
  as a precedent heads for the Court.
- **Excluding opinions that discuss the overruling** gives a clear post-overruling fall (65%). About a third of it
  appears before overruling on the point estimate, an estimate too uncertain to separate from zero or from the
  one-third bar.
- **Not shown:**
  - **Treatment.** Citations count whether a court follows, distinguishes or criticises a precedent; negative
    treatment is not separated.
  - **Coverage of the overruling list.** The list covers about half of SCDB's alterations.
  - **Data after 2018.** Recent overrulings cannot be read cleanly until the coverage change is modelled by court.
  - **Balance.** Matching balance is imperfect (standardised difference 0.28).

## Process and deviations

- **Preregistration:** `plan.md`, committed with the treatment assignment and before any citation count.
- **Deviations** (`deviations.md`):
  - technical: the CSV dialect and the bootstrap deadlock;
  - **D1 (post-result):** the 2019 coverage break, and a post hoc analysis restricted to windows before it.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. `code/idmap.py opinions`, then `clusters` and `dockets`.
2. `code/overruled.py`.
3. `code/counts.py`.
4. `code/event.py`, then `code/event.py pre2019`.
5. `code/secondary.py`, then `code/secondary.py pre2019`.
6. `code/figures.py`.

The data are CourtListener bulk files (2026-09-30), SCDB 2026 Release 01 and the Wikipedia list (CC BY-SA).
