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
  - EF1% cannot exceed min(100, 1/hit-rate), because the top 1% holds 0.01n slots: 100 for the 20 targets whose hit
    rate is at or below 1%, but 4.8 for CYP3A4, 2.5 for CYP2C19 and 2.0 for SYK.
    - **Correction**, made before any score: an earlier draft of this entry gave the ceiling as 1/hit-rate alone
      (567 for SNCA), which is only the bound for hit rates above 1%.
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

## D3 — 2026-10-28 00:57 NZDT — inactive cap; before any method was fitted

Both benchmarks hold targets far larger than the plan assumed: LIT-PCBA's median target has 246,069 compounds (10 of
15 above 50,000) and NEW has 7 targets above 50,000, up to 474,716. Five methods x five folds over those sets is not
computable on this shared machine.

- **Cap.** At most 50,000 compounds per target (seed 20261027), and for LIT's published split, per target and
  split, so training and validation stay disjoint.
  - Both classes are subsampled proportionally, which preserves the hit rate exactly and so preserves EF1%'s
    ceiling, min(100, 1/hit-rate).
  - When that would leave fewer than 150 actives, all actives are kept and only the inactives are capped. The rate
    then rises, but only for targets that stay below a 1% hit rate, where the ceiling is 100 either way.
  - NEW keeps 570,362 of 1,555,249 rows and LIT 1,540,526 of 5,460,747; 616,425 unique structures remain.
- **Checked, not assumed** (`code/subsample.py check`, `results/tables/subsample_check.json`). On the three largest
  NEW targets, the memorization baseline's EF1% on an 80/20 split, full set against capped set:

  | target | compounds | hit rate full / capped | EF1% full / capped |
  |---|---|---|---|
  | ALOX12 | 474,716 | 1.30% / 1.16% | 19.8 / 18.7 |
  | ATXN2 | 336,588 | 0.76% / 0.77% | 27.6 / 33.9 |
  | IP6K1 | 142,851 | 0.79% / 0.79% | 13.3 / 17.8 |

  The hit rate is preserved and EF1% is of the same size, with the residual scatter expected from evaluating about
  10,000 instead of 30,000-95,000 compounds.
  - **An earlier version of this cap kept all actives and capped only the inactives.** That raised ALOX12's hit
    rate from 1.3% to 10.9% and cut its EF1% from 19.8 to 7.4. The check caught it, and the rule above replaced it
    before any method was fitted.
- The cap applies identically to NEW and LIT, so H1's comparison stays like for like.

- **G6 note.** Two ledger DOIs initially resolved to unrelated papers (an Auto3D paper in place of MF-PCBA, and in
  the single-cell lead a crystallography paper in place of Open Targets). Both were caught by the title check, not
  by resolution. MF-PCBA is 10.1021/acs.jcim.2c01569 and is dated 2023, not 2022 as the lead states.
