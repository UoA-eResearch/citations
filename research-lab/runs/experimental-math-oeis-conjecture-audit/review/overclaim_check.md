# Overclaim check (G5)

Fill in every row: backing = the table/figure and number that supports the sentence; label = one of Supported, Partially supported, Overstated, Not addressed, Exploratory-labelled. Every Overstated / Not addressed / Partially supported row needs a fix (the rewritten sentence, applied to report.md). Re-run after edits; unchanged sentences keep their labels.

| # | where | sentence | backing | label | fix |
|---|---|---|---|---|---|
| 1 | title | Machine-guessed OEIS conjectures that fit their entry's terms almost always keep fitting: 3 of 3,114 fail against the b-file up to a median 185 terms further, and every falsification found was already noted in its entry; but hundreds of conjectured formulas are false as written by their entry's own terms | primary.json bdeep 3/3114, median 185; falsifications.csv notes; contradicted_audit.json | Supported | retitled after review |
| 2 | standfirst | Every OEIS entry (the OEIS data repository, 2026-10-25) was searched for formula lines marked "conjecture" or "empirical": 38,637 lines in 24,168 entries. | primary candidate_lines 38,637; entries 24,168 | Supported |  |
| 3 | standfirst | Linear recurrences, rational generating functions and P-recursive relations were parsed into exact predictors, checked against the entry's own terms, then compared beyond the data with the entry's LODA program and, for a random sample, directly with the entry's b-file. | parse.py, screen.py, bdeep.py | Supported |  |
| 4 | standfirst | The plan was committed before any entry was parsed. | git: plan before parse output | Supported |  |
| 5 | standfirst | Revised after an independent review (fix first; D2). | D2 | Supported |  |
| 6 | verdict | **Verdict: H1 Refuted by the preregistered rule (fewer than 100 confirmed falsifications). | primary.json H1_preregistered_rule Refuted; confirmed 3 | Supported |  |
| 7 | verdict | The accurate reading is "not supported within this pipeline's coverage", not a refutation of the claim.** | review finding 4; coverage counts | Supported | reworded at review |
| 8 | verdict | **H1 (at least 100 conjectured recurrences and g.f.s in OEIS are false, as shown by two independent term sources): fewer than 100 confirmed.** | primary.json confirmed_falsifications_all 3 | Supported |  |
| 9 | verdict | **3 confirmed lines** on 2 entries: A076217's g.f. | primary.json confirm confirmed 3; falsifications.csv | Supported |  |
| 10 | verdict | (it fails at n = 81) and two lines of A267515. | falsifications.csv A076217 first_fail 81 | Supported |  |
| 11 | verdict | None is new. | A267515 [Wrong] tag; A076217 later %F note (entry text) | Supported |  |
| 12 | verdict | A267515's block is tagged "[Wrong]" by editors, and A076217's entry carries a later note that the conjectured recurrence fails at powers of 3. | entry text A267515, A076217 | Supported |  |
| 13 | verdict | The rule was followed, but the count is a lower bound on a partial population (below), and the pipeline itself finds hundreds of statements false as written. | contradicted_audit.json; primary.json coverage | Supported |  |
| 14 | verdict | So "Refuted" means "not supported within this coverage". | review finding 4 | Supported |  |
| 15 | verdict | **Two strata, not one rate** (corrected after review). | primary.json screened_by_bfile_stratum | Supported |  |
| 16 | verdict | LODA programs are checked against up to 1,000 known terms, so where an entry has a b-file, LODA is not an independent source. | ledger O5 (LODA README full_check.txt) | Supported |  |
| 17 | verdict | **Entries with a b-file:** 1 of 11,778 screened conjectures disagrees with LODA beyond the data (0.008%; Wilson 0.002% to 0.048%). | primary.json with_bfile 1/11778 wilson [1.5e-5, 4.8e-4] | Supported |  |
| 18 | verdict | This is agreement with the b-file in practice. | ledger O5 | Supported |  |
| 19 | verdict | **Entries without a b-file:** 13 of 1,767 disagree (0.74%; 0.43% to 1.25%). | primary.json without_bfile 13/1767 wilson [0.0043, 0.0125] | Supported |  |
| 20 | verdict | There LODA was mined on the data alone, so these disagreements are unresolved extrapolations, not near-zero error. | review finding 2; confirm.parquet bfile_too_short 13 | Supported |  |
| 21 | verdict | None can be confirmed: the b-file holds only the published terms. | primary.json confirm bfile_too_short 13 | Supported |  |
| 22 | verdict | The first draft pooled these into one rate (0.10%) and called LODA independent throughout. | primary_v1 (review) | Supported |  |
| 23 | verdict | **A direct b-file test** (post hoc; finding 5). | primary.json bdeep | Supported |  |
| 24 | verdict | The plan allowed 2,000 b-file fetches and the confirmation used 13. | plan section 1; confirm.parquet 13 entries | Supported |  |
| 25 | verdict | The rest went to a seeded random sample of 1,987 of the 8,586 entries with a b-file and a consistent conjecture. | bdeep_meta.json sampled 1987, population 8586 | Supported |  |
| 26 | verdict | 3,114 conjectures were compared with up to 1,000 b-file terms each, a median of 185 terms beyond the data (10th to 90th percentile 105 to 717). | primary.json bdeep lines_tested 3114; beyond_data_checked median 185 p10 105 p90 717 | Supported |  |
| 27 | verdict | 3 fail, on 2 entries: 0.10% (Wilson 0.03% to 0.28%). | primary.json bdeep contradicted 3/3114 wilson [0.00033, 0.0028] | Supported |  |
| 28 | verdict | Both failures lie beyond the LODA screen's depth (a(62) on A267514; 532 terms beyond the data on A210247), and both are noted in later lines of their entries. | bdeep_contradictions.csv; entry text | Supported |  |
| 29 | verdict | Scaled to the 13,510 consistent conjectures on entries with b-files, that suggests about 13 contradicted by their b-file (roughly 4 to 38). | bdeep_meta.json population_lines 13510 x rate | Supported |  |
| 30 | verdict | This is one source of terms, not the plan's two. | design | Supported |  |
| 31 | verdict | **False as written by the entry's own terms.** 747 parsed lines contradict their own entry's data. | contradicted_audit.json contradicted_lines 747 | Supported |  |
| 32 | verdict | The first draft set these aside as "mostly conditions the parser ignores", which was wrong (finding 3): | review finding 3 | Supported |  |
| 33 | verdict | **188 state a range that starts too early** (183 in "Conjectures from …" blocks), and hold from a median 2.5 indices later. | contradicted_audit.json stated_range_too_early 188, in_block 183, shift median 2.5 | Supported |  |
| 34 | verdict | They are false as written, by a boundary slip. | contradicted_audit.json | Supported |  |
| 35 | verdict | 107 hold only from a later index with no range stated, and 8 g.f.s match with a shifted offset. | contradicted_audit.json holds_from_later_index 107, gf_offset_slip 8 | Supported |  |
| 36 | verdict | 328 carry a parity or residue condition the parser ignores, in the line or in the next formula line. 13 more carry other conditional wording, and 2 are exponential g.f.s (corrected after the confirmation pass). | contradicted_audit.json (D3) parity_or_residue 328, conditional_wording 13, egf 2 | Supported |  |
| 37 | verdict | **101 are contradicted with no mechanical explanation** (61 recurrences or g.f.s, 40 polynomial closed forms). | contradicted_audit.json no_simple_fix 101 (P 40, G 27, D 20, C 14) | Supported |  |
| 38 | verdict | They are listed by A-number for editors in `results/tables/contradicted_no_simple_fix.csv`. | contradicted_no_simple_fix.csv | Supported |  |
| 39 | verdict | 29 of the first draft's 776 were parser artefacts and are now consistent. | contradicted_audit.json first_draft_contradicted_now consistent 29 | Supported |  |
| 40 | plain terms | The Online Encyclopedia of Integer Sequences (OEIS) is mathematics' great catalogue of number sequences. | background | Supported |  |
| 41 | plain terms | Thousands of its entries carry formulas found by computer: a program looks at the known terms and guesses a rule that fits them, recorded as "Conjecture" or "Empirical". | OEIS conjecture/empirical keywords | Supported |  |
| 42 | plain terms | A guess that fits 40 terms could fail at the 41st, so how many are wrong? | framing | Supported |  |
| 43 | plain terms | We turned about 21,000 of these guessed formulas into code. | primary.json parsed C/G/D 20,932 | Supported |  |
| 44 | plain terms | Where an entry has a longer list of terms on file (a "b-file"), we tested a random sample of about 3,100 guesses against it, a median of 185 terms beyond what the guesser saw. | primary.json bdeep | Supported |  |
| 45 | plain terms | Only 3 failed, and the encyclopedia had already noted both of the entries involved. | bdeep_contradictions.csv; entry text | Supported |  |
| 46 | plain terms | Comparing with programs from the LODA project found 14 disagreements; the one new to us that we could check (A076217) was also already known. | falsifications.csv A076217 (only untagged confirmed); entry note | Supported |  |
| 47 | plain terms | But the check turned up a different kind of error. | contradicted_audit.json | Supported |  |
| 48 | plain terms | Hundreds of the guessed formulas don't even fit the terms printed in their own entry. 188 state a range that starts a few terms too early and 107 more hold only from a later index, slips in how the range was written, and about 100 more fail for no obvious reason. | contradicted_audit.json stated_range_too_early 188, holds_from_later_index 107, no_simple_fix 101 | Supported |  |
| 49 | plain terms | Those are listed for the editors. | contradicted_no_simple_fix.csv | Supported |  |
| 50 | plain terms | So formulas that fit their entry keep fitting far beyond it, and the editors have caught the failures we could confirm. | primary.json bdeep; confirmed all noted | Supported |  |
| 51 | plain terms | The weaker point seems to be how the formulas are written down. | contradicted_audit.json vs primary.json bdeep (interpretation) | Supported | softened |
