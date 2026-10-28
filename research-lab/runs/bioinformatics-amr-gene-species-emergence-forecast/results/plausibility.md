# Plausibility (G3)

## Base rates

- **Emergence is rare and effort-driven.** 847 of 472,779 candidate pairs emerged in 2023–2025 (0.18%). The
  training task's rate was 0.33% (1,271 of 386,001). Fewer first appearances in the later window is consistent with
  the corpus: 2023–2025 holds 349,205 dated isolates against 416,410 in 2020–2022.
- **Emergence happens where sequencing happens.** The median emergent pair's species has 414 isolates in the
  forecast window. The sampling-effort null is built on exactly this and reaches precision@100 of 8%, a 44-fold lift
  over the base rate, which is why it is the baseline that matters.

## Three emergent pairs traced, and what the trace revealed

| pair | genus count | co-occurrence | gene frequency | horizon isolates of the species | carriers found in 2023–2025 |
|---|---|---|---|---|---|
| blaACT × *Enterobacter cancerogenus* | 14 | 0.44 | 0.002 | 20 | 2 isolates, 2 BioProjects, 2023 |
| aph(3'')-Ib × *Bacillus cereus* | 0 | 0.98 | 0.200 | 738 | 2 isolates, 1 BioProject, 2024 |
| aph(6)-Id × *Burkholderia cepacia* | 2 | 0.83 | 0.200 | 47 | 1 isolate, 2023 |

Only the first is a clean first appearance. The other two reach the two-BioProject threshold during the horizon
only because an earlier isolate, before 2023, supplies the other BioProject.

**That is general, not a quirk of these three.** Of the 847 labelled emergences, **705 (83%) had already been
observed at least once before 2023** (median first sighting 2019); only 142 are first appearances of the pair. The
training task is the same (979 of 1,271). The two-BioProject rule was chosen to suppress outbreak clones, and it
does, but it turns most "emergences" into confirmations of a pair already seen once.

The plan anticipated this by listing a one-isolate outcome variant, and that variant is reported in the results as
the first-appearance reading of the question.

## Why the preregistered model fails, checked rather than assumed

- **Its top 100 are saturated.** 118 candidates score above 0.999, and the top 100 have a median of 24 isolates in
  the forecast window, against 414 for real emergences. Sixty-seven of the 100 are in one species
  (*Edwardsiella piscicida*) and 26 in another (*Pluralibacter gergoviae*).
- **The cause is the protein-embedding feature.** ESM-2 similarity between AMR gene products is high everywhere
  (median nearest-neighbour cosine 0.971 across all candidates, 0.995 among emergent ones), because many AMR genes
  are allele variants of each other. The model learns that a near-identical protein already present predicts
  emergence, which nominates β-lactamase variants in species that are barely sequenced, where emergence is
  nearly impossible.
- **Removing it fixes the model.** Without the embedding, precision@100 is 0.18 against the null's 0.08.
- **It is not survivorship.** Splitting the test candidates into those that were already candidates at the 2019
  cutoff and those newly eligible does not rescue the full model (0.00 and 0.07), so the failure is not that the
  earlier period used up the high-propensity pairs.
- **It is not a tie artefact.** The top 1,000 scores hold 989 distinct values, so the ranking is not arbitrary.

## Sanity of the data build

- 1.62 million isolates from 106 organism groups, 264 species, 4,417 gene symbols, 19,436 observed pairs.
- 99.5% of gene calls have a reference protein.
- The catalog restriction (D1) keeps 4,250 of 4,417 symbols and 1,116 of 1,160 emergent pairs, so it is not doing
  the work of the result.
