# How long does a new medicine take to reach New Zealanders, and which stage takes the time? Preregistration

Lead: `future-health-nz-medicine-access-lag`. Written 2026-10-17. Examined beforehand, deliberately, because none
involves an outcome:
- the structure of the source pages and files (one Medsafe search for pembrolizumab; three Schedule Update PDFs; one
  PBS Medicine Status record);
- the cohort, which is built only from FDA and EMA approval dates.

No Medsafe, PHARMAC or PBS date has been linked to the cohort.

## 1. Question and hypotheses

NZ's medicines-access debate rests on industry-commissioned figures with unpublished denominators:
- 7.7 years from Medsafe approval to a PHARMAC funding decision, and 1,050 days in NZ against 556 in Australia
  (Medicines NZ / Shawview 2023);
- 7–10 years from Medsafe approval to funding (a 2026 industry-sponsored review).

This study builds an open, stage-decomposed timeline per new active substance.

**Stages.** For each substance:
- T0, first approval by FDA or EMA;
- T1, Medsafe application (the first new-medicine application for a product containing it);
- T2, Medsafe consent (the first product approval);
- T3, first PHARMAC funded listing.

That gives three stages: sponsor (T0→T1), Medsafe review (T1→T2) and funding (T2→T3).

**H1 (from the lead).** For substances first approved 2010–2023 and funded in NZ:
- **H1a.** The regulatory stage (T0→T2, which includes the sponsor's filing delay) accounts for less than 25% of the
  total time T0→T3.
- **H1b.** The median total lag T0→T3 is at least 1,500 days.

The 2010–2023 window is used because PHARMAC–Medsafe parallel assessment (from February 2024) and the 2026 "Rule of
Two" fast track change the regulatory stage; 2024 approvals are reported separately.

**H2 (from the lead, restricted; see section 6).** The NZ median T0→T3 exceeds Australia's median T0→first PBS listing
by at least 400 days, on a matched cohort.

**H3 (from the lead).** The "7.7 years" figure is survivor-weighted: a figure within ±1 year of it is reproduced from
Medsafe consent to funding (T2→T3) only when unfunded substances are excluded.

**H4 (prospective).** A model frozen now predicts which currently Medsafe-approved but unfunded substances are funded
in the next 12 months better than the base rate. It is scored in October–November 2027.

## 2. Sources (frozen with checksums)

| item | source | access |
| --- | --- | --- |
| US first approvals | Drugs@FDA bulk files (dafdata20261014), all application types | open zip |
| EU first approvals | EMA medicines output table (16 Oct 2026), human, non-generic, non-biosimilar | open xlsx |
| Medsafe applications and consents | Medsafe Product/Application Search (a Blazor app, queried by ingredient in a headless browser, one query at a time) | open |
| PHARMAC listings | all 248 monthly Schedule Update PDFs on cpsupdates.php (2002–Oct 2026) | open |
| Australian listings | PBS Medicine Status Website records ("Medicine listed on the PBS" date), document pages | open |

## 3. Cohort (`code/cohort.py`, `code/names.py`)

**Substances.** Each substance is a normalised ingredient name: lowercase, salts, hydrates and parenthetical text
removed, FDA four-letter biologic suffixes removed. Combination products contribute each component. Substances use
the INN, or EMA's active-substance field where the INN is absent.

**First approvals.**
- **FDA:** the first original approval of any application containing the substance.
- **EMA:** the first marketing authorisation of any centralised, non-generic, non-biosimilar human product containing
  it, including products since withdrawn.
- **T0:** the earlier of the two.

**Inclusion.**
- T0 between 2010-01-01 and 2024-12-31.
- If the FDA approval came first, it must have entered through an NDA Type 1 or 1/4 (new molecular entity) or a BLA,
  on its first-approval date. This drops old substances first marketed in the US in a kit or new formulation.
- Excluded: vaccines, diagnostics, contrast and imaging agents, allergens (EMA ATC J07, V01, V04, V08, V09 and a name
  list).

That gives **731 substances** (FDA first 519, EMA first 212).

**Covariates:** EMA orphan flag, ATC, FDA review priority.

## 4. Linking (`code/medsafe.py`, `code/pharmac.py`, `code/msw.py`, `code/link.py`)

- **Medsafe.** Each substance's normalised name is searched as an ingredient, in both the Product and the Application
  search.
  - T2 is the earliest approval date among returned products whose active ingredients contain the substance (any
    status: consent given, lapsed, revoked).
  - T1 is the earliest application date among "New … Medicine Application" rows for such products. The application
    search starts in January 2006.
  - Provisional consent counts as consent.
- **PHARMAC.** Every Schedule Update is parsed for its "New listings" entries (community Section B and hospital
  Section H, where present), each with the chemical name before the brand in brackets and the effective date.
  - T3 is the effective date of the first new listing whose chemical name contains the substance (alone or in
    combination).
  - T3B (community) and T3H (hospital) are kept separately.
  - Listings before 2010 cannot be later than T0 for this cohort and are ignored.
- **Australia.** Every Medicine Status record is crawled. T3_AU is the earliest "Medicine listed on the PBS" date among
  records whose drug name contains the substance.
- **Data cutoff.** 1 November 2026: the latest Schedule Update (16 October 2026) lists from 1 November. Unfunded
  substances are censored there.

**Validation (before any lag is computed).** A random 150 cohort substances (seed 20261020) are checked by the agent
against the saved source records:
- the Medsafe product list for T1/T2;
- the Schedule Update text for T3, or confirmation that no listing exists, from the current Schedule.

**Thresholds.**
- If the precision of T2 or T3 (correct within 31 days, or correctly absent) is **< 0.90**, the linking is revised
  once and re-validated on a fresh 100.
- If it is still < 0.90, results are reported as unreliable.
- Recall is checked from the other side: 50 random new listings of chemicals that look new are traced to the cohort.

## 5. Analysis (`code/analysis.py`)

All intervals are 2,000 bootstrap resamples of substances (seed 20261020).

**H1a.** Among substances with T0 in 2010–2023 and an observed T3, the **aggregate regulatory share**
Σ(T2−T0) / Σ(T3−T0), over substances with T0 ≤ T2 ≤ T3.
- Supported if the interval's upper end is < 0.25.
- Refuted if its lower end is > 0.25.
- Inconclusive otherwise.
- Substances funded before Medsafe consent (Section 29 supply) or never consented are counted and reported, and
  excluded from the share.
- The median per-substance share is reported alongside.

**H1b.** The median T0→T3 among the same funded substances.
- Supported if it is ≥ 1,500 days and the interval's lower end is ≥ 1,500 × 0.9.
- Refuted if the interval's upper end is < 1,500.
- Inconclusive otherwise.

**H3: three denominators, side by side.** For Medsafe consent to funding (T2→T3) and for T0→T3:
- funded only: mean and median;
- all Medsafe-consented substances, unfunded censored at the cutoff: Kaplan–Meier median and restricted mean to 10
  years, with the share funded by 5 and 10 years;
- all cohort substances from T0 (T0→T3, KM).

Verdict:
- Supported if only the funded-only mean or median of T2→T3 lies within 7.7 ± 1 years.
- Refuted if no denominator gives 7.7 ± 1 years, or if a censoring-aware figure also does.

The 2026 "7–10 years" claim and the 1,050-day figure are checked the same way.

**Competing risks.** Funded vs Medsafe consent lapsed or revoked before funding, with Aalen–Johansen cumulative
incidence of funding.

**Stage split.** Medians, and the aggregate share of T0→T1, T1→T2 and T2→T3 among funded substances, by T0 period
(2010–14, 2015–19, 2020–23) and for 2024 separately.

## 6. Australian benchmark (H2)

Historical PBS listing dates are no longer openly downloadable: the legacy extracts are discontinued and the public
API holds 12 months. The Medicine Status Website covers submissions from about 2019. H2 is therefore tested on
substances with **T0 in 2019–2024**, the window in which a first PBS listing would fall within the Website's coverage.
- NZ T0→T3 and AU T0→T3_AU are both Kaplan–Meier estimates, censored at the cutoff.
- If both medians are reached, the difference has a bootstrap interval:
  - Supported if the difference is ≥ 400 days and the lower end is > 0;
  - Refuted if the upper end is < 400.
- If either median is not reached, H2 is reported as not testable as stated, and the share listed by 3 years is
  compared instead.

The lead's original 2010–2024 benchmark is not attempted, and the report says so.

## 7. Frozen forecast (H4, `code/forecast.py`)

**Training.** Annual snapshots on 1 November 2012–2024 of substances Medsafe-consented but unfunded at that date. The
outcome is funded in the next 12 months. The model is logistic regression with:
- EMA orphan status;
- ATC first level;
- years since T0;
- years since T2;
- FDA priority review;
- an Australian listing by the snapshot date (from the Website only, so it is set to missing before 2019);
- the snapshot year.

**Forecast.** Every substance consented but unfunded on 1 November 2026, with probabilities. Written to
`results/forecast_2026.csv` and committed with its sha256 before any later Schedule Update is read.

**Scoring.** Against Schedule Updates through November 2027:
- Brier skill score against the training base rate;
- Supported if the skill is > 0 with the bootstrap lower end > 0;
- Refuted if the upper end is < 0.

## 8. Threats to validity

1. **Name matching** across four naming systems (validated in section 4). Combination-only listings are counted as
   funding of the new component.
2. **Medsafe coverage.** The application search starts in 2006, and product approval dates are by product, so a
   substance first approved in a product that was later cancelled is still found only if the search returns
   cancelled products. Lapsed and revoked products are returned.
3. **Funding routes.** Hospital-only funding (Section H), Named Patient Pharmaceutical Assessment and the Cancer
   Treatments list are different routes. T3 counts B and H listings; NPPA is not funding of a substance for a
   population.
4. **Policy changes** in 2024 and 2026 break stationarity; hence the 2010–2023 primary window.
5. **The process, not the decision.** This measures timing. It does not say whether any funding decision was right,
   and it does not interpret delays in terms of any population's health. Doing so would require Māori and Pacific
   health leadership, as the lead's engagement note says.
