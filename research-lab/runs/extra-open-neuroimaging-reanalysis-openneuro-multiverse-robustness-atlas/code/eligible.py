"""Dataset eligibility (plan section 0). Metadata only: no image or time series is read.

For every dataset with a spec in demidenm/openneuro_glmfitlins/statsmodel_specs: the first task (alphabetically) with
a spec, the spec's subject list, the first run-level contrast, and whether the fMRIPrep derivatives
(s3://openneuro-derivatives/fmriprep/<ds>-fmriprep/) hold MNI152NLin2009cAsym res-2 preprocessed BOLD and confounds
for that task, and the raw dataset (s3://openneuro.org/<ds>/) holds events files for it.

  eligible.py -> data/specs/<ds>/..., results/tables/eligible.csv, results/tables/coverage.json (stage "datasets")
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN.parents[1] / "tools"))
from coverage import Coverage  # noqa: E402

UA = {"User-Agent": "research-lab openneuro-multiverse study (open-data research; github.com/UoA-eResearch/citations)"}
REPO, REF = "demidenm/openneuro_glmfitlins", "main"
DERIV, RAW = "https://openneuro-derivatives.s3.amazonaws.com", "https://s3.amazonaws.com/openneuro.org"


def get(url, tries=4):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read()
        except Exception:
            time.sleep(5 * (k + 1))
    return None


def s3_keys(base, prefix, delimiter=None, limit=None):
    keys, prefixes, token = [], [], None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if delimiter:
            q["delimiter"] = delimiter
        if token:
            q["continuation-token"] = token
        t = (get(f"{base}/?{urllib.parse.urlencode(q)}") or b"").decode()
        keys += re.findall(r"<Key>([^<]+)</Key>", t)
        prefixes += re.findall(r"<Prefix>([^<]+)</Prefix>", t)[1:] if delimiter else []
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", t)
        if not m or (limit and len(keys) >= limit):
            return keys, prefixes
        token = m.group(1)


def main():
    (D / "specs").mkdir(parents=True, exist_ok=True)
    T.mkdir(parents=True, exist_ok=True)
    tree = json.loads(get(f"https://api.github.com/repos/{REPO}/git/trees/{REF}?recursive=1"))
    sha = json.loads(get(f"https://api.github.com/repos/{REPO}/commits/{REF}"))["sha"]
    paths = [x["path"] for x in tree["tree"] if x["path"].startswith("statsmodel_specs/") and x["path"].endswith("_specs.json")]
    by_ds = {}
    for p in paths:
        ds = p.split("/")[1]
        m = re.match(rf"{ds}-(.+)_specs\.json$", p.split("/")[-1])
        if m:
            by_ds.setdefault(ds, []).append((m.group(1), p))
    rows = []
    for ds in sorted(by_ds):
        task, path = sorted(by_ds[ds])[0]
        raw = get(f"https://raw.githubusercontent.com/{REPO}/{sha}/{path}")
        row = {"ds": ds, "task": task, "spec_path": path, "repo_sha": sha}
        if raw is None:
            rows.append({**row, "status": "spec not downloadable"}); continue
        (D / "specs" / ds).mkdir(exist_ok=True)
        (D / "specs" / ds / Path(path).name).write_bytes(raw)
        spec = json.loads(raw)
        subs = spec.get("Input", {}).get("subject", [])
        run_node = next((n for n in spec.get("Nodes", []) if n.get("Level", "").lower() == "run"), None)
        con = (run_node or {}).get("Contrasts", [])
        row.update({"n_spec_subjects": len(subs), "n_run_contrasts": len(con),
                    "contrast": con[0]["Name"] if con else None,
                    "contrast_conditions": json.dumps(con[0].get("ConditionList")) if con else None,
                    "contrast_weights": json.dumps(con[0].get("Weights")) if con else None,
                    "contrast_test": con[0].get("Test") if con else None})
        # fMRIPrep derivatives: first spec subject's func folder
        s0 = subs[0] if subs else None
        keys, _ = s3_keys(DERIV, f"fmriprep/{ds}-fmriprep/sub-{s0}/") if s0 else ([], [])
        tk = [k for k in keys if f"_task-{task}_" in k]
        row["has_mni_res2"] = any("space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz" in k for k in tk)
        row["has_confounds"] = any(k.endswith("desc-confounds_timeseries.tsv") for k in tk)
        row["has_mask"] = any("space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz" in k for k in tk)
        # raw events: per-subject or top-level
        rk, _ = s3_keys(RAW, f"{ds}/sub-{s0}/") if s0 else ([], [])
        ev = [k for k in rk if f"_task-{task}_" in k and k.endswith("_events.tsv")]
        top, _ = s3_keys(RAW, f"{ds}/task-{task}_events.tsv")
        row["has_events"] = bool(ev or top)
        ok = row["has_mni_res2"] and row["has_confounds"] and row["has_mask"] and row["has_events"] and bool(con)
        row["status"] = "eligible" if ok and len(subs) >= 10 else (
            "fewer than 10 spec subjects" if ok else "missing: " + ", ".join(
                k for k, v in [("MNI res-2 BOLD", row["has_mni_res2"]), ("confounds", row["has_confounds"]),
                               ("mask", row["has_mask"]), ("events", row["has_events"]), ("run contrast", bool(con))] if not v))
        rows.append(row)
        print(ds, task, len(subs), row["status"], flush=True)
    E = pd.DataFrame(rows)
    E.to_csv(T / "eligible.csv", index=False)
    c = Coverage("datasets", T / "coverage.json")
    c.add_counts(ok=int((E.status == "eligible").sum()), drops=E[E.status != "eligible"].status.value_counts().to_dict())
    c.save()
    print(E.status.value_counts().to_dict())


if __name__ == "__main__":
    main()
