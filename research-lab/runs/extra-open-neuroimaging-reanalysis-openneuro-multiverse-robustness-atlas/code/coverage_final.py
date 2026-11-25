"""G2: subject-, run- and arm-level coverage after the first level, added to results/tables/coverage.json.

Counts come from results/tables/firstlevel_log.csv (the last entry per subject; earlier entries are reruns after
D5-D9), the subject maps in /mnt/data/omv/out and results/tables/atlas.csv.

  coverage_final.py   (then: python3 -I ../../tools/coverage.py RUN_DIR)
"""
import ast
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN.parents[1] / "tools"))
sys.path.insert(0, str(RUN / "code"))
from coverage import Coverage  # noqa: E402
import driver  # noqa: E402

log = pd.read_csv(RUN / "results" / "tables" / "firstlevel_log.csv", dtype=str, keep_default_na=False)
# the first log rows (14 November) wrote some subject labels without their leading zero ("6" for "06"):
# map every label to the spec's spelling before taking the last entry per subject
from firstlevel import spec_for  # noqa: E402
_spec = {ds: [str(x) for x in spec_for(ds)[0]["Input"]["subject"]] for ds in log.ds.unique()}
log["sub"] = [s if s in _spec[d] else next((x for x in _spec[d] if x.lstrip("0") == s.lstrip("0")), s)
              for d, s in zip(log.ds, log["sub"])]
last = log.drop_duplicates(["ds", "sub"], keep="last")

# subjects: the seeded first 100 of each eligible dataset's spec list
cov = Coverage("subjects", RUN / "results" / "tables" / "coverage.json")
st = Counter(last.status)
drops = Counter()
for r in last[last.status == "no usable run"].itertuples():
    reasons = ast.literal_eval(r.runs_dropped) if r.runs_dropped else ["no run with BOLD, confounds and events"]
    drops["no usable run: " + "; ".join(sorted(set(reasons)))] += 1
cov.add_counts(ok=st["ok"], drops=dict(drops))
if st.get("failed"):
    cov.add_counts(drops={"failed": st["failed"]})
cov.save()

# runs within analysed subjects: used, and dropped by the D6/D8 usability rules
cov = Coverage("runs", RUN / "results" / "tables" / "coverage.json")
used, rdrops = 0, Counter()
for f in sorted((driver.F.OUT).glob("ds*/sub-*.npz")):
    meta = json.loads(str(np.load(f)["meta"]))
    for m in meta:
        if m.get("status") == "ok":
            used += 1
        else:   # "no design" = a run outside the spec's Input.run list (D11 wording), not a failed design
            st = m.get("status", "unknown")
            rdrops["outside the spec's run list" if st == "no design" else st] += 1
cov.add_counts(ok=used, drops=dict(rdrops))
cov.save()

# FSL arm (D3): the first 20 subjects of each dataset's seeded order; ds003397 skipped (D9)
cov = Coverage("fsl_arm_subjects", RUN / "results" / "tables" / "coverage.json")
ok = skipped = missing = 0
for r in last[last.status == "ok"].itertuples():
    from firstlevel import spec_for
    import random
    subs = list(spec_for(r.ds)[0]["Input"]["subject"])
    order = [str(s) for s in random.Random(driver.SEED).sample(subs, len(subs))]
    if order.index(str(r.sub)) >= driver.FSL_N:
        continue
    e = np.load(driver.F.OUT / r.ds / f"sub-{r.sub}.npz")["eff"]
    has = all(np.isfinite(e[k].astype(np.float32)).any() for k in driver.FSLK)
    if r.ds in driver.FSL_SKIP and not has:     # D11: by the maps, not the log flag (the D11 rerun logs fsl=False;
        skipped += 1                            # ds003397 sub-05 and sub-11 kept their FSL maps from before D9)
        continue
    if has:
        ok += 1
    else:
        missing += 1
cov.add_counts(ok=ok, drops={"skipped for ds003397 (D9)": skipped, **({"no FSL maps": missing} if missing else {})})
cov.save()

# robustness index per dataset: defined unless no configuration has a suprathreshold voxel
cov = Coverage("robustness_index", RUN / "results" / "tables" / "coverage.json")
atlas = pd.read_csv(RUN / "results" / "tables" / "atlas.csv")
undefined = int(atlas.R.isna().sum())
cov.add_counts(ok=int(atlas.R.notna().sum()),
               drops={"R undefined: no suprathreshold voxel in any configuration (all pairs empty)": undefined})
cov.save()
