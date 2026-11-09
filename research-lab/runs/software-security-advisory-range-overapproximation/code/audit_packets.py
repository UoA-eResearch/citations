"""G4 audit packets (plan section 5). A stratified sample of 30 over-approximated and 30 tight advisories (seed
20261107). Each packet holds the fix diff and, for two in-range releases, the release's source files that match the
fix's files (plus the release's full source-file list):
  release A = the earliest in-range release (the one the classification turns on);
  release B = for over-approximated advisories the first present release, for tight ones the middle in-range release.
A and B are presented in publish order without labels. The pipeline's classes go to a key file outside the run
directory, given as argv[2].

  audit_packets.py make OUTDIR KEYFILE
  audit_packets.py score OUTDIR KEYFILE   -> results/tables/g4_audit.json (labels in OUTDIR/labels.json)

D4 (after the independent review, post hoc): the same 60 advisories, rebuilt so that the packet no longer encodes the
class and the auditor sees what the pipeline searched.
  - release B is chosen the same way for both strata: the last in-range release, just before the fix, where the
    code the fix changes must be present (for a one-release range there is no B);
  - no publish dates; new packet IDs in a new order (seed 20261110);
  - for each fix file, the release file with the longest matching path suffix, as presence.py uses; where no release
    file shares the name, the pipeline searched the whole release, so the packet carries the (up to 5) release files
    containing the most signature lines, else the (up to 3) files sharing the most identifiers with the fix's deleted
    and context lines. The packet says only how a file was chosen (path match or content search); the counts, which
    carry the pipeline's measurement, go to the key;
  - two labellers in separate sessions, then an adjudicator for packets they label differently; each answers, for A
    and B, whether the code the fix changes is present (the pipeline's construct), and for A whether the vulnerability
    is present in any form (the flaw construct).
  audit_packets.py make_d4 OUTDIR KEYFILE
  audit_packets.py score_d4 OUTDIR KEYFILE   -> results/tables/g4_audit_d4.json
"""
import re
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


IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")
COMMON = {"self", "this", "return", "function", "const", "None", "True", "False", "null", "undefined", "else", "elif", "import",
          "from", "require", "exports", "module", "async", "await", "print", "length", "string", "object", "value", "values"}


def files_d4(url, eco, diff_paths, sig_lines, idents):
    b = P.fetch(url)
    if not b:
        return None, [], {}
    raw = {}
    try:
        import io, tarfile, zipfile  # noqa: E401
        if url.endswith((".whl", ".zip")):
            z = zipfile.ZipFile(io.BytesIO(b))
            for n in z.namelist():
                if n.lower().endswith(P.EXT[eco]) and "node_modules" not in n and z.getinfo(n).file_size < 2_000_000:
                    raw[n.split("/", 1)[1] if "/" in n and not url.endswith(".whl") else n] = z.read(n).decode("utf-8", "ignore")
        else:
            t = tarfile.open(fileobj=io.BytesIO(b), mode="r:*")
            for m in t.getmembers():
                if m.isfile() and m.name.lower().endswith(P.EXT[eco]) and "node_modules" not in m.name and m.size < 2_000_000:
                    raw[m.name.split("/", 1)[1] if "/" in m.name else m.name] = t.extractfile(m).read().decode("utf-8", "ignore")
    except Exception:
        return None, [], {}
    picked, how = {}, {}
    norm = {f: {x for x in (P.norm(l, eco) for l in txt.splitlines()) if x} for f, txt in raw.items()}
    for p in diff_paths:
        mf = P.match_file(p, raw)
        if mf:
            picked[mf] = raw[mf]; how[mf] = f"path match for {p}"
            continue
        sl = set(sig_lines.get(p, []))
        hits = sorted(((len(sl & norm[f]), f) for f in raw if sl & norm[f]), reverse=True)[:5]
        if hits:
            for n, f in hits:
                picked[f] = raw[f]; how[f] = f"content search (no release file named like {p})|{n} of {len(sl)} signature lines"
            continue
        ids = idents.get(p, set())
        hits = sorted(((len(ids & set(IDENT.findall(raw[f]))), f) for f in raw), reverse=True)[:3]
        for n, f in hits:
            if n:
                picked[f] = raw[f]; how[f] = f"content search (no release file named like {p})|0 signature lines, {n} shared identifiers"
    return picked, sorted(raw), how


def make_d4(outdir, keyfile):
    out, key = Path(outdir), Path(keyfile)
    out.mkdir(parents=True, exist_ok=True)
    old = pd.DataFrame(json.loads((Path(keyfile).parent.parent / "advkey" / "key.json").read_text())) if (Path(keyfile).parent.parent / "advkey" / "key.json").exists() else None
    K = pd.read_csv(T / "classes.csv")
    S = pd.read_csv(T / "sample.csv").set_index("id")
    if old is not None:
        pick = list(zip(old.id, old.pipeline_class))
    else:                                    # the first audit's draw, reproduced
        rng0 = np.random.default_rng(20261107)
        pick = []
        for cls in ("over-approximated", "tight"):
            g = K[K.cls == cls]
            pick += [(i, cls) for i in g.id.iloc[rng0.choice(len(g), 30, replace=False)]]
    rng = np.random.default_rng(20261110)
    rng.shuffle(pick)
    keys = []
    for k, (aid, cls) in enumerate(pick):
        pid = f"b{k:02d}"
        r = K[K.id == aid].iloc[0].to_dict()
        eco = r["ecosystem"]
        diff = (D / "commits" / f"{aid}.diff").read_text(errors="ignore")
        parsed = P.parse_diff(diff, eco)
        sig = P.signature(parsed)
        idents = {p: {w for ln in v["deleted"] + v["context_before_added"] for w in IDENT.findall(ln)} - COMMON for p, v in parsed.items()}
        rel = C.in_range_sorted(r)
        idx = [("A", 0)] + ([("B", len(rel) - 1)] if len(rel) > 1 else [])
        d = out / pid
        d.mkdir(exist_ok=True)
        detail = {}
        (d / "fix.diff").write_text(diff[:60000])
        meta = {"packet": pid, "package": S.loc[aid, "package"], "ecosystem": eco,
                "note": "A is the earliest release the advisory declares affected; B (if present) is the last release before the fix.",
                "releases": []}
        for lab, i in idx:
            x = rel[i]
            picked, listing, how = files_d4(x["url"], eco, list(parsed), sig["sig"], idents) if x.get("url") else (None, [], {})
            rd = d / f"release_{lab}"
            rd.mkdir(exist_ok=True)
            for pth, txt in (picked or {}).items():
                (rd / pth.replace("/", "__")).write_text(txt[:200000])
            (rd / "_all_source_files.txt").write_text("\n".join(listing))
            meta["releases"].append({"label": lab, "version": x["version"], "files": [{"file": f, "why": how[f].split("|")[0]} for f in sorted(picked or {})],
                                     "fetched": picked is not None, "n_source_files": len(listing)})
            detail.setdefault(lab, {f: how[f] for f in sorted(picked or {})})
        (d / "packet.json").write_text(json.dumps(meta, indent=1))
        keys.append({"packet": pid, "id": aid, "pipeline_class": cls, "A_version": rel[0]["version"],
                     "B_version": rel[-1]["version"] if len(rel) > 1 else None, "n_in_range": len(rel),
                     "A_files": len(meta["releases"][0]["files"]), "B_files": len(meta["releases"][1]["files"]) if len(rel) > 1 else None,
                     "A_path_matched": sum(f["why"].startswith("path") for f in meta["releases"][0]["files"]),
                     "file_selection_detail": detail})
        print(pid, flush=True)
    key.write_text(json.dumps(keys, indent=1))
    print(len(keys), "packets")


def kappa(a, b):
    cats = sorted(set(a) | set(b))
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return round((po - pe) / (1 - pe), 3) if pe < 1 else None


def score_d4(outdir, keyfile):
    from math import sqrt
    Kk = pd.DataFrame(json.loads(Path(keyfile).read_text()))
    labs = {w: pd.DataFrame(json.loads((Path(outdir) / f"labels_{w}.json").read_text())) for w in ("L1", "L2")}
    for w, L in labs.items():
        for c in ("A_code", "B_code", "A_flaw"):
            L[c] = L[c].fillna("n/a").str.lower()
    adj_f = Path(outdir) / "labels_adjudicated.json"
    adj = pd.DataFrame(json.loads(adj_f.read_text())) if adj_f.exists() else pd.DataFrame(columns=["packet", "A_code", "B_code", "A_flaw", "reason"])
    for c in ("A_code", "B_code", "A_flaw"):
        if c in adj:
            adj[c] = adj[c].fillna("n/a").str.lower()
    m = Kk.merge(labs["L1"], on="packet").merge(labs["L2"], on="packet", suffixes=("_1", "_2"))

    def wil(k, n, z=1.96):
        if not n:
            return [None, None]
        p_ = k / n; d_ = 1 + z * z / n; c_ = (p_ + z * z / (2 * n)) / d_
        h_ = z * sqrt(p_ * (1 - p_) / n + z * z / (4 * n * n)) / d_
        return [round(c_ - h_, 3), round(c_ + h_, 3)]
    final = []
    for r in m.to_dict("records"):
        same = r["A_code_1"] == r["A_code_2"] and r["B_code_1"] == r["B_code_2"]
        if same:
            f = {"A_code": r["A_code_1"], "B_code": r["B_code_1"], "A_flaw": r["A_flaw_1"] if r["A_flaw_1"] == r["A_flaw_2"] else "disagree", "source": "agreed"}
        else:
            a = adj[adj.packet == r["packet"]]
            f = ({"A_code": a.A_code.iloc[0], "B_code": a.B_code.iloc[0], "A_flaw": a.A_flaw.iloc[0], "source": "adjudicated"}
                 if len(a) else {"A_code": None, "B_code": None, "A_flaw": None, "source": "pending adjudication"})
        final.append({"packet": r["packet"], "pipeline_class": r["pipeline_class"], **f})
    F = pd.DataFrame(final)

    def agree(df, a, b):
        ov = df[df.pipeline_class == "over-approximated"]
        ti = df[df.pipeline_class == "tight"]
        ov_ok = (ov[a] == "absent") & ((ov[b] == "present") | ov[b].isin(["n/a"]))
        ov_judge = (ov[a] != "cannot tell") & (ov[b] != "cannot tell")
        ti_ok = ti[a] == "present"
        ti_judge = ti[a] != "cannot tell"
        return {"over": {"n": int(len(ov)), "agree": int(ov_ok.sum()), "share": round(float(ov_ok.mean()), 3), "wilson": wil(int(ov_ok.sum()), len(ov)),
                         "judgeable": int(ov_judge.sum()), "agree_judgeable": int((ov_ok & ov_judge).sum()),
                         "share_judgeable": round(float((ov_ok & ov_judge).sum() / ov_judge.sum()), 3) if ov_judge.sum() else None,
                         "wilson_judgeable": wil(int((ov_ok & ov_judge).sum()), int(ov_judge.sum())),
                         "says_present_in_A": int((ov[a] == "present").sum()), "cannot_tell": int((~ov_judge).sum())},
                "tight": {"n": int(len(ti)), "agree": int(ti_ok.sum()), "judgeable": int(ti_judge.sum()),
                          "says_absent_in_A": int((ti[a] == "absent").sum()), "cannot_tell": int((~ti_judge).sum())}}
    out = {"packets": int(len(m)),
           "labeller_1": agree(m.rename(columns={"A_code_1": "a", "B_code_1": "b"}), "a", "b"),
           "labeller_2": agree(m.rename(columns={"A_code_2": "a", "B_code_2": "b"}), "a", "b"),
           "kappa_A_code": kappa(list(m.A_code_1), list(m.A_code_2)),
           "kappa_A_flaw": kappa(list(m.A_flaw_1), list(m.A_flaw_2)),
           "raw_agreement_A_code": round(float((m.A_code_1 == m.A_code_2).mean()), 3),
           "adjudicated_packets": int((F.source == "adjudicated").sum()), "pending": int((F.source == "pending adjudication").sum())}
    Fd = F.dropna(subset=["A_code"])
    out["final"] = agree(Fd, "A_code", "B_code")
    ovf = Fd[Fd.pipeline_class == "over-approximated"]
    out["final"]["over"]["flaw_present_in_A"] = int((ovf.A_flaw == "yes").sum())
    out["final"]["over"]["code_absent_but_flaw_present_in_A"] = int(((ovf.A_code == "absent") & (ovf.A_flaw == "yes")).sum())
    out["final"]["H1_reliable_by_plan_rule"] = bool(out["final"]["over"]["share"] >= 0.8)
    # D5 (confirmation pass N1, N4, N5): with B = the last in-range release, "B present" tests the declared upper bound,
    # not the plan's "some release has the code", so the lower-bound-only reading (A absent) is reported beside the
    # two-part rule; packets whose release A has no source files at all; the unadjudicated flaw disagreement; B kappa
    a_abs = ovf.A_code == "absent"
    a_jud = ovf.A_code != "cannot tell"
    nsrc = {r["packet"]: json.loads((Path(outdir) / r["packet"] / "packet.json").read_text())["releases"][0].get("n_source_files")
            for r in final}
    empty = [pk for pk in ovf.packet if nsrc.get(pk) == 0]
    out["final"]["over"]["lower_bound_only"] = {"A_absent": int(a_abs.sum()), "n": int(len(ovf)), "wilson": wil(int(a_abs.sum()), len(ovf)),
                                                "judgeable": int(a_jud.sum()), "wilson_judgeable": wil(int(a_abs.sum()), int(a_jud.sum())),
                                                "reliable_by_80pct": bool(a_abs.mean() >= 0.8)}
    out["final"]["over"]["A_and_B_absent_packets"] = sorted(ovf[(ovf.A_code == "absent") & (ovf.B_code == "absent")].packet)
    out["final"]["over"]["confirmed_with_empty_release_A"] = sorted(set(empty) & set(ovf[(ovf.A_code == "absent") & (ovf.B_code == "present")].packet))
    conf_ne = ((ovf.A_code == "absent") & (ovf.B_code == "present") & ~ovf.packet.isin(empty))
    jud_ne = ((ovf.A_code != "cannot tell") & (ovf.B_code != "cannot tell") & ~ovf.packet.isin(empty))
    out["final"]["over"]["agree_judgeable_excluding_empty_A"] = f"{int(conf_ne.sum())}/{int(jud_ne.sum())}"
    out["final"]["over"]["flaw_disagreement_unadjudicated"] = sorted(ovf[ovf.A_flaw == "disagree"].packet)
    out["kappa_B_code"] = kappa(list(m.B_code_1), list(m.B_code_2))
    # does the packet still encode the class? (G1 probe)
    kk = Kk.copy()
    kk["A_fewer_files_than_B"] = kk.A_files < kk.B_files.fillna(kk.A_files)
    kk["A_no_path_match"] = kk.A_path_matched == 0
    o = kk.pipeline_class == "over-approximated"
    out["leak_probe"] = {f: {"over": round(float(kk[o][f].mean()), 3), "tight": round(float(kk[~o][f].mean()), 3),
                             "accuracy_as_predictor": round(float(((kk[f]) == o).mean()), 3)} for f in ("A_fewer_files_than_B", "A_no_path_match")}
    out["leak_probe"]["n_in_range_median"] = {"over": float(kk[o].n_in_range.median()), "tight": float(kk[~o].n_in_range.median())}
    out["rows"] = F.merge(Kk[["packet", "id"]], on="packet").to_dict("records")
    (T / "g4_audit_d4.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1, default=str))


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
    {"make": make, "score": score, "make_d4": make_d4, "score_d4": score_d4}[sys.argv[1]](sys.argv[2], sys.argv[3])
