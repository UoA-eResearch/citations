"""Plan section 4: sample formalizations through an OpenAI-compatible vLLM server.

For every item x condition in results/catalogue/frozen.jsonl (conditions O = original NL, T = twin NL, P = paraphrase;
controls are sampled in O only): 16 samples at temperature 0.8, top_p 0.95, seed 20261012, plus one greedy sample.
Prompts follow each model card (plan section 4); the theorem name is always `my_favorite_theorem`.
Usage: sample.py <model> <base_url> [pilot_n]   ->   data/samples/<model>.jsonl (one line per item x condition)."""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
CAT = RUN / "results" / "catalogue"
NAME, N, SEED = "my_favorite_theorem", 16, 20261012
MAX_TOKENS = {"goedel": 16384}
FEWSHOT = [
    ("Find the real number x such that 2x + 3 = 11. Show that x = 4.",
     "theorem my_favorite_theorem (x : ℝ) (h : 2 * x + 3 = 11) : x = 4 := by sorry"),
    ("Prove that n^2 + n is even for every natural number n.",
     "theorem my_favorite_theorem (n : ℕ) : Even (n ^ 2 + n) := by sorry"),
    ("Let G be a group in which every element is its own inverse. Prove that G is abelian.",
     "theorem my_favorite_theorem {G : Type*} [Group G] (h : ∀ g : G, g * g = 1) (a b : G) : a * b = b * a := by sorry"),
]
INSTR = ("Translate the following problem into a Lean 4 (Mathlib) theorem statement named my_favorite_theorem, ending with "
         "`:= by sorry`. Do not prove it.")


def request(model, nl):
    """(endpoint, body without sampling parameters) for one input text."""
    if model == "kimina":
        msgs = [{"role": "system", "content": "You are an expert in mathematics and Lean 4."},
                {"role": "user", "content": "Please autoformalize the following problem in Lean 4 with a header. Use the "
                                            f"following theorem names: {NAME}.\n\n{nl}"}]
        return "chat", dict(messages=msgs)
    if model == "goedel":
        msg = ("Please autoformalize the following natural language problem statement in Lean 4. "
               f"Use the following theorem name: {NAME}\nThe natural language statement is: \n{nl}"
               "Think before you provide the lean statement.")
        return "chat", dict(messages=[{"role": "user", "content": msg}])
    if model == "herald":
        q = ("Please translate the natural language statement to Lean4 code with the header\n**Name**\n"
             f"{NAME}\n**Informal statement**\n{nl}\n")
        return "completions", dict(prompt=f"User:{q}\n\nAssistant:")
    if model == "dsp_v2":
        return "chat", dict(messages=[{"role": "user", "content": f"{INSTR}\n\n{nl}"}])
    if model == "qwen":
        shots = "\n\n".join(f"Problem: {p}\nLean 4:\n```lean4\n{s}\n```" for p, s in FEWSHOT)
        return "chat", dict(messages=[{"role": "user", "content": f"{INSTR}\n\nExamples:\n\n{shots}\n\nProblem: {nl}\nLean 4:"}])
    raise ValueError(model)


def jobs():
    out = []
    for r in map(json.loads, open(CAT / "frozen.jsonl")):
        out.append((f"{r['item']}|O", r["nl"]))
        if r.get("N_twin"):
            out.append((f"{r['item']}|T", r["N_twin"]))
        if r.get("paraphrase"):
            out.append((f"{r['item']}|P", r["paraphrase"]))
    return out


def main(model, base, pilot=None):
    js = jobs()
    if pilot:
        js = js[:: max(1, len(js) // int(pilot))][: int(pilot)]
    out = RUN / "data" / "samples" / (f"{model}_pilot.jsonl" if pilot else f"{model}.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["key"] for l in open(out)} if out.exists() else set()
    todo = [j for j in js if j[0] not in done]
    print(f"{model}: {len(js)} item-conditions, {len(todo)} to sample", flush=True)
    mt = MAX_TOKENS.get(model, 2048)

    def post(kind, body):
        url = f"{base}/v1/{'chat/completions' if kind == 'chat' else 'completions'}"
        err = None
        for attempt in range(5):
            try:
                r = requests.post(url, json=body, timeout=7200)
                r.raise_for_status()
                return [dict(text=c["message"]["content"] if "message" in c else c["text"], finish=c["finish_reason"])
                        for c in r.json()["choices"]], None
            except Exception as e:  # noqa: BLE001
                err = repr(e)[:200]
                time.sleep(10 * (attempt + 1))
        return None, err

    def one(job):
        key, nl = job
        kind, body = request(model, nl)
        temp, e1 = post(kind, dict(body, model=model, n=N, temperature=0.8, top_p=0.95, seed=SEED, max_tokens=mt))
        greedy, e2 = post(kind, dict(body, model=model, n=1, temperature=0.0, seed=SEED, max_tokens=mt))
        return dict(key=key, outputs=temp, greedy=greedy, error=e1 or e2)

    t0 = time.time()
    with ThreadPoolExecutor(32) as ex, open(out, "a") as f:
        for i, res in enumerate(ex.map(one, todo)):
            if i < 5 and res["outputs"]:  # abort on byte-level BPE artefacts (a misconfigured tokenizer; contamination run D7)
                txt = "".join(o["text"] or "" for o in res["outputs"])
                if txt.count("Ġ") + txt.count("Ċ") > 20:
                    raise SystemExit(f"{model}: byte-level artefacts in decoded output; tokenizer misconfigured")
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            if (i + 1) % 50 == 0:
                print(f"{i + 1}/{len(todo)} | {(time.time() - t0) / 60:.1f} min", flush=True)
    print(f"{model} SAMPLING DONE", flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
