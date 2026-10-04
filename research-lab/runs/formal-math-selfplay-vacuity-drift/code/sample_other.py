"""Secondary corpora (plan.md section 2): convert to the pipeline's (prompt ending ':= by', target) form and draw the
preregistered uniform samples (seed 20261005). Rows whose code cannot be split (no theorem, or a term-mode proof) are
counted and dropped. Writes data/samples/<corpus>.parquet and results/tables/other_corpora_conversion.csv."""
import glob
import re
from pathlib import Path

import numpy as np
import pandas as pd

from vacuity import DECL, mask_comments, OPEN, CLOSE

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
OUT = RUN / "data" / "samples"
PFX = "Complete the following Lean 4 code:\n\n```lean4\n"
SEED = 20261005


def split_full(code):
    """Full file -> (prompt, target) split right after the main theorem's ':= by'. None if not possible."""
    ms = list(DECL.finditer(code))
    if not ms:
        return None
    m = ms[-1]
    masked = mask_comments(code)
    depth, colon = 0, None
    for i in range(m.end(), len(code)):
        ch = masked[i]
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth -= 1
        elif depth == 0 and ch == ":" and colon is None and masked[i + 1:i + 2] not in ("=", ":") and masked[i - 1:i] != ":":
            colon = i
        elif depth == 0 and colon is not None and masked.startswith(":=", i):
            mb = re.match(r":=\s*by\b", masked[i:])
            if not mb:
                return None  # term-mode proof
            j = i + mb.end()
            return PFX + code[:j].rstrip() if code[:j].endswith("by") else None, code[j:]
    return None


def draw(df, n, rng):
    return df.iloc[rng.choice(len(df), min(n, len(df)), replace=False)]


def main():
    rng = np.random.default_rng(SEED)
    conv, out = [], {}
    # Goedel Lean-workbook-proofs
    d = pd.read_parquet(RAW / "Lean-workbook-proofs" / "data" / "train-00000-of-00001.parquet")
    out["workbook"] = (draw(d, 5000, rng), lambda r: split_full(r.full_proof), {})
    # Goedel SFT v2: the final ```lean4 block of the assistant message
    parts = []
    fs = sorted(glob.glob(str(RAW / "SFT_dataset_v2" / "data" / "*.parquet")))
    sizes = [pd.read_parquet(f, columns=[]).shape[0] for f in fs]
    total = sum(sizes)
    alloc = np.random.default_rng(SEED + 1).multinomial(10000, np.array(sizes) / total)
    for f, k in zip(fs, alloc):
        s = pd.read_parquet(f)
        s = draw(s, k, rng).copy()
        s["code"] = s.messages.map(lambda m: (re.findall(r"```lean4\n(.*?)```", m[-1]["content"], re.S) or [""])[-1])
        s["negation"] = s.messages.map(lambda m: "_negation" in m[0]["content"])
        s["shard"] = Path(f).name
        parts.append(s[["code", "negation", "shard"]])
    sft = pd.concat(parts, ignore_index=True)
    out["sftv2"] = (sft, lambda r: split_full(r.code), {"negation": "negation"})
    conv.append(dict(corpus="sftv2", population=total))
    # DeepSeek-Prover-V1
    d = pd.read_json(RAW / "DeepSeek-Prover-V1" / "dataset.jsonl", lines=True)
    out["dsp1"] = (draw(d, 5000, rng), lambda r: (PFX + r.header + r.formal_statement.rstrip(), "\n" + r.formal_proof) if r.formal_statement.rstrip().endswith(":= by") else None, {})
    # NuminaMath-LEAN (model proofs), Lean 4.15
    n = pd.read_parquet(RAW / "NuminaMath-LEAN" / "data" / "train-00000-of-00001.parquet")
    n = n[n.formal_proof.fillna("").str.len() > 0].copy()
    n["win_rate"] = n.rl_data.map(lambda x: x["win_rate"] if x is not None else np.nan)
    n["n_proofs"] = n.rl_data.map(lambda x: x["n_proofs"] if x is not None else np.nan)
    out["numina"] = (draw(n, 10000, rng), lambda r: split_full(r.formal_proof), {"win_rate": "win_rate", "n_proofs": "n_proofs", "author": "author", "uuid": "uuid"})
    pops = {"workbook": 29750, "sftv2": total, "dsp1": len(d), "numina": len(n)}
    rows = []
    for name, (df, f, extra) in out.items():
        recs, bad = [], 0
        for i, r in enumerate(df.itertuples()):
            pt = f(r)
            if not pt or pt[0] is None:
                bad += 1
                continue
            rec = dict(row_id=i, prompt=pt[0], target=pt[1], iteration=-1.0, corpus=name)
            rec.update({k: getattr(r, v) for k, v in extra.items()})
            recs.append(rec)
        pd.DataFrame(recs).to_parquet(OUT / f"{name}.parquet")
        rows.append(dict(corpus=name, population=pops[name], drawn=len(df), converted=len(recs), dropped=bad))
    c = pd.DataFrame(rows)
    c.to_csv(RUN / "results" / "tables" / "other_corpora_conversion.csv", index=False)
    print(c.to_string(index=False))


if __name__ == "__main__":
    main()
