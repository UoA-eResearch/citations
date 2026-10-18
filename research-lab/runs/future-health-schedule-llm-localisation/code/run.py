"""Model runs (plan section 4). Each item in data/items.jsonl under three conditions: zero-shot; retrieval (top-3 BM25
passages from the item's own jurisdiction, data/passages.jsonl); retrieval with an abstention option. Plus a
paraphrase check: 100 random items (seed 20261018) zero-shot with an alternative wording. The local vLLM (Nemotron 3
Nano Omni, OpenAI-compatible API on localhost:8000), temperature 0, JSON-schema-constrained answer, 16,384-token budget,
4 requests at a time. A failed call is retried once; a remaining failure is recorded as an error and scored as
incorrect (reported). Resumable. Writes data/runs.jsonl."""
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from rank_bm25 import BM25Okapi

RUN = Path(__file__).resolve().parents[1]
API = "http://localhost:8000/v1/chat/completions"
DOC = {"NZ": "the New Zealand Pharmaceutical Schedule (Pharmac, community section)", "AU": "the Australian Pharmaceutical Benefits Scheme (PBS) General Schedule"}
Q = {("a", "NZ"): "Is {text} listed for subsidy in the community section of the New Zealand Pharmaceutical Schedule (Pharmac)?",
     ("a", "AU"): "Is {text} listed on the Australian Pharmaceutical Benefits Scheme (PBS) General Schedule?",
     ("b", "NZ"): "Does Pharmac subsidy of {text} in the community require a Special Authority?",
     ("b", "AU"): "Does PBS subsidy of {text} require an authority prescription (Authority Required, including Streamlined Authority)?",
     ("d", "NZ"): "Under Pharmac's Special Authority criteria for {chemical}, is the following one of the criteria: \"{text}\"?",
     ("d", "AU"): "Under the PBS restriction criteria for {chemical}, is the following one of the criteria: \"{text}\"?"}
P = {("a", "NZ"): "Does Pharmac fund {text} for community dispensing in New Zealand?",
     ("a", "AU"): "Is {text} subsidised under the PBS General Schedule in Australia?",
     ("b", "NZ"): "In New Zealand, is a Special Authority needed for {text} to be subsidised by Pharmac?",
     ("b", "AU"): "In Australia, is an authority prescription needed for {text} to be PBS-subsidised?",
     ("d", "NZ"): "Is \"{text}\" among the Special Authority criteria Pharmac sets for {chemical}?",
     ("d", "AU"): "Is \"{text}\" among the PBS restriction criteria for {chemical}?"}


def tok(s):
    return re.findall(r"[a-z0-9]+", s.lower())


def schema(abstain):
    return {"type": "object", "properties": {"answer": {"type": "string", "enum": ["yes", "no"] + (["not stated"] if abstain else [])}},
            "required": ["answer"]}


def prompt(it, cond, passages, para=False):
    q = (P if para else Q)[(it["family"], it["jurisdiction"])].format(**it)
    if cond == "zero":
        return f"Answer this question about {DOC[it['jurisdiction']]}.\n\n{q}\n\nReply with JSON: {{\"answer\": \"yes\"}} or {{\"answer\": \"no\"}}."
    ext = "\n".join(f"[{i + 1}] {p}" for i, p in enumerate(passages))
    tail = ("If the extracts do not state the answer, reply {\"answer\": \"not stated\"}. Otherwise reply {\"answer\": \"yes\"} or {\"answer\": \"no\"}."
            if cond == "abstain" else "Reply with JSON: {\"answer\": \"yes\"} or {\"answer\": \"no\"}.")
    return f"Extracts from {DOC[it['jurisdiction']]}:\n{ext}\n\nUsing the extracts, answer: {q}\n\n{tail}"


def call(job):
    it, cond, text = job
    body = dict(model="nemotron_3_nano_omni", temperature=0, max_tokens=16384, messages=[{"role": "user", "content": text}],
                response_format={"type": "json_schema", "json_schema": {"name": "answer", "schema": schema(cond == "abstain")}})
    err = ""
    for _ in range(2):
        try:
            r = requests.post(API, json=body, timeout=900); r.raise_for_status()
            return dict(id=it["id"], condition=cond, answer=json.loads(r.json()["choices"][0]["message"]["content"])["answer"])
        except Exception as e:  # noqa: BLE001
            err = str(e)[:200]
    return dict(id=it["id"], condition=cond, error=err)


def main():
    items = [json.loads(l) for l in open(RUN / "data" / "items.jsonl")]
    pas = [json.loads(l) for l in open(RUN / "data" / "passages.jsonl")]
    bm = {j: ([p["text"] for p in pas if p["jurisdiction"] == j]) for j in ("NZ", "AU")}
    idx = {j: BM25Okapi([tok(t) for t in docs]) for j, docs in bm.items()}
    out = RUN / "data" / "runs.jsonl"
    done = {(json.loads(l)["id"], json.loads(l)["condition"]) for l in open(out) if "answer" in json.loads(l)} if out.exists() else set()
    para_ids = set(it["id"] for it in random.Random(20261018).sample(items, 100))
    jobs = []
    for it in items:
        q = Q[(it["family"], it["jurisdiction"])].format(**it)
        top = idx[it["jurisdiction"]].get_top_n(tok(q), bm[it["jurisdiction"]], n=3)
        for cond in ("zero", "retrieval", "abstain"):
            if (it["id"], cond) not in done:
                jobs.append((it, cond, prompt(it, cond, top)))
        if it["id"] in para_ids and (it["id"], "paraphrase") not in done:
            jobs.append((it, "paraphrase", prompt(it, "zero", top, para=True)))
    print(len(items), "items;", len(jobs), "calls to make", flush=True)
    with open(out, "a") as fh, ThreadPoolExecutor(4) as ex:
        for k, res in enumerate(ex.map(call, jobs)):
            fh.write(json.dumps(res) + "\n"); fh.flush()
            if k % 100 == 0:
                print(k, flush=True)


if __name__ == "__main__":
    main()
