# Independent review: energy-nz-hydro-marginal-emissions-horizon

Reviewer: adversarial review agent, 2026-10-18. Reviewed: plan.md (df14d01), deviations.md, report.md/report.html
(456a6f6), code/, results/tables/, data/raw/ (483/483 checksums pass), data/series.pkl, data/mef_draws.npz.
Reviewer scripts and outputs are in `review/reviewer_checks/` (`check_series.py`, `check_ledger.py`,
`check_simulation.py`, `reestimate.py`, `reestimate2.py`, `reestimate3.py`, `h1_probe.py`; each writes an `out_*.json`
and a `log_*.txt`).

## Recommendation: fix first

The pipeline is sound and fully reproducible: with independent code I reproduce every MEF, first-stage F, interval,
block, tercile, simulation and ledger number to the last digit, the raw files are parsed correctly (DST days, two date
formats, header case, no lost or doubled units), and the git record shows the plan, the fetch code, D1 and the
estimator were committed before any MEF existed. The three preregistered verdicts (Inconclusive, Inconclusive,
Inconclusive) are defensible as stated.

What does not survive scrutiny is the part of the report labelled **"What the data do show clearly"** and the plain-
language section built on it. The headline levels (0.15 t/MWh within the hour, 0.7 within a week, "about seven times
the grid's average"), the mechanism ("water used now is made up with fossil generation later"; "coal at Huntly makes up
most of it") and the composition story ("coal up, gas down ... cold-weather fuel switching") all depend on two
specification choices that the data cannot adjudicate and that the report does not test:

1. **Controlling for lagged total emissions.** Dropping the lagged D/E controls (which condition on outcomes of
   earlier, correlated weather) moves MEF(1 h) from 0.154 to 0.021 and MEF(7 d) from 0.695 to 0.290; conditioning on
   3 days of weather history instead of lagged outcomes gives 0.069 / 0.132 / 0.341 at 1 h / 1 d / 7 d. Across nine
   defensible control sets MEF(1 h) ranges from −0.16 to 0.15 and MEF(7 d) from 0.13 to 0.71. The gradient's sign
   survives every variant; its size and the levels do not.
2. **The cold-and-dry channel.** The instrument predicts *lower inflow over the window*: −2.7 ± 0.6 MWh of inflow
   energy per MWh of induced demand at 1 h, −3.7 ± 0.6 at 1 d, −8.0 ± 1.6 at 7 d. Cold spells are dry spells. The plan
   controls wind over the window for exactly this reason but controls inflow only by lag. Adding window inflow as a
   control (same logic as wind) moves MEF(7 d) from 0.695 to 0.548 and the 7-day hydro/thermal split from 0.17/0.75 to
   0.49/0.50: a large part of "thermal takes over within a week" is "cold weeks are dry weeks", not water replacement.

The composition result that the report offers as evidence of fuel switching is an artefact: the coal-up/gas-down
pattern at 0.5 h exists only when lagged *total* emissions are controlled without their composition. Adding lagged
coal, gas and hydro gives, at the same MEF (0.147), gas +0.18, coal +0.06, hydro 0.78 at 0.5 h, and at 7 d coal 0.43
with gas 0.64, which contradicts "almost all coal".

Finally, H2 is not merely weakly identified; its scoring construct does not measure what the hypothesis needs (issue
7), the literal plan rule would have returned "Refuted", and with a usable instrument the preregistered scoring gives
a *negative* realised saving (capture −2.45, −4.05 to −0.99). The report should say all three things.

None of this requires re-running the preregistered pipeline. It requires (a) adding the sensitivity tables below to
the report, (b) rewriting the summary, the plain-language section, the tiles and the F1 title so that only the
robust findings are presented as findings, and (c) the disclosures in issues 7–9.

## Issues

### A. Identification and robustness (must fix)

**1. The MEF levels are not robust to the lagged-outcome controls.** *Location:* report.md summary ("What the data do
show clearly"), results table, "What this does and does not show", tiles 1–2, plain-language paragraph 4. The plan
includes D_{t−1}, E_{t−1} and their previous-day means as controls. These are outcomes of earlier weather that is
correlated with z_t (the anomaly's 1-day autocorrelation is 0.59), so partialling them re-weights the instrument in a
way that neither theory nor the data pin down. Recomputed (`out_reestimate3.json`, preregistered sample):

| Controls | MEF 1 h | MEF 1 d | MEF 7 d | F (1 h / 1 d / 7 d) |
|---|---|---|---|---|
| preregistered (D and E lags) | 0.154 | 0.314 | 0.695 | 202 / 85 / 40 |
| no lagged D/E | 0.021 | 0.095 | 0.290 | 127 / 119 / 74 |
| D lags only | −0.158 | 0.043 | 0.275 | 198 / 78 / 33 |
| E lags only | 0.068 | 0.221 | 0.450 | 205 / 171 / 127 |
| D, E, coal, gas, hydro lags | 0.148 | 0.290 | 0.709 | 203 / 82 / 36 |
| no lags, 3 days of z history | 0.069 | 0.132 | 0.341 | 159 / 120 / 63 |
| no lags + window inflow | 0.013 | 0.065 | 0.129 | 128 / 122 / 70 |
| D, E lags + window inflow | 0.153 | 0.295 | 0.548 | 203 / 85 / 32 |
| no lags, 3 d z history + window inflow | 0.058 | 0.098 | 0.176 | 160 / 123 / 56 |

The report presents 0.15 and 0.7 (and "1.5–7 times the average", "seven times") as established. *Fix:* add this table
(or the preregistered row plus the no-lag, weather-history and inflow rows) to Checks; state the levels as
specification-dependent within these ranges; restrict the "clear" findings to what every row shows: MEF(7 d) > MEF(1 h)
and MEF(1 d) > MEF(1 h), i.e. the gradient's sign.

**2. Inflow over the window is an uncontrolled exclusion channel.** *Location:* plan §4 and §7 ("inflows by lag");
report "Exclusion is the main threat". Reduced forms (`out_reestimate2.json`): per MWh of instrumented demand, window
inflow falls by 2.7 (1 h), 1.3 (4 h), 3.7 (1 d), 4.5 (2 d), 8.0 (7 d) and 14 (14 d) MWh; the window's storage change
falls by 9.3 ± 1.7 MWh per MWh at 7 d. The plan's own reasoning for the wind control applies unchanged to natural
inflow (weather-driven, not caused by demand). With window inflow controlled: MEF(1 d) 0.295, MEF(2 d) 0.328, MEF(7 d)
0.548 (F 32); hydro 0.49 and thermal 0.50 at 7 d. *Fix:* report the inflow-controlled estimates beside the
preregistered ones; rewrite the mechanism paragraph so that "water used now is replaced later" is one of two
explanations the data cannot separate (the other being that cold weeks are dry weeks and operators conserve water);
remove the mechanism from the F1 title ("water used now is replaced by coal later").

**3. The coal/gas composition is an artefact of the control set.** *Location:* report "Exclusion is the main threat"
("coal up by 0.46, gas down by 0.63 ... cold-weather fuel switching"; "by 7 days ... almost all coal (0.71 coal, 0.02
gas)"), summary ("mostly coal at Huntly"), tile 2, plain-language ("coal at Huntly makes up most of it"). Recomputed
composition at 0.5 h / 7 d (MWh per MWh of demand):

| Controls | coal 0.5 h | gas 0.5 h | hydro 0.5 h | coal 7 d | gas 7 d | hydro 7 d |
|---|---|---|---|---|---|---|
| preregistered | 0.46 | −0.63 | 1.18 | 0.71 | 0.02 | 0.17 |
| + lagged coal, gas, hydro | 0.06 | 0.18 | 0.78 | 0.43 | 0.64 | −0.20 |
| no lagged D/E | 0.07 | −0.12 | 1.05 | 0.30 | 0.01 | 0.60 |
| preregistered + window inflow | 0.47 | −0.64 | 1.20 | 0.65 | −0.16 | 0.49 |

Note also that the "coal" series is the Huntly Rankine units' metered output under the EMI fuel code; those units
also burn gas, so "coal up" is "Rankine units up", and in 2015–2019 that was substantially gas. *Fix:* drop the
fuel-switching interpretation and "mostly coal at Huntly"; if composition is kept, show it under at least the first
two rows and say that it is not stable.

**4. The 7-day estimate is fragile in several other ways that the report does not show.** *Location:* results table,
F1. (a) A one-day shift of the climatology after 29 February in leap years (the code caps day-of-year at 365; my
calendar-aligned instrument correlates 0.9997 with theirs) moves MEF(7 d) from 0.69 to 0.79 and its F from 40 to 29.
(b) Half-hour × month fixed effects move MEF(7 d) to 1.24 with F 9.2. (c) A 7-day-mean anomaly instrument, which has
F 221 at 7 d, gives MEF(7 d) = 0.38 (0.33–0.45), an interval that does not overlap the report's 0.54–0.94. Part of (c)
is a different complier pattern (a shock at the window's start versus one spread over the week), which the
water-replacement story predicts, but the report should show it rather than present 0.7 as the week-scale number.
*Fix:* add (a)–(c) to the sensitivity list; describe MEF(7 d) as "roughly 0.4–0.7 under the preregistered controls,
lower without the lagged-outcome controls".

**5. The geothermal placebo is positive and the report under-reads it.** *Location:* Checks, "Geothermal placebo".
Geothermal responds by 0.056 (0.003–0.116) at 1 d and 0.059 (0.004–0.119) at 2 d. There is a direct physical channel
for this: air-cooled binary geothermal plants (roughly 250–300 MW of the fleet) produce more in cold air. That is a
supply-side effect of the instrument, not demand, and the same mechanism raises gas-turbine output in cold air. The
preregistered flag rule ("interval excludes ±0.05") is ambiguous; under the reading "interval excludes zero" the flag is
raised at 12 h–2 d. *Fix:* name the channel; state both readings of the rule; note that the emissions consequence is
small (0.10 × 0.056 ≈ 0.006 t/MWh) but that the instrument demonstrably moves supply directly.

**6. The wind-window control: valid, but say what it does.** *Location:* plan §4, report "Controls". Conditioning on
window wind is appropriate (wind is weather-driven, not demand-driven) and the FWL two-step is exactly the joint
partialling (reproduced to 1e-16). Without it the MEFs are 0.161 / 0.399 / 0.784 at 1 h / 1 d / 7 d, so the
cold-and-windy channel is material. Curtailment is no longer negligible in 2023–2024 (new wind farms, overnight
negative prices), which would make W a weak mediator of demand; the 2020–2024 subsample gives 0.160 / 0.391 / 0.734,
so this is not driving the result. *Fix:* report the no-wind row and the curtailment caveat in one sentence.

### B. H2 (must fix)

**7. The time-of-day MEF construct does not measure the marginal emissions of load placed in a block.** *Location:*
plan §4 and §5, report H2 section, F3, simulate.py `score()`. The "block MEF" is the 1-day MEF of a window that
*starts* in the block: Cov(z_t, Σ_{24 h} E)/Cov(z_t, Σ_{24 h} D) with the demand summed over all four blocks. It is a
property of the window alignment, not of when the load sits within the day. The realised-saving formula
Σ (MEF_block(default) − MEF_block(scheduled)) × MWh then applies these as if they were block-specific marginal factors.
Because the plan defines it this way, the study implemented what it preregistered, but the quantity cannot answer H2
in principle. With a daily-mean instrument all four "blocks" are 0.23–0.33 (see issue 8), which is what one expects of
four alignments of the same 1-day MEF. *Fix:* state this limitation explicitly in the H2 section and in "What this does
and does not show"; do not describe F3 as time-of-day marginal factors.

**8. H2's verdict depends on choices made after the block first stages were known, and the report should disclose
the alternatives.** *Location:* report "H2 ... Inconclusive (weak instrument)"; simulate.py (commit ca32d4a,
15:36:01) was written after mef.json (15:35) and the F = 4.2 night block were known. The plan's rule is horizon-level;
its extension to blocks is reasonable but post hoc. Under the plan's literal decision rule the capture ratio 18
(0.83–127) has a lower bound ≥ 0.5 and H2 is **Refuted**. The night block's weakness is a property of the half-hour
instrument (F 7.5 at 0.5 h, 6.6 at 4 h, 4.2 at 1 d; the 1-day first stage is *negative*, −170 MWh/°C), not of the
data: with the calendar-day mean anomaly as instrument and the preregistered controls, the blocks are 0.30 (F 195),
0.23 (387), 0.28 (238), 0.33 (83), and the preregistered scoring gives realised −8,862 t against claimed 3,618 t:
capture −2.45 (−4.05 to −0.99), i.e. **Supported** with a negative realised saving (the scheduler moves load into the
night, whose 1-day MEF is higher than midday's). With the first-24-h mean instrument: −1.61 (−3.34 to −0.03). Without
the lagged D/E controls the blocks are 0.09–0.11 and the ratio is uninformative. *Fix:* keep "Inconclusive" as the
preregistered verdict but add: (i) the literal rule would give Refuted; (ii) the block-level weak rule was coded after
the block F's were known; (iii) the daily-mean-instrument rescoring and its dependence on the control set; (iv) that
under no scoring does the AEF scheduler show a positive, well-identified capture.

**9. "A third of the claim survives" overstates the ±1-hour variant.** *Location:* summary bullet 5, H2 Variants. In
the ±1 h variant the scheduled window overlaps the default by 6.2 of 8 half-hours on average, so only 65,220 MWh
(22% of the load) actually moves, and the entire realised saving is the 06–12 versus 12–18 block difference
(0.219 vs 0.270) applied to the load that crosses noon, in whichever direction the AEF happened to prefer. The ratio
0.34 (−0.08 to 0.75) includes zero. *Fix:* remove the headline; keep the number in the variants list with the
overlap fact and a plain statement that it is uninformative.

**10. "0.012 t per MWh moved" counts load that is not moved.** *Location:* summary and H2 section. 29.5% of
scheduled days overlap the default window (mean 1.14 half-hours); 250,640 MWh of the 292,240 MWh is actually moved.
3,618 t / 250,640 MWh = 0.0144 t per MWh moved; 0.0124 is per MWh of load. Also 15% of days the chosen window starts
at midnight and 5% at 20:00, an artefact of restricting the "24-hour window" to the calendar day. *Fix:* say "per MWh
of load (0.014 per MWh actually moved)"; note the calendar-day restriction. The plan's "share of days with a sign
reversal" (0.364) is computed but not reported; add it.

### C. H1 and the horizon design (should fix)

**11. The single half-hour instrument cannot identify 14- and 30-day windows by construction, and the report should
say that a matched instrument changes the picture.** *Location:* H1 section. The anomaly's autocorrelation is 0.04 at
7 days and 0.03 at 30 days; z_t correlates 0.22 with the 30-day window mean. This was foreseeable at preregistration.
With a 7-day-mean instrument (not preregistered) MEF(30 d) = 1.52 (F 10.8; 0.86–3.65) and MEF(30 d) − MEF(1 h) = 1.32
(0.66–3.45), not weak; with a 30-day-mean instrument MEF(30 d) = 0.79 (F 15.5; 0.37–1.44). *Fix:* keep H1 Inconclusive;
add one paragraph with these numbers, labelled exploratory, and say in "Process" that the preregistered instrument was
mismatched to the H1 horizon.

**12. The descriptive gradient's numbers are slightly off and its status needs one more sentence.** *Location:*
summary and H1 section. From mef_draws.npz: MEF(1 d) − MEF(1 h) = 0.160 (0.115–0.209), report says (0.12–0.21);
MEF(7 d) − MEF(1 h) = 0.541 (0.384–0.790), report says 0.55. The report does label it descriptive; it should also say
that it is the contrast H1 would have used had the plan chosen 7 days, and that its size is specification-dependent
(0.12–0.56 across the rows in issue 1) while its sign is not. *Fix:* correct to 0.11 and 0.54; add the sentence.

### D. Ledger, data and checks (minor; fix wording)

**13. The energy-balance "check" is near-tautological.** D is the sum of the fuel series, and wind is partialled out
of everything, so the fuel responses sum to exactly 1 minus the responses of solar, wood and "other". The reported
0.98–1.03 only says those are small. *Fix:* describe it as an arithmetic identity, or drop it.

**14. The quarterly ledger check is a within-year test.** Annual calibration forces the generation-weighted mean of
each year's four quarterly errors to zero (recomputed: −0.0005 in 2023, −0.0001 in 2024), so "7 of 8 within 0.01"
tests only the within-year shape (RMSE 0.0057 against a quarterly spread of 0.032, which is good). *Fix:* say so.

**15. The storage series is not the EA's "controlled storage" and should not be described as such.** The HMD
storage files' "Active storage (Mm³)" is measured over the observed level range, which for Te Anau, Manapōuri, Wānaka
and Wakatipu is about twice the scheme's active capacity (per-lake maximum / capacity: 2.20, 1.83, 2.00, 2.05; Ōhau
4.8; Waikaremoana 1.33; Pūkaki, Tekapō, Taupō, Hāwea 1.00–1.07). The national series peaks at 4,727 GWh against
4,351 GWh of summed capacity. Because each lake's offset is constant, the day-of-year anomaly used for H3 and the
standardized control are unaffected, and the specific energies (GWh/Mm³) are correct; only the level is wrong. Also:
`groupby.last()` silently skips the blank capacity rows for Pūkaki, Tekapō and Ōhau after 2025-04-29 (the values used
are the correct 2015–2024 ones), and Wānaka's "inflow" is the natural *outflow* series. *Fix:* one sentence in Data;
"natural inflows to nine of them" → "eight natural inflows and Wānaka's natural outflow".

**16. Minor text/number corrections.** (a) F1 caption "n = 173,569" is right; the report's Data paragraph gives
175,344, which is the series length; say both. (b) Tile 3 "the same in every 6-hour block": 0.095–0.100 (±2.5%).
(c) The plan's time-of-day design (demand × block interaction with block-specific instruments) was implemented as four
separate regressions with all controls re-partialled within block; equivalent to full interaction, but note it in
Process. (d) The Tiwai rule ("≥100 MW below the trailing 30-day median") differs from the plan's wording; say so.
(e) The MfE "Electricity Used" factor is per kWh generated (the T&D-loss factor is separate in the same file); D1's
reading is right; the report could cite the row. (f) Geothermal at 0.10 t/MWh is 15–24% of ledger CO2 each year; the
sensitivity ledgers bracket it and the gradient is unaffected, as claimed.

### E. What is right (for the record)

Data assembly: TP → UTC mapping is correct on all 20 DST days (46/50 TPs, consecutive 30-min UTC stamps, hh repeating
or skipping as it should); both date formats and header cases parse with no NaT; annual generation by fuel from an
independent raw parse matches series.pkl to 0.1 GWh in 2017 and 2024; units with several rows per date are distinct
POCs (second-participant rows are zero); HVDC sign is consistent (BEN X ↔ HAY I, r = 0.99995, loss ratio 0.964; 82%
of half-hours northward); Tiwai is export-only, 568 MW mean; temperature weighting and interpolation verified by hand;
storage "previous day" alignment verified on three dates; inflow conversion verified by hand. Ledger: heat rates and
fuel factors coded exactly as D1 states and are reasonable (0.95 t/MWh Rankine, 0.39 CCGT, 0.52 OCGT, 0.33
cogeneration); scale factors reproduce to 1e-15 and E/D equals the MfE factor in every year; E_raw and the three
sensitivity ledgers are consistent. Estimator: instrument, FWL partialling, cluster-robust F (small-sample factor
changes F by <1%), bootstrap (1-, 2- and 3-month blocks give the same intervals; analytic cluster CIs agree except
being slightly narrower at 7 d), blocks, terciles, H1, H3 all reproduce exactly. Simulation reproduces exactly; the
weak-block rule is applied as the code says. Git: plan → fetch → D1/series/estimator (15:29–15:33) → results (15:39)
→ report (15:41); mef.py unchanged since the commit that preceded mef.json.

## Recomputed numbers

| Quantity | Report | Recomputed (reviewer) | Note |
|---|---|---|---|
| MEF 0.5 h / 1 h / 2 h / 4 h | 0.153 / 0.154 / 0.157 / 0.164 | 0.1527 / 0.1540 / 0.1566 / 0.1636 | exact |
| MEF 12 h / 1 d / 2 d / 7 d | 0.229 / 0.314 / 0.367 / 0.695 | 0.2287 / 0.3136 / 0.3675 / 0.6949 | exact |
| MEF 14 d / 30 d | 1.55 / 11.9 | 1.547 / 11.88 | exact; F 7.7 / 0.18 |
| First-stage F 1 h / 1 d / 7 d | 202 / 85 / 40 | 202.2 / 84.7 / 40.1 (small-sample adj. 200 / 84 / 40) | exact |
| 95% CI MEF 7 d | 0.541–0.937 | 1-month 0.541–0.937; 2-month 0.543–0.937; 3-month 0.543–0.931; analytic 0.516–0.874 | |
| Hydro / thermal / geo at 1 h | 1.03 / −0.02 / 0.02 | 1.025 / −0.018 / 0.016 | exact |
| Hydro / thermal / geo at 7 d | 0.17 / 0.75 / 0.06 | 0.173 / 0.746 / 0.058 | exact |
| Coal / gas at 0.5 h | 0.46 / −0.63 | 0.462 / −0.626 | exact; +fuel lags: 0.06 / +0.18 |
| Coal / gas at 7 d | 0.71 / 0.02 | 0.710 / 0.024 | exact; +fuel lags: 0.43 / 0.64 |
| MEF(1 d) − MEF(1 h) | 0.16 (0.12–0.21) | 0.160 (0.115–0.209) | lower bound 0.11 |
| MEF(7 d) − MEF(1 h) | 0.55 (0.38–0.79) | 0.541 (0.384–0.790) | point 0.54 |
| H1 diff | 11.7 (−86 to 62) | 11.73 (−86.0 to 62.2) | exact |
| Blocks 1 d | −0.37 / 0.22 / 0.27 / 0.40; F 4.2 / 60 / 100 / 20 | identical | exact |
| Blocks 1 d, calendar-day-mean instrument | — | 0.30 / 0.23 / 0.28 / 0.33; F 195 / 387 / 238 / 83 | new |
| H3 low / high / diff | 0.30 / 0.32 / −0.02 (−0.14 to 0.11) | 0.298 / 0.315 / −0.017 (−0.135 to 0.111) | exact |
| H2 claimed / realised / ratio | 3,618 / — / 18 (0.8–127) | 3,618.4 / 66,073 / 18.26 (0.83–126.8) | exact; literal rule → Refuted |
| H2 ratio, daily-mean instrument | — | −2.45 (−4.05 to −0.99); first-24-h mean: −1.61 (−3.34 to −0.03) | new; prereg. controls |
| Night share of scheduled load | 41% | 41.0% | exact |
| MWh moved (24 h) | 292,000 | 292,240 load; 250,640 actually moved | 29.5% of days overlap |
| t per MWh (24 h) | 0.012 | 0.0124 per MWh load; 0.0144 per MWh moved | |
| ±1 h claimed / realised / ratio | 470 / 159 / 0.34 (−0.08 to 0.75) | 470.3 / 159.4 / 0.339 (−0.078 to 0.753) | 65,220 MWh moved |
| Share of days with sign reversal | not reported | 0.364 | plan output |
| AEF by block | 0.095 / 0.098 / 0.098 / 0.100 | 0.0950 / 0.0978 / 0.0978 / 0.1001 | exact; mean 0.0977 |
| Ledger scale factors | 0.87–1.10 | 0.8686–1.0992, all 40 reproduce to 1e-15 | |
| Quarterly check | 7 of 8 within 0.01 | 7 of 8; RMSE 0.0057; within-year mean −0.0005 / −0.0001 | forced |
| D vs 2024 grid export | r 0.997; +9% | 0.9965; 1.089 | exact |
| Annual gen. 2017 (hydro / gas / coal / geo), GWh | — | raw 24,226 / 6,322 / 904 / 7,349 = series | |
| Annual gen. 2024 (hydro / gas / coal / geo), GWh | — | raw 22,733 / 4,148 / 1,876 / 8,361 = series | |
| Tiwai episode | 9–19 Aug 2024, 138 MW; 29.9 vs 31.5 GWh/d; AEF 0.161 vs 0.172 | identical | exact |
| Inflow response per MWh demand (1 h / 1 d / 7 d / 14 d) | — | −2.7 ± 0.6 / −3.7 ± 0.6 / −8.0 ± 1.6 / −14 ± 5 | new |
| MEF with window inflow control (1 h / 1 d / 7 d) | — | 0.153 / 0.295 / 0.548; hydro 7 d 0.49, thermal 0.50 | new |
| MEF without lagged D/E (1 h / 1 d / 7 d) | — | 0.021 / 0.095 / 0.290 | new |
| MEF, no wind control | — | 0.161 / 0.399 / 0.784 | new |
| MEF, drop 2021 + 2024 | — | 0.161 / 0.278 / 0.661 | gradient holds |
| MEF, excluding Tiwai-DR windows (99 days, 2024) | — | 0.154 / 0.316 / 0.685 | gradient holds |
| MEF, 2015–19 / 2020–24 | — | 0.144 / 0.216 / 0.624; 0.160 / 0.391 / 0.734 | gradient holds |
| MEF, 7-day-mean instrument | — | 0.197 / 0.272 / 0.379 (F 36 / 51 / 221); 30 d 1.52 (F 10.8) | new |
| z autocorrelation 1 d / 7 d / 30 d | — | 0.59 / 0.04 / 0.03 | |
| Storage max vs summed capacity | — | 4,727 vs 4,351 GWh | datum, issue 15 |

## Summary of required changes

1. Add the control-set and window-inflow sensitivity tables (issues 1–3) and the 7-day-instrument row (issue 4) to
   Checks; move the levels, the mechanism and the composition out of "What the data do show clearly" and out of the
   plain-language section; keep the sign of the gradient as the robust finding.
2. Rewrite tiles 1–2, the F1 title and the plain-language paragraph 4 accordingly ("about seven times" becomes "two
   to seven times depending on specification, with the lower end under weather-only controls").
3. H2: add the construct limitation (7), the literal-rule verdict, the timing of the block rule and the daily-mean
   rescoring (8); drop "a third survives" (9); fix "per MWh moved" and add the sign-reversal share (10).
4. H1: add the matched-instrument paragraph (11); correct the gradient numbers (12).
5. Wording fixes 13–16.
