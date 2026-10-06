"""Draw the direct-verification sample (audit/deviations.md A10) reproducibly: 7 substantive numbers per report,
seed 20261006 + 7, from the reports as they stood when the sample was drawn (git commit 90930ab, before the
corrections the audit later made). Writes audit/D_verify_sample.csv; with --check, compares with the committed file."""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from snapshot import REPORTED, RUNS_ALL  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_numbers import report_numbers  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "research-lab" / "paper" / "audit"
COMMIT = "90930ab"


def draw():
    runs = sorted(REPORTED)
    rows = []
    for run in runs:
        text = subprocess.check_output(["git", "show", f"{COMMIT}:research-lab/runs/{run}/report.md"], cwd=REPO, text=True)
        for n in report_numbers(text):
            rows.append(dict(run=run, token=n["token"], substantive=n["substantive"],
                             context=text[max(0, n["start"] - 110):n["start"] + 60].replace("\n", " ")))
    a = pd.DataFrame(rows)
    a = a[a.substantive]
    rng = np.random.default_rng(20261006 + 7)
    out = []
    for run, g in a.groupby("run"):
        take = g.iloc[rng.choice(len(g), min(7, len(g)), replace=False)]
        for _, r in take.iterrows():
            out.append(dict(verify_id=f"V{len(out) + 1:03d}", run=run, token=r.token, context=r.context))
    return pd.DataFrame(out)


if __name__ == "__main__":
    d = draw()
    if "--check" in sys.argv:
        c = pd.read_csv(OUT / "D_verify_sample.csv")
        same = len(c) == len(d) and (c[["verify_id", "run", "token"]].astype(str).values == d[["verify_id", "run", "token"]].astype(str).values).all()
        print("reproduces committed sample:", bool(same), "|", len(d), "rows")
    else:
        d.to_csv(OUT / "D_verify_sample.csv", index=False)
        print(len(d), "rows written")
