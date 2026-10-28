# Nothing we tried forecasts where an antibiotic-resistance gene will appear next better than knowing where people are sequencing

*NCBI Pathogen Detection, 106 organism groups: 1.62 million isolates with uniform AMRFinderPlus calls, 264 species,
4,417 gene symbols. Candidate (gene, species) pairs not yet established at the end of 2022 were ranked for
appearance in 2023–2025 by a gradient-boosted model trained on the same task one period earlier (cutoff 2019), and
by a sampling-effort null that knows only each gene's frequency and how many isolates of each species were
sequenced in the forecast window. The plan was committed before any Pathogen Detection data were downloaded.*

**Verdict: H1 Refuted; H2 Refuted.**

- **H1 (the model's precision@100 is at least twice the null's): Refuted.**
  - The model's precision@100 is **0.00**; the null's is **0.08**. Not one of the model's 100 most confident
    predictions emerged. The ratio's 95% interval over gene resamples is 0.00–1.27.
  - The null is a strong baseline, not a weak one: 0.08 against a base rate of 0.0018 is a 44-fold lift. Where a
    gene newly appears is mostly where sequencing happens.
- **H2 (ESM-2 protein embeddings add signal beyond co-occurrence and taxonomy): Refuted.**
  - Average precision is **0.076 with the embedding and 0.081 without it**; the paired difference is −0.005
    (−0.013 to +0.001).
  - The embedding does not merely fail to help. **It is what breaks the model.** Removing it lifts precision@100
    from 0.00 to 0.18, above the null's 0.08.
- **But that repair does not survive the honest outcome definition.** Under the preregistered first-appearance
  variant, where a pair counts as emerging the first time any isolate carries it, **both models score 0.00 against
  the null's 0.10**. The no-embedding model's apparent win exists only under the primary rule.
- **Why the primary rule flatters a model.** It requires two isolates from different BioProjects, to suppress
  outbreak clones. The side effect is that **705 of the 847 labelled emergences (83%) are pairs already observed at
  least once before 2023** (median first sighting 2019). They are confirmations, not first appearances.

## In plain terms

Genes that make bacteria resistant to antibiotics spread between species. If we could forecast which gene will turn
up in which species next, surveillance could watch the right places. We tested whether that is possible using 1.6 million
sequenced isolates that one pipeline has annotated the same way, scoring honestly: train only on data collected before a
cut-off, then check against what actually appeared afterwards.

It is not, with these ingredients. A machine-learning model given gene frequencies, which species already carry
related genes, bacterial family trees and a protein language model's view of each gene's product did no better than
a simple calculation that knows only how common a gene is and how many samples of each species were sequenced. On
the strictest reading of "appeared for the first time", the model got none of its top 100 predictions right, while
the simple calculation got one in ten.

One ingredient actively hurt. The protein language model rates most resistance genes as near-identical to each other,
because many are variants of the same gene family. That led the model to predict new appearances in species that are
barely sequenced, where nothing can be detected. Dropping that one feature turned the model from worse than the
baseline to better than it — but only under the looser definition of "appeared".

The honest summary is that surveillance intensity, not biology, is what these data mainly encode about where a
resistance gene shows up next.

## What was asked

The lead (`bioinformatics-amr-gene-species-emergence-forecast`) asked whether first appearances of AMR genes in new
species can be forecast prospectively, with an explicit sampling-effort null, on the Pathogen Detection corpus.
- **The uniform calls** come from AMRFinderPlus and the Reference Gene Catalog (Feldgarden et al., 2021), which is
  what makes a corpus-wide comparison possible at all.
- **The feasibility claim** comes from Ellabaan et al. (2021), who showed resistance-gene dissemination is partly
  predictable from genomic and phylogenetic features — retrospectively, on static snapshots.
- **The gap** is prospective, calendar-time evaluation against an effort null, which is the only baseline that
  matters when surveillance intensity drives most new observations.

## How it was done

- **Corpus.** All 106 bacterial organism groups' latest metadata tables. Kept: isolates with a parseable collection
  year in 1990–2025, a resolved species binomial and an AMR call field. Point mutations are excluded; acquired genes
  only.
- **A pair is established** in a year when two isolates from different BioProjects carry that gene in that species.
- **Candidates** at the 2022 cutoff: 472,779 (gene, species) pairs not established, where the gene is established in
  at least one species and the species has at least 20 isolates. 847 emerged in 2023–2025.
- **The model** is a histogram gradient-boosted classifier over 14 features in four families: sampling effort,
  co-occurrence, taxonomy and ESM-2 (650M) embedding similarity to the nearest gene the species already carries. It
  is trained on the 2019 → 2020–2022 task and applied once to the test task; hyperparameters come from gene-grouped
  cross-validation inside the training task (D2).
- **The null** gives each candidate the probability that a gene at its overall pre-2023 frequency would appear at
  least twice among that species' 2023–2025 isolates. Both the null and the model are told the realised number of
  isolates, so this is a test of what beats effort, not of effort itself.
- **Intervals** come from resampling candidate rows by gene, 2,000 times.
- **Catalog growth was controlled** (D1): candidate genes are restricted to the 4,250 symbols already in the oldest
  reference catalog used in the corpus, so a gene newly added to the catalog cannot look like a new appearance.

## Results

| ranking | precision@100 | precision@500 | average precision |
|---|---|---|---|
| sampling-effort null | 0.08 | 0.040 | 0.015 |
| **full model (preregistered)** | **0.00** | 0.126 | 0.076 |
| model without the embedding | 0.18 | — | 0.081 |
| model without taxonomy | 0.16 | — | 0.075 |
| model without co-occurrence | 0.00 | — | 0.037 |
| effort features only | 0.00 | — | 0.012 |

- **The full model is not bad everywhere.** Its average precision (0.076) is five times the null's, and at depth 500
  it is three times better. The failure is specifically at the top of the list, which is what a horizon-scanning
  system would act on, and which the preregistered statistic measures.
- **Its top 100 are saturated and implausible.** 118 candidates score above 0.999. The top 100 have a median of 24
  isolates in the forecast window, against 414 for pairs that actually emerged, and 93 of them are in two
  rarely-sequenced species (*Edwardsiella piscicida*, *Pluralibacter gergoviae*).
- **The embedding is the cause.** Nearest-neighbour ESM-2 cosine similarity is 0.971 at the median across all
  candidates, because AMR genes are largely allele variants of one another. A feature that is near-saturated
  everywhere separates nothing, and its top tail picks out β-lactamase variants in species with almost no data.
- **It is not survivorship, and not a tie artefact.** Splitting candidates by whether they were already candidates
  at the 2019 cutoff does not rescue the model (0.00 carried over, 0.07 newly eligible), and the top 1,000 scores
  hold 989 distinct values.
- **Within-period skill is also weak.** Trained and evaluated inside the test period by cross-validation, the same
  features give precision@100 of 0.06 — below the no-embedding transfer model.

### The outcome definition decides the secondary result

| outcome rule | emergent pairs | null | full model | model without the embedding |
|---|---|---|---|---|
| two BioProjects (preregistered primary) | 847 | 0.08 | 0.00 | **0.18** |
| first isolate (preregistered variant) | 1,307 | 0.10 | 0.00 | **0.00** |

Under the first-appearance rule neither model places a single correct pair in its top 100. The no-embedding model's
advantage under the primary rule comes from the 83% of labelled emergences that were already observed once: a model
can find a pair that is about to be confirmed, but not one that is about to appear.

## What this does and does not show

- **No feature set here beats sampling effort at the top of the list.** That is the result, and it is a negative
  one. It holds for the preregistered model, for every ablation under the first-appearance rule, and within period.
- **Protein language model embeddings need care in this setting.** Used as nearest-neighbour similarity over AMR
  gene products, ESM-2 is near-saturated and actively harmful. This is a statement about this use, not about ESM-2:
  a fine-tuned or contrastive representation might behave differently.
- **The effort null deserves to be the default baseline** in work of this kind. At a 44-fold lift over the base
  rate it is hard to beat, and any paper reporting high AUROC for resistance-gene spread without one should be read
  with that in mind.
- **Limits.**
  - **Observation is not emergence.** A first observation is when a pair was first sequenced and submitted. The
    effort null addresses this only in part, and the two-BioProject rule makes it worse, as shown above.
  - **The model is not the lead's.** Gradient-boosted trees over engineered features, not a temporal graph neural
    network, chosen for auditability on CPU. A negative result is about these features, not every model.
  - **Pathogen Detection covers chosen pathogens,** mainly foodborne and clinical, so species outside it are absent.
  - **Collection dates are coarse.** Year resolution throughout; 599,000 isolates were dropped for an unparseable or
    out-of-range year, and 722,000 for having no AMR call field.
  - **The ablations re-ran the hyperparameter search,** so their comparisons include a little selection noise.
- **Not shown:** whether richer features (plasmid and mobile-element context, geography, host) would beat the null;
  whether any model can forecast first appearances at longer horizons; anything about clinical risk.

## Process and deviations

- **Preregistration:** `plan.md`, committed before any Pathogen Detection data were downloaded.
- **Deviations** (`deviations.md`): D1 the catalog-growth restriction, decided before any candidate table; D2 the
  hyperparameter rule and the post hoc diagnosis.
- **Gates:** G1 in the plan (the test period is used once; the effort features are declared inputs);
  G2 `results/tables/coverage.json`;
  G3 `results/plausibility.md`; G4 the trace of three emergent pairs against raw isolates; G5
  `review/overclaim_check.md`; G6 `results/attribution_ledger.csv`; G7 does not apply.
- **Independent review:** queued (Fable), per the lab's pacing rule.
- **Data:** NCBI Pathogen Detection and the AMRFinderPlus Reference Gene Catalog (public domain); ESM-2 650M
  (facebook/esm2_t33_650M_UR50D); the NCBI taxonomy.

## Reproducing it

1. `code/list_groups.py`, then download the metadata tables listed in `data/groups.csv`.
2. `code/build.py`, `code/taxonomy.py`, `code/proteins.py`, `code/embed.py` (a few minutes on a GPU).
3. `code/candidates.py 2019 2022 train` and `code/candidates.py 2022 2025 test`; with `RULE=any` for the variant.
4. `code/analyse.py` (several hours on 20 cores), then `code/posthoc.py` and `code/variant_any.py`.
