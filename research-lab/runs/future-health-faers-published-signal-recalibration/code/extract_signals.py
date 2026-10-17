"""LLM extraction of published signals from abstracts (plan section 2). The local vLLM (Nemotron 3 Nano, OpenAI-
compatible API on localhost:8000) at temperature 0 with a JSON schema; 4 requests at a time so the shared server stays
responsive. Research articles only (Europe PMC source MED/PMC, not preprints, reviews, letters or errata).
Writes data/extract/signals_raw.jsonl (one row per paper: id, the model's JSON, or an error)."""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
API = "http://localhost:8000/v1/chat/completions"
SCHEMA = {"type": "object", "properties": {
    "window": {"type": ["object", "null"], "properties": {"start_year": {"type": "integer"}, "start_quarter": {"type": "integer"},
                                                       "end_year": {"type": "integer"}, "end_quarter": {"type": "integer"}},
               "required": ["start_year", "start_quarter", "end_year", "end_quarter"]},
    "signals": {"type": "array", "items": {"type": "object", "properties": {
        "drug": {"type": "string"}, "event": {"type": "string"},
        "measure": {"type": "string", "enum": ["ROR", "PRR", "IC", "EBGM", "other"]},
        "estimate": {"type": ["number", "null"]}, "ci_low": {"type": ["number", "null"]}, "ci_high": {"type": ["number", "null"]},
        "n_cases": {"type": ["integer", "null"]},
        "level": {"type": "string", "enum": ["PT", "SOC", "HLT", "SMQ", "unclear"]}},
        "required": ["drug", "event", "measure", "estimate", "ci_low", "ci_high", "n_cases", "level"]}}},
    "required": ["window", "signals"]}
PROMPT = """You extract data from the abstract of a pharmacovigilance study that used the FDA Adverse Event Reporting System (FAERS).

Return JSON with:
- "window": the FAERS data period the study analysed, as start/end year and quarter (Q1=1..Q4=4). If the abstract gives only years, use Q1 of the start year and Q4 of the end year. If no period is stated, null.
- "signals": every drug-adverse event association for which the abstract reports a numeric disproportionality estimate. One entry per drug-event-measure. Copy numbers exactly as written. "drug" is the single drug name as written; "event" is the adverse event name as written; "level" is PT if the event is a single specific adverse event term, SOC if it is a system organ class (e.g. "cardiac disorders"), SMQ/HLT if it is a grouped query or category, else unclear. "n_cases" is the number of reports for that drug-event if stated, else null. Do not include associations without a numeric estimate. Do not invent values.

Abstract:
"""


def is_article(r):
    if r.get("source") not in ("MED", "PMC"):
        return False
    types = {t.lower() for t in (r.get("pubTypeList") or {}).get("pubType", [])}
    return not (types & {"review", "letter", "editorial", "comment", "published erratum", "retraction of publication", "systematic review"})


def call(rec):
    ab = re.sub(r"<[^>]+>", " ", rec.get("abstractText") or "")
    body = dict(model="nemotron_3_nano_omni", temperature=0, max_tokens=4096,
                messages=[{"role": "user", "content": PROMPT + ab}],
                response_format={"type": "json_schema", "json_schema": {"name": "extraction", "schema": SCHEMA}})
    try:
        r = requests.post(API, json=body, timeout=600)
        r.raise_for_status()
        txt = r.json()["choices"][0]["message"]["content"]
        return dict(id=rec["id"], source=rec["source"], out=json.loads(txt))
    except Exception as e:  # noqa: BLE001
        return dict(id=rec["id"], source=rec["source"], error=str(e)[:200])


def main(limit=None):
    recs = [json.loads(l) for l in open(RUN / "data" / "raw" / "epmc" / "records.jsonl")]
    recs = [r for r in recs if is_article(r) and r.get("abstractText")]
    out = RUN / "data" / "extract" / "signals_raw.jsonl"; out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in open(out) if "out" in json.loads(l)} if out.exists() else set()
    todo = [r for r in recs if r["id"] not in done][:limit]
    print(len(recs), "articles with abstracts;", len(todo), "to do", flush=True)
    with open(out, "a") as fh, ThreadPoolExecutor(4) as ex:
        for k, res in enumerate(ex.map(call, todo)):
            fh.write(json.dumps(res) + "\n"); fh.flush()
            if k % 100 == 0:
                print(k, flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None)
