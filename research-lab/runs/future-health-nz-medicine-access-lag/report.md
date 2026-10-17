# How long does a new medicine take to reach New Zealanders, and which stage takes the time?

*An open, stage-by-stage timeline for 705 new active substances first approved by the FDA or EMA in 2010–2024: when
each was first approved abroad, when its sponsor applied to Medsafe, when Medsafe consented, and when PHARMAC first
funded it.*

**Verdict: Refuted, on the lead's two main claims.** The industry's "7.7 years" is not an artefact of leaving out
unfunded medicines, and the regulatory stage is not a small share of the wait.

- **The regulatory stage is about 40% of the wait, not under 25% (H1a, Refuted).** Among funded substances, the time
  from first approval abroad to Medsafe consent is 40% of the time to funding (95% interval 33–48%). Most of it is
  the sponsor's delay in applying to Medsafe (30%). Medsafe's own review is 14%, and funding takes the remaining 56%.
- **The median total wait for funded substances is 1,556 days**, about 4¼ years (H1b, Inconclusive: interval
  1,329–2,200 days, against a predicted at least 1,500).
- **"7.7 years" is not survivor-weighted (H3, Refuted), but the reverse.**
  - Counting only medicines that were funded, the wait from Medsafe consent to funding is short: median 2.1 years,
    mean 3.2.
  - Counting every consented medicine, with those not yet funded still waiting, gives a median of 12 years and a mean
    (to 10 years) of 7.0. The industry's 7.7 years fits this censoring-aware measure.
  - Only a third of consented medicines are funded within 5 years.
- **Australia (H2, not testable as stated).** Australia's open listing records start in 2019. For substances first
  approved in 2019–2024, neither country's median is reached yet. Three years after first approval, 3.7% were funded in
  NZ and 17.5% PBS-listed in Australia.
- **A frozen forecast** of which of 125 consented but unfunded medicines PHARMAC will fund by October 2027 was
  committed and pushed before any later data, to be scored then (H4).

This measures process timing. It does not judge whether any funding decision was right.

## In plain terms

New Zealanders often hear that new medicines take years longer to arrive here than elsewhere, with figures from
industry reports whose workings are not public. We built an open timeline from public records for 705 medicines first
approved in the US or Europe between 2010 and 2024. For each, we recorded four dates:
- first approved overseas;
- the company applied to New Zealand's regulator, Medsafe;
- Medsafe approved it;
- PHARMAC first funded it.

Most never complete the journey. Only about three in ten have been approved by Medsafe, and about one in eight funded.
For those that were funded, the whole journey took a median of about four and a quarter years:
- **Waiting for the company to apply in New Zealand:** about 30% of the time. That delay is the company's choice, not
  the regulator's.
- **Medsafe's own review:** about 14%.
- **Waiting for funding after approval:** the rest, about 56%.

The often-quoted "7.7 years to funding" is not exaggerated by leaving out medicines that were never funded, as some
have suggested. If anything, the opposite holds. Medicines that did get funded waited about two years after approval.
But once you count the many approved medicines still waiting, the typical wait is far longer, and 7.7 years is a
reasonable summary of it.

We could not make a fair comparison with Australia's funding, because its open records only go back to 2019. Its
regulator approved the same medicines a median of about 14 months earlier than Medsafe.

## What was asked

The lead (`future-health-nz-medicine-access-lag`) asked how long new medicines take to reach NZ and which agency is the
bottleneck. Four preregistered hypotheses:
- **H1a:** among substances first approved 2010–2023 and funded, the regulatory stage (first approval abroad to
  Medsafe consent) is under 25% of the total time to funding.
- **H1b:** the median total time is at least 1,500 days.
- **H2:** NZ's median exceeds Australia's PBS median by at least 400 days.
- **H3:** the "7.7 years to a funding decision" figure is reproduced only when unfunded medicines are excluded.

A fifth, prospective test, H4, forecasts which consented, unfunded medicines are funded in the next 12 months.

## What was already known

| Work | What it established | What it left open |
| --- | --- | --- |
| Medicines NZ / Shawview (2023) | 7.7 years to a PHARMAC decision; 1,050 days in NZ against 556 in Australia | industry-commissioned; denominators and data not released |
| 2026 industry-sponsored review (tabled in Parliament) | 7–10 years from Medsafe approval to funding | same |
| NZMJ waiting-list study (industry-funded) | some recommended medicines waited more than 8 years | no regulatory stage, no matched cohort |
| CSIRO-published analysis (J Prim Health Care) | much of the delay reflects PHARMAC's assessment; agency roles overlap | no open decomposition |

No open, stage-decomposed, reproducible dataset existed.

## How it was done

**Cohort.**
- **Definition.** Every substance whose first approval by the FDA (Drugs@FDA, any application type) or the EU (EMA
  centralised, non-generic, non-biosimilar) fell in 2010–2024.
- **FDA-first entries** had to come through a new-molecular-entity NDA or a BLA.
- **Excluded:** vaccines, diagnostics and allergens.
- **Names** were normalised (salts and hydrates removed). The same drug under FDA and EMA name variants was merged with
  the earliest date (D6).
- **Size.** **705 substances** (FDA first 510, EMA first 195).
- **Old substances.** 25 more were excluded because Medsafe consented them, or PHARMAC listed them, more than a year
  before their first FDA or EMA approval (old medicines first centrally authorised later). That leaves **680** for
  analysis.

**Sources, all public.**

| date | source |
| --- | --- |
| T1, T2 | Medsafe's Product and Application searches, queried substance by substance in a headless browser, since the search is an interactive web app |
| T3 | PHARMAC's monthly XML archives of the community Pharmaceutical Schedule (2006–2026) and the Hospital Medicines List (2013–2026), with Schedule Update PDFs filling the archive's gap (June 2024 to December 2025, January 2018) |
| T3_AU | the PBS Medicine Status Website |
| T_app, T_dec, T_TGA | from the [UoA-eResearch/pharmac](https://github.com/UoA-eResearch/pharmac) repository (commit 3e3e850): PHARMAC application-tracker data, a Medsafe register snapshot (used as an independent cross-check of T2) and the TGA register |

The data cutoff is the October 2026 Schedule.

**Validation, before any lag was computed (plan §4).**
- **First check.** 150 random substances were adjudicated against the saved evidence. Precision: T1 0.985, T2 0.966,
  T3 0.979, all above the preregistered 0.90.
- **What it exposed.** Duplicate substances, two FDA approvals under brand or proper names, and names Medsafe shortens
  ("Polatuzumab" for polatuzumab vedotin). These were fixed (D6).
- **Re-validation.** A fresh 100 then gave T1 1.000, T2 0.990, T3 1.000.
- **Cross-check.** Agreement with the independent Medsafe register snapshot is 678 of 678 comparable substances.
- **Recall.** In 50 random new PHARMAC listings, every new active substance of the period was in the cohort, with the
  right date.

**Analysis.**
- **H1a:** the aggregate share Σ(T2−T0) / Σ(T3−T0), with a 2,000-resample substance bootstrap.
- **Censoring-aware measures:** Kaplan–Meier and restricted mean survival to 10 years, censored at the cutoff.
- **Competing risks:** funding against consent lapsing first (Aalen–Johansen).

## Results

### H1: where the time goes

Of 627 substances first approved 2010–2023, 87 have been funded. 74 have the dates in order (first approval, then
consent, then funding) and form the H1 population. Of the other 13:
- 5 were funded before Medsafe consent;
- 5 were funded with no consent;
- 3 were consented in NZ before their first FDA or EMA approval.

**H1a, Refuted.** The regulatory stage (T0→T2) is **40%** of the total time to funding (aggregate 0.40, 95% interval
0.33–0.48; median per substance 0.40). The plan's threshold was below 25%.

**H1b, Inconclusive.** The median total time is **1,556 days** (interval 1,329–2,200) for the 74. It is 1,447 for all
87 funded. Supported needed the interval's lower end at or above 1,350.

**The stage split.** Among the 49 funded substances with all four dates (Figure 1):

| stage | median days | share of total |
| --- | --- | --- |
| sponsor's delay before applying in NZ (T0→T1) | 494 | 30% |
| Medsafe's review (T1→T2) | 269 | 14% |
| funding (T2→T3) | 931 | 56% |

The total median is 2,200 days. The 40% "regulatory stage" is therefore mainly the sponsor's decision about when to
apply in NZ, not Medsafe's review.

Splitting the funding stage at the PHARMAC application, for the 33 substances where the application fell between
consent and funding: 134 days from consent to application, and **1,065 days** from application to listing (88% of the
funding stage). A further 41 funded substances had a PHARMAC application before Medsafe consent, so the two processes
often run in parallel.

![Figure 1](results/figures/F1_stages.png)

*Figure 1. Median days per stage for funded new active substances with all four dates, by period of first approval.
Stacked medians do not sum to the median total. 2020–23 has only 2 substances so far.*

### H3: the denominator, and what "7.7 years" measures

| measure (years) | Medsafe consent → funding | PHARMAC application → approval to fund |
| --- | --- | --- |
| funded or approved only: mean | **3.2** (n = 79) | 3.4 (n = 75) |
| funded or approved only: median | **2.1** | 2.2 |
| all, censored: Kaplan–Meier median | **12.0** (n = 204) | 8.7 (n = 177) |
| all, censored: restricted mean to 10 years | **7.0** | 6.6 |

**H3, Refuted.** The plan's rule needed only the funded-only figure to fall within 7.7 ± 1 years. It does not (3.2 and
2.1), while a censoring-aware figure does (7.0). The industry's 7.7 years is consistent with counting medicines still
waiting, as it should be, not with leaving them out.

Of the consented medicines:
- 33% were funded within 5 years and 43% within 10;
- 24 of 204 had their consent lapse or be revoked before any funding (Aalen–Johansen cumulative incidence of funding:
  0.33 at 5 years, 0.44 at 10).

The other industry figures check out as follows:
- "1,050 days": the median consent-to-funding time for funded medicines is 780 days.
- "7–10 years": the funded-only mean (3.2) is outside that range, and the censoring-aware restricted mean (7.0) is
  just inside it.

![Figure 3](results/figures/F3_denominators.png)

*Figure 3. Medsafe consent to PHARMAC funding under different denominators, against the 7.7-year industry figure.*

### H2: Australia, and the two regulators

**H2, not testable as stated.**
- **Coverage.** The PBS Medicine Status Website records submissions from 2019, so H2 was restricted to substances first
  approved 2019–2024 (310).
- **Events so far.** 15 have been funded in NZ and 77 PBS-listed in Australia. Neither median is reached.
- **Three years after first approval:** **3.7%** funded in NZ against **17.5%** PBS-listed in Australia.

**A secondary regulator comparison (D3.3) covers the whole cohort.**
- **Same substance.** Among the 184 substances registered by both, Medsafe consented a median **427 days after**
  Australia's TGA.
- **By 2 years** after first approval: 15% Medsafe-consented, 39% TGA-registered.
- **By 5 years:** 29% against 53%.
- **Median time to TGA registration:** 1,469 days; NZ's median is not reached.
- **Caveat.** The TGA register lists current entries, so a cancelled first entry makes a TGA date late.

![Figure 2](results/figures/F2_milestones.png)

*Figure 2. Cumulative share of new active substances reaching each milestone, by years since first FDA/EMA
approval (Kaplan–Meier). The PBS curve covers only substances first approved 2019–2024.*

### H4: the frozen forecast

A logistic model was trained on 977 substance-years (2012–2024 snapshots; base rate 6.9% funded within 12 months). It
gives a probability for each of the 125 substances consented but unfunded at the cutoff. The forecast file
(`results/forecast_2026.csv`, sha256 70b7aec5…) was committed and pushed before any later Schedule was read. It is
scored after October 2027 by `code/score_forecast.py` against the base rate.

## What this does and does not show

- **It shows where the time goes for medicines that complete the journey.** The largest single block is the wait for
  funding. The next is the sponsor's delay before applying in NZ. Medsafe's own review is the smallest. "Regulatory
  delay" in public debate often lumps the sponsor's choice in with the regulator.
- **It shows that the denominator decides the headline.** Funded-only averages say about 2–3 years. Censoring-aware
  measures that count medicines still waiting say about 7 years on average, with half still unfunded after 12.
- **Not shown:**
  - whether any decision was right;
  - what the delays mean for patients;
  - how access differs between communities. That would need Māori and Pacific health leadership, as the lead's
    engagement note says.
- **Limitations:**
  - **Late T2.** Medsafe's register appears to record the latest consent. For medicines that went from provisional to
    full consent (12 of 209 consented show a provisional route), T2 may be late.
  - **Missing NZ consents.** The application search failed for 16 substances, which leaves their T1 missing.
  - **Late T0.** FDA biologics approved under a different brand and proper name are not detected (about 1 in 150).
  - **Cohort impurity.** About 2% of entries are old substance concepts under new EU names.
  - **Funding routes.** Hospital and community listings are both counted as funding. Named Patient Pharmaceutical
    Assessment is not.
  - **Policy change.** Parallel PHARMAC–Medsafe assessment (2024) and the 2026 "Rule of Two" change the process after
    the primary window.

## Process and deviations

Preregistered in `plan.md` (8d0bc67), with all code committed before the outputs it produces. Deviations are in
`deviations.md`:

- **D1:** the Australian benchmark restricted to 2019–2024; the regulatory stage split into sponsor and Medsafe;
  the 2010–2023 primary window.
- **D2:** PHARMAC's XML archive used for T3; the old-substance exclusion.
- **D3:** applications, the Medsafe register and the TGA register from the user-suggested UoA-eResearch/pharmac
  repository.
- **D4:** the XML archive gap filled from Schedule Update PDFs.
- **D5:** nine non-new entries excluded; Medsafe retries.
- **D6:** the first validation; duplicate merging, T0 overrides, alias matching.
- **D7:** the fresh-sample re-validation.

## Reproducing it

```
venv/bin/python code/cohort.py                 # cohort from Drugs@FDA + EMA
venv/bin/python code/medsafe.py                # Medsafe searches (Playwright, PLAYWRIGHT_BROWSERS_PATH)
venv/bin/python code/medsafe_parse.py
venv/bin/python code/fetch_xml.py; venv/bin/python code/pharmac.py      # PHARMAC XML archives
venv/bin/python code/fetch_pharmac.py; venv/bin/python code/su_text.py; venv/bin/python code/su_listings.py
venv/bin/python code/msw.py                    # PBS Medicine Status Website
venv/bin/python code/link.py; venv/bin/python code/crosscheck_medsafe.py
venv/bin/python code/validate.py sample|merge; venv/bin/python code/validate.py sample_v2|merge_v2
venv/bin/python code/analysis.py; venv/bin/python code/forecast.py; venv/bin/python code/supplementary.py
venv/bin/python code/figures.py
# after 2027-10-01: fetch_xml.py; pharmac.py; score_forecast.py
```

**Released** in `results/tables/`: the result JSONs, the stage table, both validation adjudications, and the frozen
forecast. The linked per-substance table (`data/linked.csv`) is released as `results/tables/linked.csv`.
