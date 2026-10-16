# Preregistration — Does New Zealand's geothermal fleet hold its output?

*Achievable output, field by field, from 26 years of half-hourly market metering, tested against the planning
assumption that existing geothermal plant is flat must-run capacity.*

Committed before any output series was built. Examined beforehand, deliberately, because none involves output:
which plants appear in the EMI datasets and when (coverage only), the EMI plant register, and the MBIE documents.
All code is committed with this plan and has been run only on synthetic data.

## 1. The question

New Zealand's electricity scenario models treat existing geothermal plant as steady baseload. Is that what has
happened? How fast does each field's *achievable* output — what it can deliver when running, as distinct from
how much it happened to generate — change over time?

### 1.1 What the lead claimed, and a correction before any data

The lead compared realised decline with "MBIE's 3%/yr annual run down". Reading the source (Lawless, van Campen
& Randle, *Future Geothermal Generation Stack*, MBIE, Revision D, March 2020, §3.3) shows the 3% is something
else. It is the assumed natural decline of wells and resources, used to size the cost of **make-up drilling**
("For a 55MW project ... around one well every 5.5 years"), which is then carried as fixed O&M so that output is
maintained. The same report notes it "would be too low for Ohaaki ... and too high for Kawerau". EDGS 2024
assumes no geothermal output decline at all.

So the 3% is gross resource run-down **before** make-up drilling, and metered output is **after** it. A fleet
whose realised achievable output is flat would be consistent with MBIE's assumption, not evidence against it. A
field declining faster than 3%/yr *despite* drilling would be a genuine departure. The lead's decision thresholds
are kept below, because they are still informative, but the report will interpret them in this light. The
substantive test is of the flat-capacity assumption. Logged as deviations D1.

### 1.2 Hypotheses as preregistered

**H1 (primary).** The fleet's capacity-weighted trend in achievable output is a decline of less than 1.5%/yr.
Supported if the 95% interval's lower end is above −1.5%/yr; Refuted if its upper end is below −1.5%/yr;
Inconclusive otherwise. The report also states whether the interval is consistent with flat (contains 0).

**H2 (secondary).** At least two of the eight fields decline faster than 3%/yr. Supported if ≥ 2 fields have a
point estimate below −3%/yr with the interval's upper end below 0. Refuted if fewer than 2 fields have an interval
reaching below −3%/yr. Inconclusive otherwise.

## 2. What is already known

| Work | What it establishes | What it leaves open |
| --- | --- | --- |
| MBIE FGGS (Lawless et al. 2020) | 3%/yr resource run-down for costing make-up drilling; Ohaaki 108 MW originally, 57 MW installed, ~40 MW produced (2019) | measured, fleet-wide realised trends |
| NZGA annual geothermal reviews; MBIE Energy in NZ | aggregate generation and capacity by year | separating decline from outages, upgrades and new plant |
| O'Sullivan et al. (2015, WGC), modelling retrospective on Wairakei and Ohaaki | old reservoir models were too pessimistic; fewer make-up wells needed than forecast | other fields; post-2015 |
| NZ Geothermal Workshop field papers | single-field reservoir and emissions analyses | a common, metering-based measure across the fleet |

A search on 2026-10-17 (web; the lead's scouting search of NZGW/IGA proceedings) found no fleet-wide,
metering-based estimate of realised achievable-output trends.

## 3. Data (all open, no accounts)

| Source | Use | Vintage |
| --- | --- | --- |
| EMI *Generation_MD*, 2000-01 to 2026-09 (321 monthly files) | half-hourly metered generation by plant, fuel codes | 213 MB, retrieved 2026-10-16T11:46Z, hashes in `data/raw/VINTAGE_emi_gmd.txt` |
| EMI dispatched-generation plant register (2026-07-02) | nameplate, commissioning dates | `data/raw/emi_fleet/` |
| MBIE FGGS (2020) and EDGS 2024 (Wayback copies) | the 3% assumption; plant histories | `data/raw/docs/` |

The unit-level dataset the lead named (*Unit_level_generation_IR*) was downloaded and inventoried first. It holds
Wairakei and Ohaaki units only for 2000–2003 and lacks Mokai, Poihipi and Rotokawa entirely, so it cannot carry the
study. Generation_MD is plant-level and covers every geothermal plant (inventory below).

## 4. What was known before any output

Geothermal plant series in Generation_MD (coverage only):

| field | plants (first month – last month) |
| --- | --- |
| Wairakei | Wairakei 2000-01–; Poihipi 2000-01–; Te Mihi 2013-10– |
| Ohaaki | Ohaaki 2000-01– |
| Mokai | Mokai 2000-01– |
| Kawerau | kawerau_geo (KAW0111) 2000-01–2008-03; Kawerau KGL 2008-06–; KAW0111 "kawerau" 2020-01–; Norske Skog 2020-01–; TOPP2 2025-08– |
| Rotokawa | Rotokawa 2009-01–; Nga Awa Purua 2010-01– |
| Tauhara | Te Huka 2010-05–; Tauhara 2023-11–; Te Huka 3 2024-08– |
| Ngatamariki | Ngā Tamariki 2013-03– |
| Ngawha | KOE0331 2009-01–2012-03; KOE1101 2012-04– |

All run to 2026-09 unless an end is shown. The **field** is the unit, not the plant, because plants on one field
share a consented fluid take. At Wairakei, fluid "is prioritised to Te Mihi and Poihipi ... Wairakei utilises the
balance and ramps up during outages on other plants" (Contact, quoted in FGGS). A single plant's output there
reflects allocation, not the reservoir.

## 5. Design

**Achievable output.** For each field and month: the 95th percentile (P95) of half-hourly field output (the sum
of its reporting plants; a half-hour where any reporting plant has no value is missing, not zero). P95 is the
level reached or exceeded in about 36 hours of the month. It ignores outages, maintenance and short flexing as long
as the field runs at its capability for a day and a half. In synthetic tests (`code/test_analysis.py`) it recovered
a true −2.00%/yr trend as −2.00 (sd 0.003) through annual three-week maintenance, Poisson forced outages, summer
derating and flexing. With forced outages becoming more frequent and no true decline, P95 gave −0.01%/yr while the
monthly mean (a capacity factor) gave −1.86%/yr.

**Segments.** A field's record is cut wherever the set of reporting plants changes, or at a documented capacity
change of a reporting plant (table below; the window is excluded). A newly built plant's first 6 months are
excluded as commissioning ramp. Segments under 60 months are not used. Within a segment, months with < 80% of
half-hours valid, or with P95 below 20% of the segment median (a whole-month outage), are dropped and counted.
Retirements and deratings are **not** cut: losing capacity because the steam ran out is the decline being measured.

| field | excluded window | capacity change | source |
| --- | --- | --- | --- |
| Wairakei | 2004-01 – 2005-12 | Wairakei binary bottoming plant, 14 MW | FGGS Table 2 |
| Mokai | 2005 | stage 2 | FGGS Table 2 |
| Mokai | 2007 | stage 1A (total 112 MW) | FGGS Table 2 |
| Kawerau | 2017 | KGL rerated 100 → 117 MW | FGGS §Kawerau |
| Kawerau | 2018 | Te Ahi O Maui, 25 MW | FGGS Table 2 |
| Ngawha | 2020-01 – 2021-12 | OEC4 / Ngāwhā B, 31.5 MW (register 2020; FGGS expected mid-2021) | EMI register; FGGS |
| Ngatamariki | 2026-01 onward | OEC5, +46 MW, Jan–Mar 2026 | Mercury NZX, Jan 2026 |

From the inventory, the usable segments should be: Wairakei 2006-01–2013-09 and 2014-04–2026-09; Ohaaki
2000-01–2026-09; Mokai 2000-01–2004-12 and 2008-01–2026-09; Kawerau 2000-01–2008-03, 2008-12–2016-12 and
2020-01–2025-07; Rotokawa 2010-07–2026-09; Tauhara 2010-11–2023-10; Ngatamariki 2013-09–2025-12; Ngawha
2012-04–2019-12. The code computes them; any difference will be reported.

**Trend.** Within each segment: log(P95) on month-of-year dummies (ambient temperature; air-cooled binary plants
lose output in summer) plus a linear trend, by GLS with AR(1) errors. A field's trend is the inverse-variance
weighted mean of its segment trends. The fleet trend is the capacity-weighted mean of field trends (weights = mean
P95 MW over the field's segment months). Its variance uses the correlation of the fields' monthly residuals over
common months (0 for pairs with < 36), and the perfect-correlation bound is also reported. %/yr = 100(e^b − 1).

## 6. Validation, before the real data (`code/test_analysis.py`, 9/9 pass)

1. P95 recovers a known −2%/yr through outages, maintenance, derating and flexing (mean −1.999, sd 0.003).
2. P95 is unaffected by rising outage frequency (−0.011); the monthly mean is not (−1.86).
3. Interval coverage on AR(1) monthly noise (φ = 0.6, 144 months): 0.950. Newey–West intervals, tried first,
   covered 0.67–0.88 across 60–144-month segments and φ = 0.3–0.8, against GLS-AR(1)'s 0.87–0.95. Newey–West is
   therefore a sensitivity only.
4. Segments are cut at an event window, a membership change and a commissioning ramp as specified.
5. The field sum treats a missing plant value as missing, not zero.
6. The decision rules give the intended verdicts on constructed inputs.

## 7. Sensitivities (reported; none changes a verdict)

P50, P99 and the monthly mean in place of P95; equal field weights; the last ten years only (2016-10–2026-09);
excluding Wairakei (consent-limited, run as the field's swing plant); Newey–West intervals. Also reported,
descriptively: plant-level trends and a rolling five-year trend per field (decline phases and drilling recoveries).

## 8. Threats to validity

1. **Achievable is not natural.** Trends include make-up drilling, consent limits and fluid allocation; they
   measure what the fleet delivered, not what the reservoir would do untouched (§1.1).
2. **Undocumented capacity changes** (a turbine upgrade, a gas-reinjection retrofit that adds parasitic load —
   flagged by REN21 GSR 2025 for some NZ sites) would bias a segment's trend. The rolling-trend figure is the check;
   a step found there is reported, not used to re-cut segments.
3. **Dispatch.** Geothermal offers at near-zero prices and rarely flexes; P95 needs only ~36 hours a month at
   capability, so occasional flexing does not register. Sustained flexing would.
4. **Metering scope.** Generation_MD covers grid-connected and some embedded plant; a field's reporting set can
   change for administrative reasons (segment boundaries handle this, at the cost of shorter segments).
5. **Ambient warming** over the period would add a tiny negative trend at air-cooled plant; not modelled.
6. **Eight fields** make "fleet" a weighted mean of few units; the interval reflects this.

## 9. Scope and care

The analysis unit is generating plant and market metering. Several fields are owned, co-owned or hosted by iwi and
Māori land trusts (for example Tuaropaki Trust at Mokai, Ngāti Tūwharetoa and Tauhara North No. 2 Trust
interests, the Kawerau A8D Ahu Whenua Trust). Field-level trends are reported as what the public metering
shows, framed as capability of plant under its current consents. They are not judgements about resource
stewardship, and the report says what each trend can and cannot attribute.

## 10. Process commitments

- `build_series.py`, `analysis.py` and the tests are committed with this plan; no real output series has been
  computed.
- Departures go in deviations.md, timestamped with `date`.
- An independent adversarial review (Fable 5.1) runs on the pre-review draft.
- Released: monthly field and plant series, all code. EMI data are public and not redistributed.
