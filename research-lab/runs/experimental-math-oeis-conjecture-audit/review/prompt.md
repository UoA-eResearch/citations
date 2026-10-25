You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/experimental-math-oeis-conjecture-audit/ (read-only except your output in
review/).

**The question.** Are at least 100 machine-guessed OEIS conjectures (linear recurrences, rational g.f.s, P-recursive
relations) false, as shown by an independent LODA program and the entry's b-file?

**Reported:** H1 Refuted. 14,671 screened; 15 disagree with LODA beyond the data; 2 confirmed by b-files (A076217,
A267515). 13 are unconfirmable because their b-files cover only the data.

**What to read:** plan.md, deviations.md (D1 parser scope before screening), report.md, code/ (parse.py,
screen.py, analyse.py, figures.py) and results/tables/ (primary.json, falsifications.csv). The data are in
data/interim/*.parquet. The raw OEIS entries are in data/raw/oeisdata/seq, the LODA programs in
data/raw/loda-programs, the interpreter at data/raw/loda (set LODA_HOME=data/loda-home and HOME=data/loda-home), and
b-files in data/bfiles/*.json.

**Git.** Read-only git is fine. Verify that the plan preceded parsing, and D1 the screening.

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. Keep CPU to at most 8 processes. Do NOT
fetch from oeis.org beyond 20 requests in total, at most 1 per second.

Check at least:

1. **Parser correctness, both directions.**
   - False agreements: could a misparse make a wrong conjecture "agree", for example a recurrence parsed with the
     wrong start or g.f. offset alignment (run_gf's two conventions)? Spot-check about 30 "agree" cases by hand
     against the entry text.
   - False disagreements: check all 15 disagreements by hand.
   - Are recurrences with "for n > k" handled right at the boundary?
2. **The data check** as a filter. The 776 own-data contradictions are claimed to be mostly parser artefacts. Sample
   and verify. Are any real typos or errors in OEIS?
3. **Screening.**
   - LODA term alignment with the offset (b-file format output), the 20 s limit, and the "agree" requirement (at
     least one term beyond the data).
   - The beyond-data depth (median 26): is the test deep enough to support "almost always hold"?
   - The "no_program" share (7,221): is there any bias in which conjectures get screened?
4. **Confirmation.** The b-file parsing, the data agreement, and the rule. Are A076217 and A267515 genuinely false?
   Is A267515's "[Wrong]" tag handled honestly?
5. **Interpretation and report.**
   - Is "Refuted" fair given coverage (a lower bound by design)?
   - Do the plain-terms section and title overstate reliability, given the short range?
   - Check every number against the tables.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7; this study predates the gates, so G5 and G6 were run as a pre-review gate).**
Verify:
- **G5:** `review/overclaim_check.md` passes and is honest.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check . --show`.
- **G2/G4:** the newly stated screening drops (104 predictor failures) — could they hide falsifications? Check the
  keyword audit of the 776 self-contradicted lines (`code/contradicted_audit.py`).
- **G1:** is the LODA program truly independent of the conjecture (programs mined from the same terms or formula)?

Report any gate that is missing or hollow as a finding.
