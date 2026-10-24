You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/computational-reproducibility-notebook-noise-aware-verdicts/ (read-only except
your output in review/).

**The question.** Among PMC-linked Python notebooks that run but fail exact output matching, is every mismatch
run-to-run variability in at least 30% (H1)? Do exact-match verdicts overstate irreproducibility by at least 1.4×
(H2)?

**Reported:**
- **H1 Inconclusive:** 7/34, 20.6%, Wilson 10.4–36.8%.
- **H2 Inconclusive:** 1.26, 1.09–1.58.
- **Validation:** 94/100.
- **D3:** a plotting-backend bug forced a full re-run, after a first comparison.

**What to read:** plan.md, deviations.md (D1–D3), report.md, code/ (select_nb.py, runner.py, compare.py, figures.py,
import_map.json) and results/tables/ (primary.json, notebooks.csv, validation.json, posthoc_*.json,
primary_pass_agg_bug.json). Executed notebooks are in data/runs/<nbid>/ (asof_1..3, latest_1, with JSON status).
Repositories are in data/repos/. Sample files are in data/interim/.

**Git.** Read-only git is fine. Check the D3 timeline honestly: what was seen before the re-run?

**Environment.** Python is venv/bin/python, with -I. Do NOT pip install. Do NOT execute any notebook or repository
code on the host, and do not run Docker containers yourself. Work from the stored outputs. Keep CPU moderate. Put
scripts under review/reviewer_checks/.

Check at least:

1. **Selection.** The D1 eligibility fields against the dataset's schema. The as-of checkout. Notebooks whose stored
   outputs at that commit differ from what the dataset compared against. Repository size filtering (GitHub sizes)
   and bias.
2. **Environments.** The import map and requirements discovery. D2's full-image retry (is it fair, and does it bias
   the completing set?). AS-OF and LATEST image mismatch for the retried notebooks.
3. **The comparator.** Masking rules (over-masking that hides real differences?), displayed-precision rounding,
   perceptual hash, the envelope rule, and the decision to exclude stderr and error outputs. Re-label a fresh sample
   of about 30 cells yourself.
4. **The intrinsic definition and H1/H2 arithmetic.** Are shell "command not found" cells handled sensibly? Is H2's
   base (only the dataset's irreproducible notebooks) properly caveated?
5. **D3.** Is the bug fix complete? Do any other environment settings (for example the backend, timezone or locale)
   distort outputs?
6. **Report.** Check every number against the tables. Are the title, the plain-terms section and the "40% now match"
   claim fair?

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.
