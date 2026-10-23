You are the independent reviewer of /mnt/citations/research-lab/runs/auckland-nz-kauri-dieback-multitemporal-lidar/,
doing the CONFIRMATION PASS. Your review is review/review.md ("fix first", 9 findings), and your scripts are in
review/reviewer_checks/. The fixes are logged as D1 (see git log).
- features.py does a single-linkage 2 m merge (6,871 / 222 / 77).
- model.py computes the per-fold AUC with a within-block shuffle null (200 shuffles).
- report.md is rewritten.

The new results:
- H1 Refuted: 0.55 (0.47–0.58), against a place null of 0.48 / 0.52.
- H2 Refuted: gain +0.021 (−0.034 to +0.045).
- 2021: 0.557 against a place null of 0.539 / 0.560.

Be economical. Check that:
- each finding is addressed;
- the per-fold estimator and the null are implemented correctly, and the bootstrap of fixed predictions is described
  honestly;
- the report's numbers match primary.json;
- the label-geometry and the height-dependent-rise statements are fair;
- no coordinates are published.

Write review/confirmation.md: a verdict (publish / publish with edits / fix first), one line per finding, then any new
issues. Reply with the verdict line and the new issues only.
