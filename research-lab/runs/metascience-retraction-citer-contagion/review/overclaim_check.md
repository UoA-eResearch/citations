# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Innocent citers of retracted papers suffer no measurable citation penalty in a post hoc comparison with not-yet-treated controls: the apparent effects come from comparing them with the wrong controls | posthoc_b depth1 +0.003 (-0.015 to +0.021); labelled post hoc in title | Supported | added 'in a post hoc comparison with not-yet-treated controls' (design B was post hoc) |
| 2 | standfirst | Retraction Watch retractions 2000–2021, matched to 61,527 OpenAlex works. 86,463 works cited a later-retracted paper before its retraction and share no author or institution with it (depth 1), and 69,865 cite such a work (depth 2, sampled). | pipeline: 61,527 matched works; primary exposed 86,463 / 69,865 | Supported |  |
| 3 | standfirst | Citations per year come from the full local OpenAlex snapshot. | plan.md data | Supported |  |
| 4 | standfirst | The plan and analysis code were committed before any citer or citation count was built. | git: plan and analysis code before builds | Supported |  |
| 5 | verdict | **Verdict: H1 Inconclusive (no penalty); H2 not testable; H3 Refuted as preregistered.** | primary verdicts; D1 | Supported |  |
| 6 | verdict | **H1 (unrelated depth-1 citers lose citations after the retraction): Inconclusive by the preregistered rule, and there is no penalty.** | plan H1; primary H1 Inconclusive | Supported |  |
| 7 | verdict | The preregistered matched DiD is **+0.068 log points** (95% interval +0.054 to +0.082; 4,355 retractions): exposed works *gain* relative to controls. | primary H1 did 0.0678 (0.0543-0.0815), 4,355 retractions | Supported |  |
| 8 | verdict | It fails its own premise, because exposed works were already pulling ahead before the retraction. | primary pretrend depth1 -0.075 | Supported |  |
| 9 | verdict | **Post hoc design B** compares citers with works that also cite retracted papers, but only papers retracted after the event window ("not-yet-treated" controls), matched on the trajectory to T−1. | posthoc_b design (labelled post hoc) | Exploratory-labelled |  |
| 10 | verdict | Its event profile is flat, and the effect is **+0.003 (−0.015 to +0.021)**: no penalty larger than about 1.5%, and no gain. | posthoc_b depth1 0.0032 (-0.0148 to 0.0210) | Exploratory-labelled |  |
| 11 | verdict | **H2 (the penalty is at least twice as large for misconduct as for honest error): not testable.** | plan H2 | Supported |  |
| 12 | verdict | The preregistered contrast reads "Supported" (C = 0.116, 0.026 to 0.205), but only because both groups *gain* and the honest-error group gains more. | primary H2 C 0.116 (0.026-0.205); both did positive | Supported |  |
| 13 | verdict | The contrast assumes positive penalties, so this is not support (D1). | deviations.md D1 | Supported |  |
| 14 | verdict | Under design B, misconduct retractions show −0.000 (−0.021 to +0.020), and honest-error retractions +0.054 (+0.006 to +0.105; 406 retractions). | posthoc_b misconduct -0.0004 (-0.021 to 0.020); honest 0.054 (0.006 to 0.105), n 406 | Exploratory-labelled |  |
| 15 | verdict | **H3 (the penalty attenuates to zero at depth 2): Refuted as preregistered, but there is no penalty to attenuate.** | primary H3 Refuted; posthoc_b depth2 ~0 | Supported |  |
| 16 | verdict | The preregistered depth-2 DiD is +0.088 (+0.073 to +0.102), which excludes zero. | primary H3 did 0.088 (0.073-0.102) | Supported |  |
| 17 | verdict | Under design B, depth 2 is +0.010 (−0.005 to +0.026). | posthoc_b depth2 0.010 (-0.005 to 0.026) | Exploratory-labelled |  |
| 18 | verdict | **Why the naive comparisons mislead.** | heading | Supported |  |
| 19 | verdict | Works that cite later-retracted papers grow faster than same-venue, same-year works that cite no retracted paper at all. | primary pretrend negative (exposed pulling ahead); posthoc design A | Supported |  |
| 20 | verdict | Matching on citations at any single year then leaves a kink at that year: a dip before T when matched at T−2, and a jump of about +0.09 at T when matched at T−1 (post hoc design A). | posthoc.json design A profiles (event_profile_t1) | Exploratory-labelled |  |
| 21 | verdict | The same pattern appears at depth 2, for all reason classes and in every field. | primary by_domain all positive; H3 depth2 positive | Supported |  |
| 22 | verdict | Not-yet-treated controls, drawn from the same citation communities, remove it. | posthoc_b flat profile (event_profile_nyt.csv) | Exploratory-labelled |  |
| 23 | plain terms | When a paper is retracted, do the scientists who innocently cited it, people with no connection to the authors, pay a price in fewer citations to their own work? | question | Supported |  |
| 24 | plain terms | Earlier studies found a penalty for the retracted authors' other work and for closely related papers, but no study we found had estimated the effect on innocent citers across all of science. | ledger R1-R3; R7 (conditional absence claim, softened) | Supported | was 'no one had checked' (absence claim; softened to 'no study we found had estimated') |
| 25 | plain terms | We followed about 86,000 such papers, and 70,000 papers one step further removed, around 4,000 retractions from 2000–2021. | exposed 86,463 / 69,865; retractions 4,355 / 3,827 | Supported |  |
| 26 | plain terms | A first, preregistered comparison suggested the citers actually *gained* citations. | primary H1 did +0.068 | Supported |  |
| 27 | plain terms | But that comparison was flawed: papers that cite soon-to-be-retracted work belong to faster-growing research communities than typical papers in the same journal. | primary pretrend; design A | Supported |  |
| 28 | plain terms | When we then compared them, in a check added after the first result, with papers from the same communities, ones that cited work retracted only years later, the difference vanished. | posthoc_b, labelled as an added check | Exploratory-labelled | added 'in a check added after the first result' |
| 29 | plain terms | Innocent citers neither lost nor gained citations after the retraction, to within about 2%. | posthoc_b depth1 CI -1.5% to +2.1% | Exploratory-labelled |  |
| 30 | plain terms | This held for misconduct retractions too. | posthoc_b misconduct -0.000 (-0.021 to 0.020) | Exploratory-labelled |  |
| 31 | plain terms | Citing a paper that is later retracted does not, on this evidence, cost your paper citations. | posthoc_b depth1 and depth2 null | Exploratory-labelled | was 'damage your paper's standing' (only citations were measured) |
