# Deviations from plan.md

## D1 — 2026-10-27 20:23 NZDT — before any activity outcome or compound list was read

- **LIT-PCBA archives.** The plan said the "full data" archive carries the published training/validation sets. It
  does not: `full_data.tgz` holds each target's complete actives and inactives (used here for the LIT
  analog-disjoint control). The published per-target training/validation split is distributed in
  `AVE_unbiased.tgz` (the AVE-debiased split the LIT-PCBA authors released for machine learning). "LIT-PCBA as
  published" (plan section 3; H1 and H3) therefore uses `AVE_unbiased.tgz`'s training and validation sets.
- **PubChem outcomes.** PUG REST rejects `cids_type=inconclusive`, so inconclusive and unspecified compounds are
  counted as all − active − inactive CIDs (`fetch.py`, `build.py`).
- **Embedding image.** The current MoLFormer-XL snapshot (361063d) ships modelling code that needs transformers 5.
  The image is therefore torch 2.10.0 (CPU) with transformers 5.16.1, run offline. Both models were checked on four
  test SMILES (finite 384- and 768-dimensional embeddings).
- **BEDROC formula.** The first implementation of the secondary BEDROC metric was wrong (a perfect ranking scored
  0.003). It was corrected to the Truchon & Bayly definition before any benchmark score was computed, and checked:
  perfect 1.0, worst 0.0, random about 0.05 at alpha 20.

## D2 — 2026-10-27 21:51 NZDT — benchmark composition; before any method was fitted or any score computed

The NEW benchmark has 28 targets (12 deposited 2023 or later), 1,555,249 compound-target rows and 578,057 unique
compounds. Seen while checking the build, from assay composition only:

- **Hit rates vary enormously**, from 0.18% (SNCA) to 49% (SYK). The plan set floors on actives and compounds but no
  ceiling on the hit rate.
  - EF1% cannot exceed 1/hit-rate, so the ceiling is 567 for SNCA but 2.0 for SYK, 2.5 for CYP2C19 and 2.6 for
    CYP1A2.
  - Seven targets (SYK, NSD2 and five CYP counterscreens) have hit rates above 20%. These are counterscreens, not
    virtual-screening decks.
  - This matters for H1: A_NEW would be small for those targets whatever the leakage, which pushes H1 towards
    Supported for a mechanical reason.
- **Decisions** (the preregistered analysis is unchanged):
  - the primary H1, H2 and H3 results keep all 28 targets, as preregistered;
  - **post hoc:** the same statistics are reported for the 19 targets with a hit rate at or below 5%, which is the
    screening-like regime LIT-PCBA occupies (its targets are near 0.1-1%);
  - every metrics table carries each target's hit rate and EF1% ceiling, and a normalised EF1%/ceiling column
    (post hoc), so the mechanical bound is visible;
  - if the preregistered and the restricted results disagree, the report leads with that disagreement rather than
    with the preregistered verdict alone.
- **Frequent hitters** are 29% of all actives (compounds active in at least 30% of the NEW assays that tested them,
  among those tested in at least 5). The preregistered sensitivity that drops them is therefore substantial, not
  cosmetic.
