# Plausibility (G3)

## The check that caught a bug

The first full run (see deviations.md D5) gave Wellington an out-of-sample O/E of 0.13: 3 exceedances against 23
expected.
- That is not credible for a region with several damaging storms since 2017.
- Tracing it showed steady annual totals but 6-hour maxima down by a third after 2015, when gauges moved to 0.2 mm
  buckets.
- The reader had been dropping tips that shared a minute. On Akatarawa River at Cemetery in 2022/23 it lost 16% of
  the year's rain.
- After the fix, Wellington's O/E is 0.98, and a raw refetch of 10 random gauge-years matches the stored series
  exactly (`results/tables/g4_raw_check.csv`).

## Three gauges traced, raw series to exceedance

| gauge | water year | records | year total | 6-h maximum (window end) | HIRDS 10% AEP 6-h depth (SE) | exceeds |
|---|---|---|---|---|---|---|
| Maharakeke Stream at Limeworks (Hawke's Bay) | 2022/23 | 31,779 | 1,233 mm | 61.0 mm (14 Feb 2023, 07:45) | 58.2 mm (5.9) | yes |
| Anatoki at Paradise (Tasman) | 2017/18 | 13,313 | 5,964 mm | 159.6 mm (1 Jul 2017, 12:40) | 135.0 mm (12.0) | yes |
| Akatarawa River at Cemetery (Wellington) | 2022/23 | 51,395 | 2,227 mm | 38.7 mm (7 Aug 2022, 01:25) | 82.0 mm (7.3) | no |

- **Hawke's Bay.** The maximum falls on 14 February 2023, during Cyclone Gabrielle. It exceeds the 10-year depth
  by 3 mm, within one HIRDS standard error.
- **Tasman.** The maximum falls on the first day of the water year, so the boundary handling was checked. A raw
  refetch spanning 30 June to 1 July gives the same 642 records and 320.0 mm as the stored series, and hourly totals
  of 20–30 mm for eight hours on 1 July. The storm is real; its timing is a coincidence.
- **Wellington.** A wet mountain site in a year without an extreme short burst: the 6-hour maximum is under half
  the 10-year depth.

## Where the exceedances fall

The exceedances cluster in known storms:
- February 2023: 54, of which 48 are in Hawke's Bay (Cyclone Gabrielle);
- March 2022: 28, in Hawke's Bay and Northland;
- February 2018: 19, led by Tasman.

The largest single storm cluster holds 52 of the 261 exceedances. That clustering is why the year-block and
storm-cluster intervals are wide.

## The in-sample control

- Over water years up to 2014/15 (113 gauges with at least 10 complete in-sample years), O/E is 0.89
  (0.69–1.12). The interval includes 1.0, so the harvest and HIRDS agree where HIRDS was fitted, and the
  out-of-sample comparison is interpretable.
- The point estimate below 1 is consistent with the known downward biases of the method:
  - hidden outages in gauges that log only around rain;
  - the 5-minute grid, which is within 0.4% of the exact maximum (G4);
  - undetermined gauge-years counted as non-exceedances.
- This makes the out-of-sample excess, if anything, conservative.

## Magnitude against the literature

- **The size of the excess.** An excess of about 50% over stated frequency is large for nine years, but it is not
  out of line with a warming signal. HIRDS v4's own augmentation factor for the 6-hour, 10-year depth is 10.8% per
  degree of warming (HIRDS v4 report, Table 6), and a modestly deeper storm is exceeded much more often than a
  fixed depth implies.
- **The mid-century comparison.** Against HIRDS's RCP4.5 and RCP8.5 2031–2050 depths, the observed frequency is at
  the stated rate: O/E 1.02 and 0.99.
- **The caution.** Without January–February 2023, O/E falls to 1.19. The excess is concentrated in a few storm
  seasons, as the plan's year-by-year secondary anticipated.
