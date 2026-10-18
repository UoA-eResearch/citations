"""Focused extraction-check sheet: of the sampled papers, those that either yielded a candidate-eligible signal (ROR with
estimate and 95% CI, lower bound > 1, a window) or whose abstract mentions a numeric ROR (so an eligible signal could
have been missed). Full abstract, then the extracted ROR signals. The rest of the sample (no numeric ROR in the abstract
and no ROR extracted) has nothing to verify for eligible signals. Writes data/validation/extraction_focus.txt."""
import json
import re
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
RORNUM = re.compile(r"(ROR|reporting odds ratio)[^.;]{0,160}\d", re.I)


def main():
    pick = json.load(open(RUN / "data" / "validation" / "extraction_sample.json"))
    recs = {str(json.loads(l)["id"]): json.loads(l) for l in open(RUN / "data" / "raw" / "epmc" / "records.jsonl")}
    ex = {json.loads(l)["id"]: json.loads(l) for l in open(RUN / "data" / "extract" / "signals_raw.jsonl") if "out" in json.loads(l)}
    out, n_focus, n_rest = [], 0, 0
    for pid in pick:
        ab = re.sub(r"<[^>]+>", " ", recs[pid].get("abstractText") or "")
        o = ex[pid]["out"]
        ror = [(j, s) for j, s in enumerate(o.get("signals") or []) if s.get("measure") == "ROR"]
        cand = [(j, s) for j, s in ror if s.get("estimate") is not None and s.get("ci_low") is not None and s.get("ci_high") is not None and s["ci_low"] > 1 and o.get("window")]
        if not cand and not RORNUM.search(ab) and not any(s.get("measure") in ("PRR",) and s.get("ci_low") for s in o.get("signals") or []):
            n_rest += 1; continue
        n_focus += 1
        out.append(f"### {pid}\nABSTRACT: {ab}\nWINDOW: {o.get('window')}")
        for j, s in enumerate(o.get("signals") or []):
            mark = "CAND" if (j, s) in cand else "    "
            out.append(f"  {mark} s{j}: {s.get('measure')} | {s.get('drug')} | {s.get('event')} [{s.get('level')}] | {s.get('estimate')} ({s.get('ci_low')}-{s.get('ci_high')})")
        out.append("")
    (RUN / "data" / "validation" / "extraction_focus.txt").write_text("\n".join(out))
    print(n_focus, "papers to check;", n_rest, "with no numeric ROR and nothing extracted")


if __name__ == "__main__":
    main()
