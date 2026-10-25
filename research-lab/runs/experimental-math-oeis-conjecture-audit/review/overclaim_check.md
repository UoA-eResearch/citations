# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Machine-guessed OEIS conjectures almost always agree with independent programs beyond the data: of 14,671 screened, 15 disagree and only 2 are confirmed false | primary screened 14,671; disagree 15; confirmed 2 | Supported | was 'almost always hold' (checked a median of 26 terms beyond the data, against programs); now 'agree with independent programs beyond the data' |
| 2 | standfirst | Every OEIS entry (the OEIS data repository, 2026-10-25) was searched for formula lines marked "conjecture" or "empirical": 38,637 lines in 24,168 entries. | primary candidate_lines 38,637; entries 24,168 | Supported |  |
| 3 | standfirst | Linear recurrences, rational generating functions and P-recursive relations were parsed into exact predictors, run beyond each entry's data, and compared with the entry's LODA program, run locally. | plan.md; parse.py classes C/G/D | Supported |  |
| 4 | standfirst | Disagreements were checked against the entry's b-file. | confirm.parquet | Supported |  |
| 5 | standfirst | The plan was committed before any entry was parsed. | git: plan before parse output | Supported |  |
| 6 | verdict | **Verdict: H1 Refuted.** | primary H1 Refuted | Supported |  |
| 7 | verdict | **H1 (at least 100 machine-guessed conjectures are false, as shown by two independent term sources): Refuted.** | plan.md H1 | Supported |  |
| 8 | verdict | **2 confirmed falsifications** (A076217 and A267515; the latter was already marked "[Wrong]" by OEIS editors). | falsifications.csv; confirmed 2; ledger O6 | Supported |  |
| 9 | verdict | **Screening.** | heading | Supported |  |
| 10 | verdict | Of the 14,671 data-consistent conjectures with a working LODA program, **15 disagree with it** beyond the data: a rate of 0.10% (Wilson 95% interval 0.06% to 0.17%). | screened_disagree_rate 0.00102 (Wilson 0.00062-0.00169) | Supported |  |
| 11 | verdict | The comparison reaches a median of 26 terms beyond the published data (10th–90th percentile: 18 to 46). | beyond_data_terms_checked median 26, p10 18, p90 46 | Supported |  |
| 12 | verdict | **Most disagreements cannot be confirmed.** For 13 of the 15, the b-file holds only the published terms, so there is no second source. | confirm bfile_too_short 13 | Supported |  |
| 13 | verdict | Eight are off by small amounts at large indices (for example 65,287,195,195 against …194). | falsifications.csv first_disagree values | Supported |  |
| 14 | verdict | Several are on floor-of-ratio or "rounded down" sequences, where a rational g.f. can fit for dozens of terms and then drift. | falsifications.csv entry keywords (descriptive) | Supported |  |
| 15 | verdict | These 13 are listed for OEIS editors, not counted as false. | confirm bfile_too_short 13 listed, not counted | Supported |  |
| 16 | verdict | **By class:** | by_class table matches primary.json by_class | Supported |  |
| 17 | verdict | **Coverage.** | heading | Supported |  |
| 18 | verdict | 22,774 lines parsed; 21,998 consistent with their own data. | status parsed 22,774; data_consistent 21,998 | Supported |  |
| 19 | verdict | Most of the 776 that are not carry a condition the parser ignores: 541 (70%) mention an index restriction such as "for n > k" (385) or a parity or residue condition (167). | contradicted_audit.json: 541 of 776 with condition keywords (385 index, 167 parity) | Supported | was 'mostly parsing artefacts: for n even, e.g.f.s, iff' (unaudited; e.g.f. and iff are 2 and 4) |
| 20 | verdict | Exponential g.f.s and "if and only if" statements are rare (2 and 4) (`results/tables/contradicted_audit.json`). | contradicted_audit.json e.g.f. 2, iff 4 | Supported |  |
| 21 | verdict | 7,221 data-consistent conjectures have no LODA program and were not screened. | screen no_program 7,221 | Supported |  |
| 22 | verdict | A further 104 whose predictor failed to run, and 2 whose LODA output was short or mismatched, were also left out of the 14,671. | screen predict_failed 104; loda_mismatch_or_short 2 | Supported | added at the gate (G2: these units were dropped silently) |
| 23 | plain terms | The Online Encyclopedia of Integer Sequences (OEIS) is mathematics' great catalogue of number sequences. | background | Supported |  |
| 24 | plain terms | Thousands of its entries carry formulas found by computer: a program looks at the known terms and guesses a rule that fits them, recorded as "Conjecture" or "Empirical". | OEIS conjecture/empirical keywords | Supported |  |
| 25 | plain terms | Nobody has proved most of these rules. | formula lines marked conjecture or empirical | Supported |  |
| 26 | plain terms | A guess that fits 40 terms could fail at the 41st, so how many of them are wrong? | illustrative | Supported |  |
| 27 | plain terms | We turned about 22,000 of these guessed formulas into code. | parsed 22,774 | Supported |  |
| 28 | plain terms | For each one that also has an independent program in the LODA project, we computed further terms both ways and compared them. | screen with LODA programs | Supported |  |
| 29 | plain terms | Disagreements were rare: 15 out of 14,671. | 15 of 14,671 | Supported |  |
| 30 | plain terms | Only 2 could be confirmed with a third, independent list of terms. | confirmed 2 (b-file) | Supported |  |
| 31 | plain terms | One of those was already flagged as wrong by the encyclopedia's editors. | A267515 [Wrong] (ledger O6) | Supported |  |
| 32 | plain terms | So the computer-guessed formulas in the OEIS are, as far as this check reaches, highly reliable. | disagree rate 0.10% over a median 26 terms (hedged) | Supported |  |
| 33 | plain terms | The handful of disagreements are worth an editor's look. | 13 disagreements listed for editors | Supported |  |
