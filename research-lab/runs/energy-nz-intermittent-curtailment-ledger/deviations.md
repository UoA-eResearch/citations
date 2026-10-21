# Deviations from the preregistration

## D1 — 2026-10-22 00:50 NZDT — fetching and reading the inputs (before any curtailment series)

1. **One day is not published.** EMI has no offers file for 31 August 2026: its listing goes from 30 August to
   1 September, and the blob store returns 404. The day is outside both hypothesis periods and is missing only from
   the ledger and the projection.
2. **December 2025 prices** are missing from the monthly price folder, so the fetcher assembled that month from its
   31 daily files (361,585 rows, against 349,921 for the 30 days of November).
3. **Column-name case** in Generation_MD varies between months (`Trading_date`, `Trading_Date`); the reader now
   matches names case-insensitively.
4. **The offer layout**, read before the plan was written: each tranche row of the latest submission repeats that
   submission's potential, while tranches carried over from earlier submissions keep stale potentials, so *P* is
   taken from the highest-numbered latest submission, as `build.py` does.
