# New Zealand's outage limits are not ratcheting with storms, because there was no national trend to absorb; but the choice of major-event rule decides whether some distributors breach

*16 non-exempt electricity distributors. The data are the Commerce Commission's interruption-level records, published
with its 2020 (DPP3) and 2025 (DPP4) price-quality path models, for disclosure years 2009–2024, together with the
reliability limits and boundary values of the 2015, 2020 and 2025 determinations, transcribed by double entry. The
plan was committed before any interruption outcome was aggregated.*

**Verdict: H1 Inconclusive; H2 Inconclusive; H3 Supported.**

- **H1 (the IEEE 2.5-beta rule masks an outage trend): Inconclusive.**
  - There is no trend to mask. National unplanned SAIDI changed by **−0.7% a year** over 2014–2024 (95%
    distributor-cluster bootstrap −5.3 to +3.4).
  - Storm years dominate it: 2023, the year of Cyclone Gabrielle, recorded 426 minutes, against 100–277 in other
    years.
  - With major-event days excluded, the index is flat: +0.4% a year (−2.3 to +2.6).
- **H2 (a rolling threshold removes more of the trend than a frozen one): Inconclusive.** The difference is +0.10
  percentage points a year (−0.10 to +0.38).
- **H3 (the major-event rule decides compliance): Supported.**
  - For **3 of 15 distributors**, the Commission's rolling-24-hour rule and the IEEE daily 2.5-beta rule give
    different exceedance years in 2021–2024, each limit computed from the same 2010–2019 window.
    - Electricity Invercargill exceeds in 2022 only under IEEE.
    - Firstlight Network exceeds in 2022 only under IEEE.
    - Vector exceeds in 2023 only under IEEE.
  - Against the determinations' own DPP3 limits, 2 distributors differ.
  - The IEEE boundaries are 1.5 to 13 times the Commission's.
- **The lead's ratchet question is answered descriptively.**
  - **Published parameters.** The Commission's own uncapped DPP4 limits differ from DPP3's by a median of about +2%.
    The ±5% cap bound for 13 of 15 distributors, holding 7 down and 6 up.
  - **Recomputed targets.** Of the total +115-minute rise in targets across distributors from the DPP3 window to the
    DPP4 window, +104 comes from outcomes at a fixed boundary and only +11 from re-estimating the boundary.

## In plain terms

Each local power company in New Zealand is allowed a set number of outage minutes a year before it is in breach.
Days hit by big storms are partly excused. Every five years the regulator resets the allowance from the previous
ten years. The worry was that, as storms get worse, the allowance quietly creeps up with them, so the system loosens
exactly when it should bite.

We rebuilt the regulator's calculations from its own outage records and reproduced its numbers. Over 2014–2024
there was no steady rise in outage minutes to creep up with: the total jumps around with storm years, Cyclone
Gabrielle above all, and the storm-adjusted figure stays flat. Where allowances did rise, it was mostly because
those networks had more ordinary outages, not because the storm threshold moved. The regulator also stopped any
allowance moving more than 5% at the last reset, and that cap bound for almost every company.

What does matter is how a "storm day" is defined. The regulator uses a rolling 24-hour window with a fixed number
of storm events a year. The international standard (IEEE 1366) uses a statistical threshold on calendar days. When
we swapped one for the other, three of fifteen companies changed between "in breach" and "not in breach" in at
least one year. So the excusing rule is not a technicality: it decides outcomes.

## What was asked

The lead (`energy-nz-edb-quality-standard-ratchet`, Energy signature area) asked whether the five-yearly resets ratchet
reliability limits upward with the storms of the reference period. It is an external check of the lab's US finding
(`runs/energy-outage-major-event-day-ratchet`), using official data instead of outage-map proxies.

Two things changed the plan before it was committed (plan section 0):
- **The published parameters already answer the level question.** The DPP4 boundary values, the Commission's uncapped
  limits and the cap, read during the double-entry check, already show it.
- **The lead's DPP2 → DPP4 limit comparison is not like for like.** DPP2 limits cover 0.5 × planned + unplanned
  SAIDI with a daily boundary. DPP3 and DPP4 cover unplanned SAIDI with a rolling, fixed-count boundary.

The tests therefore use the interruption data. H1 and H2 replicate the US study's masking and ratchet tests, and H3
asks whether the choice of rule changes compliance.

## How it was done

- **Data.**
  - The Commission's DPP3 model data supplies disclosure years 2009–2013, and its DPP4 model data (the
    "transitional" series) 2014–2024. The two agree exactly in all 96 overlapping distributor-years.
  - Eastland is Firstlight. Centralines is dropped, because the DPP4 file's Unison excludes it.
  - The 2025 disclosure fails the plan's identification check, so the window ends in 2024 (D1).
- **The Commission's rule** is re-implemented from its R (DPP4) and Stata (DPP3) code:
  - interruptions are rounded to the half-hour, and rolling 24-hour totals are formed;
  - the boundary is the total ranked 1,104th over ten years (2.3 major events a year), with small-distributor
    adjustments;
  - half-hours inside a major event are capped at boundary ÷ 48;
  - target = mean annual normalised SAIDI, and limit = target + 2 SD.
- **The validation gate passed** after a date-parsing fix (D2):
  - all 16 DPP4 boundary values exactly;
  - DPP4 targets and uncapped limits within 0.6%;
  - all 17 DPP3 boundary values within 0.15%.
- **The IEEE 1366 rule** works on calendar-day SAIDI. The threshold is exp(α + 2.5β) of ln(daily SAIDI) on the
  non-zero days of the previous five years (rolling) or of 2009–2013 (frozen), and major-event days are excluded.
- **National index.** The ICP-weighted mean of distributor SAIDI. The trend is the slope of its log on year, with a
  distributor-cluster bootstrap (B = 2,000). A year bootstrap is a sensitivity.

## Results

### H1 and H2: no trend to mask (`results/figures/F1_national.png`)

![National unplanned SAIDI](results/figures/F1_national.png)

| series, 2014–2024 | trend, % a year | cluster bootstrap | year bootstrap |
|---|---|---|---|
| raw unplanned SAIDI | −0.73 | −5.26 to +3.37 | −8.79 to +10.81 |
| major-event days excluded, rolling threshold | +0.37 | −2.32 to +2.57 | −1.44 to +2.13 |
| major-event days excluded, frozen threshold | +0.46 | −2.14 to +2.78 | −1.32 to +2.46 |
| frozen minus rolling (H2) | +0.10 pp | −0.10 to +0.38 | −0.23 to +0.56 |

- **Major-event days are rare under IEEE in New Zealand.** The rolling rule flags 0.06–1.6 days per distributor per
  year, against the 2.3 events a year the Commission's rule fixes by construction. Daily outage minutes in New
  Zealand have heavy tails, which inflates β.
- **Sensitivities:**
  - **Without Aurora:** −0.85% a year raw, still Inconclusive.
  - **Without 2023:** the raw trend turns negative, −5.0% a year (−9.2 to −1.3), while the excluded index stays
    flat (−0.3%). The preregistered H1 rule then mechanically returns "Supported", because the ratio 0.06 is below
    0.5. But the rule assumed a rising trend, and a falling one is not masked growth. This sensitivity is not
    evidence for H1.
- **SAIFI:** −1.0% a year raw (−3.5 to +0.2), Inconclusive. H2 is also Inconclusive (+0.18 pp, −0.07 to +0.44).

### The reset itself: outcomes, not the moving boundary (`results/figures/F2_decomposition.png`)

![Decomposition](results/figures/F2_decomposition.png)

- **Size of the change.** Moving the reference window from 2010–2019 to 2015–2024 raises the median distributor's
  normalised target by 4.7% and its limit by 3.3%. These are recomputed, uncapped values; the Commission's published
  uncapped limits imply about +2%.
- **What drives it:**
  - Across distributors, targets rose by 115 minutes in total. Re-normalising 2015–2024 at the DPP3 boundary values
    accounts for +104, and the boundary's re-estimation for +11.
  - The largest rises are at Firstlight (+37), The Lines Company (+36), Aurora (+29), Top Energy (+28) and Vector
    (+16). Each is mostly outcomes.
  - Orion's fall (−23) reflects the 2011 Canterbury earthquakes leaving its window.
- **Share removed by normalisation.** The median share of raw unplanned SAIDI that normalisation removes fell from
  47% to 40%.
- **Gabrielle and Unison.** Unison's raw reference-window mean more than doubled (123 → 283 minutes, Cyclone
  Gabrielle), but its target rose by only 1.4 minutes. The fixed-count rule absorbed the cyclone, as intended.

### H3: the rule decides who exceeds (`results/figures/F3_compliance.png`)

![Compliance](results/figures/F3_compliance.png)

| distributor | Commission's rule: years over limit | IEEE rule: years over limit |
|---|---|---|
| Electricity Invercargill | none | 2022 |
| Firstlight Network | 2023, 2024 | 2022, 2023, 2024 |
| The Lines Company | 2023 | 2023 |
| Top Energy | 2023 | 2023 |
| Vector Lines | none | 2023 |

- **Counts.** 4 exceedances under the Commission's rule and 7 under IEEE, across 15 distributors.
- **Against the determinations' own DPP3 limits,** Vector also exceeds in 2023 under the Commission's rule, so 2
  distributors differ (Invercargill and Firstlight).
- **SAIFI:** 3 differ.
- **Consistency with the record.** The Commission's rule puts Top Energy over its limit in 2023, consistent with its
  contravention for that year.

## What this does and does not show

- **No evidence that the regime loosens with storms over 2014–2024.** There was no national trend in raw outage
  minutes to absorb.
  - Where reset targets rose, the rise came mainly from more outage minutes on ordinary days, not from the
    major-event threshold moving.
  - The ±5% cap then held most limits near their DPP3 values.
- **The US result does not transfer.** Not because the rule behaves differently, but because New Zealand's series,
  unlike the US one, shows no underlying trend over this window.
- **The rule is consequential.** IEEE's daily 2.5-beta threshold is far higher than the Commission's fixed-count
  threshold for New Zealand's heavy-tailed outage data. It excuses less, raising both limits and assessed values, and
  that changes compliance for a fifth of distributors.
- **Not shown:**
  - **Contraventions.** The regime's two-of-three-year contravention rules, and its exclusions for major external
    factors and catastrophic events, are not modelled.
  - **DPP3 limits.** The determination's limits are not fully reproduced: 9 of 17 differ by more than 1% from
    target + 2 SD (D2).
  - **Trends beyond 2024,** and causes: network condition and recording practice are not separated from weather.

## Process and deviations

- **Preregistration:** `plan.md`, committed after the double-entry transcription and before any outcome aggregate.
- **Deviations** (`deviations.md`):
  - D1: panel checks; 2025 is unusable, so the window ends in 2024; a planned descriptive item is impossible because
    DPP4's first assessment year is 2026.
  - D2: a day-first date-parsing bug, caught by the validation gate before any hypothesis statistic.
- **History.** This lead was first skipped on 21 October 2026, after a novelty check. The Commission's DPP4 reasons
  paper (Attachment E, Table E16) already tabulates the uncapped and capped DPP3 → DPP4 limit changes, which answers
  the lead's level question, and the remaining rule comparison looked too thin on one or two years of interruption
  data. It was revisited because the Commission's model bundles hold interruption-level data for 2009–2024. Plan
  section 0 reports the level answer descriptively, consistent with Table E16.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. `code/transcribe.py`.
2. `code/panel.py load`, then `check`, then `build`.
3. `code/rules.py validate`.
4. `code/analysis.py`.
5. `code/figures.py`.

The data are the Commission's DPP3 and DPP4 model bundles and the EDB information-disclosure files, all public.
