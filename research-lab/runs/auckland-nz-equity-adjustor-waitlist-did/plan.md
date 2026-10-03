# Preregistration: did ending Auckland's ethnicity-inclusive waitlist prioritisation change who waits longest?

Lead: `auckland-nz-equity-adjustor-waitlist-did` (research-lab/leads.json). Written 2026-10-03 and committed to git
before any outcome value in this run's data has been tabulated.

## What has been seen before writing (disclosure)

- **The lead scout** looked at raw, unadjusted quarterly gap series for six districts during feasibility checks:
  long-wait share, Māori+Pacific minus European/Other. These probably included Auckland. The lead's 4-percentage-point
  threshold was therefore not set blind.
- **The lead critic** downloaded the Q4 2025/26 extract and checked its structure only.
- **In this run:**
  - The five extract vintages were downloaded: Q1–Q4 2025/26 and the 2024/25 file.
  - The structure of the Q4 2025/26 file was examined: sheets, columns, district, specialty and ethnicity lists, and
    the month range (Jan 2015 – Jun 2026, extracted 2 Sep 2026).
  - No waiting counts were tabulated.
- **No Māori or Pacific health-equity input on framing was sought before this plan.** The lead critic recommended it;
  the lab owner directed on 2026-10-03 that the study go ahead without it. See section 7.

## 1. Question

From February 2023, Te Toka Tumai Auckland prioritised elective-surgery waitlists with a five-factor Equity Adjustor
Score: clinical need, time waiting, rurality, deprivation and ethnicity (Māori and Pacific). The rollout was halted
for review in June 2023 and the tool was discontinued in August 2024. Auckland is reported to have weighted ethnicity
in some form before 2023. The estimand is therefore the effect of ending ethnicity-inclusive prioritisation.

After discontinuation, did the gap in long waits between Māori+Pacific and European/Other patients widen in Auckland,
relative to the same gap in districts that never used such a tool?

## 2. Data and sample

**Data.** Health NZ waitlist detailed data extracts, Elective Waitlist sheet. Cells are month × district × specialty ×
ethnicity (Māori, Pacific, Asian, European/Other), with "waiting under 120 days" and "total waiting". Counts of 1–4
are suppressed as "<5". The primary analysis uses the Q4 2025/26 vintage; the others are used for revision checks.

**District.** "District" is the Health NZ district reported in the extract. Whether this is the district of service or
of domicile is not documented in the file; it is assumed to be the district of service.

**Groups.**

- MP: Māori + Pacific, counts summed.
- EO: European/Other, the reference.
- AS: Asian, used as a negative control against EO.

**Districts.**

- Treated: Auckland.
- Controls: the 15 districts that never used an ethnicity-weighted tool. This is all 20 districts minus Auckland,
  Waitematā and Counties Manukau (tool coverage uncertain), Northland (a later adopter that stopped earlier) and
  Southern (its own tool).

**Periods.**

| Period | Months |
|---|---|
| Pre | Jul 2021 – Jan 2023 |
| Tool era | Feb 2023 – Jul 2024; modelled separately, not part of the contrast |
| Discontinuation month | Aug 2024; excluded |
| Post | Sep 2024 – Jun 2026 |
| Hold-out | Jul – Dec 2026; confirmatory persistence test from the next two vintages, not yet published |

**Outcome.** The long-wait share of a cell, L = 1 − (under 120 days / total waiting), in percentage points.

**Weighting and suppression.** Cells are weighted by total waiting. A "<5" count is set to 2.5 in the primary
analysis. Cells with total waiting of 0 are dropped.

## 3. Primary model

A weighted triple-difference regression on district × specialty × group × month cells, for MP and EO only:

L ~ β·(Auckland × MP × post) + τ·(Auckland × MP × tool era) | district×specialty×group + specialty×month + district×month + group×month

- β is the change in Auckland's MP−EO long-wait gap, from pre to post, relative to the change in the control
  districts.
- **Negative control.** The same model with AS in place of MP.
- **Permutation.** β is re-estimated with each of the 16 districts in turn as the "treated" district. Auckland's rank
  among the 16 estimates gives p = rank / 16. The 15 control-district estimates form the placebo distribution, with
  5th and 95th percentiles q05 and q95.

## 4. Decision rules (co-primary, per the lead critic)

| Verdict | Condition |
|---|---|
| Supported | β ≥ +4 pp, Auckland's β ranks first of 16, and the Asian negative control's \|β\| < 2 pp |
| Contradicted | β − q05 < +4 pp: even subtracting the most negative placebo noise leaves it below the 4 pp prediction |
| Inconclusive | otherwise |

**Hold-out (pending; about Dec 2026 – Mar 2027).** The same model with post = Jul–Dec 2026, from the Q1 and Q2
2026/27 vintages. Persistence is confirmed if β ≥ +4 pp and Auckland ranks first of 16. The result is reported as a
separate verdict.

## 5. Secondary analyses (no verdicts)

- **Event study.** Monthly Auckland × MP coefficients from Jul 2021 to Jun 2026, relative to the pre-period mean, with
  breaks marked at Feb 2023, Jun 2023 and Aug 2024.
- **Tool-era effect τ,** and the split of the tool era at June 2023.
- **Alternative treated set:** Auckland + Waitematā + Counties Manukau as treated.
- **Suppressed counts.** "<5" set to 1 and to 4 (bounds).
- **Unweighted estimates.**
- **Specialty heterogeneity.** General surgery, orthopaedics, ENT, gynaecology, and all others.
- **Māori and Pacific separately.**
- **Vintage revisions.** How much pre-period values (Jul 2021 – Jan 2023) differ across the five vintages.

## 6. Threats (fixed now)

- **Unclear tool use.** Which specialties used the tool, and when, is not documented in open sources.
- **Ethnicity weighting before 2023.** Auckland weighted ethnicity in some form before 2023, so "pre" is not "no
  weighting".
- **The outcome is a stock.** The long-wait share moves with referral and addition rates and with waitlist
  validation and removals, not only with scheduling order.
- **Concurrent Auckland-specific shocks.** These include private outsourcing (2024–26), theatre capacity and
  industrial action. District × month fixed effects absorb only shocks shared across groups.
- **One treated district.** Inference rests on the permutation rank. With 16 districts, p cannot go below 1/16.
- **Revisions and suppression.** The data are live and revisable, and small cells are suppressed.

## 7. Framing and engagement

The study uses only published aggregate data. It frames any effect as a property of how the health system prioritised
patients, not of communities, and avoids deficit framing.

The lead critic advised getting Māori and Pacific health-equity input on framing before this preregistration. The lab
owner chose to proceed without it, so the design above is the analyst's alone. The report recommends review by Māori
and Pacific health researchers and the Tāmaki Makaurau Iwi-Māori Partnership Board before any wider release.

The topic is politically polarised, so the report states results neutrally, including a null or a widening, with the
same prominence.

## 8. Review and reporting

- An independent reviewer agent checks code and results before any verdict.
- The report opens with "In plain terms".
- Derived tables are committed.
