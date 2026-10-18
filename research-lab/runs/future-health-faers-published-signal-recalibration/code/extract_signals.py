"""LLM extraction of published signals from abstracts (plan section 2). The local vLLM (Nemotron 3 Nano, OpenAI-
compatible API on localhost:8000) at temperature 0 with a JSON schema; 4 requests at a time so the shared server stays
responsive. Research articles only (Europe PMC source MED/PMC, not preprints, reviews, letters or errata).
Writes data/extract/signals_raw.jsonl (one row per paper: id, the model's JSON, or an error).
v2 (deviation D2; `python code/extract_signals.py v2`): the revised prompt and schema, a 16,384-token budget, the round-2
validation sample first, then the round-1 sample, then the rest; writes data/extract/signals_raw_v2.jsonl."""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import os

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


SIGNAL2 = {**SCHEMA["properties"]["signals"]["items"]["properties"],
           "database": {"type": "string", "enum": ["FAERS", "other", "unclear"]},
           "comparison": {"type": "string", "enum": ["all drugs", "subgroup", "comparator", "interaction", "unclear"]}}
SCHEMA2 = {"type": "object", "properties": {
    "window": SCHEMA["properties"]["window"],
    "signals": {"type": "array", "items": {"type": "object", "properties": SIGNAL2,
                "required": ["database", "drug", "event", "measure", "estimate", "ci_low", "ci_high", "n_cases", "level", "comparison"]}}},
    "required": ["window", "signals"]}
PROMPT2 = """You extract data from the abstract of a pharmacovigilance study.

Return JSON with:
- "window": the period of FAERS data the study analysed, as start/end year and quarter (1-4). Convert months to quarters: January-March = 1, April-June = 2, July-September = 3, October-December = 4. Examples: "January 2004 to June 2023" -> start 2004 quarter 1, end 2023 quarter 2; "Q3 2012 to Q1 2024" -> 2012 quarter 3 to 2024 quarter 1; "July 2019 to March 2024" -> 2019 quarter 3 to 2024 quarter 1; "2004 to 2021" (years only) -> 2004 quarter 1 to 2021 quarter 4. Use the end quarter that contains the stated end month; use quarter 4 only when the end is a year alone, December or Q4. If the start or the end of the FAERS period is not stated, or a period is given only for another database, null.
- "signals": every drug-adverse event association for which the abstract reports a numeric disproportionality estimate, one entry per drug-event-measure. Copy numbers exactly as written.
  - "database": "FAERS" if the estimate comes from FAERS (or openFDA, which serves FAERS data); "other" if it comes from another source (for example JADER, EudraVigilance, VigiBase, VAERS, a hospital, claims or survey database, or a trial); "unclear" if the abstract does not say which.
  - "drug": the drug the estimate belongs to, as written. If the estimate belongs to a drug class, a combination product, a treatment regimen or the co-administration of several drugs, write that whole class, product, regimen or combination, never one component of it.
  - "event": the adverse event the estimate belongs to, as written. Keep grouped names whole: "ventricular arrhythmias and cardiac arrest" is one event, not two.
  - "measure": "ROR" (including an adjusted ROR), "PRR", "IC", "EBGM", or "other".
  - "estimate": the point estimate of that measure. "ci_low" and "ci_high": the 95% confidence interval of that same estimate. If only a bound is reported (for example ROR025 or IC025), set "estimate" to null and put the bound in "ci_low". Never take an interval from a different measure.
  - "comparison": "all drugs" if the drug is compared with all other drugs in the whole database; "subgroup" if the estimate is computed within a patient subgroup or stratum (for example by sex, age, indication, dose or country); "comparator" if the comparison is against a specific drug, drug class or restricted background; "interaction" if the estimate is for a drug-drug interaction or for a factor other than taking the drug; "unclear" otherwise.
  - "level": "PT" if the event is a single specific adverse event term, "SOC" if it is a system organ class (e.g. "cardiac disorders"), "SMQ" or "HLT" if it is a grouped query or category, else "unclear".
  - "n_cases": the number of reports for that drug-event if stated, else null.
Do not include associations without a numeric estimate. Do not invent values.

Abstract:
"""
V2 = len(sys.argv) > 1 and sys.argv[1] == "v2"


def is_article(r):
    if r.get("source") not in ("MED", "PMC"):
        return False
    types = {t.lower() for t in (r.get("pubTypeList") or {}).get("pubType", [])}
    return not (types & {"review", "letter", "editorial", "comment", "published erratum", "retraction of publication", "systematic review"})


def call(rec):
    ab = re.sub(r"<[^>]+>", " ", rec.get("abstractText") or "")
    body = dict(model="nemotron_3_nano_omni", temperature=0, max_tokens=16384 if V2 else int(os.environ.get("MAX_TOKENS", 4096)),  # D1, D2
                messages=[{"role": "user", "content": (PROMPT2 if V2 else PROMPT) + ab}],
                response_format={"type": "json_schema", "json_schema": {"name": "extraction", "schema": SCHEMA2 if V2 else SCHEMA}})
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
    out = RUN / "data" / "extract" / ("signals_raw_v2.jsonl" if V2 else "signals_raw.jsonl"); out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in open(out) if "out" in json.loads(l)} if out.exists() else set()
    todo = [r for r in recs if r["id"] not in done][:limit]
    if V2:   # round-2 validation sample first, then the round-1 sample, then the rest
        v = RUN / "data" / "validation"
        rank = {p: 0 for p in json.load(open(v / "extraction_sample_round2.json"))}
        rank.update({p: 1 for p in json.load(open(v / "extraction_sample.json"))})
        todo.sort(key=lambda r: rank.get(r["id"], 2))
    print(len(recs), "articles with abstracts;", len(todo), "to do", flush=True)
    with open(out, "a") as fh, ThreadPoolExecutor(4) as ex:
        for k, res in enumerate(ex.map(call, todo)):
            fh.write(json.dumps(res) + "\n"); fh.flush()
            if k % 100 == 0:
                print(k, flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None)
