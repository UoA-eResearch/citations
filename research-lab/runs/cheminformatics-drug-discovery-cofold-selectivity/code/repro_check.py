"""plan.md §4's reproducibility check, which the run failed to perform: predict one complex twice at the
same seed (the affinity values must be identical) and once at a changed seed (which gives the run-to-run
spread). Writes results/tables/repro.csv.

This matters for reading the sampling arm. That arm's evidence is a correlation of 0.979 between two
sampling settings, and without a same-setting replicate there is no reference for what 0.979 means: it
cannot distinguish "the setting does not matter" from "0.979 is simply the noise floor". The changed-seed
run supplies that reference.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boltzrun as B  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
PAIR = "O00238__10113978"          # first panel pair in name order; nothing about it is special


def one(tag, seed):
    indir = RUN / "data" / f"inputs_repro_{tag}"
    outdir = RUN / "out" / f"repro_{tag}"
    indir.mkdir(parents=True, exist_ok=True)
    shutil.copy(RUN / "data" / "inputs_panel" / f"{PAIR}.yaml", indir / f"{PAIR}.yaml")
    B.run(indir, outdir, seed=seed)
    f = next(outdir.rglob(f"affinity_{PAIR}.json"))
    return json.load(open(f))


def main():
    rows = []
    for tag, seed in (("a", B.SEED), ("b", B.SEED), ("c", B.SEED + 1)):
        r = one(tag, seed)
        rows.append(dict(run=tag, seed=seed, pair_id=PAIR, **r))
        print(tag, seed, r["affinity_pred_value"], flush=True)
    import pandas as pd
    t = pd.DataFrame(rows)
    out = RUN / "results" / "tables" / "repro.csv"
    t.to_csv(out, index=False)
    a, b, c = t.affinity_pred_value.tolist()
    print(f"\nsame seed:    {a!r} vs {b!r}  identical={a == b}")
    print(f"changed seed: {a!r} vs {c!r}  |difference|={abs(a - c):.4f} log units")
    print("wrote", out)


if __name__ == "__main__":
    main()
