"""Extraction check (plan section 5): a random 15% of processed papers (at least 50; seed 20261019), whatever they
yielded, so both precision and recall can be judged. The sheet shows the abstract, the extracted window and ROR
signals, and an automatic flag for whether each extracted number appears verbatim in the abstract. Hand adjudication is
entered in results/tables/extraction_validation.csv (per signal: correct drug/event/estimate/CI/window; per paper:
eligible signals missed)."""
import json
import random
import re
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]


def num_in(x, text):
    if x is None:
        return None
    s = f"{x:g}" if isinstance(x, float) else str(x)
    return bool(re.search(r"(?<![\d.])" + re.escape(s) + r"(?![\d])", text))


def main():
    recs = {str(json.loads(l)["id"]): json.loads(l) for l in open(RUN / "data" / "raw" / "epmc" / "records.jsonl")}
    ex = [json.loads(l) for l in open(RUN / "data" / "extract" / "signals_raw.jsonl")]
    ex = {r["id"]: r for r in ex if "out" in r}
    ids = sorted(ex)
    k = max(50, round(0.15 * len(ids)))
    pick = sorted(random.Random(20261019).sample(ids, k))
    lines = []
    for pid in pick:
        ab = re.sub(r"<[^>]+>", " ", recs[pid].get("abstractText") or "")
        o = ex[pid]["out"]
        lines.append(f"### {pid} | {recs[pid].get('title', '')[:140]}\nABSTRACT: {ab}\nWINDOW: {o.get('window')}")
        for j, s in enumerate(o.get("signals") or []):
            flags = {f: num_in(s.get(f), ab) for f in ("estimate", "ci_low", "ci_high")}
            lines.append(f"  s{j}: {s.get('measure')} | {s.get('drug')} | {s.get('event')} [{s.get('level')}] | {s.get('estimate')} "
                         f"({s.get('ci_low')}-{s.get('ci_high')}) n={s.get('n_cases')} | verbatim {flags}")
        lines.append("")
    (RUN / "data" / "validation").mkdir(parents=True, exist_ok=True)
    (RUN / "data" / "validation" / "extraction_sheet.txt").write_text("\n".join(lines))
    json.dump(pick, open(RUN / "data" / "validation" / "extraction_sample.json", "w"))
    print(len(pick), "papers sampled of", len(ids))


if __name__ == "__main__":
    main()
