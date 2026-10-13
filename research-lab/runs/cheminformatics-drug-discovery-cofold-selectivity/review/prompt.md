You are an independent, adversarial reviewer of a preregistered study run by an AI research agent. Find what is wrong,
unsupported or overstated before the verdict is published. Do not soften findings.

Study: /mnt/citations/research-lab/runs/cheminformatics-drug-discovery-cofold-selectivity/ (read-only except your
output in review/).

The claim under review: Boltz-2's affinity head, used the way selectivity work wants to use it — hold a ligand fixed,
rank proteins — does or does not track measured binding. The study holds each of 32 kinase inhibitors fixed, asks the
model to rank 32 human kinase domains, and compares with the Davis et al. 2011 Kd panel.

**What to read:**

- plan.md (preregistration, commit c9fa258 — committed before any panel prediction);
- deviations.md (D1-D7);
- report.md (pre-review draft, commit <<DRAFT_COMMIT>>);
- code/: panel.py, validate_data.py, check_smiles.py, build_inputs.py, boltzrun.py, postcutoff.py, shard.py,
  analysis.py, test_analysis.py, assemble.py, secondary.py, geometry.py, figures.py, env_record.py,
  run_all.sh, lane2.sh, lane3.sh, msa_queue.sh;
- results/tables/, results/figures/ and logs/.

**Git.** You may run read-only git commands in /mnt/citations, for example to check that each stage's code was committed
before the outcomes it could affect. The analysis code (analysis.py, assemble.py) and the model-free baseline numbers
were committed before any model prediction existed; check that claim.

**Environment:**

- **Python.** venv/bin/python in the run directory (boltz 2.2.1, torch, rdkit, pandas, numpy, scipy).
- **Data.**
  - The Davis matrix is the DeepDTA release; code/panel.py loads it. 68 ligands x 442 kinase assays, every cell
    measured, Kd in nM, 10 µM = right-censored.
  - The chosen rectangle is data/panel.json; results/tables/panel_kinases.csv and panel_ligands.csv describe it.
  - Per-pair model read-outs are results/predictions.jsonl and results/tables/pairs_<arm>.csv.
  - Boltz outputs are under out/<arm>/boltz_results_inputs_<arm>/predictions/<pair_id>/ (not redistributed, but
    present locally for checking).
  - MSAs are data/msa/<name>.a3m, one per protein, reused across every complex that protein appears in.
- **Limits.**
  - The GPU holds the owner's vLLM container plus whatever remains of this study's runs. **Do not start or stop any
    Docker container.** If you want to re-predict a complex, check free GPU memory first and run one process only.
  - Re-predicting a handful of complexes is affordable (about 34 s each over both passes); re-predicting the panel is
    not.

Check at least:

1. **Timing and disclosure.**
   - Was plan.md committed before any panel prediction? Were the estimators and the baselines committed before the
     outcomes?
   - D1-D7 are the declared departures. Is anything post hoc presented as confirmatory? In particular D3 (geometry.py,
     added after the plan) and the exploratory kinase-geometry analysis.
   - Is anything done but not disclosed? Compare the logs/ directory and the git history against what the report says
     was run. Note deliberately abandoned work: a three-shard decoy run was killed and its 22 complexes deleted (D4,
     D6).
2. **The panel.** Re-derive the rectangle independently from the Davis release and UniProt:
   - the kinase eligibility rules (no parenthesised Davis name, not phospho, exact sequence match to a reviewed human
     entry, exactly one protein-kinase domain of 220-350 aa, one Davis name per accession);
   - the largest-remainder allocation across the eight Manning groups;
   - the ligand rules (RDKit-parseable, single fragment, MW <= 700, >= 8 uncensored cells among the chosen kinases);
   - the crop (kinase domain ± 20 residues) against the UniProt annotation, for at least five kinases;
   - the claim that the rectangle is 72.9 % uncensored against the whole matrix's 30.4 %.
   Does the selection give the model an easier or a harder test than the kinome, and is the report honest about it?
3. **The read-out and the pipeline.**
   - Is `pred = 6 - affinity_pred_value` the right direction and the right scale? Check against Boltz's own
     documentation and source for what `affinity_pred_value` means.
   - Does the YAML construction give the model what it should see (one protein chain, one ligand chain, the right
     `affinity` binder declaration, the cached MSA)? Verify against the installed boltz schema code.
   - Spot-check at least three complexes end to end: YAML in, stored read-out out, row in pairs_panel.csv, cell in the
     matrix used by the analysis.
   - **The collector bug (D7) deserves attention.** It silently collected nothing for three finished arms. Confirm
     the fixed version collects every stored read-out exactly once, that the de-duplication on (arm, pair_id) cannot
     mix the sampling arm's re-predictions with the panel's, and that no read-out was lost or double-counted across
     the two host crashes and the resume.
4. **The statistic.** Recompute, independently of analysis.py, from pairs_panel.csv:
   - P1 (median within-ligand Spearman across kinases, censored cells as ties at 5.0), P2 (uncensored-only), P3
     (within-kinase), P4 (top-1, precision@3), P5 (two-way variance decomposition);
   - the 2000-draw ligand cluster bootstrap interval, and whether the ligand cluster is the right resampling unit;
   - the verdict from plan.md §6, including which branch fires and whether the "protein-blind" clause applies.
   - Check the `rho` convention that returns 0.0 (not nan) when the predictor has no variation. Is it defensible? It
     is what makes the ligand-only baseline exactly 0. Does it flatter or penalise the model anywhere?
   - Check the handling of ties: censored cells are a 27 % block of identical values, so the Spearman is tie-heavy.
     Is the tie correction right, and would a concordance or AUC-style statistic tell a different story?
5. **The baselines.** These carry the argument, so attack them.
   - B1 (target promiscuity, no chemistry) is claimed at 0.386 and B0 (ligand-only) at exactly 0 on the selectivity
     axis; B0 is claimed at 0.489 on the conventional axis. Recompute all four baselines.
   - B1 uses a leave-the-ranked-ligand-out mean, and `base_promiscuity_full` (no leave-one-out) is used only for the
     within-kinase axis because the LOO version correlates -1 there. Is that switch legitimate, or does it flatter the
     baseline on one axis and not the other? Is it disclosed?
   - B2 (nearest chemical neighbour) uses the measured labels of the neighbour, so it is not a model-free baseline in
     the same sense. Is it labelled correctly in the report?
   - Is the report's central comparison — "both preregistered thresholds are weaker than trivial baselines" — fair,
     and does it survive your recomputation?
6. **The secondary arms.**
   - **Decoy** (4 non-kinase proteins x 32 ligands). H4 was restated as a spread comparison (D1, plan §1.2) because
     Koch's target-identification benchmark pre-empts the original framing. Is the restatement honest, and is the
     arm's conclusion limited to what 4 proteins can support? Is HSP90α a fair "non-kinase" control given that it is
     a nucleotide-binding protein?
   - **Promiscuity probe** (8 least-promiscuous kinases x 32 ligands, 5-9 uncensored cells each). With that much
     censoring, is any statistic on it meaningful?
   - **Sampling** (96 pairs re-predicted at 400 affinity sampling steps and 9 diffusion samples). Does it support the
     claim that the result is not a sampling artefact? One setting change is weak evidence; say so if it is.
   - **Post-cutoff** (11 compounds first published >= 2025, 93 pairs, 61 kinases). Check the ChEMBL year query
     actually identifies first publication, not just a document year. Is 93 pairs enough for the claim made from it?
   - **Support gradient.** Is the pre-2024 ChEMBL compound count a sound proxy for training support, and is the
     absence or presence of a gradient interpreted correctly?
   - **Geometry (D3, exploratory).** The Mantel-style comparisons and the near-identical-pair check (CSNK1D/CSNK1E at
     97 % identity) are the strongest evidence about whether the head responds to the protein at all. Check the
     centring, the distance definition, and whether the conclusion drawn is stronger than three correlations on one
     panel can carry.
7. **Threats the plan declared.** Work through plan.md §9 and judge whether each is actually handled in the analysis
   or merely mentioned: censoring, panel selection, the kinase-domain crop, training exposure, assay type, wild-type
   only, failed predictions. The crop is the one most likely to be doing hidden work — if the model is given a
   300-residue domain instead of a full-length protein, how much of any null result is the crop's fault? Is the
   high-confidence recomputation an adequate check?
8. **Numbers.** Does every number in report.md and in the figures match the results files? Check the figures for
   per-ligand and per-kinase ordering bugs (one was found and fixed during the run: string-sorted versus int-sorted
   ligand ids).
9. **Interpretation and scope.**
   - Is the verdict stated with the right scope: one model version, one head, one panel, one axis, cropped inputs?
   - Does the report avoid claiming anything about the conventional axis beyond the one number reported for scale?
   - Use web search to check novelty: in-kinome selectivity evaluation of co-folding affinity prediction, Boltz-2
     affinity audits, Koch et al. target identification, MIRAGE, BoltzOmics. Are those papers' claims stated
     accurately, and is the contribution claim still standing?
10. **Plain-language summary.** Is "## In plain terms" accurate, and does it avoid both overstatement and false
    modesty? It is the part most people will read.

<<RESULTS_SPECIFIC — filled in when the draft is complete: the headline numbers, the verdict branch that fired, and
the two or three claims that most need attacking.>>

Write your review to review/review.md with:

- a recommendation (publish / publish with edits / fix first);
- numbered issues, each with its location and a concrete fix;
- a table of the numbers you recomputed.

Put any scripts you write in review/reviewer_checks/. Reply with the recommendation and the number of issues.
