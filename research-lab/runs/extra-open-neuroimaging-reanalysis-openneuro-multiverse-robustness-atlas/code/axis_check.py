"""G3 invariant added after the review (D11): configurations that differ on an axis must give different maps.

For every dataset, the first three subjects' stored maps: for each axis (smoothing, HRF, confounds, noise model),
every pair of nilearn configurations that differ only on that axis is compared; a pair is "identical" if the two
float16 maps are equal wherever finite. An axis is void for a dataset if all its pairs are identical in all three
subjects. 6P and 6P + spikes are identical by design for runs without a volume above 0.5 mm FD, so a few identical
confound pairs are expected; a void axis is not.

  axis_check.py -> results/tables/axis_check.json
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import firstlevel as F  # noqa: E402

AXES = {"smoothing": 0, "hrf": 1, "confounds": 2, "noise": 3}
LEVELS = (3, 2, 4, 2)


def pairs(axis):
    out = []
    for combo in itertools.product(*[range(n) for n in LEVELS]):
        if combo[axis] != 0:
            continue
        for lv in range(1, LEVELS[axis]):
            other = list(combo)
            other[axis] = lv
            out.append((F.cfg_index(0, *combo), F.cfg_index(0, *other)))
    return out


def main():
    res = {}
    for d in sorted(p for p in F.OUT.iterdir() if p.is_dir() and p.name.startswith("ds")):
        files = sorted(d.glob("sub-*.npz"))[:3]
        if not files:
            continue
        E = [np.load(f)["eff"][:48].astype(np.float32) for f in files]
        ds_res = {}
        for name, ax in AXES.items():
            ident = total = 0
            for a, b in pairs(ax):
                for e in E:
                    m = np.isfinite(e[a]) & np.isfinite(e[b])
                    total += 1
                    ident += int(np.array_equal(e[a][m], e[b][m]))
            ds_res[name] = {"identical_pairs": ident, "pairs": total, "void": ident == total}
        res[d.name] = ds_res
    void = {ds: [a for a, v in r.items() if v["void"]] for ds, r in res.items() if any(v["void"] for v in r.values())}
    out = {"void_axes": void, "per_dataset": res}
    (RUN / "results" / "tables" / "axis_check.json").write_text(json.dumps(out, indent=1) + "\n")
    print("void axes:", void or "none")


if __name__ == "__main__":
    main()
