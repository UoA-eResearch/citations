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
5. **Fuel codes.** Generation_MD labels older plants `Wind`/`Solar` and newer ones `WIN`/`SOL` (technology
   `ONW`/`PV`). The first build matched only the older labels, which left out eight solar farms (Dannevirke,
   Kōwhai Park, Pāmu Rā ki Whitianga, Te Herenga o te Rā, Clandeboye, Tauhei, and two at Maungaturoto) and two wind
   farms (Kaiwaikawe, Kaiwera Downs stage 2). Both codings are now read. Mahinerangi (offer unit MAH0 at HWB0331)
   has no wind generator in Generation_MD, only the Waipori hydro scheme at that point, so it remains unmatched and
   is excluded. Rotohiko (HLY0331) is a battery (fuel `ELE`) and is excluded as not wind or solar. KOE1101 carries
   three offer units but two metered solar farms (Kohira, Pukenui); its output is 0.72 of its potential, and it is
   kept, with the bias correction absorbing the difference, and named in the leave-one-out.
6. **Partial or missing metering.** Some matched plants have metered output far below their potential:
   - Kōwhai Park (ISL0661, from August 2026) and Kaiwaikawe (MPE1101, from July 2026) report only zeros;
   - Pāmu Rā ki Whitianga (KPU0661, from November 2025) reports commissioning-scale values;
   - Maungaturoto (MTO0331) offers two units but has one metered generator (output 0.21 of potential).

   The preregistered bias correction already scales potential to metered output per plant-quarter, so a plant with
   *k* near zero contributes almost nothing to either curtailed or available energy. Added before any curtailment
   figure was computed: a variant dropping plant-quarters with *k* below 0.5.

## D2 — 2026-10-22 01:41 NZDT — after the primary results: the measurability gate fails, and a post hoc decomposition

The first full run gave the following:
- **Gate:** the median plant's detection floor is 27% of its mean potential in 2025/26, above the 25% gate, so by
  plan section 3 curtailment is **not reliably measurable from offers alone**.
- **H1:** Refuted by its rule; the 2020 share is 2.27% (2.13 to 2.42).
- **H2:** Supported by its rule; 72.7% of curtailed energy is non-price (64.1 to 82.3).

The rule in plan section 1 flags a TP as curtailed when its gap exceeds the 95th percentile of gaps on unconstrained
TPs, and counts all TPs, so about 5% of *unconstrained* TPs are flagged by construction and forecast error alone
yields a positive share. Unconstrained TPs are, by definition, ones where prices exceed the unit's offer, so this noise
mass also lands in H2's "non-price" share. `code/diagnostics.py` (written after seeing the results; exploratory)
splits curtailed energy by the class of TP it falls in (unconstrained, offer-limited, price-driven, other). It also
tracks, by 12-month window, curtailment in TPs where the node price is at or below the unit's own offer price, the
clearest real signal. Verdicts are reported as the rules give them, with the gate's statement leading.
