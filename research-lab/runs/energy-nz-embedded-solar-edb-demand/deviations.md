# Deviations from the preregistration

## D1 — 2026-10-21 18:32 NZDT — reading the grid-exit data and the H4 specification (before any panel was built)

Found while checking file formats, before `build_panel.py` was run:

1. **Flow direction.** EMI names metered flows from the grid's side. `Grid_export` (flow X) is energy leaving the grid
   into a network, the networks' offtake; `Grid_import` (flow I) is energy entering the grid from a network (embedded
   generation spilling upstream). Plan section 2 said "net offtake = import − export"; it is **export − import**. The
   Grid_import files hold only about half the grid exit points, which is how this showed up.
2. **Points included.** Only grid-exit points of connection (generation type GN) are summed; grid-connected generators
   (GG) and directly connected consumers (GD) carry their own codes and are not network offtake. The code BOPD (one
   point, Matahina, in Horizon's region) is not one of the 29 distributors and is left out.
3. **File schema.** Column names are upper case to 2019 and mixed case from 2020, and the date format changed; both
   are read.
4. **H4 specification.** Section 3 lists "ICPs" among H4's controls while also saying all slopes are estimated in
   per-ICP form. H4 is estimated per ICP, weighted by ICPs, as for H1–H3; the levels form with ICPs as a control is
   reported with the robustness set. ICPs for H4 come from the Authority's registry (ICPs with solar ÷ uptake rate),
   because summer 2025/26 falls in a disclosure year not yet published.

## D2 — 2026-10-21 18:39 NZDT — ICPs from the Authority's registry (after building the panel, before any estimate)

The plan derived average ICPs from Schedule 1 (energy delivered ÷ energy delivered per average ICP). Checked against
the Authority's registry (ICPs with solar ÷ uptake rate, mean of the disclosure year's month-ends) before any slope was
estimated, the two agree closely (median ratio 1.00, interquartile range 1.00–1.02) except in four places: Westpower 2024
(its disclosed ratio of 2,520 kWh per ICP implies 91,158 ICPs against about 14,300), Electra 2015 (0.92) and MainPower
2015 (1.16), and OtagoNet, whose derived count drifts from 1.07 to 1.33 times the registry over 2018–2025. The derived
count also depends on energy delivered itself, one of the outcomes. **The registry count is used for all
normalisation and weights.** The disclosure-derived count, with Westpower 2024 excluded, is reported as a sensitivity.

Six distributor-years leave "electricity supplied from distributed generation" blank (Centralines 2015, Electricity
Invercargill 2021, Network Waitaki 2015, Scanpower 2018, 2021, 2023). They are left out of H1 and the export slope,
not imputed.

H4's merged units, from points of connection shared in the metered data (rule fixed in plan section 3): Alpine with
Network Waitaki, Aurora with OtagoNet, Electricity Invercargill with The Power Company, The Lines Company with
Powerco, Nelson Electricity with Network Tasman: 24 units.

## D3 — 2026-10-21 19:35 NZDT — after the primary results: H4 robustness completed, and a post hoc placebo

The first run gave H1–H3 Inconclusive with minimum detectable slopes far above the expected effects, and H4 Supported
(−0.84 MW per MW, −1.01 to −0.16). Two additions, made after seeing those results:

1. **Plan section 4 applied to H4 as well.** The first run carried only the levels and unweighted variants for H4.
   Leave-one-unit-out (24 units) and first differences are added, as section 4 lists them without restricting them
   to H1–H3.
2. **A post hoc placebo, not preregistered.** If the midday slope reflected general load trends in networks with
   faster solar uptake, rather than solar output, offtake in hours when panels produce nothing would fall too. The same
   H4 model is run on mean offtake 18:00–21:00 (trading periods 37–42) and 02:00–05:00 (5–10). Reported as
   exploratory; it does not change H4's verdict.

## D4 — 2026-10-21 20:16 NZDT — after the placebo: a midday-minus-evening contrast (exploratory)

D3's placebo did not come back clean. Per MW of solar, evening offtake (18:00–21:00) moves −0.49 (95% interval
−0.65 to +0.21) and night offtake (02:00–05:00) −0.33 (−0.54 to +0.24). Both intervals include zero, but the
point estimates are large: networks adding solar faster also draw less from the grid at hours when panels produce
nothing. Part of H4's −0.84 may therefore be a network-wide trend rather than solar output. The same model is run on
midday offtake minus offtake in each placebo window, which nets out changes common to all hours in a
network-summer. Exploratory; H4's preregistered verdict is unchanged and is reported with this beside it. The bootstrap
was also moved onto precomputed arrays (same scheme and seed; it reproduces the first run's intervals exactly).

## D5 — 2026-10-21 23:31 NZDT — after independent review

The review (`review/review.md`, fix first) reproduced the H4 bootstrap exactly, and confirmed the accounting, D1,
D2, the merged units and the trading-period timing. Its findings were checked with the study's own estimator in
`code/sensitivity_post_review.py` (same bootstrap and seed) before the report was changed:

1. **H4 rests on two units.** Without EA Networks and Top Energy, the two networks that added solar farms, the slope
   is −0.48 (−1.31 to +0.19). Without the 11 units holding at least 5 MW of industrial-segment solar it is −0.95
   (−3.40 to +0.15); the review's narrower set of seven farm units gave −0.05. The report no longer calls the result
   stable.
2. **Rooftop solar is not separately detectable.** Behind-the-meter capacity alone gives −1.49 (−2.67 to +0.23),
   industrial capacity alone −0.96 (−1.27 to −0.11). The title, verdict and plain-terms section no longer credit
   rooftop solar.
3. **The 18:00–21:00 window has sun** in a New Zealand summer (elevation 26–35° at 18:00 daylight time), so the
   midday-minus-evening contrast of D4 subtracted solar output. It is withdrawn, along with "best estimate". The
   night window (02:00–05:00) replaces it: midday minus night −0.51 (−0.56 to −0.25), and −0.33 (−0.61 to −0.06)
   without the two farm units. Exploratory.
4. **Confounds disclosed.**
   - Solar capacity two years ahead predicts lower offtake now (midday −0.22, night −0.26): a pre-trend.
   - Top Energy has been a net grid injector since summer 2020/21, after its geothermal expansion.
   - EA Networks' night offtake swings with irrigation.
   - Non-solar DG as a control gives −0.80 (−1.02 to −0.31).
5. **Plan section 4 for H4, completed.** The 15% jump filter gives −0.62 (−1.53 to +0.33), and it removes the farm
   years themselves; first differences (−0.58, −0.86 to +0.43) are now discussed.
6. **Segments** contain some farm-sized steps; the excluded embedded networks hold 0.9% of capacity. Disclosed.
7. **Process.** D4's code and outputs were committed together (8f12116); recorded.
8. **Wording.** "Half to three-fifths" becomes "two-fifths to three-fifths" (now moot with the evening window
   withdrawn); "could not have succeeded" is qualified as "with the disclosed annual totals".

H4's verdict under the preregistered rule is unchanged: Supported.
