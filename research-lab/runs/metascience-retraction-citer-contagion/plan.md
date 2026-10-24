# Plan (preregistration): do innocent citers of a retracted paper lose citations after the retraction?

Lead: `metascience-retraction-citer-contagion`. Written before any citer, control or citation count is built.

**Seen before this plan:**
- the Retraction Watch file's reason codes and their frequencies (reused from the lab's retraction studies);
- the local OpenAlex snapshot's column names.

**Novelty** (2026-10-25: OpenAlex, web):
- Azoulay et al. (2015) measure spillovers to topically *related* articles, not citers.
- Cor and Sood (2022) count citations *to* retracted papers.
- RealSpill (Zenodo, 2026-09) is a causal-inference benchmark that links papers to retractions by pre-event citations
  and reports design-based reference effects. It does not stratify by retraction reason or citation depth, and it is
  framed as a benchmark.
- No study was found of the penalty to unrelated citers by reason and depth.

## 0. Hypotheses

The effect is the difference-in-differences (DiD) of log(1 + citations per year) between exposed works and matched
controls: the mean over event years T+1 to T+4, minus the mean over T−4 to T−2, where T is the retraction year and
T−1 is omitted as the reference. It is expressed in log points. A penalty means DiD < 0.

- **H1 (unrelated depth-1 citers lose citations).**
  - **Supported** if the 95% upper bound of DiD is below 0.
  - **Refuted** if the 95% interval lies inside (−0.01, +0.01), within about ±1%.
  - **Inconclusive** otherwise.
- **H2 (the penalty is at least twice as large for misconduct as for honest error).** The contrast is
  C = P_misconduct − 2 × P_honest, where P = −DiD.
  - **Supported** if C's lower bound exceeds 0.
  - **Refuted** if C's upper bound is below 0.
  - **Inconclusive** otherwise.
- **H3 (it attenuates to zero at depth 2: citers of citers).**
  - **Supported** if the depth-2 DiD interval lies inside (−0.01, +0.01).
  - **Refuted** if the interval excludes 0.
  - **Inconclusive** otherwise.

**Intervals:** a cluster bootstrap over retracted papers, 2,000 resamples.

## 1. Data

- **Retractions.**
  - Retraction Watch (Crossref distribution, the copy used by the lab's retraction studies), RetractionNature
    "Retraction", retraction year 2000–2021, with an original-paper DOI that resolves to an OpenAlex work in the
    local snapshot (September 2026).
  - Records with RetractionDate before OriginalPaperDate are dropped.
  - **Reason classes**, fixed here:
    - **misconduct:** any of Falsification/Fabrication of Data or of Image; Manipulation of Images; Misconduct by
      Author; Misconduct – Official Investigation(s) and/or Finding(s); Investigation by ORI; Paper Mill;
      Compromised Peer Review; Plagiarism of Article / Text / Image / Data; Euphemisms for Plagiarism; Duplication
      of/in Article; Duplication of/in Image; Duplication of Data; Duplication of Text; Euphemisms for Duplication;
      False/Forged Authorship; False/Forged Affiliation; Rogue Editor; Computer-Aided Content or Computer-Generated
      Content.
    - **honest error:** at least one of Error in Data, Error in Analyses, Error in Results and/or Conclusions, Error
      in Methods, Error in Image, Error in Text or Results Not Reproducible, and no misconduct reason.
    - **other:** neither. Included in H1 and H3, excluded from H2.
- **Works.** The OpenAlex snapshot: type article or review, not paratext, not retracted (OpenAlex `is_retracted`
  false, and not in Retraction Watch).
- **Depth-1 exposed works.** For retraction r (year T): works whose reference list contains r, published in T−6 to
  T−2, sharing no OpenAlex author id and no institution id with r.
  - A work exposed to several retractions keeps its earliest.
- **Depth-2 exposed works.** Works citing a depth-1 work of r, published in T−6 to T−2, not citing r, and sharing no
  author or institution with r.
  - Up to 20 are sampled per retraction (random, seed 20261025).
  - A work is used once, at its earliest exposure.
- **Controls.**
  - Candidates are works in the same source and publication year as the exposed work, of type article or review,
    that cite no Retraction Watch-retracted work and are not themselves exposed.
  - Up to 20 random candidates are drawn per exposed work.
  - The control is the candidate nearest on (log(1 + cumulative citations by T−2), log(1 + citations in T−2)), with
    replacement, within a caliper of 0.25 on each.
  - Exposed works without a control within the caliper are dropped and counted.
- **Citations per year** are counted from the full snapshot: every work's reference list, dated by the citing work's
  publication year.

## 2. Estimation

- **The pair DiD** is computed per matched pair, then averaged over pairs within each retraction, and then over
  retractions. Each retraction counts equally, so large citer sets do not dominate.
- **Event years** run from max(T−4, publication year + 1) to T+4. Pairs with no pre year or post year are dropped.
- **The pre-trend** is reported as the mean pair difference in T−4 to T−2 relative to T−1, and the event-year
  profile is plotted.

## 3. Secondary (labelled as such)

1. The event-study profile by depth and reason class.
2. The penalty by field (OpenAlex primary-topic domain) and by retraction era (2000–2010 vs 2011–2021).
3. Depth-1 citers that cite the retracted paper more than once in the text are not identifiable, so they are not
   analysed. Citers with author overlap ("related citers", excluded from H1) are reported as a contrast.
4. Sensitivity: controls matched with exact pre-period citation counts instead of the caliper.

## 4. Limits stated in advance

- **Citation counts are noisy.** OpenAlex reference lists are incomplete for some sources, and citation dating uses
  publication year.
- **Unobserved selection.** The design matches on venue, year and pre-period citations. It cannot rule out that
  works citing later-retracted papers differ in unobserved ways, such as topic hotness, that change around T. The
  Azoulay-style field decline is absorbed only to the extent that same-venue controls share the field.
- **Matching is imperfect.** "No author or institution overlap" uses OpenAlex identifiers, which miss unmatched
  names.
