You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/seismology-geophysics-dynamic-triggering-strain-test/ (read-only except your
output in review/).

**The question.** Do distant (≥ 1,000 km) global M ≥ 7 earthquakes trigger small local earthquakes at western-US
stations more often than chance, and does the excess grow with peak dynamic strain? The study uses a catalogue-free
proxy from QuakeScope 2026 PhaseNet picks (3-station-coincident P–S pairs), a β ≥ 2 test of the 24 h post window
against a 7-day baseline, and an empirical null of 500 matched pseudo-triggers per station.

**Reported:**
- **H2 Refuted:** mean excess −0.003 (−0.007 to +0.001); 15,042 significant against 15,742 expected; 228,963 pairs,
  350 triggers, 1,496 stations.
- **H1 Inconclusive:** E5 −0.007 (−0.015 to +0.002), E1 +0.002; E5 − 3·E1 interval includes 0.
- All robustness variants agree.
- **D1 (post hoc):** an exposure correction for masked time removes most of the slight negative strain trend.
- **Exploratory:** a detection shadow during the surface waves.
- **Per trigger:** spread 10 times binomial; 39 triggers above 3 SE and 55 below.

**What to read:**
- plan.md, deviations.md, report.md, results/plausibility.md, results/attribution_ledger.csv.
- results/tables/: primary.json, coverage.json, pairs_*.parquet, null_*.parquet, proxy_validation.json,
  strain_check.*, handtrace.json, trigger_dispersion.json.
- code/: fetch.py, catalogs.py, proxy.py, windows.py, analyse.py, validate.py, strain_check.py, handtrace.py,
  trigger_dispersion.py, figures.py.
- **Data:** data/picks/ (531M picks, partitioned), data/proxy/ (hourly local-pair counts, neighbour counts,
  validation-day pairs), data/raw/ (stations, availability), data/cat/ (ComCat), data/manifest.csv.gz (frozen
  listing).

**Git.** Read-only git is fine. Verify that the plan (e0e884d) and the proxy, window, null and analysis code preceded
any count, and that D1 was logged after the primary result.

**Environment.** Use venv/bin/python with -I. Do NOT pip install. The machine is shared: use at most 8 workers. A full
windows.py run takes about 10–15 minutes. proxy.month((y, m)) recomputes one month in under a minute.

Check at least:

1. **Data.** Exact-duplicate removal (repeated processing runs); channel merging within 0.5 s; the frozen listing;
   the 7 partition-edge picks; whether the September–October 2026 re-read leaves stale or overlapping files.
2. **The proxy.**
   - P–S pairing (first S 0.8–8 s, no P between, up to 3 picks ahead); t0 = tP − 1.37(tS − tP).
   - The 3-station coincidence (neighbours "with picks that month"; 50 km; ±2.5 s) and teleseismic masking (TauP
     table, ±60 s, more than 1,000 km).
   - Is the 46% recall diagnostic right? Does recall vary by station density in a way that interacts with strain?
3. **Windows and null.**
   - Window arithmetic (hour rounding, wave-train end at 2.5 km/s plus 2 h, 7-day baseline) and the β statistic,
     including β = 0 when N = 0.
   - The validity rules: every station-day loaded, 2 or more neighbours, prior-30-day activity, local M ≥ 3.5 in the
     baseline.
   - Does the availability rule (1,496 of 9,336 stations qualify) bias the population?
   - Pseudo-trigger construction (hour matching, ±45 days, ±12 years, exclusions) and the deterministic seeding.
4. **Strain.** The Lay & Wallace inversion, the Mw cap at 8.3, and the quintiles. Is the strain check (Spearman 0.47,
   2,546 of 6,634 pairs measured) fair, and does it threaten H1?
5. **Analysis.** The two-way bootstrap with product weights; the H1 and H2 rules; whether "Inconclusive" and
   "Refuted" are right; whether the per-trigger dispersion claim is computed correctly.
6. **D1.** Is the exposure correction right (`windows.masked`, the interval union), and is it fairly labelled? Could
   masking bias anything else, such as baselines containing big earthquakes?
7. **Report.** Check every number against the tables, and that the title and plain terms are fair, including "no
   detectable remote dynamic triggering" given the proxy's recall.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered findings
(severity, evidence with file:line or your check's output, the fix). Put supporting scripts in
review/reviewer_checks/.

**Gate checks (METHODS.md G1–G7).** Verify:
- **G1:** plan.md section 7's leakage audit is real and complete; look for strain-correlated fields it missed.
- **G2:** `results/tables/coverage.json` exists (picks_fetch, picks_proxy and pairs_* stages), and no unplanned
  fallback entered a statistic.
- **G3:** `results/plausibility.md` traces three units, and the asserted invariants hold.
- **G4:** does not apply (no classifier or labelling; the proxy recall is a validation with its denominator); confirm.
- **G5:** `review/overclaim_check.md` passes and is honest; re-label any sentence you disagree with.
- **G6:** `results/attribution_ledger.csv` passes `python3 -I ../../tools/attribution.py check . --show`; spot-check
  5 claims against their sources, including the role and conditions.
- **G7:** does not apply (no labels); confirm.

Report any gate that is missing or hollow as a finding.
