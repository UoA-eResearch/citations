# Does Public Domain Day unlock new editions? The open catalogue is too thin to say: a rule-passing +86% rests on a post-result fix and fails its robustness checks, while Project Gutenberg clearly responds

*US books registered in 1923–1930: renewed books, whose copyright expired on 1 January 2019–2025, against same-vintage
never-renewed books, in the public domain since the 1950s. Registrations come from the Catalog of Copyright Entries
(NYPL XML) and renewals from the NYPL renewal files. Open Library editions are linked through works (2026-09-30 dumps).
The plan was committed before any edition was linked or counted.*

**Verdict: Inconclusive.**
- **H1 by rule:** Supported, but only after a post-result fix (D1). As first run it was Refuted, and neither result is
  robust.
- **Project Gutenberg (secondary):** a clear expiry response.

- **H1 (expiry raises new Open Library editions by at least 50%).**
  - **The preregistered estimator** returned RR **0.33** (0.19–0.58), which the rule calls Refuted. That number is
    degenerate: seven cohort × event-time cells have no editions at all, almost all in 2024–2025 when Open Library
    has ingested almost nothing, and PPML pushes their coefficients towards −∞.
  - **After dropping those separated cells** (D1, the standard ppmlhdfe convention, decided after the first result
    was seen), RR is **1.86** (1.01–3.43). The pre-trend is clean (Wald p = 0.66), and the rule calls it Supported.
  - **Where the estimate comes from:** 184 renewed and 929 never-renewed works with at least one edition in
    2008–2025. That is 3.7% of the 30,329 linked works.
- **The result does not survive its checks** (preregistered secondaries):
  - **Excluding print-on-demand publishers,** which carry two-thirds of editions, the model breaks down: RR 794 and a
    pre-trend p below 0.001.
  - **Ingestion-lag filter:** RR 1.15 (0.57–2.29), with a failing pre-trend.
  - **Sun–Abraham OLS on log(1 + editions):** +0.004 (−0.001 to +0.008).
  - **By cohort,** RR runs from 0.39 to 53.
  - **The placebo** (expiry moved 3 years earlier) is null, at 1.17 (0.72–1.90).
- **Project Gutenberg responds.** 1.8% of renewed works were released on Gutenberg within two years of expiry,
  against 0.25% of never-renewed works over the same years, about 7 times as many. It is highest for the 2019 cohort
  (5.2%).
- **The linkage is the weak point.**
  - Precision is 0.81 and recall 0.38 (300 registrations labelled blind).
  - Recall is lower for renewed books (0.29) than for never-renewed ones (0.50). Popular books often have duplicate
    Open Library work records, so they are either dropped as ambiguous or have their editions split.

## In plain terms

Every 1 January, a new year of American books enters the public domain. For books from the 1920s, that only
happened if the publisher had bothered to renew the copyright. Most never did, so those books have been free for
decades. That gives a natural comparison: when a renewed book's copyright finally expires, do new editions appear,
compared with similar old books that were already free?

We linked about 30,000 registered books from 1923–1930 to Open Library, the largest open book catalogue, and
counted editions each year. The data turned out to be very thin. Only about 1,100 of the books had any new edition
at all in 2008–2025, and Open Library has barely recorded books published in the last two years. Our first,
planned calculation gave a nonsense answer, an apparent two-thirds drop in editions, because of those empty recent
years. After fixing that the standard way, we got an 86% rise. But the fix was made after we had seen the first
answer, and the rise disappears or explodes under the checks we planned in advance. We cannot tell whether
expiry raises new editions in this catalogue.

One thing is clear: Project Gutenberg, the volunteer e-book library, puts newly freed books online. Renewed books
were about seven times as likely to appear there within two years of expiry as comparable books that were already
free.

## What was asked

The lead (`legal-digital-humanities-public-domain-day-renewal-did`) asked what the annual US copyright expiries since
2019 unlock. The design uses renewal status to form the control group.
- **Prior work is cross-sectional:** Reimers on bestsellers before and after 1923, and Heald on Amazon editions by
  decade.
- **No event study** of the annual expiries with a renewal-based control was found.

## How it was done

- **Registrations and renewal.**
  - The data are 94,683 A-class book registrations for 1923–1930.
  - A registration is renewed if its number matches a renewal's original registration number, the dates are within
    a year, and the titles match (token-set similarity at least 60).
- **Linkage to Open Library works:**
  - blocking on author surname and first title token;
  - title similarity at least 90, with the author surname present;
  - the work's first publish year no later than registration year + 1;
  - ambiguous registrations dropped.

  30,705 registrations are linked, of which 30,329 have registration years in range.
- **Outcome.** Open Library editions per work per publish year, 2008–2025.
- **Model.** PPML with work and year fixed effects and saturated cohort × event-time dummies (Sun–Abraham):
  - event time is binned to [−8, +6], with −1 as the reference;
  - RR is the cohort-weighted average over events 0–2;
  - the pre-trend is the Wald test on events −5 to −2;
  - standard errors are clustered by work.
- **Validation.** 300 registrations (150 renewed, 150 not) were labelled by a separate agent. It saw lettered
  candidates and not the matcher's choice.

## Results

### H1 (`results/figures/F1_event_study.png`)

![Event study](results/figures/F1_event_study.png)

| run | RR (events 0–2) | 95% CI | pre-trend p | treated / control works |
|---|---|---|---|---|
| preregistered estimator, first run | 0.33 | 0.19–0.58 | 0.66 | 184 / 929 |
| **D1: separated cells dropped (primary as reported)** | **1.86** | **1.01–3.43** | 0.66 | 184 / 929 |
| excluding print-on-demand (D1) | 794 | 384–1,639 | <0.001 | 138 / 656 |
| ingestion lag ≥ 12 months (D1) | 1.15 | 0.57–2.29 | <0.001 | 151 / 870 |
| placebo, expiry 3 years earlier (D1) | 1.17 | 0.72–1.90 | 0.21 | 127 / 929 |

- **Event time** (D1): +0.45, +0.73 and +0.82 log points at events 0, 1 and 2. None is individually significant at
  5% except event 1.
- **The cells dropped by D1:**
  - 2019 at +6;
  - 2020 at −7 and +5;
  - 2021 at +2 and +4;
  - 2022 at +3;
  - 2023 at +2.
- **By cohort** (each cohort against all controls):
  - 2019: 0.91;
  - 2020: 2.72;
  - 2021: 0.39;
  - 2022: 3.39;
  - 2023: 0.92;
  - 2024: 53;
  - 2025: 0.42.

  Each rests on 21–32 treated works.
- **Functional form.** The Sun–Abraham OLS gives +0.004 (−0.001 to +0.008) on log(1 + editions). The two-way-fixed-
  effects OLS first coded as secondary 2 gives +0.006 (SE 0.002). Both are tiny on a scale where most work-years are
  zero.

### Project Gutenberg and HathiTrust (`results/figures/F2_gutenberg.png`)

![Gutenberg](results/figures/F2_gutenberg.png)

- **Gutenberg.** 336 linked works are on Gutenberg. Within 0–2 years of expiry, 1.83% of renewed works (n = 3,827)
  were released, against 0.25% of never-renewed works over the same calendar windows (n = 25,806). The share is
  highest for the 2019 cohort (5.2%) and falls for recent cohorts (0.8% for 2025).
- **HathiTrust** (2026-10-01 snapshot). 98.8% of matched volumes of renewed 1923–1929 books are full view (`pd`),
  against 99.4% for never-renewed books. HathiTrust opens volumes at expiry. A single snapshot cannot show timing.

## What this does and does not show

- **Inconclusive for Open Library editions.** The only rule-passing estimate needs a post-result fix, has a lower
  bound of 1.01, and fails the print-on-demand and ingestion checks.
  - **Thin data.** The catalogue's coverage of recent editions is too thin: 15 editions in 2025 across all linked
    works.
  - **Undercounting.** Linkage misses popular books more often (recall 0.29 for renewed books), which undercounts
    the outcome where it matters most.
- **Gutenberg responds strongly to expiry.** That is consistent with expiry unlocking free digital access, though
  not necessarily new print editions.
- **Not shown:**
  - commercial editions outside Open Library (Amazon or WorldCat);
  - readership;
  - effects for renewed books not linked at all.

## Process and deviations

- **Preregistration:** `plan.md`.
- **Deviations** (`deviations.md`):
  - **D1 (post-result):** PPML separation handling, and the linkage validation results.
  - **Data fix:** the Gutenberg catalogue had been truncated twice by the server, and was re-fetched to full size.
- **Independent review:** queued (Fable), per the lab's pacing rule.

## Reproducing it

1. `code/registrations.py`.
2. `code/pget.py`, for the dumps.
3. `code/link.py works`, then `authors`, `resolve` and `editions`.
4. `code/validate_links.py sample`, labelling, then `code/validate_links.py score`.
5. `code/did.py primary|nopod|lag|placebo|ols`.
6. `code/secondary.py`.
7. `code/figures.py`.
