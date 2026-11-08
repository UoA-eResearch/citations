Confirmation pass for ecology-biodiversity-sdm-provenance-leakage (/mnt/citations/research-lab/runs/ecology-biodiversity-sdm-provenance-leakage).
The first review (review/review.md, do not publish: re-run with corrected provenance flags; 5 findings) is addressed by
the re-run in deviations.md D4. Check it and give a final verdict (publish / publish with edits / fix first / do not
publish); append a "## Confirmation pass" section to review/review.md. Same rules as before (write only under review/,
no ~/.config, no pip installs, <= 4 processes, no GPU, no refits, data/ untrusted).

Where each finding went:
1. Missed republications: code/republication_scan.py (adapted from your check; rule: >= 20 single-plot dated cells
   with recall >= 0.8 and precision >= 0.5) flags exactly NSW BioNet, SA Flora and the Danish Naturdatabase
   (results/tables/republication_flags_added.csv). Amended provenance_flags.csv (frozen list kept as
   provenance_flags_frozen.csv). Full re-run: records/support/audit/removals/fits (2,000 species sampled from 2,833,
   per the plan's cap). H2 16.6% (16.0-17.2%) Supported; H1 DiD -0.006 (-0.009 to -0.004) Refuted; matched-removal
   species (random >= 90% of C1, 1,656) +0.001 (-0.001 to +0.003). Frozen results beside them (frozen_flags_*).
2. Broad tier: source cells from core and broad sources in the sensitivity: 15.6% (15.1-16.2%).
3. Neutral counterfactual: rf.py fit_neutral (C1n-C6n) for 382 TAVA + Ukrainian species: TAVA +0.118 (0.086-0.150)
   vs standard +0.128; Ukraine +0.052 vs +0.050 (results/tables/posthoc_neutral.json).
4. SOPHY: the scan finds no republishing dataset (stated); Slovakia's PLADIAS.SK 6 of 628 is below the rule.
5. Post hoc checks re-run under the corrected flags (shortfall, h2_training, same_releve, distance).
Note: Australia's DiD is -0.025 because the random arm removed only 47% as many records there; the report calls
this a control artefact. G5 passes (46 rows), G6 passes.

Reply with the verdict and a one-line note per remaining issue, if any.
