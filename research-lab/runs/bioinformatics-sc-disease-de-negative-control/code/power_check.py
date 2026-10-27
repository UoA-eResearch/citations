"""G3 synthetic power check (plan section 7): in null draws of 20 random primary contrasts, double the counts of a
random 5% of expressed genes in the pseudo-disease donors, run the identical pipeline, and test the result against
that contrast's own null distribution. A working statistic must call most of them distinguishable.

  power_check.py build   -> data/jobs_power/p_<contrast>_<k>/ (one draw each)
  power_check.py run W   -> DE engine on them
  power_check.py report  -> results/tables/power_check.json
"""
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
META, JOBS, PJ, T = RUN / "data" / "meta", RUN / "data" / "jobs", RUN / "data" / "jobs_power", RUN / "results" / "tables"
SEED, N_CONTRASTS, PER, R_REAL = 20261027, 20, 5, 25


def build():
    ci = pd.read_csv(META / "contrast_index.csv")
    prim = ci[ci.primary & (ci.m >= 8)].contrast.tolist()
    rng = np.random.default_rng([SEED, 7])
    pick = sorted(rng.choice(prim, N_CONTRASTS, replace=False))
    for c in pick:
        src = JOBS / c
        meta = pd.read_csv(src / "meta.csv")
        x = np.fromfile(src / "counts.f32", np.float32).reshape(meta.ndonors[0], meta.ngenes[0])   # donors x genes
        draws = pd.read_csv(src / "draws.csv")
        for k in range(PER):
            d = draws[draws.id == 1 + R_REAL + k].iloc[0]
            a = np.array([int(v) for v in d.a.split(";")])
            expressed = np.flatnonzero(x.mean(0) >= 1)
            g = np.random.default_rng([SEED, int(c[1:]), k]).choice(expressed, max(1, int(0.05 * len(expressed))), replace=False)
            y = x.copy()
            y[np.ix_(a, g)] *= 2
            jd = PJ / f"p_{c}_{k}"
            jd.mkdir(parents=True, exist_ok=True)
            y.tofile(jd / "counts.f32")
            for f in ("meta.csv", "donors.csv", "genes.txt"):
                shutil.copy(src / f, jd / f)
            pd.DataFrame([{"id": 0, "kind": "real", "a": d.a, "b": d.b, "save": 0}]).to_csv(jd / "draws.csv", index=False)
    print(len(pick), "contrasts x", PER)


def run(workers):
    jobs = sorted(p.name for p in PJ.iterdir() if p.is_dir() and not (p / "stats.csv").exists())
    lists = [jobs[k::workers] for k in range(workers)]
    def go(k):
        (PJ / f"_list{k}.txt").write_text("\n".join(f"/jobs/{j}" for j in lists[k]) + "\n")
        return subprocess.run(["docker", "run", "--rm", "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp",
                               "-v", f"{PJ}:/jobs", "-v", f"{RUN / 'code'}:/code:ro", "sc-negctl-de:1",
                               "Rscript", "/code/de.R", f"/jobs/_list{k}.txt"], stderr=open(RUN / "logs" / f"de_worker{k}.err", "w")).returncode
    with ThreadPoolExecutor(workers) as ex:
        print(list(ex.map(go, [k for k in range(workers) if lists[k]])))


def report():
    rows = []
    for jd in sorted(PJ.glob("p_*")):
        _, c, k = jd.name.split("_")
        st = pd.read_csv(jd / "stats.csv", keep_default_na=False, na_values=["NA"]).iloc[0]
        null = pd.read_csv(JOBS / c / "stats.csv", keep_default_na=False, na_values=["NA"])   # "null" is a draw kind
        null = null[(null.kind == "null") & null.ok.astype(bool)]
        p = (1 + int((null.pi1 >= st.pi1).sum())) / (len(null) + 1)
        rows.append({"contrast": c, "k": int(k), "pi1_injected": st.pi1, "pi1_null_median": float(null.pi1.median()), "p": p})
    df = pd.DataFrame(rows)
    out = {"draws": int(len(df)), "share_p_below_0_05": round(float((df.p < 0.05).mean()), 3),
           "median_pi1_injected": round(float(df.pi1_injected.median()), 4), "median_pi1_null": round(float(df.pi1_null_median.median()), 4)}
    (T / "power_check.json").write_text(json.dumps(out, indent=1))
    df.to_csv(T / "power_check.csv", index=False)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"build": build, "report": report}.get(sys.argv[1], lambda: run(int(sys.argv[2])))()
