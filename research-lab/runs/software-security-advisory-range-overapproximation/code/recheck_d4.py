"""G2 recheck of the releases the classification rests on (D4, after the independent review, finding 8).

presence.py did not record whether a signature file was found by path or by the "any source file" fallback, nor how
many source files a release yielded; an artefact with no source files gave s = 0 and counted as absent. For every
classified advisory this re-downloads:
  - over-approximated: the absent releases before the first present one, in order, until one has at least one source
    file (normally the first), and the first present release;
  - tight: the first release (which is the first present one);
and records per release the number of source files, the match type of each signature file (path = a release file
shares at least the file name; fallback = the whole release was searched), and s recomputed (it must equal the stored
s). An over-approximated advisory whose absent releases are all empty extractions is reclassified undetermined.

  recheck_d4.py run   -> data/recheck/<id>.json, results/tables/release_recheck.csv
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
import classify as C  # noqa: E402
import presence as P  # noqa: E402


def check(sig, x, eco):
    b = P.fetch(x["url"]) if x.get("url") else None
    rf = P.release_files(b, x["url"], eco) if b else None
    if rf is None:
        return {"version": x["version"], "fetched": False}
    types = {p: ("path" if P.match_file(p, rf) else "fallback") for p in sig["sig"]}
    pr = P.presence(sig, rf)
    return {"version": x["version"], "fetched": True, "n_source_files": len(rf), "match_types": types,
            "s": pr.get("s"), "state": pr.get("state")}


def one(r):
    out = D / "recheck" / f"{r['id']}.json"
    if out.exists():
        return json.loads(out.read_text())
    p = json.loads((D / "presence" / f"{r['id']}.json").read_text())
    sig = P.signature(P.parse_diff((D / "commits" / f"{r['id']}.diff").read_text(errors="ignore"), r["ecosystem"]))
    rel = C.in_range_sorted(r)
    stored = p["releases"]
    fp = int(r["fp"])
    res = {"id": r["id"], "cls": r["cls"], "fp": fp, "absent_checked": [], "first_present": None}
    if r["cls"] == "over-approximated":
        for k in range(fp):
            if stored[k].get("s") is None or stored[k]["s"] > 0.2:      # classify(): absent means s <= 0.2
                continue
            c = check(sig, rel[k], r["ecosystem"])
            c.update({"index": k, "s_stored": stored[k].get("s")})
            res["absent_checked"].append(c)
            if c.get("fetched") and c.get("n_source_files", 0) > 0:
                break
    c = check(sig, rel[fp], r["ecosystem"])
    c.update({"index": fp, "s_stored": stored[fp].get("s")})
    res["first_present"] = c
    out.write_text(json.dumps(res))
    return res


def run():
    K = pd.read_csv(T / "classes.csv")
    K = K[K.cls.isin(["tight", "over-approximated"])].to_dict("records")
    (D / "recheck").mkdir(exist_ok=True)
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, K))
    rows = []
    for x in res:
        a = next((c for c in x["absent_checked"] if c.get("fetched") and c.get("n_source_files", 0) > 0), None)
        empties = sum(1 for c in x["absent_checked"] if c.get("fetched") and c.get("n_source_files", 0) == 0)
        fpres = x["first_present"]

        def mt(c):
            if not c or not c.get("fetched"):
                return None
            v = set(c["match_types"].values())
            return "path" if v == {"path"} else "fallback" if v == {"fallback"} else "mixed"
        rows.append({"id": x["id"], "cls": x["cls"],
                     "absent_releases_checked": len(x["absent_checked"]), "empty_absent_releases": empties,
                     "absent_version": a["version"] if a else None, "absent_n_files": a["n_source_files"] if a else None,
                     "absent_match": mt(a), "absent_s": a["s"] if a else None, "absent_s_stored": a["s_stored"] if a else None,
                     "present_version": fpres.get("version"), "present_n_files": fpres.get("n_source_files"),
                     "present_match": mt(fpres), "present_s": fpres.get("s"), "present_s_stored": fpres.get("s_stored"),
                     "cls_d4": ("undetermined (only empty extractions absent)" if x["cls"] == "over-approximated" and a is None
                                and empties > 0 else x["cls"])})
    pd.DataFrame(rows).to_csv(T / "release_recheck.csv", index=False)
    print(pd.DataFrame(rows).cls_d4.value_counts().to_dict())


if __name__ == "__main__":
    {"run": run}[sys.argv[1]]()
