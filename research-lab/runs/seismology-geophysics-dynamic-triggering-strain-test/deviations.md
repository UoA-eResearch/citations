# Deviations from plan.md

## Technical (before any window result)

- **Listing parser.** The first listing found 0 objects because S3 inserts checksum elements between ETag and Size.
  The parser now reads each Contents block field by field and raises if a page parses to nothing.
- **Partition edges.** The proxy reads the 2002–2025 partitions only, so 7 picks dated in range but stored in December
  2001 or 2026 partitions are not used (531,327,099 kept at download, against 531,327,092 read by the proxy).
- **Proxy validation** (G3, `results/tables/proxy_validation.json`): recall of ComCat M ≥ 1 within 30 km is 46%,
  nearly flat with magnitude (52% at M ≥ 3). A diagnostic of the M ≥ 3 misses, run before any window result was read,
  found design causes rather than a bug:
  - very near events with S−P under the 0.8 s minimum, which give a P pick but no pair;
  - pairs without 2 coincident neighbours in sparse areas;
  - stations with no picks for the event.

  The proxy trades recall for false-coincidence control, as planned.

## D1 (2026-10-26 16:10 NZDT; POST-RESULT: after the primary H1/H2 result was read)

- **Primary result:**
  - H2 Refuted: mean excess −0.0031 (−0.0067 to +0.0006); 15,042 significant pairs against 15,742 expected.
  - H1 Inconclusive: E5 −0.0066 (−0.0147 to +0.0021).
  - The excess falls slightly with strain.
- **A suspected artefact of the masking design.** The proxy removes picks within ±60 s of predicted teleseismic P
  arrivals of every ComCat M ≥ 4.5. Great earthquakes have many M ≥ 4.5 aftershocks in the 24 h post window, so real
  post windows lose more observation time than baselines or pseudo-trigger windows. β's f does not account for that,
  which biases β down at high strain.
  - Consistent with this, removing triggers above M 8 moves E5 from −0.0066 to −0.0008.
- **POST HOC check.** `windows.py exposure` (and `exposure_post6h`) recomputes every real and pseudo window with
  effective exposure: window length minus the union of masks. It is reported beside the preregistered result, which
  stands.

## D2 — 2026-11-07 — fixes after the independent review (verdict: fix first)

Everything here follows the first review (`review/review.md`) and is post hoc. No pick, window or null was
recomputed; the preregistered results stand as computed and are reported beside the corrected ones.

1. **Comparable arms (finding 1, G1).** Pseudo-triggers were rejected near other large earthquakes, and real triggers
   were not. New `code/comparable.py` classifies the real pairs and re-applies the preregistered H1/H2 rules and
   bootstrap (`analyse.summarise`) to each class (`results/tables/comparable.json`).
   - The null's own rule applied to real triggers is the corrected primary: no other M ≥ 7 within 10 days and no
     other M ≥ 6.5 within 3 days. It keeps 68 of 350 triggers and gives a mean excess of +0.000 (−0.008 to +0.008),
     so H2 is Inconclusive.
   - Pairs with no other M ≥ 6.5 in their own windows: +0.004 (−0.002 to +0.011).
   - Post-window contamination alone: −0.013 (−0.019 to −0.006).
   - The contaminated share rises from 16% (lowest strain quintile) to 33–36% (top two).
   - The title and verdict are rewritten. The preregistered "H2 Refuted" stays beside the corrected result.
2. **Station population (finding 2).** The title and verdict say about 1,500 long-running stations. The station map
   carries a caveat: per-station nulls rest on a median of 212 random times.
3. **Detectability (finding 3).** The verdict states the proxy's recall (46%; 52% at M ≥ 3) and the size of rise a
   significant result needs, and that instantaneous triggering cannot be tested.

## D3 — 2026-11-09 — edits after the confirmation pass (verdict: publish with edits)

- **The H1 bullet** now says Inconclusive in the corrected primary, the preregistered analysis and every
  preregistered variant, and notes that the contaminated baseline-only subset gives Refuted.
- **Quintile uncertainties** are given for both analyses: ±0.015–0.023 on comparable arms, about ±0.008 as
  preregistered.
- **The title** says "no rise with strain is seen" instead of "nothing grows with strain".
