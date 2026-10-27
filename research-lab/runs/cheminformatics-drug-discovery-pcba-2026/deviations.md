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
