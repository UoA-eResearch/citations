# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Do Supreme Court precedents die before they are overruled? Not in lower-court citations: in a post hoc check of clean windows, overruled precedents were cited more, not less, in the years before | posthoc_pre2019.json D(-1) -0.555 (cited 55% more), labelled post hoc in title | Supported | added 'in a post hoc check of' (the clean-window result was a post hoc analysis) |
| 2 | standfirst | 71 explicitly overruled US Supreme Court decisions (overruled 1960–2024), each against 10 matched never-overruled Supreme Court decisions. | primary.json treated 71, controls_per_stack_mean 10; overrulings 1960-2024 | Supported |  |
| 3 | standfirst | The data are lower-court citations from CourtListener's citation map (2026-09-30 snapshot; 10.6 million lower-court citing–cited pairs to Supreme Court decisions), in a stacked PPML event study. | stacks.json / pipeline log: 10.6M pairs; CourtListener 2026-09-30 snapshot (ledger P10) | Supported |  |
| 4 | standfirst | The plan was committed before any citation was counted. | git history: plan.md committed before citation counting | Supported |  |
| 5 | verdict | **Verdict: H1 not testable** (the preregistered post-overruling decline is not detectable). | primary.json H1 'not testable' | Supported |  |
| 6 | verdict | Post hoc, in windows before a 2019 coverage break, the evidence runs against erosion. | posthoc_pre2019.json D(-1) -0.555 (CI -0.957 to -0.208) | Supported |  |
| 7 | verdict | **H1 (at least a third of the five-year post-overruling decline has happened by the year before overruling): not testable by the preregistered rule.** | plan.md H1; primary.json | Supported |  |
| 8 | verdict | Five years after overruling, the overruled precedents' lower-court citations are 27% below their matched controls', but the interval includes zero (−13% to +49%). | primary.json D5 0.267 (CI -0.126 to 0.489) | Supported |  |
| 9 | verdict | The pre-share (0.68) is therefore undefined. | primary.json pre_share 0.677; CI spans (-14.6, 7.7) | Supported |  |
| 10 | verdict | The year before overruling the gap is 18% (−65% to +54%). | primary.json D(-1) 0.181 (CI -0.648 to 0.537) | Supported |  |
| 11 | verdict | Overruled cases keep being cited, often in opinions that discuss the overruling itself. | excl_cocite D5 0.652 vs primary 0.267: co-citing opinions carry the post-overruling citations | Supported |  |
| 12 | verdict | **Without opinions that also cite the overruling decision,** the post-overruling decline is clear: 65% (37% to 83%) at five years. | primary.json excl_cocite D5 0.652 (37% to 83%) | Supported |  |
| 13 | verdict | The pre-share is 0.31 (−1.43 to 0.81), under the one-third bar but with an interval that cannot exclude it. | excl_cocite pre_share 0.308 (-1.43 to 0.81) | Supported |  |
| 14 | verdict | **A coverage break distorts the recent stacks (D1, found after the primary result).** | deviations.md D1 | Supported |  |
| 15 | verdict | CourtListener's federal lower-court citations to the Supreme Court triple from 2018 to 2020 (127,000 to 385,000 a year), while state citations stay near 45,000. | scotus_cites_by_year.csv federal 126,788 (2018) -> 384,806 (2020); state 51,884 -> 44,673 | Supported |  |
| 16 | verdict | Stacks whose windows cross 2019 mix that coverage change into the treated–control contrast. | deviations.md D1; posthoc_pre2019 vs primary | Supported |  |
| 17 | verdict | Chevron's path shows it: a sudden 55% "decline" in exactly 2019. | secondary.json Chevron path (secondary 6): D = 0.55 at 2019; deviations.md D1 | Supported |  |
| 18 | verdict | **Post hoc, windows before the break** (57 overrulings up to 2013, citations up to 2018): | posthoc_pre2019.json treated 57 | Supported |  |
| 19 | verdict | overruled precedents are cited **55% more** than their controls the year before overruling (21% to 96%); | posthoc_pre2019.json D(-1) -0.555 (-0.957 to -0.208) | Exploratory-labelled |  |
| 20 | verdict | they peak at 74% more in the year of overruling; | posthoc_pre2019.json D(0) -0.743 | Exploratory-labelled |  |
| 21 | verdict | they are back to control levels by five years after (+1%, −34% to +44%). | posthoc_pre2019.json D5 -0.008 (CI -0.440 to 0.335) | Exploratory-labelled |  |
| 22 | verdict | That is the opposite of fading: citations rise as a precedent heads for the Court. | posthoc_pre2019.json D(-5..0) all negative | Exploratory-labelled | was 'salience rises' (an interpretation citations cannot show); now 'citations rise' |
| 23 | plain terms | When the US Supreme Court overrules one of its own past decisions, was that decision already dying? | question framing | Supported |  |
| 24 | plain terms | A recent essay argues that precedents "die before they are overruled", as the Supreme Court narrows and criticises them while lower courts often keep applying them. | ledger P1 (Feldman essay: Supreme Court erosion; lower courts often keep applying) | Supported | was 'lower courts stop relying on them years ahead' attributed to the essay (misattribution, ledger P2) |
| 25 | plain terms | We asked the lower-court version: do lower courts stop relying on a precedent years before it is overruled? | plan.md H1 | Supported |  |
| 26 | plain terms | We tested this on the full record of lower-court citations in the open CourtListener database. | CourtListener citation map, all lower courts | Supported |  |
| 27 | plain terms | We compared 71 overruled decisions with similar decisions from the same era and subject that were never overruled. | primary.json 71 treated; matching on era and SCDB issue area | Supported |  |
| 28 | plain terms | The best evidence we have says no, though it comes from a check we added after seeing the first result. | posthoc_pre2019.json; labelled as an added check | Exploratory-labelled | was 'The answer is no, as far as citations can show' (the planned test was not testable) |
| 29 | plain terms | In the years before an overruling, the doomed decisions were cited more than comparable ones, not less, presumably because they were being fought over. | posthoc_pre2019.json D(-5..-1) negative; follows the post hoc label in row 28; 'presumably' marks the interpretation | Exploratory-labelled |  |
| 30 | plain terms | After overruling, citations fell back. | posthoc_pre2019.json D5 -0.008 (back to control levels) | Exploratory-labelled |  |
| 31 | plain terms | Lower courts kept citing overruled cases for years, often to explain that they had been overruled. | excl_cocite D5 0.652 vs primary 0.267 | Supported |  |
| 32 | plain terms | One caution changed how we read our own first result. | deviations.md D1 | Supported |  |
| 33 | plain terms | The database's coverage of federal courts tripled after 2018, and that distorts comparisons for recent cases, such as the 2024 overruling of Chevron. | scotus_cites_by_year.csv federal x3 2018-2020; secondary Chevron path | Supported |  |
| 34 | plain terms | Our planned test could not reach a verdict, and the clearest evidence comes from the cases decided before that change. | primary.json H1 not testable; posthoc_pre2019.json | Supported |  |
