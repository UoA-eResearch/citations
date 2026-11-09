"""Post hoc numbers after the independent review (D4). Replaces the hand-added fields of posthoc_strict.json: every
number the report gives for the strict reading, the calibrated range, the first audit and the H2 sensitivity comes from
here. -> results/tables/posthoc_d4.json

  1. strict reading under one convention: non-strict over-approximations count as not over-approximated (all 411
     classified advisories stay in the denominator), for both H1 and H2; the other convention (non-strict and unknown
     dropped from the denominator) as a sensitivity;
  2. the first G4 audit (data/audit, key in the job's advkey/): agreement on all 30 over-approximated packets and on the
     judgeable ones (neither A nor B "cannot tell"), with each "cannot tell" classed as a packet artefact (release A had
     no file in the packet, or the reason says a file was not provided) or not;
  3. the audit-calibrated H1 share, k/n x audit agreement, with the agreement's Wilson interval carried through:
     measured agreement (10/30), the most generous reading (agree + cannot tell), and judgeable items only;
  4. H2 with the corrected range starting earlier: at the first release with s > 0.2, and just after the last absent
     release before the first present one (the reported start is the first release with s >= 0.8);
  5. the G2 recheck (release_recheck.csv), if present: match types, source-file counts, empty extractions, and H1 with
     empty-extraction absences treated as undetermined;
  6. the D4 re-audit (g4_audit_d4.json), if present: the calibrated H1 share under the pipeline's construct (code the
     fix changes absent in A and present in B) and under the flaw construct (the vulnerability absent from A in any
     form), with Wilson intervals carried through.

  posthoc_d4.py OLD_KEY.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
SEED = 20261107


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 4), round(c + h, 4)]


def h2(dec, cor, seed=SEED):
    dec, cor = np.asarray(dec, float), np.asarray(cor, float)
    rng = np.random.default_rng(seed)
    bs = []
    for _ in range(2000):
        i = rng.integers(0, len(dec), len(dec))
        bs.append(dec[i].sum() / cor[i].sum())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return {"factor": round(float(dec.sum() / cor.sum()), 3), "ci": [round(float(lo), 3), round(float(hi), 3)],
            "verdict_vs_1.5": "above" if lo > 1.5 else "below" if hi < 1.5 else "spans"}


K = pd.read_csv(T / "classes.csv")
st = pd.read_csv(T / "classes_strict.csv")[["id", "strict"]]
K = K.merge(st, on="id", how="left")
cl = K[K.cls.isin(["tight", "over-approximated"])].copy()
ov = cl.cls == "over-approximated"
strict = ov & (cl.strict == True)  # noqa: E712
out = {}
# 1. strict reading
n_all = len(cl)
k_s = int(strict.sum())
dec = cl.n_in_range.to_numpy(float)
cor_strict = np.where(strict, cl.n_in_range - cl.fp.fillna(0), cl.n_in_range).astype(float)
keep = (~ov) | strict
out["strict"] = {"over_approximated": int(ov.sum()), "strict": k_s, "not_strict": int((ov & (cl.strict == False)).sum()),  # noqa: E712
                 "unknown": int((ov & cl.strict.isna()).sum()),
                 "convention_main": "non-strict counts as not over-approximated; all classified advisories in the denominator",
                 "H1_main": {"share": round(k_s / n_all, 4), "k": k_s, "n": n_all, "wilson": wilson(k_s, n_all)},
                 "H2_main": h2(dec, cor_strict),
                 "convention_sensitivity": "non-strict and unknown over-approximations dropped from the denominator",
                 "H1_sensitivity": {"share": round(k_s / int(keep.sum()), 4), "k": k_s, "n": int(keep.sum()), "wilson": wilson(k_s, int(keep.sum()))},
                 "H2_sensitivity": h2(dec[keep.to_numpy()], cor_strict[keep.to_numpy()])}
# 2. the first G4 audit
key = pd.DataFrame(json.loads(Path(sys.argv[1]).read_text()))
lab = pd.DataFrame(json.loads((D / "audit" / "labels.json").read_text()))
m = key.merge(lab, on="packet")
for c in ("A", "B"):
    m[c] = m[c].str.lower()


def a_files(pid):
    meta = json.loads((D / "audit" / pid / "packet.json").read_text())
    return len(meta["releases"][0]["matched_files"])


m["A_files_in_packet"] = m.packet.map(a_files)
mo = m[m.pipeline_class == "over-approximated"].copy()
mt = m[m.pipeline_class == "tight"].copy()
mo["agree"] = (mo.A == "absent") & (mo.B == "present")
mo["cannot"] = (mo.A == "cannot tell") | (mo.B == "cannot tell")
mo["artefact"] = mo.cannot & ((mo.A_files_in_packet == 0) | mo.reason.str.contains("not provided|unprovided|not included|missing from the packet", case=False, na=False))
mo = mo.merge(K[["id", "strict"]], on="id", how="left")
judge = ~mo.cannot
out["audit_v1"] = {"over": {"n": int(len(mo)), "agree": int(mo.agree.sum()), "wilson": wilson(int(mo.agree.sum()), len(mo)),
                            "cannot_tell": int(mo.cannot.sum()), "cannot_tell_packet_artefact": int(mo.artefact.sum()),
                            "cannot_tell_A_had_no_file": int((mo.cannot & (mo.A_files_in_packet == 0)).sum()),
                            "artefact_packets": sorted(mo[mo.artefact].packet.tolist()),
                            "judgeable": int(judge.sum()), "agree_judgeable": int((mo.agree & judge).sum()),
                            "wilson_judgeable": wilson(int((mo.agree & judge).sum()), int(judge.sum())),
                            "says_present_in_A": int((mo.A == "present").sum())},
                   "tight": {"n": int(len(mt)), "agree": int((mt.A == "present").sum()), "judgeable": int((mt.A != "cannot tell").sum()),
                             "says_absent_in_A": int((mt.A == "absent").sum())},
                   "strict_cases_audited": {"n": int((mo.strict == True).sum()),  # noqa: E712
                                            "A_had_no_file_in_packet": int(((mo.strict == True) & (mo.A_files_in_packet == 0)).sum()),  # noqa: E712
                                            "note": "packets carried only same-name files, and strict means release A has none, so the auditor saw an empty A in every strict case"}}
# 3. calibrated share
k, n = int(ov.sum()), n_all
a = out["audit_v1"]["over"]
measured = a["agree"] / a["n"]
generous = (a["agree"] + a["cannot_tell"]) / a["n"]
jud = a["agree_judgeable"] / a["judgeable"]
wm, wg, wj = wilson(a["agree"], a["n"]), wilson(a["agree"] + a["cannot_tell"], a["n"]), a["wilson_judgeable"]
out["calibrated_H1"] = {"pipeline_share": round(k / n, 4),
                        "measured": {"point": round(k / n * measured, 3), "range": [round(k / n * wm[0], 3), round(k / n * wm[1], 3)]},
                        "most_generous": {"point": round(k / n * generous, 3), "range": [round(k / n * wg[0], 3), round(k / n * wg[1], 3)]},
                        "judgeable_only": {"point": round(k / n * jud, 3), "range": [round(k / n * wj[0], 3), round(k / n * wj[1], 3)]},
                        "first_draft_range_without_uncertainty": [round(k / n * measured, 3), round(k / n * generous, 3)],
                        "assumes": "the audited 30 represent all 308; tight-side errors ignored; the undetermined half behaves like the classified half"}
# 4. H2 corrected-start sensitivity
starts = {"first_s_ge_0.8 (reported)": [], "first_s_gt_0.2": [], "after_last_absent": []}
partial_before = 0
for r in cl.to_dict("records"):
    if r["cls"] != "over-approximated":
        for v in starts.values():
            v.append(r["n_in_range"])
        continue
    rel = json.loads((D / "presence" / f"{r['id']}.json").read_text())["releases"]
    fp = int(r["fp"])
    s = [x.get("s") for x in rel[:fp]]
    first_partial = next((j for j, v in enumerate(s) if v is not None and v > 0.2), fp)
    last_absent = max(j for j, v in enumerate(s) if v is not None and v <= 0.2)
    partial_before += first_partial < fp
    starts["first_s_ge_0.8 (reported)"].append(r["n_in_range"] - fp)
    starts["first_s_gt_0.2"].append(r["n_in_range"] - first_partial)
    starts["after_last_absent"].append(r["n_in_range"] - (last_absent + 1))
undet_removed = 0
removed = 0
for r in cl[ov].to_dict("records"):
    rel = json.loads((D / "presence" / f"{r['id']}.json").read_text())["releases"][: int(r["fp"])]
    removed += len(rel)
    undet_removed += sum(1 for x in rel if x.get("s") is None or 0.2 < x["s"] < 0.8)
out["H2_start_sensitivity"] = {lab_: h2(dec, cor) for lab_, cor in starts.items()}
out["H2_start_sensitivity"]["over_approximated_with_partial_presence_before_the_cut"] = int(partial_before)
out["H2_start_sensitivity"]["removed_releases"] = int(removed)
out["H2_start_sensitivity"]["removed_releases_not_shown_absent"] = int(undet_removed)
# 5. G2 recheck
rc = T / "release_recheck.csv"
if rc.exists():
    R = pd.read_csv(rc)
    o = R[R.cls == "over-approximated"]
    t = R[R.cls == "tight"]
    out["recheck"] = {"advisories": int(len(R)),
                      "s_reproduces": {"absent": int((o.absent_s == o.absent_s_stored).sum()), "absent_checked": int(o.absent_s.notna().sum()),
                                       "present": int((R.present_s == R.present_s_stored).sum()), "present_checked": int(R.present_s.notna().sum())},
                      "over_absent_release_match": o.absent_match.value_counts(dropna=False).to_dict(),
                      "over_present_release_match": o.present_match.value_counts(dropna=False).to_dict(),
                      "tight_release_match": t.present_match.value_counts(dropna=False).to_dict(),
                      "over_with_an_empty_absent_release": int((o.empty_absent_releases > 0).sum()),
                      "over_absent_release_has_few_files_le_2": int((o.absent_n_files <= 2).sum()),
                      "cls_d4": R.cls_d4.value_counts().to_dict()}
    k2 = int((R.cls_d4 == "over-approximated").sum())
    n2 = int(R.cls_d4.isin(["over-approximated", "tight"]).sum())
    out["recheck"]["H1_empty_extractions_undetermined"] = {"share": round(k2 / n2, 4), "k": k2, "n": n2, "wilson": wilson(k2, n2)}
    o2 = o[o.absent_match == "path"]
    k3 = int(len(o2))
    n3 = k3 + int((t.present_match == "path").sum())
    # G2: count the fallback for the release each classification turns on (the plan names the any-file fallback)
    sys.path.insert(0, str(RUN.parents[1] / "tools"))
    from coverage import Coverage  # noqa: E402
    FB, MX = "any source file searched (no release file shares the fix file's name)", "mixed: some fix files by path, some by any-file search"
    dmatch = pd.concat([o.absent_match, t.present_match])
    cov = Coverage("deciding_release_match", T / "coverage.json", allowed=[FB, MX])
    cov.add_counts(ok=int((dmatch == "path").sum()), fallbacks={FB: int((dmatch == "fallback").sum()), MX: int((dmatch == "mixed").sum())},
                   drops={"absent releases were all empty extractions (reclassified undetermined)": int(dmatch.isna().sum())})
    cov.save()
    out["recheck"]["H1_path_matched_absences_only"] = {"share": round(k3 / n3, 4), "k": k3, "n": n3, "wilson": wilson(k3, n3),
                                                         "note": "only advisories whose deciding release was judged by a same-path file for every fix file (absent release for over-approximated, release A for tight)"}
# invariants (G3): asserted, not only stated
S_ = pd.read_csv(T / "sample.csv")
assert len(S_) == 800 and len(K) == 800
assert int((cl.cls == "tight").sum()) + int(ov.sum()) == 411
assert (cl[cl.cls == "tight"].fp == 0).all()
assert (cor_strict <= dec).all() and all((np.asarray(c) <= dec).all() for c in starts.values())
out["invariants_checked"] = ["800 sampled = 800 rows in classes.csv", "411 classified", "tight at index 0", "corrected pairs <= declared pairs (all readings)"]
# 6. calibrated share from the D4 re-audit
ga = T / "g4_audit_d4.json"
if ga.exists():
    G = json.loads(ga.read_text())
    fo = G["final"]["over"]
    rows = [r for r in G["rows"] if r["pipeline_class"] == "over-approximated"]
    flaw_absent = sum(1 for r in rows if r["A_flaw"] == "no")
    flaw_judge = sum(1 for r in rows if r["A_flaw"] in ("yes", "no"))
    w1, w2 = wilson(fo["agree"], fo["n"]), wilson(fo["agree_judgeable"], fo["judgeable"])
    w3, w4 = wilson(flaw_absent, len(rows)), wilson(flaw_absent, flaw_judge)
    out["calibrated_H1_d4_audit"] = {
        "code_construct": {"agree": f"{fo['agree']}/{fo['n']}", "point": round(k / n * fo["agree"] / fo["n"], 3),
                           "range": [round(k / n * w1[0], 3), round(k / n * w1[1], 3)]},
        "code_construct_judgeable": {"agree": f"{fo['agree_judgeable']}/{fo['judgeable']}", "point": round(k / n * fo["agree_judgeable"] / fo["judgeable"], 3),
                                     "range": [round(k / n * w2[0], 3), round(k / n * w2[1], 3)]},
        "flaw_construct": {"flaw_absent_in_A": f"{flaw_absent}/{len(rows)}", "point": round(k / n * flaw_absent / len(rows), 3),
                           "range": [round(k / n * w3[0], 3), round(k / n * w3[1], 3)]},
        "flaw_construct_judgeable": {"flaw_absent_in_A": f"{flaw_absent}/{flaw_judge}", "point": round(k / n * flaw_absent / flaw_judge, 3),
                                     "range": [round(k / n * w4[0], 3), round(k / n * w4[1], 3)]},
        "tight_errors": G["final"]["tight"]["says_absent_in_A"], "kappa_A_code": G["kappa_A_code"], "kappa_A_flaw": G["kappa_A_flaw"],
        "assumes": "the audited 30 represent all 308; the undetermined half behaves like the classified half"}
(T / "posthoc_d4.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
print(json.dumps(out, indent=1, default=str))
