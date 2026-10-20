# Preregistration: are New Zealand's gas production forecasts systematically optimistic?

Lead: `energy-nz-gas-production-forecast-calibration` (The Energy Movement). Written 2026-10-20, before any
forecast was paired with any realised outcome and before any error was computed.

**Examined beforehand (no forecast error computed):**
- the structure of one workbook vintage (the 2025-09-18 Wayback copy): sheets `Contents`, `Notes`, `Glossary`,
  `Activity`, `Oil and Condensate`, `Gas`, `LPG`, `Gas and LPG Combined`, `Gas System Deliverability`,
  `2C Resources`, `Petroleum Initially in Place`, `Oil Production Profile`, `Gas LPG Production Profile`. Its
  reserves sheets are headed "as at 1 January 2024" and its gas profile runs 2024-2037 by field, in PJ;
- the Wayback CDX listing for that file (15 captures with status 200, 2021-12-30 to 2026-05-25) and the file list
  of MBIE's energy data directory (`Gas.xlsx`, `gas-quarterly-webtable*.xlsx`, `petroleum-reserves-2019.xlsx`,
  `reserves.xlsx`);
- that MBIE's own site serves an Incapsula bot challenge to scripted downloads, so the Archive is the source.

**Novelty** (searches 2026-10-20). MBIE reports shortfalls descriptively: *Energy in New Zealand 2026* states
2025 net production was 102 PJ, 4.1% below the 107 PJ profile published in June 2025, and the May 2026 release
states 2P gas reserves fell 23% to 731 PJ with operators' 2026 profile 15% below the previous year's. A TIMES-NZ
methodology page reproduces an MBIE chart (Fig. 5, from *Energy in New Zealand 2025*) comparing profiles with
actuals for 2020-2025 and says actual production "often fell short". The international literature on
overconfidence in petroleum estimates (Capen 1976; Bratvold and Begg) is not about New Zealand. No
horizon-resolved, field-level calibration of these profiles, and no test of whether the probabilistic reserve
categories are calibrated, was found.

## 1. Question and hypotheses

Operators report to MBIE, under the Crown Minerals Act annual summary report rules, both their remaining reserves
(1P/2P/3P) and a ~14-year expected production profile per field. Those profiles are the input to MBIE's gas
outlooks, to the system operator's security-of-supply work and to industrial and electricity decisions. The
question is whether they are calibrated.

**The error measure.** For a vintage *v* (as at 1 January *Y(v)*), a field *f* and a calendar year *t*:

  e(v, f, t) = ln((F + ε) / (A + ε)),  ε = 0.05 PJ

where *F* is the forecast gas production and *A* the realised gas production. Positive e is over-forecast
(optimism). The horizon is h = t − Y(v). ε keeps fields that stop producing finite and is fixed here, before any
error is computed.

- **H1 (optimism that grows with horizon).** Let m(h) be the median e over all (vintage, field) pairs at horizon
  h, with a field-cluster bootstrap (2,000 resamples, seed 20261020).
  - **Supported** if m(1) ≥ ln(1.05) and m(3) ≥ ln(1.15), and the 95% interval of each excludes 0.
  - **Refuted** if the 95% upper bound of m(1) is below ln(1.05) and that of m(3) is below ln(1.15).
  - **Inconclusive** otherwise.
  - h = 0 is a part-observed nowcast (the vintage is published mid-year) and is reported but excluded from H1.
- **H2 (P50 reserves are not calibrated).** For consecutive vintages and the same field, compare the 2P
  *ultimate recoverable* volume, which should change only through genuine re-estimation. Let d be the share of
  field-years whose 2P ultimate recoverable is revised **down** by more than 1%, among field-years revised by
  more than 1% either way.
  - **Supported** if the 95% lower bound of d exceeds 0.50; **Refuted** if its upper bound is at most 0.50;
    **Inconclusive** otherwise. Whether d reaches the lead's 0.60 is reported either way.
- **H3 (1P is not conservative).** The same statistic for 1P ultimate recoverable, which for a maturing field is
  expected to be revised upward as probable volumes convert to proved.
  - **Supported** if the 95% lower bound of the downward share exceeds 0.10; **Refuted** if its upper bound is at
    most 0.10; **Inconclusive** otherwise.

## 2. Data

- **Forecasts and reserves.** Every retrievable vintage of MBIE's petroleum reserves workbook, from Internet
  Archive raw (`id_`) copies, deduplicated by sha256 (`code/fetch.py`, run before this plan was written; nothing
  parsed). The vintage is taken from the date written inside the workbook ("as at 1 January YYYY"), never from
  the capture date.
- **Realised production.** MBIE's published gas production series (`Gas.xlsx` and the gas quarterly web tables),
  by field where published and national otherwise.
- **Cross-checks.** Gas Industry Co's published field production, where available.

## 3. Harmonisation and pairing, fixed before any error is computed

- Field names are harmonised by lower-casing, removing punctuation and whitespace, and a rename table built
  **from the name lists alone** (for example grouped entries such as "Kauri & Manutahi" and
  "Ngatoro, Kaimiro, Winsor & Goldie"). The table is committed before pairing.
- A (vintage, field, year) cell enters the analysis if the field appears in that vintage's profile **or** has
  realised production that year: a field that produced without being forecast is a miss in the other direction
  and must not be dropped.
- Grouped entries are compared only against the same grouping on the realised side; where the realised series is
  finer, it is summed to the group.
- Only target years with a complete realised year are used, so t ≤ 2025.

## 4. Analysis

- **Primary.** m(h) for h = 0…5 with field-cluster bootstrap intervals, plus the national aggregate error by
  horizon (sum of forecasts over sum of realised), which is not sensitive to small fields.
- **Reported alongside:**
  - the error by field and by vintage;
  - the share of field-years with zero realised production but a positive forecast, and the reverse;
  - the 2P, 1P and 3P revision distributions, in PJ and relative terms;
  - gas system deliverability against realised average deliverability, descriptively.
- **Sensitivity:** clustering by vintage instead of field; dropping ε (restricting to field-years with A > 0.5
  PJ); trimming the largest 5% of absolute errors; national-only analysis.

## 5. Validation before any verdict

- Reproduce three published MBIE statements from the recovered workbooks and the realised series:
  1. 2025 realised gas production 102 PJ against the June 2025 profile's 107 PJ (−4.1%);
  2. the 1 January 2026 profile for 2026 is about 15% below the 1 January 2025 profile for 2026;
  3. 2P gas reserves 731 PJ at 1 January 2026, 23% below a year earlier.
- Check each vintage's profile total for its first forecast year against MBIE's published national expectation.
- If a reproduction fails by more than 2%, the discrepancy is investigated and reported before any hypothesis is
  scored.

## 6. Feasibility and power, fixed in advance

- **Abort rule.** If fewer than 4 distinct vintages carrying a gas production profile are recovered, H1 is not
  scored and the study is reported as a descriptive audit. If fewer than 3 consecutive vintage pairs are
  recovered, H2 and H3 are not scored.
- **Minimum detectable effect.** The bootstrap MDE for m(1) and m(3), and for the revision shares, is computed
  from the recovered sample and reported in the results, whatever the verdicts.

## 7. Threats and care

1. **Basis mismatch.** The profiles are operators' expected production; MBIE's statistics are gross or net of
   flaring, venting and reinjection, and the workbook says the two may differ. The national validation above
   measures the gap, and the analysis is repeated on both bases where published.
2. **Plan change versus optimism.** A profile is conditional on a development plan that may later change. This
   study measures calibration of the published numbers, not intent, and says so.
3. **Survivorship and new fields.** Fields enter and leave the workbook; the union rule in §3 keeps both
   directions.
4. **Few vintages.** Intervals will be wide at long horizons; the MDE is reported rather than implied.
5. **Not a resource assessment.** No claim is made about how much gas is in the ground, only about the published
   forecasts and their revisions.
6. **No individual or community data.** The units are fields and company filings.
