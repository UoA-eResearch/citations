"""Compact view of the extraction-check sample for hand adjudication: per paper, only the abstract sentences that carry
a numeric disproportionality estimate (ROR/PRR/IC/EBGM/odds ratio with a number) or the data window (quarters/years),
then the extracted window and signals with verbatim flags. A missed eligible signal must sit in one of these sentences.
Writes data/validation/extraction_compact.txt."""
import json
import re
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
NUM = re.compile(r"(ROR|PRR|IC\b|IC025|EBGM|EB05|odds ratio|BCPNN|MGPS)[^.;]{0,120}\d", re.I)
WIN = re.compile(r"(quarter|Q[1-4]\b|\b(19|20)\d\d\b)", re.I)


def main():
    pick = json.load(open(RUN / "data" / "validation" / "extraction_sample.json"))
    recs = {str(json.loads(l)["id"]): json.loads(l) for l in open(RUN / "data" / "raw" / "epmc" / "records.jsonl")}
    ex = {json.loads(l)["id"]: json.loads(l) for l in open(RUN / "data" / "extract" / "signals_raw.jsonl") if "out" in json.loads(l)}
    out = []
    for pid in pick:
        ab = re.sub(r"<[^>]+>", " ", recs[pid].get("abstractText") or "")
        sents = re.split(r"(?<=[.;])\s+", ab)
        num = [s for s in sents if NUM.search(s)]
        win = [s for s in sents if WIN.search(s) and ("FAERS" in s or "quarter" in s.lower() or "from" in s.lower())][:2]
        o = ex[pid]["out"]
        out.append(f"### {pid}\nWINDOW-SENT: {' | '.join(w[:260] for w in win)}\nEXTRACTED WINDOW: {o.get('window')}")
        for s in num:
            out.append(f"  NUM: {s[:600]}")
        for j, s in enumerate(o.get("signals") or []):
            out.append(f"  s{j}: {s.get('measure')} | {s.get('drug')} | {s.get('event')} [{s.get('level')}] | {s.get('estimate')} ({s.get('ci_low')}-{s.get('ci_high')})")
        out.append("")
    (RUN / "data" / "validation" / "extraction_compact.txt").write_text("\n".join(out))
    print(len(pick), "papers;", sum(1 for x in out if x.startswith("  NUM")), "numeric sentences")


if __name__ == "__main__":
    main()
