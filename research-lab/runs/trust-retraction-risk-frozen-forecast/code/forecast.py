"""H3: the sealed forward forecast (plan section 5; D1).

The primary pipeline is refitted on information known by 2024-12-31 -- articles from 2018-2019 and 2021-2022 (2020 was
never extracted, D1), labels with a retraction year <= 2024 -- and scores every 2025-2026 cohort article. The score
file stays in data/forecast/ and is never published; only its SHA-256, the model's SHA-256 and aggregate counts are
committed (results/tables/forecast_seal.json). Scoring date: 2028-12-31, against the registry then.
"""
import hashlib
import json
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as M  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "forecast"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tr = pd.concat([M.load((2018, 2019)), M.load((2021, 2022))], ignore_index=True)
    fmap = M.field_codes(tr)
    tr = M.prep(tr, fmap)
    y = ((tr.ret > 0) & (tr.ret <= 2024)).to_numpy()
    rng = np.random.default_rng(M.SEED)
    keep = y | (rng.random(len(tr)) < M.NEG_SHARE)
    m = M.hgb(M.SETS["full"])
    m.fit(tr[keep][M.SETS["full"]], y[keep], sample_weight=np.where(y, 1.0, 1.0 / M.NEG_SHARE)[keep])
    mp = OUT / "forward_model.pkl"
    pickle.dump({"model": m, "cols": M.SETS["full"], "fmap": fmap}, open(mp, "wb"))
    fw = M.load((2025, 2026))
    s = m.predict_proba(M.prep(fw, fmap)[M.SETS["full"]])[:, 1]
    sp = OUT / "forward_scores.parquet"
    pd.DataFrame({"wid": fw.wid.to_numpy(), "year": fw.year.to_numpy(), "score": s}).to_parquet(sp, index=False)
    n1 = int(round(0.01 * len(s)))
    seal = {"sealed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "score_file_sha256": hashlib.sha256(sp.read_bytes()).hexdigest(),
            "model_file_sha256": hashlib.sha256(mp.read_bytes()).hexdigest(),
            "train_articles": int(len(tr)), "train_positive": int(y.sum()), "iterations": int(m.n_iter_),
            "forward_articles": int(len(s)), "forward_by_year": {str(k): int(v) for k, v in fw.year.value_counts().items()},
            "top_1pct_size": n1, "top_1pct_threshold": float(np.sort(s)[::-1][n1 - 1]),
            "forward_retracted_already_at_seal": int((fw.ret > 0).sum()),
            "rule": "H3: E@1% >= 3 against the retraction registry on 2028-12-31, publisher-clustered bootstrap as H1",
            "note": "the per-article score file is never published; only these hashes and aggregates"}
    json.dump(seal, open(RUN / "results" / "tables" / "forecast_seal.json", "w"), indent=1)
    print(json.dumps(seal, indent=1))


if __name__ == "__main__":
    main()
