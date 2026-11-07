"""Classification, H1, H2 and secondaries (plan sections 0, 3, 4). -> results/tables/primary.json, classes.csv

  classify.py downloads   npm weekly downloads per version for classified npm advisories -> data/downloads/<id>.json
  classify.py run         classes and statistics
"""
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
sys.path.insert(0, str(RUN.parents[1] / "tools"))
import presence as P  # noqa: E402
from coverage import Coverage  # noqa: E402

SEED = 20261107


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def classify(rels, present=0.8, absent=0.2):
    def st(x):
        if "s" not in x:
            return "undetermined"
        if x["s"] >= present and (x.get("patch_share") is None or x["patch_share"] < 0.5):
            return "present"
        return "absent" if x["s"] <= absent else "undetermined"
    states = [st(x) for x in rels]
    if "present" not in states:
        return "undetermined", None
    fp = states.index("present")
    if fp == 0:
        return "tight", 0
    return ("over-approximated", fp) if "absent" in states[:fp] else ("undetermined", None)


def in_range_sorted(r):
    vs = json.loads((D / "versions" / f"{r['id']}.json").read_text())["releases"]
    rel, _ = P.in_range(r["ecosystem"], vs, r["introduced"], r["fixed"])
    rel.sort(key=lambda x: (x.get("time") or "9999", x["version"]))
    return rel


def downloads():
    C = pd.read_csv(T / "classes.csv")
    S = pd.read_csv(T / "sample.csv").set_index("id")
    (D / "downloads").mkdir(exist_ok=True)
    for i in C[(C.ecosystem == "npm") & C.cls.isin(["tight", "over-approximated"])].id:
        f = D / "downloads" / f"{i}.json"
        if f.exists():
            continue
        pkg = S.loc[i, "package"]
        try:
            with urllib.request.urlopen(urllib.request.Request("https://api.npmjs.org/versions/" + urllib.parse.quote(pkg, safe="@").replace("/", "%2F") + "/last-week",
                                                               headers={"User-Agent": P.UA}), timeout=60) as resp:
                f.write_bytes(resp.read())
        except Exception as e:
            f.write_text(json.dumps({"error": str(e)[:80]}))
        time.sleep(1.0)
    print("downloads fetched")


def run():
    S = pd.read_csv(T / "sample.csv")
    rows, stat = [], {}
    for r in S.itertuples():
        f = D / "presence" / f"{r.id}.json"
        if not f.exists():
            stat["no presence file"] = stat.get("no presence file", 0) + 1
            continue
        p = json.loads(f.read_text())
        if p.get("status") != "done":
            stat[p.get("status")] = stat.get(p.get("status"), 0) + 1
            rows.append({"id": r.id, "ecosystem": r.ecosystem, "intro_zero": r.intro_zero, "cls": "not classifiable: " + str(p.get("status"))})
            continue
        cls, fp = classify(p["releases"])
        cls6, fp6 = classify(p["releases"], 0.6, 0.4)
        rel = p["releases"]
        row = {"id": r.id, "ecosystem": r.ecosystem, "intro_zero": r.intro_zero, "cls": cls, "cls_alt": cls6, "sig_kind": p["sig_kind"],
               "n_in_range": p["n_in_range"], "fp": fp, "fp_alt": fp6, "introduced": p["introduced"], "fixed": p["fixed"],
               "downloads_used": p.get("downloads"), "cap_hit": any(x.get("why") == "cap" for x in rel),
               "fixed_release_present": (p.get("first_fixed_release") or {}).get("state") == "present" if p.get("first_fixed_release") else None}
        if cls == "over-approximated":
            t0, t1 = rel[0].get("time"), rel[fp].get("time")
            row["gap_releases"] = fp
            row["gap_years"] = round((pd.Timestamp(t1) - pd.Timestamp(t0)).days / 365.25, 2) if t0 and t1 else None
        rows.append(row)
    C = pd.DataFrame(rows)
    C.to_csv(T / "classes.csv", index=False)
    cl = C[C.cls.isin(["tight", "over-approximated"])]
    k, n = int((cl.cls == "over-approximated").sum()), int(len(cl))
    out = {"sampled": int(len(S)), "classes": C.cls.value_counts().to_dict()}
    ci = wilson(k, n)
    out["H1"] = {"over_approximated": k, "classified": n, "share": round(k / n, 4) if n else None, "wilson": ci,
                 "verdict": "Supported" if ci[0] is not None and ci[0] > 0.25 else "Refuted" if ci[1] is not None and ci[1] < 0.25 else "Inconclusive",
                 "share_of_all_sampled_lower_bound": round(k / len(S), 4),
                 "undetermined_share": round(float((~C.cls.isin(["tight", "over-approximated"])).sum() / len(S)), 4)}
    dec = cl.n_in_range.to_numpy(float)
    cor = np.where(cl.cls == "over-approximated", cl.n_in_range - cl.fp.fillna(0), cl.n_in_range).astype(float)
    F = dec.sum() / cor.sum() if cor.sum() else None
    rng = np.random.default_rng(SEED)
    bs = []
    for _ in range(2000):
        i = rng.integers(0, len(dec), len(dec))
        bs.append(dec[i].sum() / cor[i].sum())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    out["H2"] = {"declared_pairs": int(dec.sum()), "corrected_pairs": int(cor.sum()), "factor": round(F, 3) if F else None,
                 "ci": [round(lo, 3), round(hi, 3)],
                 "verdict": "Supported" if lo > 1.5 else "Refuted" if hi < 1.5 else "Inconclusive"}
    # secondary 1: by ecosystem and lower-bound kind
    out["by_ecosystem"] = {e: {"over": int((g.cls == "over-approximated").sum()), "classified": int(len(g)),
                              "wilson": wilson(int((g.cls == "over-approximated").sum()), int(len(g)))} for e, g in cl.groupby("ecosystem")}
    out["by_lower_bound"] = {("introduced: 0" if z else "explicit"): {"over": int((g.cls == "over-approximated").sum()), "classified": int(len(g)),
                             "wilson": wilson(int((g.cls == "over-approximated").sum()), int(len(g)))} for z, g in cl.groupby("intro_zero")}
    ov = cl[cl.cls == "over-approximated"]
    out["gap"] = {"releases_median": float(ov.gap_releases.median()) if len(ov) else None,
                  "years_median": float(ov.gap_years.median()) if len(ov) and ov.gap_years.notna().any() else None}
    fr = C[C.fixed_release_present.notna()] if "fixed_release_present" in C else C.iloc[:0]
    out["upper_bound_check"] = {"checked": int(len(fr)), "vulnerable_code_still_present_at_fixed": int(fr.fixed_release_present.astype(bool).sum())}
    cla = C[C.cls_alt.isin(["tight", "over-approximated"])] if "cls_alt" in C else C.iloc[:0]
    ka = int((cla.cls_alt == "over-approximated").sum())
    out["threshold_sensitivity_0.6_0.4"] = {"over": ka, "classified": int(len(cla)), "share": round(ka / len(cla), 4) if len(cla) else None,
                                            "wilson": wilson(ka, int(len(cla)))}
    out["cap_hit"] = int(C.get("cap_hit", pd.Series(dtype=bool)).fillna(False).sum())
    # secondary: npm download-weighted share of flagged installs removed by correcting the lower bound
    dl_dec = dl_cor = 0.0
    nd = 0
    for r in cl[cl.ecosystem == "npm"].to_dict("records"):
        f = D / "downloads" / f"{r['id']}.json"
        if not f.exists():
            continue
        dd = json.loads(f.read_text()).get("downloads")
        if not dd:
            continue
        nd += 1
        rel = in_range_sorted(r)
        start = int(r["fp"]) if r["cls"] == "over-approximated" else 0
        dl_dec += sum(dd.get(x["version"], 0) for x in rel)
        dl_cor += sum(dd.get(x["version"], 0) for x in rel[start:])
    out["npm_download_weighted"] = {"advisories": nd, "weekly_downloads_in_declared_ranges": int(dl_dec), "in_corrected_ranges": int(dl_cor),
                                    "share_flagged_only_by_lower_bound": round(1 - dl_cor / dl_dec, 4) if dl_dec else None}
    cov = Coverage("classified", T / "coverage.json")
    cov.add_counts(ok=int(len(cl)), drops={**{k_: v for k_, v in stat.items()},
                                           **{f"undetermined": int((C.cls == "undetermined").sum())}})
    cov.save()
    (T / "primary.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    {"run": run, "downloads": downloads}[sys.argv[1]]()
