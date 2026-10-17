# Independent adversarial review: preprint-significance-ratchet (pre-review draft, commit 7ec85ab)

Reviewer: Claude (Fable 5.1), independent of the agent that ran the study. Date: 2026-10-17.
Everything I ran is under `review/reviewer_checks/` (scripts, outputs in `cache/`, and the re-adjudication table
`readjudication_table.csv`). I did not modify any study file.

## Recommendation: **fix first**

The verdict "Inconclusive" is right, and the study's process (preregistration, blind validation, abort rule,
timestamps, disclosure) is sound. But the draft cannot be published as written, because:

1. the preregistered fallback primary is itself made of artefacts: three of the four "exact tuple" crossings are not
   real changes (two are the same `r = 0.092` matched to the wrong partner, one is the typo `p = 0.0.46` read as
   p = 0), and the plain-language text calls them "4 trustworthy cases";
2. three of the five cited works are misdescribed (Bero 2021; JAMA Netw Open 2022; the 2026 bioRxiv preprint) and
   the most directly relevant prior finding (Sci Rep 2023: no significance change in any of 77 primary outcomes) is
   omitted;
3. two of the three "firmer" side results ("no selective dropping", "inconsistencies persist") are overstated
   relative to what the measurements can show.

The re-adjudication supports the agent's judgements (agreement 121/124, kappa 0.95), and none of my disagreements
changes any reading. The fixes are to text, framing and a few pipeline details, not to the conclusion.

## What I checked

- Read plan.md, deviations.md, report.md/html, all code, all result tables, the validation samples and keys.
- Verified the git sequence and second-level mtimes (adjudications recorded before `analysis.py` and
  `analysis_v2.py` ran; D3 committed before any v2 file existed; v2 code matches the D3 text).
- Ran the study's tests (16/16, 7/7, and the nine v2 tests via a small runner since the venv has no pytest).
- Recomputed every number in report.md from the result files and the raw aligned data; diffed numbers in
  report.md against report.html.
- Re-adjudicated, from the blind displays only (id, two sentences, two statistics), all 64 v2 strict crossings and
  60 v1 items (the 12 crossings judged correct plus a seeded random 48 of the other 188). Caveat on independence:
  I had read the agent's notes before re-adjudicating, so I judged each item from its text and wrote my note before
  comparing; I cannot claim to have been unaware of the agent's verdicts.
- Spot-checked extraction, section typing, table handling and alignment on real records; checked version fields,
  posting dates (bioRxiv API locally; Crossref for a seeded sample of 150 Research Square and 150 medRxiv v1 pairs),
  the title-Jaccard filter, and the literature (OpenAlex, Europe PMC, bioRxiv API, web search).

## Issues

Ordered by how much they matter. "Fix" is what I would require before publication.

### A. The primary result and its framing

**1. Three of the four preregistered-fallback crossings are artefacts (report.md "The preregistered primary";
"In plain terms": "only 4 trustworthy cases"; D3).**
The four exact-tuple crossings in the version-1 population (`reviewer_checks/cache/recompute_primary.out`):
- 10.1101/2021.02.01.21250493, two crossings (one up, one down): the preprint caption holds `r=0.092, p=0.0029`
  (nucleocapsid IgG) and `r=0.092, p=0.28` (NTD total Ig). Neither has df. `align()` matches tuples on test, df
  and statistic only, ignores section and sentence, and takes the first free partner, so each was paired with the
  other's published counterpart. Both values are unchanged between versions; the "crossings" are the swap.
- 10.21203/rs.3.rs-823166/v1 (down): preprint `F(1,44) = 0.55, p = 0.0.46` read as p = 0; the published version
  has p = 0.46. Same value, broken decimal.
- 10.21203/rs.3.rs-2183410/v1 (down): preprint `F(2, 40) = 2.42, p = 0.004` becomes `F(2,40) = 2.43, p = 0.101`.
  Real, and a correction (F = 2.42 on 2,40 df gives p of about 0.10; the published post-hoc list carries p = 0.004).
So the fallback primary is 0 up of 1 real crossing, not 1 of 4. Across all versions, 10 of the 13 exact crossings
in the D2.5 tally (8 up / 5 down) have an empty df, and eight have p = 1.0 or p = 0.0 on one side (mojibake or
broken decimals): that tally is noise. The plan's premise that "tuple matches are the robust subset" (plan 7.1) is
false whenever df is absent, and 5,232 of the 10,031 exact matches (52%) have no df.
*Fix:* require df (or an identical sentence) for exact matching, or at least exclude df-less tuples from the
fallback; restate the primary as "1 real crossing (down) among 4 automated ones, 3 of them artefacts"; delete "4
trustworthy cases"; add this to the failure taxonomy and the methods lesson.

**2. Verdict framing (report header; D3.1).**
Reporting Inconclusive instead of the rule's mechanical Refuted is justified, but the draft gives the weaker of two
reasons. The percentile bootstrap over 3 papers is degenerate (the up-crossing's paper has share 0.5, so the
resampled share can never exceed 0.5 and the interval [0.00, 0.50] is an artefact of clustering, not evidence); more
decisive is issue 1: the subset the rule falls back on is contaminated, so the preregistered test could not be run
at all. The decision was taken after the result was known and is therefore post hoc, but it moves in the
conservative direction, is disclosed, and the D2.5 tally did not reveal the v1-population result (1 of 4) before
`analysis.py` ran. On the plan's wording: no reading of section 6 lets the all-crossings estimate (0.489) carry a
verdict once precision is below 0.90; it is "reported as unreliable", and the draft does so correctly.
*Fix:* put the mechanical outcome in the verdict line: "Inconclusive. The preregistered rule, applied mechanically
to the fallback subset, returns Refuted; it is not credited because 3 of the 4 fallback crossings are extraction or
matching artefacts and a percentile bootstrap over 3 papers is degenerate." Also state that the automated strict
estimate (0.516, 0.40 to 0.63, exploratory_v2.json) reads "against a 2:1 ratchet" under D3's own thresholds but is
not credited because its precision is 0.66; the report shows it only as a hollow mark.

**3. The 52 verified crossings are a heterogeneous pool, and the headline treats them as one thing (report
"What hand verification shows"; "Verified crossings").**
- 6 of 52 lie outside the version-1 population (5 of unknown version, 1 known version 2: v182); the v1 validation
  sample was drawn from all versions (`validate_alignment.py` has no v1 filter), the v2 census from v1 only. A random
  sample of one population pooled with a census of another has no defined target population.
- 12 of 52 are not changed results: 9 "corrections or typos" (`.46` to `.046`; `p > 0.05` to `p < 0.05` in a star
  legend, v182, which the BOILER filter should have removed), 2 permuted values (w024/w090, one up and one down by
  construction), and w050/w094-type contradictions.
- Duplicates: w049 and w094 are the same mortality comparison in the abstract and the results of one paper;
  w024/w090 are one sentence. 52 verified crossings are fewer than 52 results.
- The "kind" labels come from an ad hoc keyword map (`supplementary.kind`): "value changed"/"value differs" become
  "correction or typo" (w064, w079, w108, none of which the notes call a typo), while "changed result" becomes
  "reason not stated"; w053 and w057 carry the same note but different kinds ("n 15" matches "data changed" first).
- My re-adjudication (section below) disagrees on 3 items; the sensitivity is 30/49 = 0.61 (exact 0.46 to 0.75);
  excluding also v182 and the permuted pair, 28/46 = 0.61; changed results only (no corrections), 25/38 = 0.66
  (0.49 to 0.80). All inconclusive.
*Fix:* lead with the census of the version-1 population restricted to changed results, deduplicated by result;
report corrections, permutations and the pooled 52 as labelled sensitivities; derive kinds from an explicit coding
of each note rather than keyword matching, and publish the coding.

**4. "Crossings are rare, under 2 per 1,000" (headline bullet; plain terms).**
The denominator is the 23,272 strict-eligible determined pairs in the v1 population (64/23,272 = 2.75 per 1,000,
times 42/64). Two qualifications are missing. (a) Under the preregistered aligner, 1,411 automated crossings among
about 46,000 determined aligned v1 pairs at 12% precision implies about 3.6 per 1,000, so "under 2" is specific
to the strict subset, which by construction keeps sentences that changed least. (b) Recall is unmeasured: a result
whose sentence was rewritten enough to fall below cosine 0.6 is "dropped" plus "added", never a crossing, so every
rate here is a lower bound among alignable, lightly edited statistics.
*Fix:* "Among statistics that could be matched in near-identical sentences, roughly 2 to 4 per 1,000 changed
significance; the rate among all reported statistics is unknown because rewritten sentences cannot be matched."

### B. Adjudication

**5. Blinding to version order is weaker than claimed (plan 6, D1.5, report "Adjudication").**
The labels are hidden but the text often is not: Europe PMC preprint text carries mojibake (`Â±`, `â`),
journal text carries copy-editing (`i.e.,` vs `i.e.`, `P` vs `p`, en dashes, "Fig." vs "Figure"). The agent's own
notes refer to "the published version" (w001, v133), so it formed beliefs about order; in both cases the guess was
wrong (pre_is shows the typo in the preprint), which is reassuring about the outcome but not about the design. v2's
ftfy repair removed the mojibake tell, not the copy-editing tells. The stratum is also inferable: a pair whose two
displayed values differ in significance is a crossing.
*Fix:* say "version labels hidden; the text may reveal order; two notes show the adjudicator guessing (wrongly)";
drop "blind to stratum" or qualify it.

**6. The identity criterion is applied inconsistently to fragments and positional matches (alignment_validation*.csv).**
The criterion that emerges from the notes is "same quantity and comparison, and the extracted significance on each
side matches what the text says". That is defensible and explains the apparently opposite treatment of w085
(broken `p<0. 05` read as p < 0, significance still right, judged correct) and w054/w060 (`P=001`, `p =0. 07`,
significance wrong, judged incorrect). The inconsistency is elsewhere: the four `CLP + E-5, p = ...; vs.` fragments
(w029, w040, w067, w091) were rejected as "identity cannot be verified", but `MD, p = 0.0087; sham vs.` (v136) and
`Large F1, 21.12 = 7.47, p = 0.012).` (v020) were accepted, and the two unnamed items of a "respectively" pair
(w053, w057: rho -0.87 to -0.09 with n 15 to 13; rho 0.52 to 0.26) were accepted on position alone with the note
"same position". w024/w090 (the same three values reassigned across M/S1/S2) are handled reasonably in the sense that
they are flagged and cancel, but they are relabellings, not changed results, and should be excluded from "crossings".
*Fix:* write the criterion down in the report; apply the fragment rule uniformly (I would reject v136, w053, w057);
report the sensitivity.

**7. Adjudication speed and batch notes (process).**
200 judgements were written between 15:53:43 and 15:56:55 and 114 between 16:07:56 and 16:09:00; 44 of 88
rejections carry the identical default note. The judgements nevertheless hold up (121/124 agreement), so this is a
disclosure point, not a correctness one.
*Fix:* say in the report that adjudication was done in two batch passes by the agent, and that 44 rejections share
a default note.

### C. Pipeline

**8. Table and figure text leaks into "result" text; the strict rule's "no tables, no legends" is not enforced
(parse_jats.py `text_of(s)`; analysis_v2.py `strict`).**
`text_of` flattens a `<sec>` with all descendants. In PMC XML, `<table-wrap>` and `<fig>` sit inside sections: in
197 of 400 published articles the full text of a table also appears inside a result-typed section (4 of 4,000
preprints). The sentence splitter needs whitespace after the period, so `groups.Association` and `Table 1Dataset`
do not split: 20.8% of strict-eligible pairs and 13 of the 64 strict crossings contain such glued text (6 have
"sentences" over 600 characters). w027/w107 (a table) and w003/w023 (a figure caption) failed for exactly this
reason. Published table statistics are also extracted twice (as "result" and as "table"), which inflates "added"
and helps explain 51,978 added against 19,024 dropped.
*Fix:* remove `table-wrap` and `fig` subtrees from section text before `text_of` (they are already captured
separately); split sentences on `[.!?](?=[A-Z])` as well; recompute S1 and the strict set.

**9. Extraction false positives absent from the taxonomy (extract.py; pipeline.py BOILER).**
- p = 0 exactly and p = 1 exactly are almost always artefacts (broken decimals, comma and middle-dot decimals,
  mojibake exponents, and index variables such as `(p = 1, ..., P)`); `significance()` treats p = 0 as significant.
  Several v1 failures (v087, v102, v135, the F(1,44) case) and the strict failures w054/w060 would vanish if p = 0 and
  p = 1 were undetermined.
- Glued table cells produce invented values: v068 reads `p = 0.424` followed by the cell `115 (74)` as p = 0.424115.
- Star-definition legends (`*p < 0.05, **p < 0.01`) pass the BOILER filter: 6 of my 60 v1 items are such legends,
  they inflate "other" precision, and one (v182) is counted as a verified crossing.
- `TUPLE_RE` makes df optional (issue 1) and, with re.I, `\bt`/`\bz`/`\bF` match any capital letter followed by
  `= number, p ...`.
*Fix:* p == 0 and p == 1 undetermined; extend BOILER to star legends (v2's STAR regex, applied globally); require df
for exact matching.

**10. v2 middle-dot repair breaks middle-dot multiplication (extract_v2.py MIDDOT).**
`P = 2·10-5` becomes `2.10-5` and reads as p = 2.1 (undetermined); v1 read it correctly as 2e-05. Lancet-style text
uses `·` both as decimal and as multiplication (478 v1 statistics sit in sentences containing `digit·10-digit`).
It loses determined values rather than manufacturing crossings, so the effect on direction is nil, but D3 claims the
repairs only fix things. *Fix:* exclude `·10` followed by an exponent from MIDDOT.

**11. Greedy one-to-one matching and the rank tie-breaker misalign systematically (align.py).**
Beyond issue 1: tables become one "sentence", so a dropped row shifts every later cell (v000, v130, v170, v083);
`rank()` keys on sentence text, so repeated identical sentences merge; the TF-IDF is fitted per pair on masked text,
so near-duplicate rows are interchangeable. `significance()` itself is right: `p < 0.1` and `p > 0.01` are None,
p = 0.05 is None; `p <= 0.05` is treated as significant although it admits p = 0.05 (minor).

**12. Section typing drops text asymmetrically (parse_jats.py `sec_type`).**
15% of preprints (49% of Preprints.org, 14% of Research Square) and 8% of published articles have no result-typed
section; "Findings", "Main" (Nature family) and "Case Presentation" map to "other" and are excluded; bodies without
`<sec>` are excluded entirely. 10,171 of 23,220 pairs (44%) contributed no statistic. Where only one version loses
its results text, everything becomes dropped or added.
*Fix:* map "Findings" and "Main" to result; report the share of pairs with no statistics and why.

### D. Secondaries

**13. S1 "no selective dropping" is overstated (headline; plain terms; report S1).**
Dropped and added are mostly alignment failures and (issue 8) duplicated table text, so both pools are near-random
draws from each version's statistics and both show the base rate (0.82); a real difference among genuinely removed
results would be diluted several-fold. The share significant by section is 0.73 (tables) to 0.92 (figure legends)
in both pools, which is what a mixture of base rates looks like. The CI (-1.7 to +2.6 points) excludes nothing of
interest. "Inflated in both directions" is not a defence: dilution hides, it does not cancel.
*Fix:* "We found no difference, but the comparison has little power to detect selective removal because most
unmatched statistics are matching failures." Better: compare statistics whose sentence has a counterpart that lacks
the statistic (true removals/additions).

**14. S2 "inconsistencies persist" rests on false positives, and the "robust part" argument is backwards
(report S2; analysis.py `consistent`).**
Of 3,460 aligned tuple pairs, 2,099 cannot be evaluated (no df) and 3,064 have an identical p and comparator. Of the
187 preprint "inconsistencies", 153 are verbatim unchanged tuples, so "persist" is trivially true for them; at
least 52 are explained by a one-tailed p (reported p within rounding of half the two-tailed value); several are the
`p = 0.001` floor convention flagged by the 0.0005 tolerance (e.g. `F(2,335) = 8.158, p = 0.001`, recomputed
0.00035); one of the 19 "repairs" is a lost-exponent extraction error (`z = -3.34, p = 8.3` to 0.00083). False
positives are copied verbatim into the published version and therefore are never "repaired": they bias the repair
rate downward, so the low repair rate is the least robust part, not the most. The subset that matters, decision
inconsistencies (reported significance contradicts the recomputed p), is 29 with 3 repaired, and is not reported.
`recompute_p` itself is correct for t, F, r (t = r sqrt(df/(1 - r^2))), chi-square and z; `consistent` reads the
statistic's decimals from `str(float)`, which drops trailing zeros and is lenient, fine.
*Fix:* report evaluable n, the one-tailed and floor-convention shares, and the decision-inconsistency subset; reword
to "reported p-values that disagree with their own test statistic were almost always carried over unchanged".

**15. S3 (report S3).** Described appropriately as unreliable automated estimates; "other" is 90% Research Square
and should say so. Fine.

### E. Linkage and population

**16. The title-Jaccard filter removes mostly true pairs, and plausibly the most revised ones (D1.1; report
"Pairs").**
2,664 of 31,261 candidates (8.5%) are rejected. In a random 14, 13 are the same study retitled ("Regulation of
LRRK2 by inflammation and IL-4" to "Inflammation and IL-4 regulate ... LRRK2") and 1 is a wrong link. Retitling
correlates with heavy revision, so the filter selects against the pairs most likely to carry crossings. It is
adequate for precision, not neutral for the question.
*Fix:* say so; give the rejected count by server (medRxiv 1,234; Research Square 789; bioRxiv 469); a sensitivity at
0.3 would be cheap.

**17. "Version 1 predates peer review" holds for most but not all (plan 1.2(3), 7.3; report "Pairs").**
Research Square is 53% of the v1 population (6,066 of 11,508); its /v1 DOIs are posted at submission by the
In Review workflow, so they predate review at that journal, though not necessarily at an earlier journal. Dates:
bioRxiv v1 pairs with API dates (1,037): none posted after publication, 5.4% within 30 days of it, 18% within 60.
Crossref sample of v1 pairs: Research Square (150) 0.7% posted after the article, 4.7% within 30 days; medRxiv
(150) 0.7% and 8.7%. A preprint posted a week before the article (e.g. medRxiv 10.1101/2020.04.02.20051128,
8 days) is an accepted manuscript. 11,508 v1 pairs map to 11,402 published articles (106 duplicates).
*Fix:* report these shares; add a sensitivity excluding pairs posted within 30 days of publication.

### F. Literature

**18. Cited works (report "What was already known"; plan section 2).**
- *Bero et al. 2021* (BMJ Open, 10.1136/bmjopen-2021-051821) studied 67 COVID-19 treatment/prevention studies from
  the Cochrane register, not "bioRxiv epidemiology preprints"; it found 23/67 (34%) with no discrepancy and named
  "differences in numerical values and statistical significance" as common discrepancies. The "~10% of 121 preprints
  changed main findings; 7 changed p-values" belongs to some other source (plan: "the bioRxiv epidemiology cohort
  (Peer Review Congress)"), which I could not identify. *Fix:* cite Bero correctly; find or drop the 121 figure.
- *JAMA Netw Open 2022* (Janda et al., 10.1001/jamanetworkopen.2022.45847): the 97.6% concordance is of primary
  end point *definitions*. Results for primary end points were concordant in 81.1% (434/535); 101 pairs discordant,
  66 of them in the same direction and statistically consistent. "Primary end points were concordant in 98%" is
  literally true and misleading in context. *Fix:* give the 81% results figure.
- *Sci Rep 2023* (Sommer et al., 10.1038/s41598-023-44291-4): 16.8% is 27 of 161 published preprints (not of 329),
  and the report omits the directly relevant finding: "Among the 77 studies reporting statistical significance
  (47.8%), we did not observe any changes between the preprint and the peer-reviewed journal report, neither from
  statistically significant to nonsignificant nor vice versa." *Fix:* cite it; it is prior evidence for "crossings are
  rare" at the primary-outcome level.
- *bioRxiv 2026.06.30.735556* exists, as "Tracking claim changes from preprint to publication across 72,644
  biomedical studies using large language models", DOI 10.64898/2026.06.30.735556 (bioRxiv's new prefix; it is not
  under 10.1101; Europe PMC indexes it under that DOI, first published 2026-07-01). The report's "claims rarely change" misstates it: primary claims
  unchanged in about 40%, minor revision in about half, substantial revision in about 10%; hedging shifts rare and
  toward caution about twice as often as toward confidence; abstracts only. *Fix:* give the full DOI and the
  figures.
- *Nuijten & Wicherts 2024* (AMPPS, 10.1177/25152459241258945): exists and says what the report claims.
- Omitted, and closer to this study than any cited work: Nelson et al. 2022, Lancet Global Health
  (10.1016/S2214-109X(22)00368-0), over 1,000 epidemiological point estimates in 100 matched COVID-19 preprint pairs,
  no systematic shift after review; Brierley et al. 2022, PLoS Biology (10.1371/journal.pbio.3001285), abstract-level
  changes in 7 to 17% of pairs. The novelty claim (no version-matched study of the *direction of significance
  crossings across all reported statistics*) survives, narrowly, and should be stated against these.

### G. Numbers and wording

**19. Numbers.** Every number in report.md and both captions matches the result files (table below). report.html
carries no number that contradicts report.md (its extra tokens are captions, meta text and a URL-encoded glyph).
Two wording slips: "The 23,220 with an open-access published version in PMC were fetched" (22,941 articles were
fetched for 23,220 preprint pairs); Figure 2's first row is labelled "preregistered primary" and plots 1 of 4 that
are mostly artefacts (issue 1).

**20. Plain-language summary and headline.**
- "Our planned test therefore had only 4 trustworthy cases": wrong (issue 1).
- "no sign of non-significant results being quietly dropped": overstated (issue 13).
- "internal arithmetic errors in preprints were rarely fixed": overstated (issue 14).
- "Crossings are rare ... under 2 per 1,000": qualify (issue 4).
- The methods lesson is right and should add: require df for tuple matching; strip tables and captions out of
  section text; treat p = 0 and p = 1 as undetermined; filter star legends; measure recall, not only precision.

## Numbers recomputed

| quantity | report | recomputed | note |
| --- | --- | --- | --- |
| pairs / version-1 pairs | 23,220 / 11,508 | 23,220 / 11,508 | 22,941 / 11,402 distinct published articles |
| statistics; aligned | 271,195; 110,143 | same | dropped 38,493, added 122,559 (all versions) |
| v1 validation precision, crossings / other | 12/100; 79/100 | same | 46 of the 100 sampled crossings are from unknown-version preprints |
| all crossings, v1 population | 1,411 in 514 papers; 0.489 (0.453-0.526) | same | seed 20261017 reproduces exactly |
| all crossings, all versions | 0.510 (0.483-0.536), 2,940 | same | |
| exact-tuple crossings, v1 | 4, 1 up; boot [0.00, 0.50]; exact 0.006-0.806 | same arithmetic | 3 of 4 artefacts; real: 0 up / 1 down |
| exact-tuple crossings, all versions (D2.5) | 8 up / 5 down | 8 / 5 | 10 of 13 df-less; 8 with p = 1.0 or 0.0 on one side |
| strict eligible; strict v1 crossings | -; 64 | 54,877; 64 in 47 papers, 33 up, 0.516 (0.397-0.631) | all 64 are similarity matches (cosine 0.80-1.00, median 0.89) |
| strict crossings per 1,000 determined | 2.8 | 2.75 (64/23,272) | all-aligner route implies about 3.6 |
| v2 precision, crossings / other | 42/64 = 0.66; 50/50 | same | |
| verified v2 census | 24/42 = 0.57; exact 0.41-0.72; boot 0.41-0.73; 35 papers | 0.571; 0.410-0.723; 0.415-0.725; 35 | |
| combined verified | 52, 31 up; 0.60; exact 0.45-0.73; boot 0.45-0.73; 44 papers; overlap 2 | 0.596; 0.451-0.730; 0.453-0.731; 44; 2 | 46 v1, 5 unknown version, 1 version 2 |
| kinds (n / up) | 13/9, 13/8, 9/4, 14/8, 1/1, 2/1 | same | keyword map, see issue 3 |
| failure tables, v1 / v2 | 44, 15, 14, 9, 6 / 8, 6, 5, 2, 1 | same | |
| S1 v1 | 81.5% of 19,024 vs 82.0% of 51,978; +0.5 (-1.7, +2.6) | 0.8154; 0.8201; +0.47 (-1.68, +2.58); 5,261 papers | by section: tables 0.73/0.71, legends 0.93/0.92, text 0.77/0.80 |
| S1 v2 | 81.4% vs 82.3% | 0.8143 vs 0.8235 | |
| S2 | 3,460 pairs; 187; 187; 19 (10%) | same | 3,186 exact; 2,099 not evaluable; 153/187 verbatim unchanged; 52 one-tailed-explicable; decision inconsistencies 29, repaired 3 |
| S3 by server | medRxiv 0.474 (624); other 0.499 (748); bioRxiv 0.538 (39) | same | |
| posting-to-publication gap, v1 | not reported | bioRxiv (1,037): 0% after, 5.4% <= 30 d; RS sample (150): 0.7%, 4.7%; medRxiv sample (150): 0.7%, 8.7% | `cache/date_gap.csv`, `cache/crossref_dates_sample.csv` |
| title-Jaccard rejections | 31,261 -> 28,597 | 2,664 (8.5%) | 13 of 14 sampled rejections are true pairs retitled |
| result-typed section present | not reported | preprints 3,382/4,000; published 366/400 | table text duplicated inside result text: 197/400 published, 4/4,000 preprints |
| glued table/caption text in strict set | not reported | 11,437/54,877 pairs (20.8%); 13/64 strict crossings | |
| timestamps | adjudication before analysis | confirmed | raw CSV 15:56:55 -> commit 15:57:45 -> primary.json 15:57:59; v2: 16:09:00 -> 16:09:17 -> 16:09:25; D3 15:59:52 before extract_v2.py 16:00:12 |

## Re-adjudication

Table: `review/reviewer_checks/readjudication_table.csv` (124 rows: sample, id, stratum, pair, reviewer judgement,
agent judgement, reviewer note). Blind displays used: `blind_v1.md`, `blind_v2.md`; selection in
`readjudication_ids.json`; script `agreement.py`.

| set | n | agree | kappa | reviewer correct | agent correct |
| --- | --- | --- | --- | --- | --- |
| v1, all 60 | 60 | 59 (0.983) | 0.966 | 34 | 35 |
| v1, the 12 crossings judged correct | 12 | 11 | - | 11 | 12 |
| v1, random 48 others | 48 | 48 (1.000) | 1.000 | 23 | 23 |
| v2, all 64 strict crossings | 64 | 62 (0.969) | 0.932 | 40 | 42 |
| all | 124 | 121 (0.976) | 0.949 | 74 | 77 |

Disagreements, all in one direction (I reject what the agent accepted): v136 (fragment `MD, p = ...; sham vs.`,
up), w053 and w057 (positional match in an unnamed "respectively" pair, both down). Effect on the verified shares:
census 24/40 = 0.60 (exact 0.43-0.75) instead of 24/42; pooled 30/49 = 0.61 (0.46-0.75) instead of 31/52. The
disagreements do not bias the direction toward or against a ratchet in any reading. Agreements I would still flag:
w024/w090 (relabelled values, not a changed result), v182 (a star-legend typo, not a result), v020 (labelled
fragment), w086/w101 (exposure group redefined), w049/w094 (one result counted twice).

## Answers to the brief's ten checks, in one line each

1. Adjudication: holds up (kappa 0.95); criterion consistent on extraction errors, inconsistent on fragments and
   positional matches; w024/w090 flagged but should be excluded; w053/w057 should be rejected (issues 5-7).
2. Primary: 3 of 4 exact crossings are artefacts; Inconclusive is right for a stronger reason than D3 gives; state
   the mechanical verdict in the verdict line; the all-crossings estimate carries no verdict under any reading (1-2).
3. v2: specified before built (timestamps and text match); the strict rule leaks table and caption text and selects
   the least-edited sentences; the middle-dot repair has a small regression; tests pass (8, 10).
4. Verified estimates: 24/42 and 31/52 and their intervals reproduce; dedup is right (2 overlaps); pooling is not
   defensible as an estimate, acceptable as a labelled sensitivity; kinds come from a keyword map, not coding (3).
5. S1 diluted, S2 biased by false positives and trivial persistence, S3 fine (13-15).
6. Pipeline: df-less exact matching, table flattening, sentence splitting, p = 0/1, star legends (1, 8-12).
7. Linkage: Jaccard filter precise but removes retitled (revised) pairs; version 1 predates publication for over
   99% and review for roughly 91-95%; Research Square dominates (16-17).
8. Literature: Bero and JAMA misdescribed, Sci Rep's zero-significance-change finding omitted, 2026 preprint
   misdescribed and needs its 10.64898 DOI, Nelson 2022 and Brierley 2022 omitted (18).
9. Numbers: all match (19).
10. Plain language: three of the four quoted claims need rewording (20).
