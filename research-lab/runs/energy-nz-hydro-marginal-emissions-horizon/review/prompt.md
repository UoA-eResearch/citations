You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/energy-nz-hydro-marginal-emissions-horizon/ (read-only except your output in
review/).

**The question.** In New Zealand's hydro-dominated grid, how large is the marginal emissions factor (MEF) of extra
demand as a function of the horizon over which emissions are counted, and does carbon-aware (average-factor-guided)
load shifting capture the saving it claims?

**Design.**
- Half-hourly data, 2015–2024:
  - EMI metered generation by unit;
  - Tiwai offtake and HVDC transfers;
  - HMD daily storage and inflows;
  - Open-Meteo temperature.
- An emissions ledger: heat rates × MfE fuel factors, with geothermal at 0.10 t/MWh, calibrated annually to MfE's
  grid-average CO2 factor (D1).
- **MEF(h) by 2SLS.** The window's emissions sum is regressed on the window's demand sum. The instrument is the
  population-weighted heating-degree anomaly at t.
- **Controls:** the previous day's anomalies, lags, storage, inflows, HVDC, Tiwai, wind over the window, and fixed
  effects.
- **Inference:** a calendar-month block bootstrap.

**Hypotheses.**
- **H1:** MEF(30 d) − MEF(1 h) > 0.
- **H2:** an AEF-guided daily scheduler captures < 0.5 of its claimed saving, scored with time-of-day MEFs at 1 d.
- **H3:** MEF(1 d) is higher in the low-storage tercile than the high.
- **Rule:** any hypothesis resting on a first stage with F < 10 is Inconclusive.

**What to read:**
- plan.md (preregistration, commit df14d01);
- deviations.md (D1 and its addenda);
- report.md and report.html (pre-review draft, commit 456a6f6);
- code/: fetch.py, series.py, mef.py, simulate.py, checks.py, figures.py;
- results/tables/: mef.json, mef_horizons.csv, simulation.json, checks.json, ledger_calibration.csv;
- data/:
  - raw/ (EMI generation, tiwai, hvdc, grid_export, hmd, temperature, mfe; SHA256SUMS);
  - series.pkl (the assembled half-hourly series, read with pandas);
  - mef_draws.npz.

**Git.** Read-only git in /mnt/citations is fine. Check from commits and timestamps that the code was committed before
the outputs it produced, and that D1 came before any MEF was computed.

**Environment.**
- Python: venv/bin/python in the run directory (pandas, numpy, scipy, statsmodels, matplotlib, holidays). Do NOT pip
  install into it.
- Your own scripts and outputs go under review/reviewer_checks/, with caches under review/reviewer_checks/cache.
- Use at most 8 cores.

Check at least:

1. **Data assembly** (series.py).
   - Trading-period to UTC mapping, including the DST days with 46 and 50 trading periods.
   - The date parsing across the files' two date formats and their header-case changes.
   - Whether any unit or month is lost or double-counted. Re-derive annual generation by fuel from the raw files for
     two years.
   - Tiwai and HVDC signs.
   - Storage in GWh: the specific-energy conversion, the "previous day" alignment, and the gap filling.
   - Inflow construction.
2. **The ledger.**
   - Are the heat rates and fuel factors reasonable, and coded as stated in D1?
   - Is the annual calibration done correctly (target = MfE CO2 factor × total generation)?
   - Is the calibrated E used consistently?
   - Do the sensitivity ledgers do what they claim?
   - Is the quarterly check computed correctly?
3. **The instrument and identification.**
   - Recompute the heating-degree anomaly and the climatology smoothing.
   - Is the first-stage F (month-clustered) computed correctly?
   - Is the FWL two-step (base controls, then wind over the window) a valid partialling-out?
   - Is a single starting-half-hour instrument appropriate for 30-day windows?
   - Probe exclusion. The report itself shows coal up and gas down at 0.5 h. Can you find a better explanation, for
     example fuel-availability shocks, Huntly unit commitment, seasonality left in the controls, or a coding issue in
     the coal/gas split?
   - Does conditioning on wind over the window introduce bias?
4. **Re-estimate.**
   - Reproduce MEF(h) for at least 1 h, 1 d and 7 d with your own code, from series.pkl or from raw.
   - Try reasonable alternatives:
     - no wind-window control;
     - daily-mean instrument;
     - dropping 2021 and 2024 (gas-shortage winters);
     - excluding Tiwai demand-response periods.
   - Does the horizon gradient survive?
5. **H2 simulation** (simulate.py).
   - Is the scheduler implemented as preregistered?
   - Is the realised-saving scoring correct: blocks, signs, MWh?
   - Is the weak-block rule applied correctly?
   - Is the ±1-hour variant fairly described as descriptive?
   - Is "0.012 t per MWh moved" right?
6. **Verdicts.** Check H1/H2/H3 against the plan's decision rules. Is "Inconclusive (weak instrument)" the right call
   for H1 and H2? Is the descriptive MEF(7 d) − MEF(1 h) gradient presented with appropriate caution, given that it
   is not preregistered?
7. **Numbers.** Does every number in report.md, report.html, the tiles (results/tables/tiles.json) and the figure
   captions match the results files?
8. **Framing and the plain-language section.** Is anything overstated? For example:
   - "about seven times the grid's average";
   - "coal at Huntly makes up most of it";
   - "Water used now is made up with fossil generation later";
   - the composition caveat.

Write your review to review/review.md with:
- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of recomputed numbers.

Do not modify anything outside review/, and do not commit.
