# Innocent citers of retracted papers suffer no measurable citation penalty in a post hoc comparison with not-yet-treated controls: the apparent effects come from comparing them with the wrong controls

*Retraction Watch retractions 2000–2021, matched to 61,527 OpenAlex works. 86,463 works cited a later-retracted
paper before its retraction and share no author or institution with it (depth 1), and 69,865 cite such a work (depth
2, sampled). Citations per year come from the full local OpenAlex snapshot. The plan and analysis code were committed
before any citer or citation count was built.*

**Verdict: H1 Inconclusive (no penalty); H2 not testable; H3 Refuted as preregistered.**

- **H1 (unrelated depth-1 citers lose citations after the retraction): Inconclusive by the preregistered rule, and
  there is no penalty.**
  - The preregistered matched DiD is **+0.068 log points** (95% interval +0.054 to +0.082; 4,355 retractions):
    exposed works *gain* relative to controls. It fails its own premise, because exposed works were already pulling
    ahead before the retraction.
  - **Post hoc design B** compares citers with works that also cite retracted papers, but only papers retracted
    after the event window ("not-yet-treated" controls), matched on the trajectory to T−1. Its event profile is
    flat, and the effect is **+0.003 (−0.015 to +0.021)**: no penalty larger than about 1.5%, and no gain.
- **H2 (the penalty is at least twice as large for misconduct as for honest error): not testable.**
  - The preregistered contrast reads "Supported" (C = 0.116, 0.026 to 0.205), but only because both groups *gain*
    and the honest-error group gains more. The contrast assumes positive penalties, so this is not support (D1).
  - Under design B, misconduct retractions show −0.000 (−0.021 to +0.020), and honest-error retractions +0.054
    (+0.006 to +0.105; 406 retractions).
- **H3 (the penalty attenuates to zero at depth 2): Refuted as preregistered, but there is no penalty to attenuate.**
  - The preregistered depth-2 DiD is +0.088 (+0.073 to +0.102), which excludes zero.
  - Under design B, depth 2 is +0.010 (−0.005 to +0.026).
- **Why the naive comparisons mislead.**
  - Works that cite later-retracted papers grow faster than same-venue, same-year works that cite no retracted
    paper at all. Matching on citations at any single year then leaves a kink at that year: a dip before T when
    matched at T−2, and a jump of about +0.09 at T when matched at T−1 (post hoc design A).
  - The same pattern appears at depth 2, for all reason classes and in every field. Not-yet-treated controls,
    drawn from the same citation communities, remove it.

## In plain terms

When a paper is retracted, do the scientists who innocently cited it, people with no connection to the authors,
pay a price in fewer citations to their own work? Earlier studies found a penalty for the retracted authors' other
work and for closely related papers, but no study we found had estimated the effect on innocent citers across all of science.

We followed about 86,000 such papers, and 70,000 papers one step further removed, around 4,000 retractions
from 2000–2021. A first, preregistered comparison suggested the citers actually *gained* citations. But that
comparison was flawed: papers that cite soon-to-be-retracted work belong to faster-growing research communities than
typical papers in the same journal.

When we then compared them, in a check added after the first result, with papers from the same communities, ones that cited work retracted only years
later, the difference vanished. Innocent citers neither lost nor gained citations after the retraction, to within
about 2%. This held for misconduct retractions too. Citing a paper that is later retracted does not, on this evidence, cost your paper citations.

## What was asked

The lead (`metascience-retraction-citer-contagion`) asked whether unrelated citers suffer collateral citation
damage, whether it is larger for misconduct, and whether it fades by citation depth 2. Prior work:
- the retracted authors' own work (Lu et al. 2013; Jin et al. 2019);
- topically related articles (Azoulay et al. 2015; a 5–10% decline);
- continued citation of retracted papers themselves (Hsiao and Schneider 2021);
- RealSpill (Zenodo, 2026), which builds a retraction-spillover benchmark on pre-event citations, not stratified by reason
  or depth.

## How it was done

- **Retractions.**
  - Retraction Watch "Retraction" records, retraction year 2000–2021, with original-paper DOIs resolved in the
    OpenAlex snapshot (61,527 matched of 61,848 DOIs over all years).
  - Reason classes are fixed in the plan: misconduct (fabrication, falsification, manipulation, plagiarism,
    duplication, paper mill, compromised review and others); honest error (only "Error in…" or "Results Not
    Reproducible"); other.
- **Exposed works.**
  - **Depth 1:** articles and reviews citing the retracted paper, published T−6 to T−2, sharing no OpenAlex author
    or institution with it, at each work's earliest exposure.
  - **Depth 2:** works citing a depth-1 work in the same window, not citing the retracted paper, with no overlap;
    up to 20 per retraction.
- **Citations per year** are counted for 2.7 million target works (exposed and candidates) from every reference list
  in the snapshot.
- **Designs.**
  - **Preregistered:** controls from the same source and year citing no retracted work, matched on citations to
    T−2 (caliper 0.25 log points). The DiD is the mean of T+1..T+4 minus the mean of T−4..T−2, averaged within and
    then across retractions.
  - **Post hoc A** (D1.3): the same controls, matched on the trajectory to T−1. The effect is the mean of T+1..T+4
    minus T−1.
  - **Post hoc B** (D1.4, specified before it was run): controls from the same source and year that cite retracted
    work, but only work retracted after T+4. Matching and the effect are as in A.
- **Intervals:** a cluster bootstrap over retractions (2,000 resamples).

## Results

### Event profiles (`results/figures/F1_event_profiles.png`)

![Profiles](results/figures/F1_event_profiles.png)

| design | depth 1 effect (95% CI) | retractions | depth 2 effect (95% CI) | retractions |
|---|---|---|---|---|
| preregistered DiD | +0.068 (+0.054 to +0.082) | 4,355 | +0.088 (+0.073 to +0.102) | 3,827 |
| post hoc A (clean controls, matched to T−1) | +0.068 (+0.056 to +0.080) | 5,513 | +0.078 (+0.068 to +0.087) | 4,858 |
| **post hoc B (not-yet-treated controls)** | **+0.003 (−0.015 to +0.021)** | 3,203 | **+0.010 (−0.005 to +0.026)** | 3,520 |

| reason class, depth 1 | preregistered | post hoc B |
|---|---|---|
| misconduct | +0.060 (+0.044 to +0.078) | −0.000 (−0.021 to +0.020) |
| honest error | +0.088 (+0.044 to +0.132) | +0.054 (+0.006 to +0.105) |
| other | +0.079 (+0.053 to +0.103) | −0.017 (−0.055 to +0.021) |

- **The preregistered estimate is positive everywhere.** It is positive in every field (life sciences +0.053,
  health +0.071, physical +0.078, social +0.104) and in both eras (2000–2010: +0.080; 2011–2021: +0.067), and it is
  unchanged with exact matching on pre-period counts (+0.086). All these share the same flawed control group.
- **Pre-trends.** Preregistered: −0.075 (depth 1) and −0.101 (depth 2), the mean of T−4..T−2 relative to T−1.
  Designs A and B: within ±0.015 at T−2 to T−3.

## What this does and does not show

- **No collateral penalty to innocent citers is visible.** Against controls from the same citation communities,
  their post-retraction citations track their peers to within about 1.5–2%, at both depths and for misconduct.
- **Naive designs are biased.** Comparing citers of retracted work with typical same-venue papers is confounded by
  community growth: such work sits in faster-growing literatures. Matching on one pre-period year does not fix it.
  This matters for any study of retraction spillovers that uses "clean" controls.
- **Not shown:**
  - **The honest-error gain.** The +0.054 is one subgroup among several, with 406 retractions and an interval that
    nearly reaches zero, so it should not be over-read.
  - **Effects on other outcomes,** such as reputation, hiring or the content of later citations.
  - **Effects on papers that build heavily on the retracted result,** which reference lists cannot identify.
  - **Retractions after 2021.**
  - **Bias in design B.** It assumes works citing papers retracted later are comparable; if late-retracted work is
    systematically different, it could be biased too.

## Process and deviations

- **Preregistration:** `plan.md`, with the build and analysis code committed before outcomes.
- **Deviations** (`deviations.md`, D1, after the primary results):
  - the pre-trend;
  - the uninterpretable H2 contrast;
  - post hoc design A;
  - post hoc design B, specified before it was run.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. `code/run_build.sh`: Retraction Watch classes, then four snapshot passes (about 25 minutes on 14 cores).
2. `code/analyse.py`.
3. `code/posthoc.py`.
4. `code/posthoc_b.py select`, then `count`, then `analyse`.
5. `code/figures.py`.
