# Preregistration — Does peer review push p-values across 0.05 in one direction?

*Version-matched statistics in preprints and their published journal versions: of the reported p-values present in
both and crossing the 0.05 line between them, how many go from non-significant to significant?*

Committed before any statistic was extracted from real text. Examined beforehand, deliberately, because none involves an
outcome: the Europe PMC preprint full-text shards (structure and version numbers only), the preprint-to-publication
links (counts below), and the code, tested only on crafted text.

## 1. The question

When a preprint becomes a journal article, reported results change. If those changes are random, a p-value that
crosses 0.05 between versions is as likely to go from significant to non-significant as the reverse. A ratchet - more
results moving into significance than out - would point to selective reporting or analysis changes during review.

### 1.1 Hypothesis (from the lead, unchanged)

**H1.** Among aligned statistic pairs (one in the preprint, its counterpart in the published version) whose
significance at α = 0.05 is determined in both and differs, at least 67% cross from non-significant to significant
(a 2:1 ratchet), against a null of 50%. Supported if the point estimate is ≥ 0.67 and the 95% interval's lower end
is above 0.50; Refuted if the interval's upper end is below 0.67; Inconclusive otherwise. The interval is a bootstrap
over papers (2,000 resamples), so a paper with many crossings counts once per resample.

**Secondary.**

- S1: significance among dropped statistics (preprint only) against added ones (published only).
- S2: statcheck-style consistency; how many preprint inconsistencies are repaired in the published version (the
  lead predicted fewer than half).
- S3: H1 restricted to exact tuple matches, and split by server.

### 1.2 What changed from the lead, and why (deviations D1)

1. **Linkage routes are not independent.** The lead required agreement of ≥ 2 of four routes. Europe PMC's "Preprint
   of" links are loaded from Crossref (their note says "CrossRef Pre-print loader"). PreprintToPaper's "Published"
   label is bioRxiv's own link. Crossref's is-preprint-of relation on bioRxiv DOIs is deposited by bioRxiv itself.
   So the routes reduce to one server assertion for most pairs. Instead, every server-asserted link (bioRxiv/medRxiv
   API or Crossref) must be **confirmed independently** by title similarity (token Jaccard ≥ 0.5) between the
   preprint and the published record.
2. **Embedding residue.** The lead's "small local embedding model" step for alignment is dropped. Masked-number
   TF-IDF similarity plus exact tuple matching is used, and validated (§6).
3. **Preprint population.** It is Europe PMC's full-text preprints (PPR shards; bioRxiv, medRxiv, Research Square,
   Preprints.org, ChemRxiv). The primary uses full texts known to be version 1 (about 11,500 pairs, above the lead's
   10,000); the 57% of usable pairs whose version Europe PMC does not give form a sensitivity.

## 2. What is already known

| Work | What it establishes | What it leaves open |
| --- | --- | --- |
| Nuijten & Wicherts (2024, *AMPPS*) | statcheck adoption at journals reduces decision inconsistencies near .05 | version-matched changes |
| Sci Rep 2023 (10.1038/s41598-023-44291-4) | 329 medRxiv prevention preprints: 16.8% changed primary-outcome magnitude | direction of significance changes at scale |
| Bero et al. (2021) and the bioRxiv epidemiology cohort (Peer Review Congress) | ~10% of 121 preprints changed main findings; 7 changed p-values | scale; direction |
| JAMA Netw Open 2022 (medRxiv vs journal) | primary end points concordant in 98% | non-primary statistics |
| bioRxiv 2026.06.30.735556 | 72,644 pairs, LLM-classified claim changes: wording more cautious, claims rarely change | statistic-level direction |

A search on 2026-10-17 found no version-matched comparison of the direction of significance crossings across the
population of reported statistics.

## 3. Data

| item | source | vintage |
| --- | --- | --- |
| preprint full text | Europe PMC preprint shards (8 files, 75,217 full-text records) | `data/raw/VINTAGE.txt` |
| server links | bioRxiv/medRxiv API /pubs; Crossref works relations | `data/raw/links/` |
| published metadata | Crossref works | `data/raw/links/published_crossref_meta.jsonl` |
| published full text | PMC Open Access subset (AWS open data), via the NCBI ID converter | `data/raw/published/` |

Linkage, before any statistic (counts only):

| step | pairs |
| --- | --- |
| preprints with a server-asserted publication link (Crossref 22,348; bioRxiv API 717; both 155 - of the usable set) | 31,261 candidate pairs |
| confirmed by title similarity (Jaccard >= 0.5) | 28,597 |
| published version in the PMC OA subset and fetched (882 not OA) | 23,220 unique preprints |
| **preprint full text known to be version 1** (Europe PMC article-version, or the DOI's /vN) - **primary** | **about 11,500** (Research Square 6,066; medRxiv 4,290; bioRxiv 1,040; other 112) |
| version unknown (bioRxiv 5,274, medRxiv 2,676 and others: Europe PMC gives no version and the DOI does not encode it) | in the all-versions sensitivity only |

## 4. Extraction (`code/extract.py`, 16 tests)

- **Statistics:** p-values (equalities, inequalities, scientific notation, Unicode comparators, "p-value of"), and
  statcheck-style tuples (t, F, r, χ², z with df), each with its sentence.
- **Sections:** abstract, results (including "Results and Discussion"), tables, figure captions.
- **Excluded:** methods and all other sections, and boilerplate threshold sentences ("p < 0.05 was considered
  significant", "significance level", "α = 0.05").
- **Significance at 0.05:** "=" is significant if p < 0.05; "<" and "≤" are significant if the bound is ≤ 0.05;
  ">" and "≥" are not significant if the bound is ≥ 0.05. Anything else, including "p = 0.05" exactly, is
  undetermined and excluded from crossings.

## 5. Alignment (`code/align.py`, 7 tests)

1. Tuples match on test, df and statistic (within 1%).
2. Remaining statistics match one-to-one by TF-IDF cosine of their sentences, with every number masked so a changed
   p-value does not reduce similarity. The threshold is ≥ 0.6, within the same section group (abstract;
   results/tables/figures; other).
3. Several statistics in one sentence are paired by order.
4. Unmatched statistics are "dropped" (preprint) or "added" (published).
5. Classes: unchanged; changed but not crossing; crossing up; crossing down; undetermined.

## 6. Validation and abort rule (before H1 is computed)

`code/validate_alignment.py` draws all crossings up to 100 and 100 other aligned pairs. Each is shown as two
sentences in random order, unlabelled, with the stratum hidden. The adjudicator (the agent running the study; there
is no human coder) records whether they report the same statistic. Because the version order is hidden, the
adjudication is blind to the direction of every crossing.

- **Precision among crossings ≥ 0.90:** H1 is tested on all crossings.
- **Precision < 0.90:** H1 is tested on exact tuple matches only, labelled as such, and the all-crossings estimate
  is reported as unreliable.

The crossing tallies are computed by `code/analysis.py` only after the adjudication is recorded.

## 7. Threats to validity

1. **Misalignment:** a misaligned pair looks like a crossing. The validation and abort rule address it, and tuple
   matches are the robust subset.
2. **Legitimate changes:** published versions add data, correct errors and change analyses at reviewers' request. A
   ratchet would show direction, not misconduct, and the report will say so.
3. **Version history:** Europe PMC may hold a later preprint version than v1 for some papers. The primary uses v1
   full texts only.
4. **Selection:** only pairs with an OA published version enter, so journals and fields with OA mandates are
   over-represented.
5. **Extraction:** inequalities and rounding make some significance statuses undetermined; these are excluded,
   which could matter if exclusion differs between versions.
6. **Clustering:** papers contribute unequally; the paper-level bootstrap handles this.

## 8. Process commitments

- `parse_jats.py`, `link.py`, `fetch_published.py`, `extract.py`, `align.py`, `pipeline.py`,
  `validate_alignment.py`, `analysis.py` and tests are committed with this plan.
- The pipeline runs only after the commit. The validation is adjudicated before `analysis.py` runs.
- Departures go in deviations.md, timestamped with `date`.
- An independent adversarial review (Fable 5.1) runs on the pre-review draft.
- Released: the aligned-statistics table (statistic-level, with DOIs and sentences), the extractor, the code.
