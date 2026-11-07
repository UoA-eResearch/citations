"""G4 audit packets (plan section 5). A stratified sample of 30 over-approximated and 30 tight advisories (seed
20261107). Each packet holds the fix diff and, for two in-range releases, the release's source files that match the
fix's files (plus the release's full source-file list):
  release A = the earliest in-range release (the one the classification turns on);
  release B = for over-approximated advisories the first present release, for tight ones the middle in-range release.
A and B are presented in publish order without labels. The pipeline's classes go to a key file outside the run
directory, given as argv[2].

  audit_packets.py make OUTDIR KEYFILE
  audit_packets.py score OUTDIR KEYFILE   -> results/tables/g4_audit.json (labels in OUTDIR/labels.json)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import classify as C  # noqa: E402
import presence as P  # noqa: E402


def files_for(url, eco, diff_paths):
    b = P.fetch(url)
    if not b:
        return None, []
    import io
    import tarfile
    import zipfile
    raw = {}
    try:
        if url.endswith((".whl", ".zip")):
            z = zipfile.ZipFile(io.BytesIO(b))
            for n in z.namelist():
                if n.lower().endswith(P.EXT[eco]) and "node_modules" not in n:
                    raw[n.split("/", 1)[1] if "/" in n and not url.endswith(".whl") else n] = z.read(n).decode("utf-8", "ignore")
        else:
            t = tarfile.open(fileobj=io.BytesIO(b), mode="r:*")
            for m in t.getmembers():
                if m.isfile() and m.name.lower().endswith(P.EXT[eco]) and "node_modules" not in m.name and m.size < 2_000_000:
                    raw[m.name.split("/", 1)[1] if "/" in m.name else m.name] = t.extractfile(m).read().decode("utf-8", "ignore")
    except Exception:
        return None, []
    picked = {}
    for p in diff_paths:
        mf = P.match_file(p, raw)
        if mf:
            picked[mf] = raw[mf]
    return picked, sorted(raw)


def make(outdir, keyfile):
    out, key = Path(outdir), Path(keyfile)
    out.mkdir(parents=True, exist_ok=True)
    K = pd.read_csv(T / "classes.csv")
    S = pd.read_csv(T / "sample.csv").set_index("id")
    rng = np.random.default_rng(20261107)
    pick = []
    for cls in ("over-approximated", "tight"):
        g = K[K.cls == cls]
        pick += [(i, cls) for i in g.id.iloc[rng.choice(len(g), 30, replace=False)]]
    rng.shuffle(pick)
    keys = []
    for k, (aid, cls) in enumerate(pick):
        pid = f"a{k:02d}"
        r = K[K.id == aid].iloc[0].to_dict()
        eco = r["ecosystem"]
        diff = (D / "commits" / f"{aid}.diff").read_text(errors="ignore")
        dpaths = list(P.parse_diff(diff, eco))
        rel = C.in_range_sorted(r)
        ia = 0
        ib = int(r["fp"]) if cls == "over-approximated" else len(rel) // 2
        if ib == ia:
            ib = min(len(rel) - 1, ia + 1)
        d = out / pid
        d.mkdir(exist_ok=True)
        (d / "fix.diff").write_text(diff[:60000])
        meta = {"packet": pid, "package": S.loc[aid, "package"], "ecosystem": eco, "releases": []}
        for lab, i in (("A", ia), ("B", ib)):
            x = rel[i]
            picked, listing = files_for(x["url"], eco, dpaths) if x.get("url") else (None, [])
            rd = d / f"release_{lab}"
            rd.mkdir(exist_ok=True)
            for p, txt in (picked or {}).items():
                (rd / p.replace("/", "__")).write_text(txt[:200000])
            (rd / "_all_source_files.txt").write_text("\n".join(listing))
            meta["releases"].append({"label": lab, "version": x["version"], "published": x.get("time"),
                                     "matched_files": sorted(picked or {}), "fetched": picked is not None})
        (d / "packet.json").write_text(json.dumps(meta, indent=1))
        keys.append({"packet": pid, "id": aid, "pipeline_class": cls, "A_version": rel[ia]["version"], "B_version": rel[ib]["version"]})
        print(pid, flush=True)
    key.write_text(json.dumps(keys, indent=1))
    print(len(keys), "packets")


def score(outdir, keyfile):
    L = pd.DataFrame(json.loads((Path(outdir) / "labels.json").read_text()))
    Kk = pd.DataFrame(json.loads(Path(keyfile).read_text()))
    M = Kk.merge(L, on="packet", how="left")
    M["audit_over"] = (M.A.str.lower() == "absent") & (M.B.str.lower() == "present")
    M["audit_tight"] = M.A.str.lower() == "present"
    ov, ti = M[M.pipeline_class == "over-approximated"], M[M.pipeline_class == "tight"]
    out = {"packets": int(len(M)),
           "over_approximated": {"n": int(len(ov)), "auditor_agrees": int(ov.audit_over.sum()),
                                 "auditor_cannot_tell": int(((ov.A.str.lower() == "cannot tell") | (ov.B.str.lower() == "cannot tell")).sum()),
                                 "auditor_says_present_in_A": int((ov.A.str.lower() == "present").sum())},
           "tight": {"n": int(len(ti)), "auditor_agrees": int(ti.audit_tight.sum()),
                     "auditor_cannot_tell": int((ti.A.str.lower() == "cannot tell").sum())},
           "disagreements": M[~((M.pipeline_class == "over-approximated") & M.audit_over) & ~((M.pipeline_class == "tight") & M.audit_tight)]
           [["packet", "id", "pipeline_class", "A", "B", "reason"]].to_dict("records")}
    o = out["over_approximated"]
    o["agreement"] = round(o["auditor_agrees"] / o["n"], 3) if o["n"] else None
    t = out["tight"]
    t["agreement"] = round(t["auditor_agrees"] / t["n"], 3) if t["n"] else None
    out["H1_reliable_by_plan_rule"] = bool(o["agreement"] is not None and o["agreement"] >= 0.8)
    (T / "g4_audit.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "disagreements"}, indent=1))


if __name__ == "__main__":
    {"make": make, "score": score}[sys.argv[1]](sys.argv[2], sys.argv[3])
