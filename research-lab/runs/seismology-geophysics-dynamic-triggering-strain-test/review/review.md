# Review: seismology-geophysics-dynamic-triggering-strain-test

Reviewer: independent adversarial review (Fable 5.1), 2026-11-05. Scripts and outputs in `review/reviewer_checks/`
(`checks1.py/.txt`, `checks2.py/.txt`). Checks used `venv/bin/python -I` with the study's `analyse.summarise`
imported, on the stored `pairs_*.parquet`, `null_primary.parquet` and the ComCat files; no proxy or window run was
repeated.

## Verdict: fix first (the H2 verdict does not survive a like-for-like null; H1 stays Inconclusive)

The pipeline is carefully built and I found no arithmetic or bookkeeping error: every number in the report matches
`primary.json`, `coverage.json`, `proxy_counts.csv`, `trigger_dispersion.json` and `strain_check.json` (351
triggers ≥ 1,000 km, 350 with pairs; 9,336 stations with proxy data, 1,496 with ≥ 100 valid pseudo-triggers;
95.6 M pairs, 49.9 M local; 15,042 vs 15,742.2); the window arithmetic, β rule, two-way bootstrap and
per-trigger dispersion are implemented as stated; the timeline holds (plan 10:58, code 11:04, first windows 16:05,
D1 16:10). The problem is the null's design. Pseudo-triggers are rejected within 10 days of any global M ≥ 7 and
3 days of any M ≥ 6.5 (`windows.py:170-175`), but real triggers are not: 282 of the 350 population triggers fail
that rule, and 115 of them have another M ≥ 6.5 inside their own post window. Those windows carry the other
earthquake's surface-wave detection shadow (the study's own "instant" result: −1.4 pp) and aftershock masking,
which the pseudo windows never do. Restricted to the 105 triggers whose baseline and post windows contain no other
M ≥ 6.5, the mean excess is +0.005 (−0.002 to +0.012) and H2 is Inconclusive, not Refuted; the contaminated
post windows alone give −0.013 (−0.018 to −0.007). The headline "no more common than at matched random times" is
therefore not established by a matched comparison.

## Findings

### 1. (Major, G1) The null excludes times near other large earthquakes; the real triggers do not, and that drives the negative excess

Evidence: `checks1.txt` §C, `checks2.txt` §B. By the pseudo-trigger rule, only 70 of 357 catalogue triggers (68 of
the 350 in the population) are "clean". Classifying real pairs by what sits inside their own windows:

| real pairs | triggers | pairs | E1 | E5 | all | H1 / H2 |
|---|---|---|---|---|---|---|
| preregistered (all) | 350 | 228,963 | +0.002 | −0.007 | −0.003 (−0.007, +0.001) | Inconclusive / Refuted |
| no other M ≥ 6.5 in baseline or post window | 105 | 70,010 | +0.004 | +0.006 (−0.009, +0.024) | **+0.005 (−0.002, +0.012)** | Inconclusive / **Inconclusive** |
| another M ≥ 6.5 inside the post window | 115 | 74,008 | −0.011 | −0.014 | **−0.013 (−0.018, −0.007)** | Inconclusive / Refuted |
| M ≥ 6.5 in the baseline only | 130 | 84,945 | +0.010 | −0.007 | −0.001 (−0.007, +0.004) | Inconclusive / Refuted |
| pseudo rule applied to real triggers (10 d / 3 d) | 68 | 43,771 | +0.002 | −0.003 | 0.000 (−0.008, +0.009) | Inconclusive / Inconclusive |

The contamination is strain-correlated: the share of pairs with an M ≥ 6.5 in the post window rises from 21% in
quintile 1 to 36–40% in quintiles 4–5, because big triggers have big early aftershocks. D1's exposure correction
removes only the ±60 s P-arrival masks of M ≥ 4.5 events; it does not touch the hours-long surface-wave shadow
of an M ≥ 6.5 aftershock, which is why E5 stays negative after it (−0.002) and turns positive (+0.006) only when
the contaminated windows are set aside. The plan's section 7 audit lists "bigger triggers have more aftershocks"
and handles it with P masking; it missed that the pseudo-trigger exclusion rule makes the null cleaner than the
data in exactly this respect.

Fix: make the two arms comparable, either by applying the pseudo exclusion rule (or the within-window rule) to
real triggers, or by dropping the rule for pseudo-triggers so that both arms sample the same mixture; recompute
H1 and H2; state the result as primary with the preregistered one beside it. On the comparable set H2 is
Inconclusive with a point estimate at the 0.5 pp bar, so the title and verdict must change.

### 2. (Moderate) The station population is 16% of stations, chosen by availability, and most stations' nulls rest on a few hundred pseudo-triggers

Evidence: `checks2.txt` §A, `coverage.json`. The median station has 3 valid pseudo-triggers of 500 drawn (4,176 of
9,336 have none), because every station-day in a 9-day window must be "loaded"; 84% of real pairs are dropped
for the same reason. The 1,496 population stations have a median of 212 valid pseudo-triggers (10th–90th
percentile 114–385), so a station's p0 carries a standard error of about 0.017 against p0 ≈ 0.07. That is fine
for means over 1,496 stations but means per-station excesses (F2) are noise-dominated and should not be mapped
as if informative. The availability rule is symmetric, as the report says, but the population it leaves is
permanent-network stations with long continuous records; the plain-terms section says this, the title does not.

Fix: say in the title or verdict that the test covers about 1,500 long-running stations; drop or heavily caveat
the station map.

### 3. (Moderate) Recall and detectability bound what "no detectable triggering" can mean

Evidence: `proxy_validation.json`; `primary.json` instant. The proxy catches 46% of ComCat M ≥ 1 events at the
nearest analysable station (52% at M ≥ 3), only 21% of pairs have any local pair in either window, and β ≥ 2
needs roughly a doubling of a station's weekly rate inside 24 h. The design can detect a triggered swarm that
doubles a station's rate for a day; it cannot detect a few extra M ≤ 1 events. The report's closing sentence
says this; the title ("No detectable remote dynamic triggering") reads as a general statement. The instant
window shows the proxy loses 1.4 pp of significant rises during the wave train, so instantaneous triggering,
where most published cases sit, is untestable here (the report says so).

Fix: title → "no detectable excess of day-scale local-event rises after distant M7+ earthquakes at 1,500
western-US stations" or similar.

### 4. (Minor) Things checked and right

- Cleaning: 2,088,914,320 picks read, 18.9 M exact duplicates (3.4%) dropped, 531,327,099 kept; channel merge
  removed 18,069; masking removed 16.2 M (3.0%); 7 partition-edge picks are immaterial.
- Proxy: pairing (first S 0.8–8 s, no P between, three picks ahead), t0, 3-station coincidence in ±2.5 s with
  2,500 ms buckets, neighbours "with picks this month" all as described (`proxy.py:134-163`).
- Windows: hour rounding, 2.5 km/s wave-train end + 2 h, 7-day baseline, β with f = T_post/(T_post + T_base), β = 0
  at N = 0 (21% of pairs), validity rules; `masked()` unions intervals correctly.
- Null: deterministic seeds (crc32), hour matched, ±45 d and ±12 × 365 d, inherited Δ-windows.
- Analysis: product-weight two-way bootstrap; H1/H2 rules as preregistered; quintiles by rank; dispersion ratio
  10.0, 39 above / 55 below 3 SE, reproduced from the pairs table.
- Strain: Prague formula with M capped at 8.3; Spearman 0.47 on 2,546 measured pairs (4,088 of 6,634 requests
  returned no LHZ data). Top quintile is 83 triggers; the five largest contribute 10% of its pairs, so it is not
  dominated by one event.
- G3 traces match but are weak (counts of 0/10, 0/1, 0/1); a trace of a significant pair would be more telling.

## Gate checks

- **G1:** the audit in plan.md §7 is real but incomplete: the pseudo-trigger exclusion rule is a field present
  in the null and absent in the data (finding 1), and it correlates with strain.
- **G2:** `coverage.json` has picks_fetch, picks_proxy and all pairs_* stages; no fallbacks; all drops reasoned.
- **G3:** `plausibility.md` traces three pairs; invariants hold; the traces omit masking and are trivial counts.
- **G4, G7:** not applicable, confirmed.
- **G5:** `review/overclaim_check.md` consistent with the tables; rows 1, 6, 8–10, 34–35 and 39 should be
  relabelled after finding 1 (Overstated: they rest on H2 Refuted and on "matched random times").
- **G6:** `python3 -I ../../tools/attribution.py check . --show` → "G6 passed (8 claims)". S4 (van der Elst &
  Brodsky 2010), S6 (Kennett & Engdahl 1991), S7 (Lay & Wallace) and S8 (ComCat) resolve to the right works with
  sensible roles; S1–S3 summarise abstracts I could not read offline; S5's bucket citation is as the plan states.
