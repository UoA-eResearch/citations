# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Do Supreme Court precedents die before they are overruled? Lower-court citation counts show no decline beforehand: the preregistered test could not reach a verdict, and post hoc, overrulings of 1960–89 were cited more in the run-up and those of 1990–2013 about as often | primary not testable; posthoc_d2 era1960_89 D-1 -1.01, era1990_2013 -0.05 | Exploratory-labelled | was 'cited more, not less, in the years before' without the era (review finding 1, G5 row 1) |
| 2 | standfirst | 73 explicitly overruled US Supreme Court decisions (overruled 1960–2024), each against 10 matched never-overruled Supreme Court decisions. | primary treated 73; stacks.json | Supported |  |
| 3 | standfirst | The data are lower-court citations from CourtListener's citation map (2026-09-30 snapshot; 10.6 million lower-court citing–cited pairs to Supreme Court decisions), in a stacked PPML event study. | counts.py; scotus_cites_by_year.csv | Supported |  |
| 4 | standfirst | The plan was committed before any citation was counted. | git order (review: plan before counts) | Supported |  |
| 5 | standfirst | This version includes fixes made after independent review (D2): controls restricted to SCDB-identified decisions as planned, a citation-parsing fix, and post hoc analyses by era and without district-court citations. | deviations.md D2 | Supported |  |
| 6 | verdict | **Verdict: H1 not testable** (the preregistered post-overruling decline is not detectable). | primary.json primary H1 not testable | Supported |  |
| 7 | verdict | Post hoc analyses find no clear decline in citation counts before overruling in any era. | posthoc_d2: every D(-1) CI includes 0 or lies below it | Exploratory-labelled | was 'the evidence runs against erosion' (review G5 row 6) |
| 8 | verdict | **H1 (at least a third of the five-year post-overruling decline has happened by the year before overruling): not testable by the preregistered rule.** | plan.md H1 | Supported |  |
| 9 | verdict | Five years after overruling, the overruled precedents' lower-court citations are 29% below their matched controls', but the interval includes zero (−5% to +51%). | primary.json primary D5 0.2911 (-0.0532 to 0.513) | Supported |  |
| 10 | verdict | The pre-share (0.73) is therefore undefined. | primary.json primary pre_share 0.7262 | Supported |  |
| 11 | verdict | The year before overruling the gap is 21% (−62% to +54%). | primary.json primary D-1 0.2114 (-0.6244 to 0.5423) | Supported |  |
| 12 | verdict | **Without opinions that also cite the overruling decision,** the five-year decline is clear: 66% (41% to 83%). | primary.json excl_cocite D5 0.6616 (0.4055 to 0.8281) | Supported |  |
| 13 | verdict | Part of that decline is mechanical, because later discussion of a precedent tends to cite its overruling decision, so 66% is an upper bound. | review finding 7 (mechanical co-citation) | Supported | added: 'an upper bound' (review) |
| 14 | verdict | The pre-share is 0.35 (−1.22 to 0.81), Inconclusive by H1's rule. | excl_cocite pre_share 0.3513 (-1.2217 to 0.8087), H1 Inconclusive | Supported |  |
| 15 | verdict | **A coverage break distorts recent windows (D1, D2; found after the primary result).** | deviations.md D1, D2 | Supported |  |
| 16 | verdict | CourtListener's district-court citations to the Supreme Court jump from 59,504 pairs in 2018 to 319,779 in 2020. | F2 caption: FD 59,504 (2018), 319,779 (2020) | Supported | was 'federal ... triple'; the break is district courts only (review finding 2) |
| 17 | verdict | Courts of appeals stay flat, and state courts roughly flat (14% lower in 2020 than in 2018). | F2 caption: appeals 60,273 -> 55,757; state 51,884 -> 44,673 (-13.9%) | Supported | was 'stay flat' (confirmation) |
| 18 | verdict | Stacks whose windows cross 2019 mix that change into the treated–control contrast. | review finding 2; secondary.json chevron | Supported |  |
| 19 | verdict | **Post hoc: the break removed at its source.** Keeping all overrulings and dropping district-court citations (68 stacks): D(−1) −0.27 (−0.74 to −0.01), D(+5) +0.09 (−0.26 to +0.37). | posthoc_d2 noFD: 68, D-1 -0.2741 (-0.7407 to -0.0055), D5 0.0935 | Exploratory-labelled |  |
| 20 | verdict | Citations were, if anything, slightly higher than controls before overruling. | posthoc_d2 noFD D-1 CI upper -0.0055 | Exploratory-labelled |  |
| 21 | verdict | **Post hoc: the pattern depends on era.** | posthoc_d2 era variants | Exploratory-labelled |  |
| 22 | verdict | **Overrulings of 1960–89 (42 stacks, citations to 2018):** cited about twice as often as controls the year before overruling. | posthoc_d2 pre2019_era1960_89 D-1 -1.0143 (rate ratio 2.0) | Exploratory-labelled |  |
| 23 | verdict | D(−1) is −1.01 (−1.57 to −0.47). | posthoc_d2 pre2019_era1960_89 Dm1_ci | Exploratory-labelled |  |
| 24 | verdict | **Overrulings of 1990–2013 (17 stacks):** cited about as often as controls until overruling, D(−1) −0.05 (−0.32 to +0.14), and clearly less five years after, D(+5) +0.41 (+0.21 to +0.65). | posthoc_d2 pre2019_era1990_2013 D-1 -0.0548, D5 0.4102 (0.2084 to 0.651) | Exploratory-labelled |  |
| 25 | verdict | H1's precondition holds in this group, and its pre-share of −0.13 (−1.22 to +0.31) would read narrowly **Refuted** by H1's rule (upper bound 0.31 against the 0.33 bar). | posthoc_d2 pre2019_era1990_2013 pre_share -0.1336 (-1.2188 to 0.3108), H1 Refuted | Exploratory-labelled | 'narrowly' and the bound added (confirmation) |
| 26 | verdict | **Overrulings of 2014–2024, without district-court citations (13 stacks):** D(−1) +0.10 (−0.72 to +0.29), D(+5) +0.51 (+0.11 to +0.68). | posthoc_d2 noFD_recent | Exploratory-labelled |  |
| 27 | verdict | **Post hoc: windows before the break** (59 overrulings up to 2013): cited 52% more than controls the year before overruling (18% to 96%); 71% more the year after (the largest gap); back to control levels by five years after (D(+5) +0.03). | posthoc_pre2019.json D-1 -0.5211, D1 -0.7104, D5 0.029 | Exploratory-labelled | was 'peak 74% in the year of overruling' (review G5 row 20) |
| 28 | verdict | This mixes the two eras above. | posthoc_d2 era results | Exploratory-labelled |  |
| 29 | verdict | **The pooled estimates weight stacks by citation volume.** | review finding 3 | Supported |  |
| 30 | verdict | In the pre-2019 sample, the five most-cited stacks carry 49% of the weight. | posthoc_d2 weighting top5_weight_share 0.494 | Exploratory-labelled |  |
| 31 | verdict | Fitted alone, 68% of stacks have negative D(−1) (median −0.26). | posthoc_d2 weighting share 0.678, median -0.262 | Exploratory-labelled |  |
| 32 | verdict | Dropping the 1 to 10 most-cited stacks leaves D(−1) between −0.39 and −0.47. | posthoc_d2 pooled_Dm1_without_top1/3/5/10 | Exploratory-labelled |  |
| 33 | verdict | Fay v. | posthoc_d2 weighting top5 (372 U.S. 391) | Exploratory-labelled |  |
| 34 | verdict | Noia, the textbook overruled habeas precedent and the fourth-heaviest stack, does show erosion (+0.35). | posthoc_d2_per_stack.csv 372 U.S. 391 Dm1 0.352 | Exploratory-labelled |  |
| 35 | plain terms | When the US Supreme Court overrules one of its own past decisions, was that decision already dying? | framing | Supported |  |
| 36 | plain terms | A recent essay argues that precedents "die before they are overruled", as the Supreme Court narrows and criticises them while lower courts often keep applying them. | ledger P1-P3 (Feldman) | Supported |  |
| 37 | plain terms | We asked the lower-court version: do lower courts cite a precedent less in the years before it is overruled? | plan.md | Supported |  |
| 38 | plain terms | We tested this on the full record of lower-court citations in the open CourtListener database. | counts.py | Supported |  |
| 39 | plain terms | We compared 73 overruled decisions with similar decisions from the same era and subject that were never overruled. | primary treated 73 | Supported |  |
| 40 | plain terms | Our planned test could not reach a verdict, because citations did not fall clearly enough even after overruling. | primary.json primary D5 CI includes 0 | Supported |  |
| 41 | plain terms | The checks we added afterwards all point the same way: none finds lower courts citing doomed precedents clearly less beforehand. | posthoc_d2 (all D(-1) CIs) | Exploratory-labelled | was 'the best evidence we have says no' (review G5 row 28) |
| 42 | plain terms | For overrulings from the 1960s to the 1980s, the doomed decisions were cited more than comparable ones in the run-up, perhaps because they were being contested. | posthoc_d2 era1960_89; 'perhaps' marks the explanation as a guess | Exploratory-labelled |  |
| 43 | plain terms | Some of that rise may simply be the litigation that led to the overruling. | review G5 row 29 (mechanical part) | Exploratory-labelled | added after review |
| 44 | plain terms | For overrulings since 1990, they were cited about as often as comparable decisions until the overruling, and less afterwards. | posthoc_d2 era1990_2013 D-1 -0.05, D5 0.41 | Exploratory-labelled |  |
| 45 | plain terms | Citation counts cannot tell following a precedent from criticising it. | review G5 row 6 | Supported |  |
| 46 | plain terms | So this shows no fall in how often lower courts cite these decisions, not that the courts went on relying on them. | review G5 rows 6 and 28 | Supported | added after review |
| 47 | plain terms | One caution changed how we read our first result. | deviations.md D1 | Supported |  |
| 48 | plain terms | The database's coverage of federal district courts jumped after 2018, which distorts comparisons for recent cases unless district courts are set aside. | F2; posthoc_d2 noFD | Supported | was 'federal courts tripled' |
