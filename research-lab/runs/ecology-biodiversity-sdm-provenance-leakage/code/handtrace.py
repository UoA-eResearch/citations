"""G3 hand trace: refit SAGE's RF for two species (one with a West African source plot, one at random) under C0 and
C1 in a fresh process, bypassing the result cache, and compare AUROC on source cells with the stored results.
-> results/tables/handtrace.json"""
import json
import sys
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import rf  # noqa: E402

rf.load()
rf.G["n_jobs"] = 8
stored = {(json.loads(f.read_text())["sp"], json.loads(f.read_text())["cond"]): json.loads(f.read_text())
          for f in (rf.W / "rf").glob("C*.json")}
tava = sorted(s for (s, c), r in stored.items() if c == "C0" and (r.get("auroc_db") or {}).get("TAVA West_Africa") is not None)
pop = sorted({s for s, _ in stored})
pick = [tava[len(tava) // 2], pop[np.random.default_rng(20261025).integers(len(pop))]]
out = []
for s in pick:
    for cond in ("C0", "C1"):
        f = rf.W / "rf" / f"{cond}_{s}.json"
        keep = f.read_text()
        f.unlink()                                          # bypass the per-condition cache
        caches = list((rf.W / "rf").glob(f"hash_{s}_*.json"))
        saved = {c: c.read_text() for c in caches}
        for c in caches:
            c.unlink()
        try:
            r = rf.fit_one((s, cond))
        finally:
            f.write_text(keep)                              # restore the stored results exactly
            for c, t in saved.items():
                c.write_text(t)
        st = json.loads(keep)
        out.append({"sp": s, "cond": cond, "n_pres_stored": st["n_pres"], "n_pres_refit": r["n_pres"],
                    "auroc_src_stored": st["auroc_src"], "auroc_src_refit": r["auroc_src"]})
        print(out[-1], flush=True)
(RUN / "results" / "tables" / "handtrace.json").write_text(json.dumps(out, indent=1))
