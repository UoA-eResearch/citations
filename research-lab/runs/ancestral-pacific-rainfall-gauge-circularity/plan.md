# Preregistration: is gridded rainfall skill over Pacific Island countries circular?

Lead: `ancestral-pacific-rainfall-gauge-circularity` (Ancestral Futures / Blue Pacific). Written 2026-10-18, before
any product value was compared with any gauge.

**Examined beforehand (no skill computed):**
- the GHCN-Daily inventory: 148 Pacific Island stations with precipitation after 1985;
- one CHIRP and one CHIRPS grid, for the land mask only. CHIRP has values at all 148 stations; CHIRPS masks 14 as
  ocean;
- the CHIRPS monthly "stations used" lists (1981-01 to 2026-09, 549 files) and their format;
- read speeds from the data servers;
- Wild, Chua & Kuleshov (2021, *Remote Sensing* 13:3929): a monthly collocation analysis over six south-west
  Pacific sub-regions against MSWEP, which is itself gauge-blended. It is not gauge-based and not twin-based. With the
  2026 Fiji study, it is the closest prior work.

## 1. Question and hypotheses

Gauge-blended rainfall products look more skilful than their satellite-only twins at gauges. Over Pacific islands,
the gauges used to check them are often the gauges blended into them. How much of the blended product's advantage
survives at gauges it did not ingest?

**Primary pair:**
- CHIRP (satellite plus model, no stations);
- CHIRPS v2.0 (CHIRP blended with station data). The two differ only by the station blending.

**Labels.** CHIRPS publishes, for each month, the stations it blended, with coordinates. A gauge-month is labelled
by the distance from the evaluation gauge to the nearest CHIRPS input station that month:
- **supported:** an input station within 25 km;
- **independent:** none within 100 km;
- **intermediate:** 25–100 km, excluded from the primary contrast.

**Skill**, at each station and in each stratum, on pentad rainfall totals (§3):
- the blending gain g = 1 − RMSE(CHIRPS) / RMSE(CHIRP);
- the KGE difference ΔKGE = KGE(CHIRPS) − KGE(CHIRP).

**Hypotheses:**
- **H1 (circularity).** The mean blending gain at independent gauge-pentads is at most half the mean gain at
  supported gauge-pentads. The ratio R = Ḡ_ind / Ḡ_sup uses station means, with a station-block bootstrap (2,000
  resamples, seed 20261018).
  - Supported: the upper bound of R is < 0.5.
  - Refuted: its lower bound is ≥ 0.5.
  - Inconclusive otherwise, including when Ḡ_sup's interval includes 0 (no gain to shrink).
- **H2 (ranking reversal).** At independent gauge-pentads, the satellite-only twin is the better product. The measure
  is the station-mean ΔKGE (independent stratum).
  - Supported: the upper bound is < 0.
  - Refuted: the lower bound is > 0.
  - Inconclusive otherwise.

  Tested for the primary pair, and for the secondary pair (§2).

## 2. Data

- **Gauges: GHCN-Daily.** PRCP for every station in the Pacific Island countries and territories, from the NCEI
  per-station `.dly` files. GSOD is not used (a descope from the lead): its Pacific stations are largely the same
  airports.
- **CHIRP pentads** (`products/CHIRP/pentads/`, 0.05°, uncompressed GeoTIFF) and **CHIRPS v2.0 pentads**
  (`global_pentad/cogs/`, COG). Station pixels are read by HTTP range request (`/vsicurl/`), one request stream at a
  time.
  - **Period.** 1981-01 to 2025-12, 3,240 pentads per product.
  - **Pentads.** Six per month: days 1–5, 6–10, 11–15, 16–20, 21–25, and 26 to the end of the month.
- **CHIRPS stations-used lists**, monthly, 1981–2025.
- **Secondary pair: PERSIANN (original, satellite-only; UCI CHRS daily, 0.25°) against PERSIANN-CDR** (NCEI daily,
  0.25°, bias-adjusted to GPCP monthly, which uses GPCC gauges).
  - **Period.** 2001–2020, because both servers are slow.
  - **Label.** GPCC Full Data Monthly v2022 gauge counts in the 2.5° GPCP cell containing the station: supported if at
    least 1, independent if 0.
  - **Scope.** The pair also differs in algorithm, so it is secondary.
  - **Feasibility abort.** If either product cannot be retrieved within 72 hours of polite fetching, the secondary
    pair is reported as not done.
- **Descoped from the lead:**
  - ERA5, as a no-gauge reference;
  - CMORPH RAW/CRT: RAW is no longer openly available, since NOAA CPC removed it and NCAR RDA and CEDA need accounts;
  - the matched tropical-continental comparison set.

## 3. Processing

**Gauge QC.**
- Keep values with a blank GHCN quality flag only.
- Remove runs of five or more consecutive identical non-zero daily values.
- A gauge pentad is the sum of its days, and only complete pentads are kept: every day valid.

**Timing.** Per station, the gauge pentads are formed with a day shift s ∈ {−1, 0, +1}. The shift is the one
maximising the Spearman correlation with **CHIRP**, the satellite-only twin, over the whole record. It is then applied
to every product, so the choice cannot favour the blended product.

**Inclusion.**
- **For the primary pair:** at least 100 valid gauge pentads in 1981–2025, and a CHIRPS cell that is not
  ocean-masked.
- **Masked stations** are a reported category: CHIRPS has no estimate there at all.
- **Station-strata** need at least 30 pentads to contribute to that stratum.

**Distance.** Great-circle distance from the gauge to every CHIRPS input station listed for the month the pentad falls
in.

## 4. Analysis (`code/analysis.py`)

- **Per station and stratum:** RMSE, KGE and its components (r, β, γ), bias, and the blending gain and ΔKGE.
- **H1 and H2** as in §1, with station-block bootstrap intervals.
- **Sensitivity:**
  - supported/independent thresholds of 10/50 km and 50/150 km;
  - log-transformed pentads (log(1+P));
  - the CHIRPS-masked stations excluded from CHIRP-only descriptives too.
- **Descriptive:**
  - per country, usable station-pentads and how many are independent;
  - which countries cannot be evaluated with open data at all;
  - the share of Pacific gauges that CHIRPS ingests, by decade.
- **The benchmark release:** station list, QC flags, labels, per-station skill tables.

## 5. Threats and care

1. **The label's resolution.** The stations-used lists are monthly. CHIRPS blends at pentad scale with its own
   station set, so a monthly list can miss pentad-only inputs. The co-located case (within 5 km) is reported
   separately.
2. **Island gauges.** Island gauges can be unrepresentative of a 0.05° cell (orography, coastal convection). That
   affects both twins equally, so it moves skill but not the within-pair gain.
3. **Error recording.** A failed read is recorded as an error, never as zero rain or as absence.
4. **Units of analysis.** These are products and gauges. No community or person is studied. Pacific climate services
   (SPREP, national meteorological services) would be the natural partners for use of the benchmark. Engagement is a
   care note, not a gate (lab policy).
