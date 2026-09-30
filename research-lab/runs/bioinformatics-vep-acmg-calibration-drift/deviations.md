# Deviations log: ACMG PP3/BP4 calibration-drift deep dive

Every departure from `plan.md`, with a timestamp (NZDT). Newest last.

### D1. Preregistration timing (2026-10-01 00:15)
`plan.md` says "written ~00:25"; git records the commit at 2026-10-01 00:15:05 +1300 (8fb806b; originally b5208b5 before the author rewrite of 2026-10-01). The commit time is
authoritative. No predictor score had been joined to a ClinVar label before it.

### D2. Download orchestration (2026-10-01 00:17-00:30)
`code/fetch_data.sh` downloads the ClinVar snapshots in parallel and then AlphaMissense. At about 1 MB/s it was
stopped after launching the ClinVar transfers (they continued to completion), and the AlphaMissense hg38 file
(Zenodo 8208688, 642,961,469 bytes) was fetched in parallel instead. No change to any input.

### D3. Order of analyses: H3's descriptive recount ran first (2026-10-01 00:23)
`code/h3_vcep.py` needs only the ClinGen export, so it ran while the ClinVar files downloaded. Its first outputs
(recount agreement and the tool-dependent fraction by approval year) were therefore seen before H1/H2/H4. None of
the H1/H2/H4 definitions changed afterwards. The H3 likelihood-ratio part (tool-independent vs all VCEP labels)
had not been computed.
- Recount agreement with the published assertion: 99.3% at the P/VUS/B group level, 97.1% exact (9,278 confident
  VCEP classifications; no unparsed codes).
- Tool-dependent fraction by approval year: 0-6% up to 2020; 11-16% (pathogenic) and 14-31% (benign) in 2023-2026.
  This covers all variant types; missense restriction and confidence intervals follow in the H3 analysis.

### D4. Data-fetch mechanics (2026-10-01 00:25-00:32)
- The MyVariant fetch keys its cache by variant (not batch position) and runs three concurrent requests
  (sequential batches took ~45 s each). It was started early on every confident variant of the four snapshots parsed
  so far (`--from-status`, 98,974 variants); the remaining snapshots add only their new variants.
- The first AlphaMissense transfer was cut by Zenodo after 22 MB (curl error 18); `code/fetch_am.sh` resumes it
  until the file size equals the published 642,961,469 bytes.
- A `pkill -f` pattern matched its own shell command line and killed it (a known pitfall); no data were affected.

### D5. AlphaMissense source: Google Cloud mirror of the same file (2026-10-01 00:32)
Zenodo throttled the transfer to ~3 MB/min. The identical file was taken from DeepMind's public bucket
(storage.googleapis.com/dm_alphamissense/AlphaMissense_hg38.tsv.gz): same size (642,961,469 bytes) and the MD5
recorded by Zenodo (9fd167735f16a1b87da6eb3e4c25fcb5) verified with `md5sum -c`.

Note on timestamps: the times in D2-D4 were first written as estimates and later corrected from the system clock and
file modification times (the H3 recount output is stamped 00:23:54, after the 00:15:05 preregistration commit).

### D6. Exploratory analyses added after the primary results (2026-10-01 01:10-01:13)
Not preregistered; labelled exploratory everywhere they appear.
- `code/explore_year_strata.py`: pooled strongest-interval LRs by cohort year x review stratum (1-star vs >= 2-star;
  VCEP vs other genes), to locate the post-2022 rise found under H2.
- Composition of newly classified benign / pathogenic labels by year x stratum (median score; share in the
  strongest intervals), to identify which class drives the rise.
- ClinVar `submission_summary` (current release, 2026-09-28): which submitters account for the post-2022
  single-submitter benign surge, and how often their submissions cite BP4 / PP3.

### D7. Reproduction gate outcome (2026-10-01 01:08-01:10)
First run: the pathogenic-side re-derivation returned NaN because bootstrap windows with no benign variants give an
infinite LR and percentile interpolation turned inf - inf into NaN; the same inf values had been dropped from the
interval-LR bootstrap bounds. Fixed in `code/calib.py` (infinite LRs kept as 1e12 so percentiles stay order
statistics); every table was regenerated. Re-derived vs published thresholds on C2019 (REVEL / AlphaMissense):
PP3 +1 0.763 / 0.797 (published 0.644 / 0.792), +2 0.872 / 0.959 (0.773 / 0.906), +3 0.931 / 0.998 (0.879 / 0.972),
+4 0.992 / 0.999 (0.932 / 0.990); BP4 -1 0.344 / 0.178 (0.290 / 0.169), -2 0.197 / 0.096 (0.183 / 0.099),
-3 0.049 / 0.055 (0.052 / 0.070), -4 (REVEL) 0.019 (0.016). The preregistered gate (REVEL PP3 Strong and BP4
Moderate within 0.1) passes: 0.060 and 0.014. The pathogenic side re-derives stricter, plausibly because the
nearest-100 window omits Pejaver's gnomAD window term and training-variant removal was not reproduced.

### D8. Independent adversarial review and response (review 2026-10-01 01:20-01:36; response from 01:36)
Fable 5.1 subagent; scratch code /home/ubuntu/.claude/jobs/14121cdb/tmp/review_acmg/ (outside the repo). Verdict:
fix-first -- numbers and code sound, the interpretation of H2/H3 overreached and two preregistered unfavourable
results were omitted from the draft report. All points accepted:
- (a)-(c) CONFIRMED: cohort construction (format changes, conflict wordings, the 2023/2025 waves are genuine new
  VariationIDs), interval assignment and verdict logic, score handling (max-over-transcripts does not inflate; AF
  missingness does not explain the benign wave). Low: 1,937 N_new variants had been confident in C2019/N_2020 and
  re-entered after a non-confident interlude; excluding them changes nothing (`code/explore_robustness.py`).
- (d) HIGH, ACCEPTED and reproduced (`code/explore_gene_standardised.py`): the preregistered H2 rise is mostly a
  change in which genes are newly classified. 54% of post-window benign labels are in genes with no pre-window
  benign label (large missense-tolerant genes: WNK2, SPTBN5, ABCA13, FSIP2, MUC17 ...), and benign labels in the >= +3
  interval are flat (171 -> 225) while benign labels quadruple (15,532 -> 62,034). Standardised to the pre-window gene
  composition: REVEL x1.29 [log 0.00, 0.51] (raw x3.16), AlphaMissense x0.81 [0.66, 0.99] (a slight decline), ESM1b
  x0.88 (n.s.); genes present in both windows: REVEL x1.70, AlphaMissense x0.86, ESM1b x0.88. The raw H2 result
  stands as preregistered; its reading changes from "labels bent towards the tools" to "case-mix drift, with at most a
  small within-gene rise for REVEL". The exploratory BP4 narrative of the draft (sec 4.5) is withdrawn.
- (e) MEDIUM, ACCEPTED: the H3 rise in tool-dependence reflects rule changes as much as behaviour -- PM2 moved from
  Moderate (79-92% of uses, 2018-20) to Supporting (89-92%, 2023-26) after the 2020 SVI recommendation, and PP3 at
  Moderate/Strong rose from 0-6% to 12-28% after the 2022 calibration; PP3 use itself is flat (77-86%). Also accepted:
  the preregistered per-interval results on VCEP labels (h3_lr.csv) were missing from the draft -- BayesDel +1
  (1.25 [0.96, 1.73]) and +2 (3.99 [3.01, 5.66]) FALL SHORT; REVEL +1/+2/+4 and AlphaMissense +2 are inconclusive.
- (f) CONFIRMED: REVEL +1 in VCEP genes 1.83 is not driven by one gene (leave-one-gene-out 1.70-2.14); benign
  variants in VCEP genes score higher (median REVEL 0.29 vs 0.10).
- (g) wording and small numbers corrected: coverage 90-100%; pathogenic medians 0.85-0.89; per-year exceptions
  (CADD -1 falls short in N_2025; AlphaMissense +3/+4 inconclusive in N_2022) reported; "most by a wide margin"
  replaced by boundary-slice and 2021-22 results (all meet: e.g. REVEL [0.932, 0.950) LR 124, 2021-22 REVEL +4 83
  [63, 118]); "by construction" and "circularity inflates by <10%" reworded; the gate described as "within the
  preregistered tolerance"; the REVEL training-set (HGMD) caveat extended to the prospective cohort.
- (h) the headline is revised: thresholds hold on ClinVar at large (robust), but not demonstrably in the
  expert-panel disease genes where labels are cleanest; the rise over time is mainly case-mix drift.

### D9. Submitter analysis and the single-laboratory bulk wave (exploratory; 2026-10-01 01:45-01:55)
ClinVar `submission_summary` (release of 2026-09-28; 394,172,714 bytes). The header detection first matched the
column-description comment block ("#VariationID:"); fixed to the tab-separated header line.
- `code/explore_submitters.py`: of 98,906 single-submitter benign submissions (SCVs) for rare missense variants newly
  classified in 2023-2026, Ambry Genetics made 59,178 (60%; 58,919 likely benign), Labcorp/Invitae 25,620 (26%), CeGaT
  6,798 (7%). Ambry's have median REVEL 0.057 and 74% are in genes with no 2021-22 benign label. Their rationale is a
  fixed template listing every evidence type ("... population frequency, ..., in silico models, amino acid
  conservation, ..."), so whether predictors were decisive cannot be read from ClinVar; the "cites computational
  evidence" count is uninformative for them. CeGaT's texts cite BP4 explicitly in 66%. Ambry's DateLastEvaluated
  spans 2021-2026 (a backlog released over several years).
- `code/explore_without_bulk.py`: excluding variants whose only ClinVar submitter is Ambry Genetics removes the
  post-2022 rise entirely: pooled >= +3 LR 2023-2026 REVEL 49 / 51 / 70 / 41 (all: 85 / 90 / 286 / 95), AlphaMissense
  34 / 29 / 24 / 19 (all: 61 / 52 / 94 / 44), ESM1b 23 / 20 / 19 / 19 -- flat for REVEL and declining for
  AlphaMissense and ESM1b relative to 2019-2021. H1 without the bulk: all intervals still meet on N_new except
  AlphaMissense +3 (15.5 [13.7, 17.6], inconclusive); on 2024-2026 alone AlphaMissense +3 (13.4 [11.4, 16.0]) and
  +4 (38.2 [32.0, 46.1]) are inconclusive, REVEL meets throughout.
Reading: H2's preregistered rise is real in ClinVar but is produced by one laboratory's bulk benign submissions in
previously unlabelled genes, not by labels bending towards the predictors. Naming the laboratory states a fact of
the public record; nothing here suggests its classifications are wrong.
