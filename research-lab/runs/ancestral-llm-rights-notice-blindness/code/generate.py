"""Generate responses from one model served by a local vLLM OpenAI-compatible server. All inference is local:
no record is sent to any third-party API. Greedy decoding (temperature 0), max 1,100 new tokens; Qwen3 in its
non-thinking mode. Resumable: rows already in the output file are skipped.

Usage: venv/bin/python code/generate.py <label> <base_url> <served_name> <set: pilot|main>
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prompts import FRAMINGS  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
MAX_TOKENS = 1100   # raised from 700 after 11 of Qwen's first 46 pilot responses hit the cap (deviations D3)


def main(label, base, served, which):
    rows = [json.loads(l) for l in open(RUN / "data" / "corpus" / f"{which}.jsonl")]
    out = RUN / "data" / "generations" / f"{label}_{which}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for l in open(out):
            r = json.loads(l); done.add((r["doi"], r["condition"], r["framing"]))
    jobs = [(r, f) for r in rows for f in FRAMINGS if (r["doi"], r["condition"], f) not in done]
    extra = {"chat_template_kwargs": {"enable_thinking": False}} if label.startswith("qwen3") else {}

    def one(job):
        r, f = job
        body = dict(model=served, messages=[{"role": "user", "content": FRAMINGS[f].format(metadata=r["metadata"])}],
                    temperature=0.0, max_tokens=MAX_TOKENS, seed=0, **extra)
        for i in range(5):
            try:
                resp = requests.post(f"{base}/v1/chat/completions", json=body, timeout=600).json()
                c = resp["choices"][0]
                return dict(doi=r["doi"], condition=r["condition"], framing=f, model=label,
                            text=c["message"]["content"], finish=c.get("finish_reason"),
                            usage=resp.get("usage"))
            except Exception as e:
                err = e; time.sleep(5 * (i + 1))
        return dict(doi=r["doi"], condition=r["condition"], framing=f, model=label, error=str(err))

    with open(out, "a") as fh, ThreadPoolExecutor(48) as ex:
        for k, res in enumerate(ex.map(one, jobs)):
            fh.write(json.dumps(res, ensure_ascii=False) + "\n")
            if k % 500 == 0:
                print(label, which, k, "/", len(jobs), flush=True)
    print(label, which, "done", len(jobs))


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:5]))
