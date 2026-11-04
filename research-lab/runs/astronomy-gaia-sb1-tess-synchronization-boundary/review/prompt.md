You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is
wrong, unsupported or overstated before the verdict is published. Do not soften findings. Be economical with tokens:
quota is tight and only one review runs at a time.

Study: /mnt/citations/research-lab/runs/astronomy-gaia-sb1-tess-synchronization-boundary/ (read-only except your
output in review/).

**The question.** In Gaia DR3's main-sequence SB1 binaries (P_orb < 10 d), does the TESS-measured synchronized
fraction step from above 70% (below 6,200 K) to below 30% (above 6,500 K) across the Kraft break (H1), and does
synchronization reach longer orbital periods than circularization (H2)?

**Reported:**
- **H1 Refuted.** f_cool 0.205 (0.187–0.225), f_hot 0.093; the transition is near 6,300 K per a profile likelihood.
- **H2 not estimable.** Neither share reaches 0.5 at any period; the e < 0.05 criterion is unsuited to Gaia
  eccentricities.
- **The report argues the 20% is a floor, partly measurement.** Its evidence: the share rises with the number of
  detecting sectors and with brightness; the G4 visual audit found 16 of 30 periods incoherent; only 41 of 135 agree
  with Gaia DR3 rotation periods.
- **D1** excluded QLP light curves from the primary before classification: 99.5% detection rate, half at 9–13 d.

**What to read:** plan.md; deviations.md (D1); report.md; results/plausibility.md; code/ (gaia, sample, tic_match,
lc_index, qlp_index, download, periods, classify, inject, analyse, posthoc, g3_traces, g4_check, g4_visual,
coverage_lc); results/tables/ (primary, secondary, posthoc, completeness*, coverage, g3_traces, g4_check,
g4_gaia_rotation, g4_visual_sample); results/figures/g4_folded.png. Data under data/ (not in git, 74 GB of light
curves under data/lc/, read freely): sample.parquet, tic.parquet, lc_index.parquet, sector_periods*.parquet,
stars*.parquet, injections.parquet.

**Git.** Read-only git is fine. Verify that plan.md preceded the first data download, and that D1 and classify.py's
ellipsoidal-before-doubling rule preceded the first classification (logs/, file times, commit order).

**Environment.** Python is venv/bin/python, with -I (local imports need the code directory on sys.path). Do NOT pip
install. At most 4 processes. The Gaia archive works through astroquery but returns sporadic HTTP 500s (and a 500
for a bad column name). VizieR is unreachable from this machine. Put scripts and outputs under
review/reviewer_checks/.

Check at least:

1. **The detection rule.** FAP < 1e-5 by Baluev on red-noise TESS light curves: how many detections are real? Is
   the report's "floor" argument sound, or could the bias run the other way?
2. **Classification.**
   - the 10% windows, the Hut pseudo-synchronous target with noise-inflated Gaia eccentricities, the
     ellipsoidal-before-doubling rule, the beaming and pulsator rules;
   - the "inconsistent" class (7,267 stars, mostly P/2P flips);
   - whether these rules bias the synchronized share in a predictable direction.
3. **D1.** Was excluding QLP decided blind to outcomes? Does it bias the sample, by brightness or ecliptic latitude?
4. **Completeness weighting.** The injection model, hosts (1,792 non-detections), cell fallbacks, and the C < 0.1
   drop.
5. **H1 statistics.** The bootstrap, the Teff logistic (its T0 sat at a starting value), and the profile-likelihood
   claim of 6,300 K.
6. **H2.** Is "not estimable" the right label under the plan's rule? Is the eccentricity-noise explanation right?
7. **Sample.** The main-sequence band, dereddening, the TIC match, and SB1 selection effects.
8. **Report.** Every number against the tables; the plain-terms section; whether "a fifth" and "near the Kraft
   break" are fair.

Write review/review.md: a verdict (publish / publish with edits / fix first / do not publish), then numbered
findings (severity, evidence with file:line or your check's output, the fix). Paraphrase rather than quote any
source text; the lab never commits quoted source text.

> **Gate checks (METHODS.md G1–G7).** Verify:
> - **G1:** plan.md's leakage audit is real and complete; look for label-correlated fields it missed.
> - **G2:** `results/tables/coverage.json` exists, and no unplanned fallback entered a statistic.
> - **G3:** `results/plausibility.md` traces three units, and the asserted invariants hold.
> - **G4:** every validation metric has an error audit with a judgeable denominator.
> - **G5:** `review/overclaim_check.md` passes and is honest; re-label any sentence you disagree with.
> - **G6:** `results/attribution_ledger.csv` passes `tools/attribution.py check`; spot-check the claims against
>   their sources, including the role and conditions. Check titles, not just resolution.
> - **G7:** validation labels come from two blind labellers (does not apply here; confirm).
>
> Report any gate that is missing or hollow as a finding.

When you finish, reply with a short summary: the verdict and a one-line description of each finding.
