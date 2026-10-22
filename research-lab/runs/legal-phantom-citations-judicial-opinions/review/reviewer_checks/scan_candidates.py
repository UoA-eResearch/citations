"""Reviewer check: one pass over candidates.jsonl and misattributions.jsonl.
Re-derives the completeness filter (analysis.prepare logic), the kept/dropped split by reporter, the Charlotin
detection recall (453/854) and the judge-attributed incidents' candidates, with their filter outcome."""
import csv, json, re, sys
from collections import Counter, defaultdict
RUN = "/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions"
S = RUN + "/data/screen"
OUT = RUN + "/review/reviewer_checks"
FLAG = re.compile(
    r"fictitious|fictional|non-?existent|does not exist|do not exist|did not exist|no such case|fabricat|"
    r"hallucinat|artificial intelligence|\bA\.?I\.?\b|chat ?gpt|generative|large language model|\bLLM\b|"
    r"sanction|show cause|could not (?:locate|find)|unable to (?:locate|find)|cannot be (?:located|found)|"
    r"bogus|\bfake\b|not a real case|misrepresent", re.I)
def norm_reporter(r): return "".join(ch for ch in r.lower() if ch.isalnum())
def volume_key(cite):
    parts = cite.split()
    if len(parts) < 3: return None
    try: vol = int(parts[0])
    except ValueError: return None
    return f"{norm_reporter(' '.join(parts[1:-1]))}|{vol}"
def period(d):
    if 20230101 <= d <= 20260930: return "screened"
    if 20190101 <= d <= 20221231: return "placebo"
    return None
vols = json.load(open(S + "/volumes.json"))["volumes"]
cal = [r for r in csv.DictReader(open(S + "/charlotin_matched.csv")) if r["matched"] == "1"]
cal_ids = {int(r["cluster_id"]) for r in cal}
judge = {int(r["cluster_id"]): r for r in cal if "judge" in r["party"].lower()}
print("calibration orders", len(cal), "judge", len(judge), file=sys.stderr)
# pass 1: uncovered counter needs cands + mis
uncovered = Counter()
cands = []
n_mis = 0
for line in open(S + "/candidates.jsonl"):
    c = json.loads(line)
    vk = volume_key(c["cite"])
    if vk: uncovered[(c["opinion_id"], vk)] += 1
    cands.append({k: c.get(k) for k in ("opinion_id","cluster_id","date","cite","cited_name","route","best_name_score","ocr")} | {"flag": bool(FLAG.search(c.get("context") or ""))})
mis_vk = Counter()
for line in open(S + "/misattributions.jsonl"):
    m = json.loads(line); n_mis += 1
    vk = volume_key(m["cite"])
    if vk:
        uncovered[(m["opinion_id"], vk)] += 1
        mis_vk[vk.split("|")[0]] += 1
print("candidates", len(cands), "misattributions", n_mis, file=sys.stderr)
def complete_for(opid, vk):
    n = vols.get(vk + "|n", 0) - uncovered[(opid, vk)]
    return n >= 20 and vols.get(vk + "|cov", 0) / n >= 0.98
kept = Counter(); drop = Counter(); kept_rep = Counter(); drop_rep = Counter(); sheet = Counter()
route_kept = Counter(); route_drop = Counter(); ocr_kept = Counter(); ocr_drop = Counter()
flagged = defaultdict(set); flagged_kept = defaultdict(set)
judge_cands = []
for c in cands:
    p = period(int(c["date"])); vk = volume_key(c["cite"]); rep = vk.split("|")[0] if vk else "?"
    t = "flag" if c["flag"] else "reliance"
    cid = int(c["cluster_id"])
    if cid in cal_ids: flagged[cid].add(t)
    ok = p is not None and vk is not None and complete_for(c["opinion_id"], vk)
    if cid in judge:
        judge_cands.append({**c, "period": p, "type": t, "complete_volume": ok, "vol_n": vols.get(vk + "|n", 0) if vk else None, "vol_cov": vols.get(vk + "|cov", 0) if vk else None})
    if ok:
        kept[p] += 1; kept_rep[rep] += 1; sheet[(p, t)] += 1; route_kept[c["route"]] += 1; ocr_kept[c["ocr"]] += 1
        if cid in cal_ids: flagged_kept[cid].add(t)
    else:
        drop[p] += 1; drop_rep[rep] += 1; route_drop[c["route"]] += 1; ocr_drop[c["ocr"]] += 1
res = {
 "kept": dict(kept), "dropped": dict(drop), "sheets": {f"{p}_{t}": n for (p, t), n in sheet.items()},
 "route_kept": dict(route_kept), "route_dropped": dict(route_drop),
 "ocr_kept": {str(k): v for k, v in ocr_kept.items()}, "ocr_dropped": {str(k): v for k, v in ocr_drop.items()},
 "recall_detection_any_candidate": {"orders": len(cal), "flagged": sum(1 for cid in cal_ids if cid in flagged)},
 "recall_detection_after_completeness_filter": {"orders": len(cal), "flagged": sum(1 for cid in cal_ids if cid in flagged_kept)},
 "judge_incidents": [{"case": r["case_name"], "court": r["court"], "date": r["date"], "party": r["party"], "cluster_id": cid,
                      "types_any": sorted(flagged.get(cid, [])), "types_kept": sorted(flagged_kept.get(cid, []))} for cid, r in judge.items()],
 "judge_candidates": judge_cands,
 "top_dropped_reporters": drop_rep.most_common(40), "top_kept_reporters": kept_rep.most_common(40),
}
# volume-level completeness summary per reporter (volumes with n>=20)
per_rep = defaultdict(lambda: [0, 0, 0])  # assessable, complete, total volumes
for k, v in vols.items():
    if k.endswith("|n"):
        rep, vol = k[:-2].split("|"); cov = vols.get(k[:-2] + "|cov", 0)
        per_rep[rep][2] += 1
        if v >= 20:
            per_rep[rep][0] += 1
            if cov / v >= 0.98: per_rep[rep][1] += 1
want = ["us","sct","led2d","f2d","f3d","f4th","fsupp","fsupp2d","fsupp3d","fappx","wl","so2d","so3d","sw2d","sw3d","ne2d","ne3d","nw2d","nw3d","p2d","p3d","a2d","a3d","se2d","calrptr3d","ny3d","ad3d","nys3d","ohio","br","fedcl"]
res["volumes_by_reporter"] = {r: {"assessable": per_rep[r][0], "complete": per_rep[r][1], "volumes_cited": per_rep[r][2]} for r in want if r in per_rep}
for vk in ("f3d|925", "fsupp2d|905", "f3d|174"):
    res[f"volume {vk}"] = {"n": vols.get(vk + "|n"), "cov": vols.get(vk + "|cov"), "complete": (vols.get(vk+"|n",0) >= 20 and vols.get(vk+"|cov",0)/max(1,vols.get(vk+"|n",0)) >= 0.98)}
json.dump(res, open(OUT + "/scan_candidates.json", "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("judge_candidates",)}, indent=1)[:6000])
