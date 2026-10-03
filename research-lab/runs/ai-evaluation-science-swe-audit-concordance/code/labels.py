"""Build the 500-task label matrix (plan.md section 2) and run the detector on Verified and on the 1,699 OpenAI-
annotated instances. Output: data/labels.parquet, data/detector_verified.parquet, data/detector_annotated.parquet,
data/resolved_matrix.parquet
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detector as D  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"


def run_detector(df, hints=False):
    rows = Parallel(n_jobs=24)(delayed(D.detect)(r, hints) for r in df.to_dict("records"))
    return pd.DataFrame(rows)


def resolved_matrix(ids):
    """Per-submission resolved lists. Most submissions store results/results.json with a 'resolved' list; the
    mini-SWE-agent submissions store per_instance_details.json {instance_id: {"resolved": bool, ...}} instead
    (D1, found in review). Empty files are treated as missing submissions."""
    cols = {}
    for d in sorted((RAW / "experiments" / "evaluation" / "verified").iterdir()):
        res = None
        rj, pj = d / "results" / "results.json", d / "per_instance_details.json"
        if rj.exists():
            r = json.load(open(rj))
            if isinstance(r, dict) and "resolved" in r:
                res = r["resolved"]
        if res is None and pj.exists() and pj.stat().st_size > 2:
            r = json.load(open(pj))
            if isinstance(r, dict) and r:
                res = [k for k, v in r.items() if isinstance(v, dict) and v.get("resolved")]
        if res is not None:
            cols[d.name] = pd.Series(1, index=res).reindex(ids, fill_value=0)
    return pd.DataFrame(cols)


def main():
    v = pd.read_parquet(RAW / "verified" / "data" / "test-00000-of-00001.parquet")
    ids = v.instance_id.tolist()
    lab = pd.DataFrame(index=pd.Index(ids, name="instance_id"))
    o = pd.read_csv(RAW / "openai_annotations" / "ensembled_annotations_public.csv").set_index("instance_id")
    lab["O"] = (o.false_negative.reindex(ids) >= 1).astype(float)
    lab["O_U"] = (o.underspecified.reindex(ids) >= 1).astype(float)
    lab["O_missing"] = o.false_negative.reindex(ids).isna()
    aba = pd.DataFrame(json.load(open(RAW / "aba_benchmark.json"))["tasks"]).set_index("task_id").reindex(ids)
    ev = lambda col, cat: aba[col].map(lambda x: x[cat]["major"] if isinstance(x, dict) else np.nan)  # noqa: E731
    lab["AS"] = (ev("static_findings_by_category", "evaluation") >= 1).astype(float)
    lab["AS_U"] = (ev("static_findings_by_category", "instruction") >= 1).astype(float)
    has_t = aba.has_trajectory_audit.fillna(False).astype(bool)
    lab["AT"] = np.where(has_t, (ev("trajectory_findings_by_category", "evaluation") >= 1).astype(float), np.nan)
    lab["AT_U"] = np.where(has_t, (ev("trajectory_findings_by_category", "instruction") >= 1).astype(float), np.nan)
    det = run_detector(v)
    det.to_parquet(RUN / "data" / "detector_verified.parquet")
    lab["D"] = det.set_index("instance_id").flag.reindex(ids).astype(float)
    lab["D_score"] = det.set_index("instance_id").score.reindex(ids)
    deth = run_detector(v, hints=True)
    lab["D_hints"] = deth.set_index("instance_id").flag.reindex(ids).astype(float)
    rm = resolved_matrix(ids)
    rm.to_parquet(RUN / "data" / "resolved_matrix.parquet")
    top = rm.mean().sort_values(ascending=False).index[:30]
    lab["B"] = (rm[top].sum(axis=1) == 0).astype(float)
    ut = json.load(open(RAW / "UTBoost" / "assets" / "useful_scripts" / "augTest.json"))
    lab["W"] = lab.index.isin(list(ut)).astype(float)
    lab.to_parquet(RUN / "data" / "labels.parquet")
    # detector on the 1,699 annotated instances (validation)
    full = pd.read_parquet(RAW / "full" / "data" / "test-00000-of-00001.parquet")
    ann = full[full.instance_id.isin(o.index)]
    da = run_detector(ann)
    da = da.merge(o[["false_negative"]], left_on="instance_id", right_index=True)
    da.to_parquet(RUN / "data" / "detector_annotated.parquet")
    print("labels built:", lab.shape, "| submissions", rm.shape[1], "| annotated instances run", len(da))


if __name__ == "__main__":
    main()
