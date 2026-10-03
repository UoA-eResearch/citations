# Deviations and implementation details

The plan (plan.md) was committed in 5d7ef7d at 2026-10-03 22:53 NZDT, before any waiting count was tabulated.
Entries are timestamped with `date`.

## D1. Implementation details not fixed in the plan (2026-10-03 22:58 NZDT)

- **Event-study baseline.** One reference month (Jan 2023) is used in estimation. The coefficients are then shifted
  so that the pre-period mean (Jul 2021 – Jan 2023) is zero, as plan section 5 specifies.
- **Older vintages.** Columns are mapped by name, because older vintages add "Quarter End when Data Extracted" and,
  in Q1 2025/26, "Rurality". Rurality rows are summed into district × specialty × ethnicity cells.
- **Vintage check.** Each vintage's β uses a post-period truncated at that vintage's last month.
- **Placebo comparison sets.** Each control district's placebo uses the other 14 controls as its comparison set.
  Auckland is never used as a comparison district in the placebos.

## D2. District-name bug in older vintages (2026-10-03 23:23 NZDT, found in review)

Two older vintages (the 2024/25 file and Q1 2025/26) spell "Hawkes Bay" without the apostrophe. Their vintage-check
rows had silently used 14 controls. read_elective now normalises the name and asserts that all 16 districts are
present. Corrected vintage betas: 8.01 (2024/25) and 8.24 (Q1 2025/26), up from 8.21 and 8.47. The primary estimate
is unaffected.

## D3. Data facts not anticipated by the plan (2026-10-03 23:23 NZDT)

- **The Q1 2025/26 file is stacked.** It is the 2024/25 extract plus rurality-split rows for Jul-Sep 2025. Its
  pre-period check is therefore by construction the same as the 2024/25 file's.
- **The zero-total filter is a no-op.** No vintage has a zero total; empty cells are absent rows.
- **"<5" cells force extreme shares.** 22.9% of raw rows have both counts "<5", which gives L = 0 at the 2.5/2.5
  imputation. Cells with a total of 5 or less carry 0.23% of the weight but dominate the unweighted estimate (D4).
- **District of service.** Auckland holds regional lists, for example dental surgery and ophthalmology, that the
  neighbouring districts do not report.

## D4. Post-hoc analyses requested by the independent review (2026-10-03 23:23 NZDT; code/review_checks.py)

The review verdict was "fix first". The preregistered verdict, Inconclusive, is unchanged. All results below are
post hoc and are labelled as such in the report.

**Specialty decomposition (Frisch-Waugh-Lovell).** Dental Surgery contributes 3.54 of the 7.22 pp. Auckland's
regional dental list grew about five-fold for every ethnicity, with long waits rising for all groups. Because
Māori+Pacific patients are over-represented on that list, an Auckland-wide shock to it loads onto beta. A
prioritisation score reorders patients within a specialty's list, so this channel is not an effect of the tool.

**Other estimates, each with its 16-district permutation rank:**

| Analysis | Beta (pp) | Auckland's rank of 16 |
|---|---|---|
| Within specialty (district x specialty x month FE) | 3.28 | 3 |
| Fully saturated FE | 3.17 | 2 |
| Quadruple difference, Maori+Pacific vs Asian (plan FE) | 1.83 | 5 |
| Quadruple difference (saturated FE) | 1.00 | 8 |
| Pre-COVID baseline, Jul 2018 - Jan 2020 (plan FE) | 3.16 | 3 |
| Pre-COVID baseline (saturated FE) | 0.65 | 5 |
| Tool era as baseline | 2.53 | 2 |
| Tool-era tau | 4.78 | 1 |
| Post Sep 2024 - Jul 2025 | 8.19 | 1 |
| Post Aug 2025 - Jun 2026 | 6.00 | 1 |
| Post Jan - Jun 2026 | 4.03 | 3 |
| Maori only (saturated FE) | 0.43 | 7 |
| Pacific only (saturated FE) | 5.39 | 4 |
| Unweighted, cells with total > 5 | 2.95 | 4 |
| Unweighted, cells with total > 20 | 4.67 | 2 |
| Unweighted, cells with total > 50 | 5.49 | 1 |

**Stock growth, pre to post (Auckland vs controls).**

| Group | Auckland stock | Auckland long waiters | Controls stock | Controls long waiters |
|---|---|---|---|---|
| Maori | x1.54 | x2.09 | x1.15 | x0.99 |
| Pacific | x1.73 | x2.70 | x1.17 | x1.03 |
| Asian | x1.52 | x2.01 | x1.33 | x1.11 |
| European/Other | x1.32 | x1.55 | x1.09 | x0.98 |

## D5. Inference wording and threats added after review (2026-10-03 23:23 NZDT)

- **Permutation p-value.** With one treated district, p = 1/16 = 0.0625 is the smallest value the design allows.
- **Placebo distribution.** q05 of the 15 placebos is essentially the minimum; the report gives the placebo min and
  max.
- **Delta lockdown.** Auckland's Delta lockdown (Aug-Dec 2021) falls inside the preregistered pre-period. It is an
  Auckland-specific shock the plan did not list.
