# Preregistration — Is the projected eastward shift of Pacific skipjack detectable yet?

*A detection-and-power test of the SEAPODYM projections behind the "13% loss from Pacific SIDS waters"
claim, against 42 years of open purse-seine data.*

Committed before any observed catch series was computed. The SEAPODYM model output and the climate
indices were examined beforehand, deliberately — they are the hypothesis-generating model and its forcing,
not the outcome — and what they showed is recorded in §4 so a reader can see exactly what was known when
the thresholds were fixed.

## 1. The question

Bell et al. (2021, *Nature Sustainability* 4:900–910) project that under RCP 8.5 the total biomass of
skipjack, yellowfin and bigeye in the combined EEZs of ten Pacific small island developing states falls by
an average of 13% (range −5% to −20%) by 2050, as tuna move east into the high seas. The figure is now
load-bearing in WCPFC, Forum Fisheries Agency and climate-finance arguments. SEAPODYM's developers validate
the model's *fit* to catch, length and tagging data; nobody has asked whether the projected *redistribution*
is detectable in the observational record, or how much power that record has to detect it.

### 1.1 Hypotheses as preregistered here

**H1 (primary).** Over 1980–2021, the ENSO-adjusted linear trend in the share of tropical purse-seine
skipjack catch taken inside the ten SIDS' EEZs is less negative than τ = **−0.1174 percentage points per
year** — SEAPODYM's own projected rate of change in the identical share (§4.3). Supported if the 95%
interval's lower bound exceeds τ; Refuted if its upper bound is below τ; Inconclusive otherwise.

**H2.** SEAPODYM's historical simulation reproduces the observed historical trend: over 1980–2010 the
difference between the observed and simulated ENSO-adjusted trends has a 95% interval that includes zero.

**H3.** SEAPODYM's historical simulation, linearly calibrated, does not beat a three-predictor ENSO /
warm-pool regression at out-of-sample prediction of the observed share (train 1980–1999, test 2000–2010):
ΔR² = R²(SEAPODYM) − R²(ENSO) ≤ 0.

**H4 (descriptive, no verdict).** The minimum trend the record can detect at 80% power, and the first year
in which a decline at rate τ beginning in 2011 becomes detectable at 80% power.

### 1.2 How these differ from the lead, and why

The lead (leads.json, `blue-pacific-tuna-redistribution-detectability`) proposed a hand-derived threshold
of −0.15 pp/yr, an observation window to 2024 and a 2010–2024 test split. Three things found before this
plan was written changed that, and all are logged in deviations.md D1:

1. **The open data end in December 2021.** The SPC mirror of WCPFC's public-domain 1°×1° file runs
   1967-12 to 2021-12. WCPFC's own downloads now sit behind a registration form, which this lab does not
   use. The window is 1980–2021.
2. **SEAPODYM's historical run ends in December 2010** and the projections begin in January 2011, forced
   by Earth system models rather than observed ocean states. A year-by-year model–observation comparison
   is only possible for 1980–2010, so H3's test period is 2000–2010.
3. **The threshold is derived from the model, not by hand** (§4.3), on exactly the share definition the
   observations use. And the model's own historical run moves the *opposite* way to its projection (§4.2),
   which changes what H1 can and cannot show (§1.3).

### 1.3 What a Supported H1 would and would not mean — fixed now

SEAPODYM's historical simulation shows the EEZ share **rising** over 1980–2010 (+0.105 pp/yr
ENSO-adjusted, 95% interval +0.033 to +0.180; §4.2). The projected decline begins only in the ESM-forced
era. So the model does *not* predict that redistribution should already be visible in the observed record.
An observed trend above τ would therefore be **consistent with SEAPODYM, not evidence against it.** The
informative tests are H2 (does the model reproduce what actually happened?) and H4 (when could the
projected signal first be seen?). The report will say this in its first paragraph whatever H1's verdict.

## 2. What is already known

The independent critic for this scouting round verified novelty: no detection-or-power test of the SEAPODYM
redistribution trend exists; the literature contains the projections themselves (Bell et al. 2021;
FAO/Common Oceans) and short-record ENSO/CPUE work. Closest prior work:

- **Bell et al. (2021)** — the projection under test.
- **SEAPODYM validation** (WCPFC-SC21-2025/SA-IP-20 §6.2; the SC22-2026 validation-score table) —
  out-of-sample fit to catch, length and tagging, not to the redistribution trend.
- **Lehodey et al. (1997, *Nature*)** and the ENSO-displacement literature — skipjack habitat tracks the
  warm-pool edge, which is why H1 adjusts for ENSO and the warm-pool edge rather than testing a raw trend.
- **Hanich et al. (2018) vs McDermott et al. (2019), *PNAS*** — the PIPA exchange, which established that
  ENSO dominates tropical-Pacific effort redistribution and that ENSO control is the crux of any inference
  from catch.
- **Dutta (2025), "Vessel Day Scheme and Tuna Catch in the Pacific Island Region"** (10.1002/app5.70042) —
  management, not fish, moves catch across EEZ boundaries; motivates §8's management sensitivity.
- **WCPFC's 2025 descriptive statistics** — about 88% of 2024 purse-seine catch inside coastal EEZs (all
  coastal states, a different denominator from the ten SIDS used here).

## 3. Data (all open, no accounts)

| Source | Use | Access |
| --- | --- | --- |
| WCPFC public-domain purse-seine catch/effort, 1°×1° monthly, 1967–2021 | observed series | SPC THREDDS `WCPFC_S_PUBLIC_BY_1x1_MM.nc`, 1,619,785,634 B, last modified 2024-11-26 |
| SEAPODYM 2° reference runs, skipjack/yellowfin/bigeye, hist (1980–2010) and GFDL/IPSL/MIROC/MPI RCP 8.5 (2011–2099), no fishing (F0) | model | SPC THREDDS `PCCOS/SEAPODYM/2DEG/` |
| Marine Regions World EEZ, 12 EEZ areas of the ten SIDS | EEZ mask | VLIZ WFS, CC-BY 4.0, no form |
| NOAA PSL Niño 3.4 (ERSST-based) | ENSO covariate | `psl.noaa.gov/data/correlation/nina34.data` |
| NOAA ERSST v5 monthly | warm-pool edge | NCEI `ersst.v5.YYYYMM.nc`, 1975–2023 |

Only the ten SIDS of Bell et al. are used: the eight Parties to the Nauru Agreement (FSM, Kiribati,
Marshall Islands, Nauru, Palau, Papua New Guinea, Solomon Islands, Tuvalu), Tokelau and the Cook Islands —
twelve EEZ areas, Kiribati counting three. The Torres Strait joint-regime area is excluded.

## 4. What SEAPODYM predicts, computed before any observation

`code/model_targets.py` and `code/indices.py` were run on model output and climate indices only.
Results are in `results/tables/model_targets.json` and `model_hist_trend.json`.

### 4.1 The headline reproduces approximately, not exactly

The EEZ mask (fractional overlap on the 2° grid) covers 16,487,700 km² against Marine Regions' stated
16,421,482 km² — ratio 1.004 — so the mask is right. From the same four ESMs Bell et al. used, the
three-species biomass change in the twelve EEZ areas, 2044–2053 against 2009–2018, is:

| ESM | change, projection-only baseline (2011–2018) | change, spliced baseline (2009–2018) |
| --- | --- | --- |
| GFDL | −11.3% | −13.1% |
| IPSL | −20.4% | −22.0% |
| MIROC | −15.6% | −16.0% |
| MPI | −9.6% | −10.3% |
| **mean** | **−14.2%** | **−15.3%** |
| *Bell et al. 2021* | *−13% (−5% to −20%)* | |

The mean is within 1–2 points; the least-negative ESM is −9.6% where the paper reports −5%. Candidate
reasons, none testable here: a later recalibration of these "reference" runs, Bell et al. using runs with
fishing where these are F0, or different EEZ boundaries in 2021. **This study tests the files SPC serves,
not the paper's exact numbers**, and says so.

Two data-integrity findings along the way, logged in D2: the bigeye projection files labelled "Btot" name
their variable `bet_B_young` although they hold total biomass (identical to adult + young, correlation
1.0000); and the bigeye *historical* "Btot" is a different quantity, 0.848 × (adult + young) and spatially
non-uniform, so it is replaced by adult + young. Skipjack and yellowfin agree to 1.0000 in every cell.

### 4.2 The model's own historical run moves the opposite way to its projection

Share of skipjack biomass in domain D (20°S–20°N, 120°E–228°E) lying inside the twelve EEZ areas:

| SEAPODYM skipjack | value |
| --- | --- |
| historical mean share, 1980–2010 | 49.4% |
| historical trend 1980–2010, raw | +0.114 pp/yr (+0.005, +0.229) |
| **historical trend 1980–2010, ENSO-adjusted** | **+0.105 pp/yr (+0.033, +0.180)** |
| historical trend, Niño 3.4 terms only | +0.112 pp/yr (+0.043, +0.186) |
| projected share, 2011–2020 mean | 47.8% |
| projected share, 2044–2053 mean | 41.6% |

### 4.3 The threshold τ

τ is the four-ESM mean linear trend in that same share over 2011–2050: **−0.1174 pp/yr**. Per ESM:
GFDL −0.074, IPSL −0.216, MIROC −0.152, MPI −0.027 pp/yr. The 2011–2030 mean rate is steeper, −0.336
pp/yr; the 2011–2050 rate is used because it corresponds to the "by 2050" claim.

## 5. Design

**Observed series** (`code/observed.py`), annual, 1980–2021, over the same domain D and the same twelve
EEZ areas (fractional mask on the 1° grid):

- **O1, catch share (primary)** — skipjack catch inside the EEZs ÷ skipjack catch in D. The quantity
  WCPFC reports and the one tied to access revenue. It mixes where the fish are with where the fleet is
  allowed and chooses to fish.
- **O2, density share (secondary)** — Σ(area × EEZ fraction × CPUE) ÷ Σ(area × CPUE) over cells fished at
  least 5 days that year, CPUE = annual skipjack catch ÷ days fished. Counts each cell by how dense the
  fish were where the fleet looked, not by how much effort it received.
- **O2u, unassociated density share (secondary)** — as O2 with CPUE = skipjack per free-school set.

The lead specified a delta-GLM CPUE standardisation; O2 and O2u replace it (D1). A share is a ratio within
one year, so fleet-wide technology creep cancels; what does not cancel is a different mix of FAD and
free-school fishing inside and outside the EEZs, which O2u tests directly. A GLM would add degrees of
freedom without addressing that.

**Coordinate convention.** The file's integer coordinates are unlabelled. Primary: south-west corner.
Sensitivities: cell centre; equator-nearest corner. They differ only for boundary cells.

**ENSO adjustment.** share_t = a + b(year − 2000) + c·Niño3.4_t + d·Niño3.4_{t−1} + e·WPE_t + ε, OLS;
b is the trend. WPE is the annual mean longitude of the eastern edge of the ≥29 °C water along the equator
(5°S–5°N), interpolated, anchored at the warm-pool maximum (§9.7). The same specification is applied to
model and observations.

## 6. Estimands and decision rules

| | estimand | rule |
| --- | --- | --- |
| **H1 (verdict)** | b for O1, 1980–2021, primary convention, full covariates | Supported if lo > τ; Refuted if hi < τ; else Inconclusive |
| H2 | b(O1) − b(SEAPODYM-hist), 1980–2010 | consistent if the 95% interval includes 0 |
| H3 | ΔR², test 2000–2010 | Supported if ΔR² ≤ 0 |
| H4 | MDE at 80% power; detection year | descriptive |

Intervals: moving-block residual bootstrap, block 4 years, 2000 draws, seed 20261016. H2 uses a paired
block bootstrap over years so both series see the same ENSO history. H3's interval resamples test years.
A Newey–West interval (HAC, 3 lags) is reported beside every bootstrap interval.

**Disclosed before use:** in 150 synthetic replicates the block-bootstrap interval covered the true trend
89% of the time against a nominal 95% (`code/test_analysis.py`). It is mildly anticonservative at n = 42.
If H1's verdict differs between the bootstrap and HAC intervals, the report says so and leads with the
more conservative one.

## 7. Power

Computed from the observed residuals after this plan is committed, by a procedure fixed now
(`analysis.h4_power`, `analysis.h4_detection_year`):

- **MDE.** Strip the fitted trend from the observed series, inject a linear decline of δ ∈ {0, 0.025, …,
  0.80} pp/yr, re-add block-resampled residuals, re-fit, and test the decline one-sided at α = 0.05 (HAC).
  1000 simulations per δ. The MDE is the smallest δ detected in ≥80% of them.
- **Detection year.** A decline at rate τ beginning in 2011 is a hinge, τ·max(0, year − 2011). Simulate
  AR(1) noise with the observed ENSO-adjusted residuals' SD and lag-1 autocorrelation (future analysts
  will have the ENSO indices, so ENSO-explained variance is not added back), and find the first year Y for
  which a 1980–Y record detects the hinge one-sided in ≥80% of 1000 simulations.

## 8. Sensitivity analyses (reported, none changes the verdict rule)

S1 coordinate convention (centre; equator-nearest corner) · S2 covariates (none; Niño 3.4 only; full plus
a 2010 step for the high-seas-pocket closure) · S3 window 1980–2010 · S4 series O2, O2u, the 10°S–10°N core
band, the EEZ share of fishing days, yellowfin and bigeye · S5 H2 on O2 and O2u.

## 9. Threats to validity, declared in advance

1. **Public-domain masking.** Cells failing WCPFC's three-vessel rule are suppressed, most often in exactly
   the sparse small-EEZ places this is about. `observed.py` measures catch recorded where effort is missing.
   **Rule fixed now:** if that exceeds 10% of in-EEZ skipjack catch in any decade, O2 and O2u are reported
   as unreliable for that decade and the report leads with O1.
2. **Catch is not biomass.** O1 reflects effort allocation and management as well as fish. The
   high-seas-pocket closures (2010), the Vessel Day Scheme (2007–) and the PIPA closure (2015) all move
   catch for regulatory reasons. S2's step term and O2 address this; neither removes it.
3. **SEAPODYM is no-fishing (F0) biomass**, compared with fished-stock observations. The comparison is
   framed on shares and trends, never levels.
4. **The domain stops at 228°E.** The WCPFC file covers the WCPFC area only. If biomass leaves the domain
   eastward it leaves the denominator as well, so the share falls less than the EEZ biomass does. The model
   and the observations use the identical domain, so the comparison stays like-for-like, but the share is
   not the 13% figure and must not be reported as if it were.
5. **The reproduction gap** (§4.1): τ is derived from the files SPC serves.
6. **Coverage** (§6): the bootstrap interval runs slightly narrow.
7. **The warm-pool edge definition** was revised before this plan, after the first version anchored at a
   fixed 140°E and lost 27 of 42 years (D3). It is collinear with Niño 3.4 (r = 0.919); S2 drops it.
8. **One trend, one domain, one fleet.** This is purse-seine skipjack in the western and central Pacific.
   Longline, pole-and-line and the eastern Pacific are outside it.

## 10. Governance and scope

The conclusions bear on Pacific Island revenue and negotiating positions. The lead names SPC's Oceanic
Fisheries Programme, the Forum Fisheries Agency and the PNA Office as the bodies to engage before any
EEZ-level or country-attributed interpretation. **This study reports only the pooled share across all
twelve EEZ areas.** It computes no per-country or per-EEZ series, converts nothing to revenue, and makes no
statement about any individual state's fishery. The unit of analysis is the model and the fleet's aggregate
catch, not Pacific people.

## 11. Process commitments

- Code is committed before the outcomes it produces. `observed.py` and `primary.py` are committed with this
  plan and have not been run.
- Every departure is appended to deviations.md with a timestamp from `date`.
- An independent adversarial review (Fable 5.1) runs on the pre-review draft; prompt, review and any
  confirmation pass go under `review/`.
- Released: the annual observed and model series, the EEZ mask, all code. Raw WCPFC and SEAPODYM files are
  public at the URLs above and are not redistributed.
