"""Extract and normalise formal statements from the benchmarks and the training corpora (plan sections 2-3).
Writes data/statements/<name>.parquet with columns: id, stmt (the theorem text up to ':= by'), norm (normalised),
numerals (sorted numeral multiset as a string) and idents (sorted identifier set as a string)."""
import ast
import json
import re
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
OUT = RUN / "data" / "statements"
THM = re.compile(r"(?ms)^(?:theorem|lemma)\s+\S+.*?:=\s*by", re.M)
NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")
IDENT = re.compile(r"[A-Za-z_Ͱ-Ͽ][\w'₀-₉Ͱ-Ͽ.]*")
KEYWORDS = {"theorem", "lemma", "by", "fun", "let", "in", "have", "show", "from", "at", "with", "if", "then", "else"}


def strip_comments(s):
    s = re.sub(r"/-.*?-/", " ", s, flags=re.S)
    return re.sub(r"--[^\n]*", " ", s)


def statement(text):
    """The last theorem/lemma in a Lean snippet, from its keyword to ':= by' (or the end if absent)."""
    t = strip_comments(text)
    t = "\n".join(l for l in t.splitlines() if not re.match(r"\s*(import|open|set_option|namespace|end|section|noncomputable)\b", l))
    ms = list(re.finditer(r"(?m)^\s*(?:theorem|lemma)\s+\S+", t))
    if not ms:
        return None
    s = t[ms[-1].start():]
    k = s.find(":= by")
    k = s.find(":=") if k < 0 else k
    return s[:k].strip() if k >= 0 else s.strip()


def normalise(stmt):
    s = re.sub(r"^\s*(?:theorem|lemma)\s+\S+", "", stmt)
    return re.sub(r"\s+", " ", s).strip()


def features(norm):
    nums = sorted(NUM.findall(norm))
    ids = sorted({w for w in IDENT.findall(norm) if w not in KEYWORDS})
    return " ".join(nums), " ".join(ids)


def table(ids, texts):
    rows = []
    for i, t in zip(ids, texts):
        if not isinstance(t, str):
            continue
        s = statement(t)
        if not s:
            continue
        n = normalise(s)
        nu, idn = features(n)
        rows.append(dict(id=str(i), stmt=s, norm=n, numerals=nu, idents=idn))
    return pd.DataFrame(rows)


def prompt_code(content):
    m = re.search(r"```lean4\n(.*?)(?:```|$)", content, re.S)
    return m.group(1) if m else content


def main(which=None):
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = {}
    # benchmarks
    k = pd.read_parquet(RAW / "minif2f_test" / "data" / "train-00000-of-00001.parquet")
    d = pd.read_json(RAW / "dsp15_minif2f.jsonl", lines=True)
    v = d[d.split == "valid"]
    jobs["bench_minif2f"] = lambda: pd.concat([table("test/" + k.name, k.formal_statement), table("valid/" + v.name, v.formal_statement)])
    v2 = pd.read_json(RAW / "miniF2F_v2" / "miniF2F_v2c.jsonl", lines=True)
    jobs["bench_minif2f_v2c"] = lambda: table(v2.split + "/" + v2.name, v2.formal_statement)
    pn = pd.concat([pd.read_parquet(f) for f in sorted((RAW / "ProofNetSharp" / "data").glob("*.parquet"))])
    jobs["bench_proofnet"] = lambda: table(pn.id.astype(str), pn.lean4_formalization)

    def putnam():
        fs = sorted((RAW / "PutnamBench" / "lean4" / "src").glob("*.lean"))
        return table([f.stem for f in fs], [f.read_text() for f in fs])
    jobs["bench_putnam"] = putnam
    # corpora
    jobs["goedel_pset"] = lambda: pd.concat([table(x.problem_id, x.formal_statement) for x in
                                             (pd.read_parquet(f) for f in sorted((RAW / "Goedel-Pset-v1" / "data").glob("*.parquet")))])
    lw = json.load(open(RAW / "Lean-Workbook" / "lean_workbook.json"))
    # D9: Lean Workbook statements end in ":=  by sorry" (two spaces); strip it before appending ":= by"
    jobs["lean_workbook"] = lambda: table([f"lw{i}" for i in range(len(lw))], [re.sub(r":=\s*by\s*sorry\s*$", "", x["formal_statement"].strip()) + " := by" for x in lw])
    dsp = pd.read_json(RAW / "DeepSeek-Prover-V1" / "dataset.jsonl", lines=True)
    jobs["dsp_v1"] = lambda: table(dsp.name, dsp.formal_statement)
    nm = pd.read_parquet(RAW / "NuminaMath-LEAN" / "data" / "train-00000-of-00001.parquet")
    jobs["numina_lean"] = lambda: table(nm.uuid, nm.formal_statement)
    lwp = pd.read_parquet(RAW / "Lean-workbook-proofs" / "data" / "train-00000-of-00001.parquet")
    jobs["goedel_lwproofs"] = lambda: table(lwp.problem_id, lwp.full_proof)

    def stp():
        parts = []
        for f in sorted((RAW / "STP_Lean_0320" / "data").glob("*.parquet")):
            x = pd.read_parquet(f, columns=["prompt"]).drop_duplicates("prompt")
            parts.append(x)
        x = pd.concat(parts).drop_duplicates("prompt").reset_index(drop=True)
        return table("stp" + x.index.astype(str), x.prompt.map(prompt_code))
    jobs["stp"] = stp

    def sft():
        parts = []
        for f in sorted((RAW / "SFT_dataset_v2" / "data").glob("*.parquet")):
            m = pd.read_parquet(f, columns=["messages"]).messages
            u = m.map(lambda s: next((x["content"] for x in (ast.literal_eval(s) if isinstance(s, str) else s) if x["role"] == "user"), ""))
            parts.append(u.drop_duplicates())
        u = pd.concat(parts).drop_duplicates().reset_index(drop=True)
        return table("sft" + u.index.astype(str), u.map(prompt_code))
    jobs["sft_v2"] = sft
    for name, fn in jobs.items():
        if which and name not in which:
            continue
        t = fn()
        t = t.drop_duplicates("norm") if not name.startswith("bench") else t
        t.to_parquet(OUT / f"{name}.parquet")
        print(name, len(t), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
