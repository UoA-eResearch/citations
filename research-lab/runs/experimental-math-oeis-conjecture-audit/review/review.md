# Review: experimental-math-oeis-conjecture-audit

Reviewer: independent adversarial review (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`dump15.py/.txt`, `checks2.py`–`checks7.py` with `.txt` outputs, `bfile_reach.csv`, `loda_structure.csv`).
All checks used `venv/bin/python -I` with `code/` on `sys.path`. The LODA binary could not be executed under the
reviewer's sandbox (executing a downloaded binary from `data/` is blocked), so LODA-side values were not recomputed;
the two confirmed falsifications were instead checked against independent ground truth (finding 6).

## Verdict: fix first

The headline survives: of the 15 screened disagreements, the 2 confirmed falsifications (A076217, A267515) are
genuine, and I found no false disagreement among the 15 and no misparse in a 30-case sample of "agree" lines.
But three things in the report are wrong as written and must be fixed before publication: (1) the funnel count
"21,998 consistent with own data" includes 4,190 conjectures whose data check was vacuous (zero data terms
checked), and 31 "agree" cases were compared on zero terms beyond the data; (2) the "two independent sources"
framing is false for 87% of the screened lines, because LODA programs are verified against the entry's b-file, and
the disagreement rate differs 45-fold between the stratum with and without a b-file; (3) the G4 audit's
statement that the 776 self-contradicted lines "carry a condition the parser ignores" is the opposite of what the
data show for the largest category (the parser applied the stated range and the statement as written is false).

## Findings

### 1. (Major) 4,190 of the 21,998 "consistent with own data" conjectures were never checked against any data term

Evidence: `checks3.txt` §A and `checks4.txt`. `run_rec` (`code/parse.py:144-168`) starts the relation at
`max(start, offset+order)` and reports `data_ok=True` when the loop never reaches a data index. For 4,190 parsed
class-C lines (2,103 with recurrence order ≥ number of data terms, 2,087 with a stated "for n > k" beyond the
data; typically Hardin-style empirical recurrences of order 13–98 on entries with 9–26 terms, e.g. A237392,
A205092, A317380) zero data terms were checked. A further 625 lines checked 1–3 terms. The unit test
`checks4.txt` ("for n > 100" on five terms → `data_ok=True`) reproduces the bug. Downstream: all 104
"predict_failed" units and 49 "agree" units are in this group; 31 "agree" units have
`beyond_data_checked = 0`, i.e. they were counted as agreeing with LODA on no term at all, contrary to plan §3
("at least one term beyond the data") and `screen.py:77` has no check for it.

Fix: add a third data-check status ("unchecked", n_checked = 0) and a minimum (say ≥ 5 data terms checked) for
"data-consistent"; require `beyond_data_checked ≥ 1` for "agree"; recompute the funnel (consistent ≈ 17,808; screened
≈ 14,640; the 15/0.10% headline barely moves). State in the report that these conjectures (mostly Hardin's) cannot
be tested from the displayed terms.

### 2. (Major) The "independent programs" framing is wrong for most screened lines; the disagreement rate is a mixture of two very different strata

Evidence: `checks2.txt` §5, `checks3.txt` §B, `bfile_reach.csv`. The LODA miner verifies programs against the
OEIS b-file (loda-programs README: programs are checked against "the default number of terms (up to 1,000)" of the
sequence; the interpreter's own strings refer to reading b-files). Using the Git-LFS pointer sizes in
`data/raw/oeisdata/files/`, 7,391 of the 8,827 screened entries have a b-file, and its size is typically 41× that of
a data-only file (median ratio; 80% ≥ 4×), so for those entries every LODA term the study compared (at most 2×
the data length ≤ 220 terms) was already enforced to equal the b-file. "LODA agrees beyond the data" there means
"the conjecture agrees with the b-file", which is good evidence but not a second independent source and not what
the title/standfirst say. The other 1,436 entries have no b-file (oeis.org serves the data terms as a synthetic
b-file; that is why all 13 "unconfirmable" cases have `bfile_max` = last data index): there the LODA program was
mined on the data alone and its extrapolation is just another fit.

Stratified: lines on entries with a b-file 12,826 screened, 2 disagree (0.016%); without a b-file 1,845 screened,
13 disagree (0.70%). The report's single rate (0.10%, Wilson 0.06–0.17%) averages a stratum where disagreement
within range is essentially a b-file contradiction with a stratum where LODA is unconstrained beyond the data and
disagreements are uninterpretable (A049609's program uses an integer fifth root, A162764's a bitwise OR and a
log, A261667's a chain of integer divisions — see `dump15.txt`). Additionally, among "agree" class-C lines, 150
LODA programs whose formula comment is a constant-coefficient linear recurrence encode the *identical* recurrence
to the conjecture (`checks4.txt`), so agreement is tautological for them (and for an unknown number of loop-form
programs without a formula comment).

Fix: report the two strata separately; retitle ("agree with the entry's b-file (median 26 further terms) …" or
similar); drop "independent" for the b-file stratum; explain in Limits that LODA is validated against b-files;
treat the 0.70% no-b-file rate as "unresolved" rather than as near-zero error. G1 (independence) should be
recorded as failing for the b-file stratum.

### 3. (Major) The G4 audit of the 776 self-contradicted lines is mis-described in the report

Evidence: `checks5.txt`, `checks6.txt`, `code/contradicted_audit.py:233`. The report (Coverage bullet) says most of
the 776 "carry a condition the parser ignores: 541 (70%) mention an index restriction such as 'for n > k' (385) or
a parity or residue condition (167)". For 372 of the 385 index-restriction lines the parser did *not* ignore the
condition: it set `start` from it. 349 of those fail within two terms of the stated start, and hand checks
(A282801, A286430, A288020, A219211) show the stated range is simply wrong (e.g. A286430 "for n > 2" fails at
n = 4, 5, 6 and holds from n = 7; A282801 "for n > 3" fails at n = 5 and holds from n = 7). These are Barker-block
statements (354 of 372 are `in_block`) that are false as written, by a trivially fixable boundary. At least one is a
genuine falsification by the entry's own terms (A202303: predicted 52606008, data 52606009 at n = 22). The
parity lines (167) are correctly described as ignored. Separately, 31 of the 141 class-D contradictions are parser
artefacts: the leading polynomial vanishes exactly at the first mismatch (`run_rec` returns `False` at
`lead == 0`, `parse.py:154`), e.g. A001784, A094294; 79 have a vanishing lead somewhere in the data range.

Fix: rewrite the bullet; split the 776 into (a) stated range too early (boundary error, false as written), (b)
ignored parity/residue condition, (c) parser artefact (vanishing lead; shifted-form start, finding 7), (d)
contradicted with no condition (candidates for real falsification, worth listing for editors). Overclaim-check row
19 should be relabelled.

### 4. (Moderate) "Refuted" is not the right word for a lower bound below the threshold

Evidence: plan §0 defines the count as a lower bound and §5 says coverage is partial; `primary.json` H1 "Refuted".
Failing to find 100 confirmed falsifications among 14,671 lines checked over ≤ 2× the data length does not refute
"at least 100 of the conjectured recurrences and g.f.s recorded in OEIS are false": 7,221 lines were unscreened,
14,322 unparsed, 4,190 unchecked (finding 1), and the pipeline itself turned up hundreds of statements that are
false as written in the 776 it set aside (finding 3). The preregistered decision rule was followed, so the verdict
line can stay, but the report must say "not supported within this pipeline's coverage" and must not let the plain-terms
section ("highly reliable") stand on the pooled rate (finding 2).

Fix: reword the verdict bullet and the plain-terms paragraph; add the stratified rates.

### 5. (Moderate) The comparison depth was capped by design, not by the data; the plan's b-file budget went unused

Evidence: `checks2.txt` §2: `beyond_data_checked == nterms` for 14,637 of 14,671 lines; relative depth
quantiles are exactly 1.0. The plan allowed 2,000 b-file fetches; 13 were made. B-files exist for 84% of screened
entries and are typically 40× the data length (finding 2), so the conjectures could have been tested directly
against ~1,000 b-file terms for a random 2,000-entry sample without LODA at all. "The test is short-range" is
presented as a limitation of the data; it is a choice.

Fix: either run the b-file comparison on a random sample within the plan's budget, or state plainly that the
depth was a design cap.

### 6. (Confirmatory) Both confirmed falsifications are genuine; A267515 adds nothing new

Evidence: `checks3.txt` §D, `checks4.txt`. A076217 recomputed from its definition agrees with the b-file for
n ≤ 119; the conjectured g.f. predicts 0 at n = 81 where the sequence has 81 (the resets at n = 3^k are not in
the g.f.). A267515 recomputed by simulating Rule 137 with a flipping background agrees with the data and b-file
for n ≤ 70; the conjectured recurrence first fails at n = 62 (…644 vs …645). But the entry already carries the
block header "[Incorrect] conjectures …", "[Wrong]" on the line, and a 2019 editor note stating that the
recurrence "starts to generate erroneous values at a(62)". The study's "confirmation" reproduces a documented
fact. The g.f. on the next line of the same block (also "[Wrong]") was not parsed because the tag text fails the
letter check in `parse_gf`, so the two lines of one block were treated inconsistently.

Fix: say in the verdict that A267515 was already documented as failing at a(62), so there is one new confirmed
falsification; exclude lines tagged [Wrong]/[Incorrect] (or their blocks) from the candidate set, or report them as
a separate class.

### 7. (Minor, parser) Shifted-form recurrences get the wrong start; "[Wrong]" and "(conjectured)" scoping

Evidence: `checks6.txt` (A364470 "a(n+4) = 4*a(n) for n >= 7": parser starts at a(7), should start at a(11); the
data satisfy the statement), `checks7.txt` (11 parsed lines written with a(n+k); 5 have an explicit start and all
5 are "contradicted"). `parse.py:92-95` sets `start` before the re-indexing at line 120 and never adds `top`.
Also A301424 (`dump15.txt`): the only "(conjectured)" in the line refers to the factorisation of the denominator,
which is true (I expanded it), while the g.f. itself is stated as fact; it is counted among the 15 disagreements
as a conjecture. Keyword selection cannot tell what the keyword modifies.

Fix: `start += top` when `top > 0`; drop A301424 from the disagreement list or flag it; note the limitation.

### 8. (Minor) Class "C" is not "constant-coefficient recurrences"

Evidence: `checks3.txt` §A: 1,464 data-consistent class-C lines have no lag at all (polynomial closed forms such as
A201976 "a(n) = (89/36)*n^6 + …"); 1,031 of them are in the screened set; 379 of the 597 class-C contradictions
are such closed forms. `parse.py:133` assigns "C" whenever all lag coefficients are constant, vacuously so.

Fix: add a class "P" (polynomial closed form) or exclude them; recompute the by-class table.

### 9. (Minor) Selection into the screened set is strongly non-random

Evidence: `checks2.txt` §1. Share with no LODA program: 7% for entries with keyword "easy" vs 36% otherwise; 7% for
A000001–A100000 vs 35% for A200001 onward; 8% for in-block (Barker) lines vs 40% for others; class D is almost fully
screened (64 of 861 without a program). The screened conjectures sit on simpler, older, better-studied sequences.
The report mentions coverage only as a count.

Fix: one sentence and a small table stating these shares; say the rate applies to LODA-covered entries.

### 10. (Minor) Reporting and reproducibility details

- `screen.parquet` stores neither the LODA term nor the predicted term at the disagreement, so "65,287,195,195
  against …194" and "eight are off by small amounts" cannot be checked from the outputs (I verified the predicted
  side only). Fix: store both values.
- "15 requests" (How it was done): 13 distinct A-numbers were fetched (`confirm()` caches per entry).
- `screen.py:157`: the label `confirmed_earlier_than_screen` is attached when the b-file fails *later* than the
  LODA index (zero cases, but the name is inverted and such a case would not be a two-source confirmation).
- 20 lines in the screened set say the conjecture was later proved or verified (`checks2.txt` §3); harmless for the
  count but contrary to "nobody has proved most of these rules" being the population.
- 41 of 5,921 screened g.f.s matched only under the shifted convention (`checks5.txt`); fine, but say so.
- D1 timing: `data/loda-home` was created at 03:03:28 and the D1 commit is 03:04:13, so screening had started
  about 45 s before the commit that records "before any screening". The deviation itself (parser scope) was
  decided at the 02:59 parse, so the substance holds.

## Gate checks

- **G1 (independence):** fails for the b-file stratum (finding 2). 150 identical-recurrence LODA programs found.
- **G2/G4 (dropped units, unaudited claims):** the 104 predictor failures hide no falsification — all 104 are in
  the zero-checked group of finding 1 and could not be evaluated at all. The G4 keyword audit exists but its
  interpretation in the report is wrong (finding 3).
- **G5 (`review/overclaim_check.md`):** present and mostly honest; rows 1, 10, 19, 32 need relabelling after findings
  2, 3 and 4 (row 1's "independent programs" is Overstated; row 19 is Not supported as written).
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (7 claims)". O5's condition
  ("programs are machine-mined (independent of the formula lines)") is the claim finding 2 contradicts.
- **Timeline:** plan commit 02:53 precedes the parser commit 02:56 and the parse output (02:59); D1 commit 03:04
  precedes the screen output (03:05). Unit tests in `parse.py test` pass.

## Numbers checked against the tables

All counts in the report match `primary.json` and `falsifications.csv` (38,637 / 24,168; 22,774 = 15,306 +
6,466 + 1,002; 21,998 / 776; 14,671 = 7,953 + 5,921 + 797; 15 = 3 + 10 + 2; 13 + 2; 7,221 / 104 / 2; median 26,
p10 18, p90 46). The numbers are internally consistent; findings 1, 3 and 8 are about what they measure.
