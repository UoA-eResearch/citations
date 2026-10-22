"""Post hoc (D2, after the test results were read): enrichment among test articles with complete metadata only
(at least one reference, at least one author, a first-author country), for every frozen model. Checks whether the
skill is only metadata completeness (well-deposited records are the ones retracted). Exploratory; no verdict changes."""
import json
import pickle
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M  # noqa: E402

test = M.load(M.TEST)
keep = ((test.n_refs > 0) & (test.nauth > 0) & (test.country1 != "")).to_numpy()
t = test[keep].reset_index(drop=True)
y = (t.ret > 0).to_numpy().astype(float)
out = {"complete_articles": int(keep.sum()), "share_of_test": round(float(keep.mean()), 4),
       "retracted": int(y.sum()), "base_rate": round(float(y.mean()), 6), "models": {}}
hashes = json.load(open(M.T / "model_hashes.json"))
for name in hashes["models"]:
    assert M.sha(M.MD / name) == hashes["models"][name]["sha256"]
    s = M.predict(pickle.load(open(M.MD / name, "rb")), t)
    e, _ = M.enrichment(s, y, 0.01)
    out["models"][name] = {"E@0.01": round(float(e), 3), "ci": M.boot(s, y, M.clusters_of(t), 0.01)}
    print(name, out["models"][name], flush=True)
json.dump(out, open(M.T / "posthoc_complete_metadata.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "models"}))
