# Adversarial review — "Is the projected eastward shift of Pacific skipjack detectable yet?"

Reviewer: Fable 5.1, independent of the author run. Reviewed draft: commit 9f05cfc (report.md, report.html, tiles.json,
figures F1–F4), plan 3cc5aff, deviations D1–D7, all code, all results tables. Scripts and logs for every number below
are in `review/reviewer_checks/` (`check_bell_d2.py`, `check_bell_eq1.py`, `check_observed.py`, `check_h1.py`,
`check_power.py`, `check_footprint.py`, each with a `.log` and most with a `.json`). All recomputation used an
independent code path where one was possible (own EEZ mask built in −180..180 space with antimeridian splitting, own
block bootstrap, own vectorised Newey–West). Nothing in the run directory outside `review/` was modified.

## Recommendation: **fix first**

The preregistered pipeline is sound and reproduces exactly: the observed series, the EEZ mask, τ, the H1 point
estimate and both preregistered intervals, the 2010 step, H2, H3 and every per-EEZ number all match to machine
precision or to Monte Carlo noise. The commit order is as stated and no preregistered file changed after 3cc5aff.
That part can be trusted.

The report's two biggest *practical* claims do not survive, and one data-integrity claim destined for SPC is wrong:

1. **The fixed-footprint headline ("the fleet moved, not the fish"; "the fish had not moved east at all") is
   unsupported.** SEAPODYM's own projected redistribution, measured inside the same 86 cells, is a centroid trend of
   +0.0095 deg/yr — inside the observed interval (−0.010, +0.013). The check cannot tell "no shift" from "exactly the
   projected shift". The report's own preregistered 50% sensitivity footprint (computed, in footprint.json, never
   mentioned in report.md) shows a significant eastward drift of +0.137 deg/yr on covered years, and so do most other
   footprint/coverage choices I ran.
2. **The verdict's intervals have ~79% coverage, not 95%, under the autocorrelation the series actually has.** The
   disclosed 0.89 was measured with white noise. A GLS-AR(1) interval for the trend is (−0.225, +0.620), which
   includes τ. "Supported" holds by the preregistered rule only; the report must say so.
3. **D2.2 is a misdiagnosis.** The historical bigeye `bet_Btot` is not "0.848 × (adult + young), varying 0.73–1.00 by
   cell". It is *identical to the adult-only file* (correlation 1.000000, max |difference| 0). The 0.848 is simply
   adult/(adult+young). The fix the code applies (use adult+young) is right; the description that will go to SPC is
   wrong.

Plus: the "2098" detection year is one end of a 2049–2120 range; the Bell reproduction mislabels its baseline and
the paper's own equation gives −13.8% not −14.2%; the H2 density-share "contradiction" and the inference drawn from
it ("deserves less confidence") rest on the 1980–89 fleet-development years and reverse sign on 1990–2010; and
three of the four headline tiles are post hoc.

---

## Issues

### A. Must fix before publication

**1. The fixed-footprint check has no power against the hypothesis it claims to reject (items 9, 13).**
*Location:* tiles.json tile 4; report.md "The eastward move is the fishery, not the fish", its last paragraph, the F4
title "On fixed grounds, the eastward move vanishes", F4 caption's last sentence, "In plain terms" ¶4.
*Evidence:* `check_footprint.py` §(d). Mapping the 86-cell footprint onto SEAPODYM's grid and computing the model's
projected 2011–2050 centroid trend *inside the footprint*: **+0.0095 deg/yr** (GFDL 0.0066, IPSL 0.0094, MIROC
0.0159, MPI 0.0062), against +0.0704 domain-wide; the 2044–53 minus 2011–20 displacement inside the footprint is
+0.32° against +4.07° domain-wide. The footprint sees 8% of the projected shift. The observed covered-years interval
(−0.010, +0.013) contains +0.0095. The model's historical within-footprint trend (−0.007, interval −0.019 to +0.004)
is likewise indistinguishable from the observed 1988–2010 value (−0.001, −0.014 to +0.013). The footprint is 18°
wide, 97% inside EEZs and in the western core; the fish can leave it without its internal centroid moving — exactly
the concern raised in the review prompt, and it is quantitatively confirmed.
*Further evidence:* the result is footprint- and coverage-rule-dependent in a way the report hides (`check_footprint.py`
§(a),(b)). Footprint ≥50% of years (366 cells, 141.5–184.5°E, 91% EEZ): coverage ≥0.8 → **+0.137 (+0.077, +0.195)**
over 1997–2021; coverage ≥0.6 → +0.070 (+0.012, +0.126) over 1990–2021. Footprint ≥60%, coverage ≥0.9 → +0.094
(+0.045, +0.146). Footprints defined on 1995–2021 or 2000–2021 (268–295 cells to 183.5°E), coverage ≥0.8 → +0.086 to
+0.088, intervals excluding zero. Only the narrowest footprints (≥70–90%, all west of 160°E) give ~0. The 50% result
is in the author's own footprint.json (`min_frac_0.5.centroid_trend_covered_years` = +0.1367, (+0.0765, +0.1951)) and
was the preregistered (D6) sensitivity; report.md does not mention it.
*Fix:* Replace the headline with what is supported: "within the western core grounds fished throughout, the density
centroid has not moved (+0.002 ± 0.011 deg/yr) — but SEAPODYM's projected shift would register there as only ~+0.01
deg/yr, so this neither detects nor excludes the projected redistribution; on wider fixed footprints the density
centroid has moved east at +0.07 to +0.14 deg/yr since the 1990s, at or above the projected rate." Report the full
threshold × coverage grid (table), including the 50% sensitivity. Retitle F4 and the section; delete the tile or
replace its note. Rewrite plain-terms ¶4: drop "the fish had not moved east at all" and "The fleet had simply spread
into new water." The D6 decision rule ("if it vanishes, the centroid result is fleet expansion") was mis-specified
because it did not ask what the model would show on that footprint; say so in D6/D7.

**2. Interval coverage and the robustness of "Supported" (item 5).**
*Location:* plan §6 "Disclosed before use"; report.md "The preregistered verdict: Supported"; verdict paragraph.
*Evidence:* `check_h1.py`. test_analysis.py check 3 generates iid noise, so the 0.89 is a white-noise coverage. With
AR(1) φ=0.56, σ=7.9 pp, n=42 and the real covariates, coverage of a nominal 95% interval is **block-4 bootstrap 0.79,
HAC(3) 0.76, HAC(8) 0.74, OLS 0.73** (600 reps). The residual PACF (0.57, 0.09, 0.16, 0.05, …) is AR(1)-like;
Ljung–Box(4) p < 0.0001. Alternatives that respect the autocorrelation: GLSAR(1) ρ=0.58 gives trend +0.198
**(−0.225, +0.620)** — includes τ=−0.117; parametric AR(1) residual bootstrap (−0.091, +0.607); HAC(5) (−0.000,
+0.511); block-8 (−0.073, +0.600). The preregistered lower bounds (−0.026 bootstrap, +0.017 HAC) clear τ by 0.09–0.13
pp/yr with intervals that are ~25–30% too narrow.
*Fix:* State that the 0.89 was measured under iid noise and that under the observed autocorrelation both
preregistered intervals cover ~75–80%; report the GLS-AR(1) interval beside them; say the verdict is "Supported by
the preregistered rule; borderline (Inconclusive under a GLS-AR(1) interval)". This does not change the substantive
story — plan §1.3 already says Supported is uninformative — but the published verdict label must not rest on an
interval the report knows is undersized. Also fix test_analysis.py check 3 to use AR(1) noise so the self-test
measures what matters.

**3. D2.2 misdescribes the bigeye historical file (item 3).**
*Location:* deviations.md D2.2; plan §4.1 second paragraph; report.md "Data-integrity findings worth reporting to
SPC"; model_targets.py `open_run` docstring.
*Evidence:* `check_bell_d2.py`. `bet_Btot_hist_F0.nc` vs `bet_Badult_hist_F0.nc`: correlation 1.000000, sum ratio
1.0000, cellwise ratio 1.000 at the 1st/50th/99th percentiles, max |difference| = 0. Regressing Btot_hist on adult
and young gives 1.0000·adult + 0.0000·young, R² = 1.00000. The "0.848" is adult/(adult+young) and the "0.73–1.00 by
cell" is the spatial variation of the young fraction. The correct statement is: **the served historical bigeye
"Btot" is the adult biomass only.** The projection-side finding (D2.1) is confirmed and strengthened by provenance:
all four `bet_Btot_<ESM>_F0.nc` carry the CDO history `cdo add bet_Byoung_… bet_Badult_…` with no `chname` step (the
skipjack files have `cdo chname,skj_B_young,skj_Btot`), so the variable name `bet_B_young` is a leftover of the first
operand. IPSL/MIROC/MPI totals are 1.00–1.04× the GFDL Btot and 6.8–7.1× the GFDL young file, so all four hold
total biomass. The hist Btot file's only history is `settunits` — it is a native upstream output, not a cdo sum.
*Fix:* Rewrite D2.2, plan §4.1 and the SPC paragraph: "hist bet_Btot = bet_Badult (adult only); projection bet_Btot =
adult + young under the wrong variable name (cdo add without chname, 16 Sep 2022)". Keep the adult+young fix.

**4. The H2 density-share "contradiction", and the inference drawn from it, is a fleet-footprint artefact (items 6,
8, 10).**
*Location:* report.md "SEAPODYM's historical run does not reproduce what was observed" (table row "density share" and
the sentence "the model's rise is contradicted by an observed decline"); "What this does and does not show" ¶2 ("It
does show the model's historical dynamics disagree with observation on density — the one observed series built to
track fish rather than fleets. A model whose historical redistribution points the wrong way … deserves less
confidence in its projected redistribution").
*Evidence:* O2 is a share over *fished* cells, so it carries the fleet's footprint just as the centroid does; the
report applies the footprint critique to the centroid (D6) but not to O2. In 1980–87 the fleet fished 25–180 cells
(`check_observed.py`), almost all inside PNG/FSM waters, so O2 ≈ 0.9 by construction; as the fleet spread to the high
seas in 1988–92 (210–410 cells) O2 fell. `check_h1.py`: over **1990–2010** the observed density-share trend is
**+0.180 pp/yr (HAC −0.126, +0.485)**, the catch share +0.556 (+0.227, +0.885), the free-school density share +0.355
(+0.020, +0.689) — all the same sign as the model's +0.221 over the same years. The 1980–2010 difference of −0.398
(−0.889, −0.045) is produced by 1980–89. The fixed-footprint density shares (`check_footprint.py`) rise or are flat
over 1980–2021 (50% footprint: +0.13 pp/yr, interval excluding zero); none declines.
*Fix:* Keep the preregistered 1980–2010 H2 numbers but withdraw the interpretation. Replace "the model's rise is
contradicted by an observed decline" with a statement that the decline is confined to the fleet's development decade
and reverses from 1990. Delete the "deserves less confidence" sentence — it is the one place the report implies the
projection is wrong, and the evidence does not carry it. Say plainly that none of the observed series is footprint-free.

**5. The detection year is presented as a point ("2098") when it is a range, and its noise model treats fleet
development and the 2010 management step as future noise (item 7).**
*Location:* tiles.json tile 3; report.md power table and the sentence "not reliably before the 2090s"; "In plain
terms" ¶3 ("not reliably until near the end of the century").
*Evidence:* `check_power.py`, calibrated test, 3000 sims per year. Baseline (σ=7.50, φ=0.56, hinge 2011, record from
1980) → **2095–2097** across three seeds (study 2098: fine). But: σ,φ from the step-adjusted residuals (5.7, 0.42) →
2072; σ,φ from the 1990–2021 step-adjusted residuals (4.2, 0.12) → **2049**; σ=5.0 (post-2010 variability) → 2074;
φ=0 → 2062; φ=0.3 → 2078; φ=0.75 → 2120; record starting 2011 → 2114; model's own 2011–2030 rate (−0.336) → 2050;
IPSL rate (−0.216) → 2064; a fishery-independent index with SEAPODYM-like noise (σ=1.26, φ=0.63) → 2036. The
baseline uses the full-sample residuals, i.e. it assumes a future monitoring programme faces the 1980s' 25-cell
fleet and another unmodelled +17 pp management step as irreducible noise. The report also states the residual SD as
7.9 (ddof=5) while the simulation uses 7.5 (ddof=1).
*Fix:* Report "detectable at 80% power between about 2050 (if post-1990, step-adjusted variability describes the
future) and 2100–2120 (if the full historical variability does)". The qualitative conclusion — not before ~2050 under
any noise model, and only a fishery-independent index gets there in the 2030s — survives and is the right headline.
Replace the tile value "2098" with the range. Give ±2–3 years of Monte Carlo uncertainty for any single figure.

**6. The Bell reproduction mislabels its baseline, and the paper's own equation closes most of the gap (item 2).**
*Location:* report.md "The headline reproduces approximately" ("2044–2053 against 2009–2018, is −14.2%"); plan §4.1
table (correct) vs report (wrong column); "attributes the gap to the files".
*Evidence:* `check_bell_d2.py` reproduces the study exactly: −14.2% is the **2011–2018** baseline; the spliced
2009–2018 baseline is −15.3%. Bell et al.'s Fig. 3 caption says 2009–2018, but their Methods equation (1) is the mean
over the 120 months of 2011–2020 of B(t+33 yr)/B(t) − 1, i.e. a 2011–2020 month-by-month baseline. `check_bell_eq1.py`
computes it: **−13.8% (range −9.3% to −19.9%)** — GFDL −10.6, IPSL −19.9, MIROC −15.6, MPI −9.3 — against the
published −13% (−5% to −20%). The study's method, not only the files, accounts for part of the gap; the residual gap
is MPI (−9.3 vs −5). Per species under eq. (1), four-ESM means: skipjack −18.8%, yellowfin −8.0%, bigeye −4.6%.
Mask and area check (ratio 1.0040) reproduce to 2e-15. The hist/projection splice step at 2010/2011 is <1% for the
three-species total with adult+young bigeye.
*Fix:* Correct the label; add the eq. (1) number as the primary reproduction (−13.8%); note the paper's internal
inconsistency on the baseline; soften "the files, not the method".

### B. Should fix

**7. "One time in six" describes a different hypothetical from the one readers will hear (items 7, 13).**
*Location:* verdict paragraph; "In plain terms" ¶3; tile 2.
*Evidence:* `check_power.py` reproduces calibrated power at τ as 0.19 (study 0.17; nominal 0.37 both) — for a linear
decline at τ running through all 42 years (≈5 pp total). For the decline SEAPODYM actually projects — a hinge
beginning in 2011, observed to 2021 — calibrated power is **0.06**, i.e. the test's size: nothing can be seen yet.
*Fix:* "Even a decline at the projected rate running through the whole 42-year record would be caught only about one
time in six; the decline the model actually projects, starting in 2011, cannot yet be seen at all."

**8. Post-hoc results carry the headline; one process claim is false (items 1, 10).**
*Location:* tiles.json (tiles 2, 3, 4 are all post hoc: calibrated power, calibrated detection year, fixed footprint);
"What this does and does not show" last paragraph: "Each was logged with its decision rule before it ran".
*Evidence:* D7 says of itself "This refinement was not specified in D6; it was prompted by the coverage figure"; the
D7 code lines were added to footprint.py in the draft commit (9f05cfc) together with footprint.json. The 80%
coverage cut-off was chosen after seeing coverage. The size-calibrated power is the statistically better pair and can
stay, labelled.
*Fix:* Change the sentence to "D5 and D6 were logged with decision rules before they ran; D7 was not." Lead the tiles
with preregistered figures (37% / 2084) with the calibrated figures beside them, or label the tiles "post hoc". Remove
tile 4 (see issue 1).

**9. The 2010 step: the report is too weak where a direct test exists, and misses a 2011 management event (item 8).**
*Location:* "What moves the share is not the fish" — "that is all this study can say about its cause"; D5 prediction.
*Evidence:* `check_observed.py`: skipjack catch outside the EEZs but inside the domain fell from 140 kt/yr (2005–09)
to 45 kt/yr (2010–14); by longitude band 140–160°E 33→11, **160–180°E 87→12**, 180–200°E 20→21, 200–228°E 1→1. The
loss is confined to the pocket longitudes and absent east of 180°E; that is the direct test of the closure the per-EEZ
decomposition could not deliver. Facts checked: CMM 2008-01 ¶22 closed the two high-seas pockets to purse seining from
1 January 2010 (adopted December 2008; the CMM lapsed 5 Feb 2013 with CMM 2012-01); the PNA Third Implementing
Arrangement (May 2008) made the same closure a licence condition for PNA-licensed vessels from 1 Jan 2010 and, from
**1 January 2011**, extended the licence-condition closure to the eastern high seas (10°N–20°S, 170°E–150°W). That
2011 extension would push PNA-licensed effort from the eastern high seas into Kiribati, Tuvalu and Tokelau waters —
which is where the non-bordering EEZs' share rose (4.4%→14.2%) — so the D5 prediction was incomplete rather than the
closure explanation wrong. Also list, as untested alternatives, a change in logsheet/observer coverage feeding the
public-domain file after PNA's 100% observer requirement, and the FAD-closure months (2009 onward). ENSO phase does
not fit: La Niña years 1988 and 1999 have the two *lowest* shares. Step placement: 2009 +14.4 pp, 2010 +17.0, 2011
+13.2 (`check_h1.py`).
*Fix:* Add the outside-EEZ-by-longitude test (a table) and say the aggregate evidence for the closure is strong even
though the per-EEZ decomposition is unidentified; add the 2011 PNA eastern closure to plan-era threat 9.2 and D6.

**10. H3 should be called uninformative, not "not supported" (item 6).**
*Location:* report.md H3 sentence.
*Evidence:* `check_h1.py`: calibration slope 1.65 trained on 20 points with r=0.37; test-period r=0.09; RMSE ENSO 9.2
pp, SEAPODYM 6.7 pp, test mean 5.6 pp, *train mean as the forecast* 5.8 pp. Both predictors lose to a constant;
n_test=11; the ENSO regression is trained across the fleet-development years. ΔR² > 0 so H3 "fails" by rule, but the
rule compares two failures.
*Fix:* "H3 is uninformative: both predictors are worse than a constant; by the preregistered rule it is not supported,
which says nothing about SEAPODYM." Keep the numbers.

**11. D4 promised a check that was never done.**
*Location:* deviations.md D4 ("One added check, labelled post hoc: compare … with the FIRMS Global Tuna Atlas 5°
total"); report.md "Public-domain suppression is unmeasurable here".
*Fix:* Either run it or state in the report that it was not done and why.

### C. Minor

**12.** "Year to year the share swings by up to 15 points" (verdict ¶, plain terms ¶3, F1 title). Largest changes are
**18.3 pp (1989)** and 18.1 pp (2010); 15.0 (2000), 14.2 (1988), 13.4 (2015). Say "up to 18 points".

**13.** report.html header reads "Report · 2026-10-13"; the work is dated 2026-10-16 throughout. `DATE` is hard-coded
in build_report_html.py line 18.

**14.** F4 caption: "only the fixed-footprint rows speak to where the fish are" — overclaim (issue 1). Also the top
rows' "+0.650" density centroid over all fished cells is +0.345 (+0.224, +0.471) on 1990–2021 alone; worth a line.

**15.** "Dutta (2025)" → Dutta, Ivekolia & Das (2025), *Asia & the Pacific Policy Studies*, DOI verified. Its finding
is a difference-in-differences estimate that catches rose in VDS members relative to non-VDS Pacific states; "moves
catch across EEZ boundaries" paraphrases it loosely — tighten. Hanich et al. and McDermott et al. are both PNAS
2018 online (McDermott print 2019); Lehodey et al. 1997 and Bell et al. 2021 citations are correct.

**16.** Coordinate convention: WCPFC's public pages do not state whether the integer is the SW corner or the centre;
the three-convention sensitivity is the right handling, but cite the metadata PDF shipped in WCPFC's download zip
and say the question was not resolved from documentation. (Verdict holds under all three; the "centre" convention
gives a tighter interval, (+0.10, +0.54).)

**17.** "Hanich et al. (2018) vs McDermott et al. (2019)" table row leaves "what it leaves open" empty; fine, but the
Lehodey row's "Long-term change once ENSO is removed" is what this study also cannot deliver, given issues 1 and 4.

**18.** Masking D4: the identical missing pattern across all 26 variables is confirmed (`check_observed.py`:
`skj_c_una` and `days` nulls coincide in 100% of cell-months in the domain).

---

## What checked out

- Commit order 3cc5aff → db9d946 → b51f02b → ddf284f → 34a5dc1 → 9f05cfc as described; plan.md, analysis.py,
  observed.py, primary.py, model_targets.py, indices.py, test_analysis.py unchanged after 3cc5aff; exploratory.py
  unchanged after b51f02b; footprint.py's only later change is the 8 D7 lines, disclosed. Working tree clean.
- EEZ mask: 12 areas, Torres Strait joint regime dropped, antimeridian handled correctly (independent route agrees to
  2e-15); fractional overlap; area ratio 1.0040.
- τ = −0.1174 pp/yr (mean of ESM slopes = slope of mean path); hist share mean 49.4%, raw trend +0.114; 2011–2030
  rate −0.336 — all reproduce.
- O1 recomputed from the raw file for 1985, 1995, 2005, 2010, 2015, 2021 (EEZ/domain tonnes shown in the log) and all
  42 years: max |difference| 6e-16. O2, O2u, days share, domain catch likewise. Skipjack summed over the five set
  types; domain 120–228°E, 20°S–20°N under the SW convention; MIN_DAYS rule as described.
- H1 +0.2555; block-4 (−0.031, +0.546) vs study (−0.026, +0.537) [seed]; HAC(3) (+0.017, +0.494) exact. Step +17.04
  (HAC +8.52, +25.56) exact; trend with step −0.2425 exact. H2 and H3 exact. Per-EEZ shares, steps, group sums,
  "four of seven negative / five of five positive" all verified. Means 80.9→91.3, 81.8→92.4, 78.8→83.5 verified.
- Power: nominal size 0.13–0.14, calibrated MDE 0.40–0.425, nominal MDE 0.30–0.325, calibrated detection year
  2095–2098, nominal 2083–2084 — all within Monte Carlo noise of the study's figures.
- Figures F1 and F4 plot the numbers in the tables. D2.1 (projection Btot = adult+young, mislabelled) confirmed and
  extended to all four ESMs by CDO history.
- Novelty: web and OpenAlex searches found no detection or power test of SEAPODYM's redistribution trend; SEAPODYM
  validation is fit to catch/length/tagging (Senina et al. 2020). The novelty claim stands.

## Numbers recomputed

| Quantity | Report / tables | Recomputed | Note |
| --- | --- | --- | --- |
| Bell reproduction, 4-ESM mean, 2011–2018 baseline | −14.2% ("against 2009–2018") | −14.20% | label wrong: this is the 2011–2018 baseline |
| Bell, spliced 2009–2018 baseline | −15.3% (plan only) | −15.34% | |
| Bell, paper's eq. (1): monthly ratios, 2011–2020 base | — | **−13.8% (−9.3 to −19.9)** | closer to published −13% (−5 to −20) |
| EEZ mask area / Marine Regions | 1.004 | 1.0040 | mask identical to 2e-15 |
| τ (pp/yr) | −0.1174 | −0.1174 | per ESM −0.074/−0.216/−0.152/−0.027 |
| hist bet Btot vs adult+young | "0.848 ×, 0.73–1.00 by cell" | ratio 0.848; **vs adult only: 1.0000, r = 1.000000, max diff 0** | it is the adult file |
| proj bet Btot vs adult+young | identical | identical, all 4 ESMs by CDO history | |
| O1 1985 / 1995 / 2005 / 2010 / 2015 / 2021 | .8833/.8176/.8203/.9639/.8045/.9197 | same to 6e-16 | EEZ t / domain t in log |
| H1 trend | +0.255 | +0.2555 | |
| H1 block-4 bootstrap | (−0.026, +0.537) | (−0.031, +0.546) | seed |
| H1 HAC(3) | (+0.017, +0.494) | (+0.017, +0.494) | |
| H1 GLS-AR(1) | — | +0.198 (−0.225, +0.620) | includes τ |
| H1 parametric AR(1) bootstrap | — | (−0.091, +0.607) | |
| Coverage, block-4 / HAC(3), AR(1) φ=0.56 | "0.89" | **0.79 / 0.76** | 0.89 / 0.85 with white noise |
| Residual ACF 1–4 | 0.56 | 0.56, 0.37, 0.33, 0.28 | PACF 0.57, 0.09, 0.16, 0.05 |
| Step 2010 | +17.0 (+8.5, +25.6) | +17.04 (+8.52, +25.56) | trend −0.2425 |
| H2 catch share diff 1980–2010 | −0.208 (−0.793, +0.240) | −0.208 (−0.793, +0.273) | |
| H2 density share diff 1980–2010 | −0.398 (−0.889, −0.045) | −0.398 (−0.873, −0.015) | |
| Observed density-share trend 1990–2010 | — | **+0.180 (HAC −0.126, +0.485)** | model +0.221 |
| H3 R² ENSO / SEAPODYM | −1.72 / −0.46 | −1.720 / −0.459 | both worse than a constant |
| Nominal size at δ=0 | 0.14 | 0.129 | |
| Power at τ, nominal / calibrated | 0.37 / 0.17 | 0.372 / 0.191 | |
| Power, hinge from 2011 to 2021 | — | **0.06 calibrated** | the actual projected signal |
| MDE nominal / calibrated | 0.325 / 0.425 | 0.30–0.325 / 0.40–0.425 | |
| Detection year baseline, calibrated | 2098 | 2095, 2097, 2096 (3 seeds) | |
| Detection year, nominal | 2084 | 2083 | |
| Detection year range over noise models | — | **2049–2120** | 2049: 1990–2021 step-adj residuals; 2120: φ=0.75 |
| Detection year, fishery-independent (σ 1.26) | — | 2036 | |
| Footprint 0.8, all years / covered years | +0.075 / +0.002 | +0.075 (+0.018, +0.132) / +0.002 (−0.010, +0.013) | |
| **SEAPODYM projected shift inside the 0.8 footprint** | — | **+0.0095 deg/yr** | domain-wide +0.0704; inside observed CI |
| Footprint 0.5, covered years ≥0.8 | +0.137 (in footprint.json, not in report) | +0.137 (+0.077, +0.195) | 1997–2021 |
| Footprint 0.5, coverage ≥0.6 | — | +0.070 (+0.012, +0.126) | 1990–2021 |
| Footprint on 1995–2021 / 2000–2021 windows, cov ≥0.8 | — | +0.088 (+0.035, +0.141) / +0.086 (+0.039, +0.130) | |
| Outside-EEZ skj catch 160–180°E, 2005–09 → 2010–14 | — | 87 → 12 kt/yr | direct closure test |
| Largest year-to-year swing | "15 points" | 18.3 pp (1989), 18.1 (2010) | |
| Means pre/post 2010: catch / days / density | 80.9→91.3 / 81.8→92.4 / 78.8→83.5 | same | |
| Per-EEZ shares and steps (12) | as reported | all match | |

## Summary for the author

Fix issues 1–6 before publishing; 7–11 should be fixed in the same pass; 12–18 are a few minutes each. The
preregistered machinery is correct and the honest core finding — that the catch share cannot test this projection
on a policy timescale, and that only a fishery-independent index could — is well supported and worth publishing.
The headline about the fish not moving is not; the data are consistent with the projected shift and, on wider fixed
grounds, show an eastward drift at or above the projected rate.
