# Preregistration: the Clean Car Discount's removal, or road-user charges? Separating two 2024 shocks to New Zealand EV uptake

Lead: `movement-nz-ev-policy-discount-vs-ruc` (The Energy Movement). Written 2026-10-20, before any registration
series was built and before any effect was estimated.

**Examined beforehand (no effect estimated):** the field list and category counts of NZTA's Motor Vehicle Register
service `MVR_Mar26` (ArcGIS FeatureServer, server-side aggregation, 2,000-record pages). It carries
`FIRST_NZ_REGISTRATION_YEAR`/`_MONTH`, `MOTIVE_POWER`, `IMPORT_STATUS`, `VEHICLE_TYPE`, `TLA` and mass. Counts of
motive-power and vehicle-type categories since 2023 were read to define the groups below, and a month count for
2026 showed the snapshot runs through September 2026. No registration series by month and powertrain was built.

**Novelty** (searches 2026-10-20). A 2026 Research Square preprint (rs-11080967) estimates the Clean Car Discount's
removal with a regression discontinuity in time and reports an immediate, lasting fall of about 24 percentage
points in battery-electric market share. From its abstract and secondary reporting it does not separate the
road-user-charge change, and does not quantify pull-forward; the full text could not be retrieved, so this study
treats it as closest prior work and will compare results rather than claim priority on the Clean Car Discount
effect itself. News coverage reports monthly shares; the Ministry of Transport's 2023 regulatory impact statement
predates both changes. No study separating the two shocks, or measuring the December 2023 pull-forward, was found.

## 1. The two shocks

- **E1, 31 December 2023:** the Clean Car Discount ended. Rebates for battery-electric (BEV) and plug-in hybrid
  (PHEV) vehicles stopped, as did smaller rebates for other low-emission vehicles including many non-plug hybrids,
  and the fees on high-emission vehicles stopped at the same time.
- **E2, 1 April 2024:** road user charges began to apply to light BEVs and PHEVs. Non-plug hybrids were **not**
  moved to road user charges: as of May 2026 the government has legislated intent but set no date, so throughout
  this study's window non-plug hybrids remain on fuel excise.

That asymmetry is the identification: non-plug hybrids are exposed to E1 but not to E2.

## 2. Data

- **NZTA Motor Vehicle Register**, service `MVR_Mar26`, queried by server-side aggregation (no bulk download;
  NZTA's web site refuses scripted requests). Counts of first New Zealand registrations by calendar month,
  motive power, import status and vehicle type, January 2021 to September 2026.
- **Universe:** light vehicles, `VEHICLE_TYPE` in `PASSENGER CAR/VAN` and `GOODS VAN/TRUCK/UTILITY`.
- **Groups:**
  - **BEV:** `ELECTRIC`, `ELECTRIC [PETROL EXTENDED]`, `ELECTRIC [DIESEL EXTENDED]`, the `ELECTRIC FUEL CELL`
    categories;
  - **PHEV:** `PLUGIN PETROL HYBRID`, `PLUGIN DIESEL HYBRID`, the `PLUG IN FUEL CELL` categories;
  - **HEV (control):** `PETROL HYBRID`, `DIESEL HYBRID`, `PETROL ELECTRIC HYBRID`, `DIESEL ELECTRIC HYBRID`;
  - **ICE:** `PETROL`, `DIESEL`, `LPG`, `CNG`, `OTHER`.
- **Treated** for E2 is BEV + PHEV.

## 3. Hypotheses

Let y(t) be the log of monthly first registrations (plus 1) of the treated group.

- **H1 (the January 2024 collapse is largely pull-forward).** Fit y on 2021-01 to 2023-09 with a linear trend and
  calendar-month effects, and predict from 2023-10 on. Let **E** be the excess registrations in December 2023
  (actual minus predicted, in levels) and **M** the shortfall over January–March 2024 (predicted minus actual, in
  levels). The measure is R = E / M.
  - **Supported** if the 95% lower bound of R is at least 0.5; **Refuted** if its upper bound is below 0.5;
    **Inconclusive** otherwise.
- **H2 (road user charges did far less than the rebate's removal).** Two effects on the treated group:
  - **δ_CCD:** the mean deviation of y from the fitted baseline over January–March 2024, the window after E1 and
    before E2;
  - **δ_RUC:** a difference-in-differences across E2, (treated May–October 2024 minus treated January–March 2024)
    minus the same difference for the HEV control. April 2024 is excluded as a transition month.
  - The measure is Q = |δ_RUC| / |δ_CCD|.
  - **Supported** if the 95% upper bound of Q is below 1/3; **Refuted** if its lower bound is at least 1/3;
    **Inconclusive** otherwise.

Intervals for both come from a residual block bootstrap (blocks of three months, 2,000 resamples, seed 20261020)
over the estimation window.

## 4. Secondary and robustness, fixed in advance

- New vehicles and used imports separately: the rebate schedules and the second-hand market differ.
- BEV and PHEV separately, since the PHEV road-user-charge rate is lower.
- Placebo difference-in-differences at 1 April 2022, 2023 and 2025, with the same windows.
- Persistence: the treated-minus-control gap through September 2026.
- The high-emission fee's removal: diesel `GOODS VAN/TRUCK/UTILITY` registrations around E1, reported descriptively.
- Market share as an alternative outcome to counts.
- Sensitivity to the estimation window (start 2021-01 or 2022-01) and to including November 2023 in the excess.

## 5. Threats and care

1. **The register is a snapshot of vehicles still registered in September 2026.** Vehicles since deregistered are
   missing, and attrition rises with age, which tilts earlier months down. The difference-in-differences compares
   powertrains within the same months, so it is largely unaffected; the trend fit for H1 is not, so H1 is repeated
   on new vehicles only, where scrappage over this window is minimal.
2. **Hybrids are a control for E2 only.** They lost rebates at E1 as well, so they cannot identify the Clean Car
   Discount effect; δ_CCD is therefore measured against the group's own fitted baseline, not against hybrids.
3. **Confounders.** Model launches, price cuts and shipping constraints cluster in these months; placebo dates and
   the new/used split test for them, but they cannot be ruled out.
4. **Announcement effects.** Road user charges attach to the vehicle, not the purchase date, so there is no
   incentive to buy before 1 April 2024; the Clean Car Discount, by contrast, rewarded registering before
   1 January 2024, which is what H1 measures.
5. **Power.** The minimum detectable effect for δ_RUC and for R is computed from the bootstrap and reported
   whatever the verdicts.
6. **No personal data.** Counts only, aggregated server-side; no vehicle, owner or address is retrieved.
