"""Prover sampling (plan section 4). For each prover, item and version (original, R1, R2 where certified in the prover's
environment): 32 samples, at most 4,096 new tokens, through an OpenAI-compatible vLLM server. Prompts follow each model
card. The informal problem text is identical across an item's versions, so only the formal statement changes.
Usage: sample.py <prover> <base_url> <served_name> [pilot_items]
Writes data/samples/<prover>.jsonl (one line per request: key, version, outputs[32] with text and finish_reason)."""
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
HEADER = "import Mathlib\nimport Aesop\n\nset_option maxHeartbeats 400000\n\nopen BigOperators Real Nat Topology Rat\n\n"
PLAN = ("Before producing the Lean 4 code to formally prove the given theorem, provide a detailed proof plan outlining the "
        "main proof steps and strategies.\nThe plan should highlight key ideas, intermediate lemmas, and proof structures "
        "that will guide the construction of the final formal proof.")
ENV = {"dsp_v2": "v49", "goedel_v2": "v49", "kimina": "v415"}
SAMPLING = {"dsp_v2": dict(temperature=1.0, top_p=0.95), "goedel_v2": dict(temperature=1.0, top_p=0.95),
            "kimina": dict(temperature=0.6, top_p=0.95)}
N, MAX_TOKENS = 32, 4096


def informal():
    k = pd.read_parquet(RAW / "minif2f_test" / "data" / "train-00000-of-00001.parquet")
    d = pd.read_json(RAW / "dsp15_minif2f.jsonl", lines=True)
    out = {"test/" + r.name: r.informal_prefix for r in k.itertuples()}
    out.update({"valid/" + r.name: r.informal_prefix for r in d[d.split == "valid"].itertuples()})
    return out


def certified_versions(env):
    f = RUN / "data" / "certify" / f"reforms_{env}.jsonl"
    ok = set()
    for line in open(f):
        r = json.loads(line)
        if r.get("status") == "checked" and r.get("ab") and r.get("ba"):
            ok.add(r["key"])
    return ok


def messages(prover, stmt, nl):
    doc = (nl or "").strip()
    code = f"{HEADER}{doc}\n{stmt} := by\n  sorry" if doc else f"{HEADER}{stmt} := by\n  sorry"
    if prover in ("dsp_v2", "goedel_v2"):
        return [{"role": "user", "content": f"Complete the following Lean 4 code:\n\n```lean4\n{code}\n```\n\n{PLAN}"}]
    problem = re.sub(r"^/--\s*|\s*-/\s*$", "", doc, flags=re.S)
    prompt = (f"Think about and solve the following problem step by step in Lean 4.\n# Problem:{problem}\n"
              f"# Formal statement:\n```lean4\n{code.replace(chr(10) + '  sorry', '')}\n```\n")
    return [{"role": "system", "content": "You are an expert in mathematics and Lean 4."}, {"role": "user", "content": prompt}]


def main(prover, base, served, pilot=None):
    ref = pd.read_parquet(RUN / "data" / "reforms.parquet")
    ok = certified_versions(ENV[prover])
    nl = informal()
    jobs = []
    for r in ref.itertuples():
        jobs.append((f"{r.id}|orig", r.orig, nl.get(r.id)))
        for k in ("R1", "R2"):
            if getattr(r, k) and f"{r.id}|{k}" in ok:
                jobs.append((f"{r.id}|{k}", getattr(r, k), nl.get(r.id)))
    if pilot:
        ids = sorted({j[0].split("|")[0] for j in jobs})[:: max(1, len(ref) // int(pilot))][: int(pilot)]
        jobs = [j for j in jobs if j[0].split("|")[0] in ids]
    out = RUN / "data" / "samples" / (f"{prover}_pilot.jsonl" if pilot else f"{prover}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["key"] for l in open(out)} if out.exists() else set()
    todo = [j for j in jobs if j[0] not in done]
    print(f"{prover}: {len(jobs)} item-versions, {len(todo)} to sample", flush=True)

    def one(job):
        key, stmt, doc = job
        body = dict(model=served, messages=messages(prover, stmt, doc), n=N if not pilot else 8, max_tokens=MAX_TOKENS, **SAMPLING[prover])
        for attempt in range(5):
            try:
                r = requests.post(f"{base}/v1/chat/completions", json=body, timeout=3600)
                r.raise_for_status()
                ch = r.json()["choices"]
                return dict(key=key, outputs=[dict(text=c["message"]["content"], finish=c["finish_reason"]) for c in ch])
            except Exception as e:  # noqa: BLE001
                time.sleep(10 * (attempt + 1))
                err = repr(e)[:200]
        return dict(key=key, error=err)

    t0 = time.time()
    with ThreadPoolExecutor(16) as ex, open(out, "a") as f:
        for i, res in enumerate(ex.map(one, todo)):
            f.write(json.dumps(res) + "\n"); f.flush()
            if (i + 1) % 50 == 0:
                print(f"{i + 1}/{len(todo)} | {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
