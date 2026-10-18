# Independent review: future-health-schedule-llm-localisation (pre-review draft 43c9877)

Reviewer: independent adversarial review, 2026-10-18. Scripts and outputs are under `review/reviewer_checks/`
(`0N_*.py` with matching `.out` files; `rc_common.py` is the reviewer's own evidence reader; `sheets/` holds the
blind screening and re-adjudication sheets; `reviewer_cf_screen.csv` and `reviewer_key_readjudication.csv` hold the
hand judgements). Nothing outside `review/` was modified. No requests were sent to localhost:8000 or to the PBS API.

## Verdict: FIX FIRST

The three hypothesis verdicts (H1 Inconclusive, H2 Inconclusive, H3 Supported) are correct and survived every check,
including a blind re-screen of all 200 counterfactuals, a fresh 96-item key re-adjudication, an independent
re-implementation of the bootstrap, and alternative analyses (pooled, unscreened, yes-bias-free). No new model calls
are needed. But the report cannot be published as written because:

- the retrieval results are misattributed (Finding 2): the 19 Australian restriction misses are BM25 ranking
  failures, not model errors, and "BM25 found the right chemical most of the time" is false for family (d)
  (Finding 3). A results subsection and three headline bullets must be rewritten, not tweaked;
- the family-(d) item set cannot be regenerated from the committed code and is not under version control
  (Finding 1), so the published study would be irreproducible;
- the Australian fabrication rate (35%) is an unscreened upper bound; under the same screen the NZ items got it is
  28% with an interval that includes 20% (Finding 4), and the plain-terms section repeats the inflated figure;
- the report says the keys were checked "against sources the generator did not parse", which is false for the
  Australian half (Finding 5).

Each fix is a text correction, a one-line code change, or committing a data snapshot.

## What reproduced (no finding)

- `01_recompute.py`: all 24 accuracy cells, the five errors, the H1 cluster-bootstrap point estimates and intervals
  for (b) and (a)+(b) (to 4 decimals, same seed; a second seed moves the bounds by < 0.01), both H3 Wilson intervals,
  the 17/17 overlapping items, the response-bias table, abstention rates and accuracy-when-answered, and the 77/100
  paraphrase agreement. The paraphrase draw reproduces `run.py`'s sample.
- Timeline (`stat` birth times; `04_misc.py` F): plan 6bd3e3c 16:43; generator before items (items.jsonl born 17:43,
  regenerated 17:49:18 after D4 at 17:49:15); D5 committed 17:56:34; `logs/run.log` born 17:56:49 and
  `data/runs.jsonl` born 17:56:52. The run therefore started after D5. The screen (18:13:48), `analysis.py`
  (18:14:26, committed 18:15:38) and `figures.py` (18:25) were written while output accumulated. "Before any output
  was opened" cannot be verified from disk, but NZ-d zero-shot calls began at job 1104 of 3247 (34%), which at the
  run's average rate falls at about 18:25, after the screen was saved. The claim is plausible.
- D5 legitimacy (check 6): D4 explicitly added a per-cell bar for family (a) negatives; failing it and demoting (a)
  is the natural reading. The H3 screen goes beyond the plan but is conservative and was fixed before any NZ-d output
  existed. Verdicts are identical under the preregistered pooled analysis (Inconclusive) and without the screen
  (Supported), so D5 changed nothing that matters.
- Blind re-screen of the 100 NZ counterfactuals (`07_screen_compare.py`): 98/100 agreement with the agent on
  distinct vs not; the reviewer additionally excludes NZ-d-0490 and NZ-d-0526 (both "monotherapy" vs "not in
  combination with other chemotherapy"; both affirmed). Screened rate 30/81 = 37.0% (Wilson 27.3-47.9%), still
  Supported. Nine more affirmed items would have to be reclassified before the lower bound fell below 20%.
- A yes-bias-free comparison (Youden's J, same bootstrap; `08_key_readjudication.py`): (b) NZ 0.368 vs AU 0.270,
  difference +0.098 (-0.035, +0.235); pooled +0.063 (-0.081, +0.213). Same conclusion as accuracy.
- GENERIC-filter asymmetry (counterfactuals are barred from generic renewal language, true controls are not): 26/100
  NZ and 20/100 AU true controls match the filter, but they are affirmed less often (62% vs 86% NZ; 75% vs 84% AU), so
  the control rows are not inflated by boilerplate.
- `report.html` carries the same verdict line and status ("pre-review draft") as `report.md`.

## Findings

### 1. Family (d) items are not reproducible from the committed generator, and the item set is not in git (Major)

Evidence: `04_misc.py` (A). Regenerating with `code/generate.py` in four fresh interpreters (two random hash seeds,
`PYTHONHASHSEED=0`, `=1`) reproduces families (a) and (b) exactly but differs from `data/items.jsonl` in all 400
family-(d) positions every time, and the regenerations differ from each other. Cause: `generate.py:180-191` builds
`stable`, `true`, `by_grp` and `cf` from Python sets, so the pool order fed to `rng.shuffle` depends on string hash
randomisation; the seed does not control it. `data/` is gitignored (`.gitignore`), so the only copy of the 400
criterion items whose answers the report rests on is `/mnt/data/.../items.jsonl` on this machine. `report.md:249-252`
("Reproducing it: ... generate.py ...") is therefore false for family (d), and `nz_counterfactual_screen.csv` refers to
ids that a re-run would not recreate.

Fix: sort the sets before sampling (`sorted(...)` on `cr[c]`, `stable[c]`, `true`, `by_grp[...]`), regenerate to
confirm (a)/(b) unchanged, and commit `data/items.jsonl` (200 KB) and `data/passages.jsonl`, or at least their SHA-256,
with the review response. State in the report that the (d) sample is preserved as a file, not re-derivable from the
seed.

### 2. The retrieval results are misattributed: the 19 AU restriction misses are BM25 ranking failures (Major)

Evidence: `03_retrieval.py`, `04_misc.py` (C). Rebuilding the index exactly as `run.py:70-78` does, the chemical's own
passage is in the top 3 for 195/195 NZ (b) items but only 179/200 AU (b) items. All 19 AU misses are among the 21 items
whose own passage was not retrieved; when the own passage was retrieved, AU (b) retrieval accuracy is 100%, the same
as NZ. The missed passages are long (median 365 tokens vs 81 for hits): BM25 length normalisation pushes oncology
passages with long criteria lists below short passages that match "tablet", "mg", "authority", "required". The report
says the cause "was not investigated" (`report.md:143-144`) and presents "With retrieval, New Zealand comes out ahead"
(`report.md:159-160`), the retrieval-gap column of the H1/H2 table (`report.md:150-153`, "+9.5 (+4.8 to +15.0)") and the
green intervals of F2 as model behaviour. They measure the retriever. Conditional on the own passage being retrieved,
the NZ-AU retrieval gap in (b) is 0.

Fix: rewrite the retrieval paragraph and the H2 row: report retrieval accuracy conditional on retrieval success,
state the own-passage hit rates (NZ (b) 100%, AU (b) 89.5%), name BM25 length bias as the cause, and drop "New Zealand
comes out ahead with retrieval". Keep the unconditional numbers only as a description of this retrieval system.

### 3. "BM25 found the right chemical most of the time" is false for family (d); the retrieval fabrication numbers mostly reflect the source passage (Major)

Evidence: `03_retrieval.py`. For counterfactual items the target chemical's passage was in the top 3 for 39/100 NZ
and 26/100 AU items; the source chemical's passage, which contains the counterfactual sentence verbatim, was retrieved
for 90/100 NZ and 58/100 AU (the criterion text in the query dominates BM25). So "Fabrication of NZ criteria drops
from 39% to 0% on the screened items" (`report.md:30`) and the 0%/11%/6% retrieval column of the H3 table
(`report.md:166-171`) describe a model that usually saw the sentence under a different drug's heading and did not see
the target drug's criteria; the 69-88% abstention on (d) negatives (`report.md:203-204`) is the same effect. The claim
at `report.md:222` ("BM25 found the right chemical most of the time") is false for the family that carries H3. The
report also calls the (d) retrieval condition "reading comprehension" (`report.md:31-32`); for counterfactuals it is
closer to a source-attribution check.

Fix: correct `report.md:222`; add the own-passage and source-passage hit rates for (d); qualify the "drops to 0%"
bullet; consider reporting (d) retrieval results split by whether the target passage was retrieved.

### 4. The Australian fabrication rate is an unscreened upper bound and would not clear the 20% bar after screening (Moderate)

Evidence: `07_screen_compare.py`, `reviewer_cf_screen.csv`, sheets `screen_AU_grouped.txt`. A blind screen of all
100 AU counterfactuals against the drug's GE restriction texts finds 14 non-distinct (4 equivalent, e.g. AU-d-0984
"for this PBS indication" vs own "for this condition"; 10 overlapping, e.g. AU-d-1041 "Bone or joint infection" vs own
"Osteomyelitis", AU-d-0990 "Metastatic breast cancer" vs own indication "Breast cancer"). 11 of the 14 were affirmed.
Screened rate 24/86 = 27.9% (Wilson 19.5-38.2%): the lower bound crosses 20%. The report gives 35% (26-45%)
(`report.md:19, 171`) with a hedge (`report.md:180-181`), and the plain-terms section says "about 1 time in 3 for
Australia" (`report.md:55-56`). The AU-NZ comparison in the plain-terms paragraph is screened-vs-unscreened.

Fix: report the AU rate as an upper bound with the reviewer's screened figure (28%, 19.5-38%) alongside, or screen
it yourself; change the plain-terms sentence to "about 1 in 4 to 1 in 3". Note the overlap tier is fuzzy: three
further AU items (0964, 1024, 1034) are implied by a broad own indication and could go either way.

### 5. The key check is described inaccurately and its (d)-negative error rate is understated (Moderate)

Evidence:
- `report.md:105-106` says the 200 items were checked "against sources the generator did not parse: the Schedule PDF
  for New Zealand and the raw PBS API records for Australia". The raw API JSON is exactly what `generate.py:102-137`
  parsed; `deviations.md:37-43` (D3) says so ("This checks the generator's parsing, keying and flag logic. It does not
  check the API against the printed Schedule"). `report.md:218` repeats the overstatement.
- The adjudication was fast and the (d) evidence thin: round 1 took under 3 minutes of wall-clock for 200 items
  (`sheet.txt` 17:45:54 to `key_validation_round1.csv` 17:48:44); the NZ (d) sheet shows 14 PDF lines per heading, often
  cut at "continued...", plus "criterion text in PDF anywhere: True", which is uninformative for a counterfactual
  taken from another chemical in the same PDF (`validate.py:53-59`). The D5 addendum itself notes round 2 caught 1 of
  17 overlapping items (`deviations.md:109-110`).
- Reviewer re-adjudication of 96 fresh items, 8 per jurisdiction x family x answer, none in either validation
  sample, with the full SA block / all restriction texts (`08_key_readjudication.py`, `sheets/key_sample.txt`): (a)
  0/32 wrong, (b) 0/32, (d) true 0/16, (d) counterfactual 3/16 wrong (NZ-d-0517, NZ-d-0472, AU-d-0984, all
  restatements of an own criterion) plus one borderline (NZ-d-0542). The (d)-negative key-error rate is therefore
  about 17-19% (consistent with 17/100 and 19/100 in the two full NZ screens and 14/100 in the AU screen), not the
  6.5% that round 2 reported for that cell.
- Exhaustive check of AU (a) negatives (`02_generation.py` iv): 5 of 47 are outright key errors (metoprolol 50 and
  100 mg, phenytoin 30 and 100 mg, desmopressin 200 mcg are listed on the General Schedule as "Tablet/Capsule
  containing ... "), i.e. at least 10.6%, not the 8.3% sampled; five more differ from a listed item only by tablet vs
  capsule. The cause is `generate.py:36` (`containing` treated as a combination marker), which also removes 272 AU
  single-ingredient tablet/capsule presentations (abiraterone, amitriptyline, bisoprolol, candesartan, ...) from the
  AU universe, biasing which chemicals reach families (a) and (b).

Fix: correct `report.md:105-106` and `:218` ("the AU half checks the generator's parsing of the API, not the API");
report the (d)-negative key-error rate as a semantic near-duplicate rate of roughly one in six, and the AU (a)-negative
rate as at least 10.6%; note the `containing` exclusion as a scope limitation of the AU universe.

### 6. The H1 comparison has an unacknowledged wording and construct asymmetry (Moderate)

Evidence: `run.py:22-23`. The AU (b) question adds "(Authority Required, including Streamlined Authority)"; the NZ
question does not gloss "Special Authority". Streamlined codes make the AU "authority" class broad (3,378 S vs 2,150
A items in GE, `02_generation.py` output), and the AU yes-rate on true-"no" items is higher (68% vs 60%,
`report.md:193-194`). Neither effect can be separated from "knowledge" without a prompt ablation. The report's
limitations section (`report.md:211-229`) does not mention it. It does not change the verdict (Youden's J gives the
same picture), but it is a reason H1 would stay Inconclusive even with a larger sample.

Fix: add a limitation sentence; if a follow-up is run, use parallel wording or a Streamlined/Authority-Required split.

### 7. Report wording: counts, caps and scope (Minor)

- `report.md:46-47` "about a thousand yes/no questions from each country's official funding data" reads as a thousand
  per country; the total is 1,049 (NZ 555, AU 494).
- `report.md:103` "at most 3 per chemical per family": `generate.py:155-166` caps per family x answer, so a chemical
  can carry 6 items in a family; 47 (jurisdiction, family, chemical) cells exceed 3. State the actual rule.
- Family (d) is mostly an oncology test: 66/100 NZ and 70/100 AU counterfactual targets, and 38/100 and 32/100 true
  controls, are in the NZ group A2501 "Chemotherapeutic Agents"; NZ (d) draws on only 54 chemicals and 29 source
  chemicals. H3 should be described as a test on Special Authority criteria dominated by cancer medicines.
- `report.md:141` "Five of the 3,247 calls returned no answer": the error is `json.loads(None)`, i.e. the server
  returned null content; say so.
- Duplicate sentences: 59 criterion sentences are asked about more than one chemical within a jurisdiction
  (`04_misc.py` B); harmless but worth a footnote.

### 8. Provenance housekeeping (Minor)

- `code/figures.py` has an uncommitted diff (F3 figure size, legend placement) and the committed PNGs were produced
  by the working-tree version (figures.py mtime 19:22:21, PNGs 19:22:22). Commit it.
- `D2` (`deviations.md:28-33`) quotes the v1 counts (NZ 100/100, AU 66/66); the final items are NZ 80/80, AU 47/47.
  Add a one-line note that D4's regeneration changed them.
- The NZ SA-inheritance code for ATC ancestors and brands (`generate.py:68-97`) is vacuous on this XML: all 301
  Special/Subsidy rules sit on Chemical (288) or Formulation (13) elements. Not wrong; D1 should not imply it was
  exercised.

## Checks performed against the review prompt

| # | Check | Script | Result |
|---|---|---|---|
| 1 | Fresh key re-adjudication, 96 items, 12 cells x 8 | `06_key_sample.py`, `08_key_readjudication.py` | 3/96 wrong, all (d) negatives (3/16); (a),(b) 0/64 |
| 1 | AU counterfactual screen (all 100) | `05_screen_sheets.py`, `07_screen_compare.py` | 14/100 non-distinct; screened AU rate 28% (19.5-38%) |
| 2 | Blind NZ re-screen (all 100) | same | 98/100 agreement; 19 vs 17 non-distinct; H3 robust (break-even 9) |
| 3 | Generation: reproducibility, caps, ATC2, other programs, vocabulary, wording | `02_generation.py`, `04_misc.py` | (d) non-deterministic; 5/47 AU (a) negatives wrong; 272 AU presentations dropped |
| 4 | Runs: prompts, schema, errors, paraphrase set, circularity, BM25 hit rate | `01_recompute.py`, `03_retrieval.py` | 5 errors = null content; paraphrase set reproduces; own passage hit 39%/26% for (d) negatives; AU (b) misses = BM25 misses |
| 5 | Analysis recomputed from runs.jsonl | `01_recompute.py` | every number reproduces |
| 6 | D5 legitimacy and alternative analyses | timeline, `01`, `07`, `08` | fixed before outputs; verdicts unchanged under pooled, unscreened, Youden's J |
| 7 | Report numbers and claims | all of the above | numbers right; Findings 2-7 are claim corrections |

## In plain terms

The study's three answers are right: this model was not worse on New Zealand questions than on Australian ones, and
it does agree with made-up eligibility rules far more than 20% of the time. But the write-up gets some of the story
wrong. Where it says the Australian answers got worse when the model was given the document, the real reason is that
the search step failed to hand the model the right page for the long oncology entries. Where it says the search
"found the right chemical most of the time", for the made-up-rule questions it usually found the wrong one. The
Australian fabrication figure is too high because those questions were never screened for rules that were really the
drug's own rules in different words. And the 400 rule questions cannot be regenerated from the code because the
sampling order depends on Python's random string hashing, so the item file must be saved with the study. Fix those
and the report can be published with the same verdict line.
