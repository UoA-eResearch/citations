"""Generate the LLM reference corpus (plan section 3) through an OpenAI-compatible endpoint.
Usage: generate.py <label> <base_url> <served_model_name> [max_paragraphs]
Tasks per generation-pool paragraph: POLISH (revise for clarity, keep facts) and DRAFT (summarise in one sentence, then
draft a preamble paragraph from the summary alone). temperature 0.7, top_p 0.95 (fixed before generation).
Writes data/llm_ref/<label>.jsonl (resumable)."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
POLISH = ("Revise this paragraph from a federal rule preamble published in the Federal Register for clarity and "
          "readability, keeping every fact, citation and number. Return only the revised paragraph.\n\nParagraph:\n{p}")
SUMMARY = ("Summarize the following paragraph from a federal rule preamble in one sentence. Return only the sentence."
           "\n\nParagraph:\n{p}")
DRAFT = ("You are drafting the preamble of a federal rule for publication in the Federal Register. Write one paragraph "
         "of the SUPPLEMENTARY INFORMATION section that makes the following point. Return only the paragraph.\n\nPoint: {s}")


def chat(base, model, prompt, max_tokens=700):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "top_p": 0.95,
            "max_tokens": max_tokens}
    if "nemotron" in model:  # reasoning model: thinking disabled so outputs are final text (plan section 3)
        body["chat_template_kwargs"] = {"enable_thinking": False}
    for attempt in range(4):
        try:
            r = requests.post(f"{base}/v1/chat/completions", json=body, timeout=600)
            r.raise_for_status()
            msg = r.json()["choices"][0]["message"]
            return (msg.get("content") or "").strip()
        except Exception:  # noqa: BLE001
            if attempt == 3:
                return None
    return None


def work(args):
    base, model, row = args
    pol = chat(base, model, POLISH.format(p=row["text"]))
    summ = chat(base, model, SUMMARY.format(p=row["text"]), max_tokens=120)
    dra = chat(base, model, DRAFT.format(s=summ)) if summ else None
    return dict(document_number=row["document_number"], para_idx=int(row["para_idx"]), polish=pol, summary=summ, draft=dra)


def main(label, base, model, max_par=4000):
    pool = pd.read_parquet(RUN / "data" / "pools" / "generation_pool_sample.parquet").head(int(max_par))
    out = RUN / "data" / "llm_ref" / f"{label}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = {(j["document_number"], j["para_idx"]) for j in map(json.loads, open(out))}
    todo = [r for r in pool.to_dict("records") if (r["document_number"], int(r["para_idx"])) not in done]
    print(f"{label}: {len(todo)} paragraphs to generate", flush=True)
    with ThreadPoolExecutor(24) as ex, open(out, "a") as f:
        for i, res in enumerate(ex.map(work, [(base, model, r) for r in todo])):
            f.write(json.dumps(res) + "\n")
            if i % 200 == 0:
                f.flush()
                print(i, flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
