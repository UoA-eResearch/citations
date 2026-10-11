"""Plan 2.3: blind defect tagging by two raters.

  tagging.py prepare   -> results/catalogue/tagging/batch_NN.md (blinded: NL, statements A and B in seeded random order,
                          theorem names replaced by X, no source or role), and the A/B key in data/tagging_key.json
                          (gitignored until the ratings are in; then copied to results/)
  tagging.py collect   -> results/catalogue/tags.jsonl (both raters' tags mapped back to D and C) and inclusion

Raters: A = Claude Opus 5.5, B = Claude Fable 5.1 subagents, each told to read only its batch file and to write
results/catalogue/tagging/rater{A,B}_NN.json."""
import json
import random
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
CAT = RUN / "results" / "catalogue"
TAG = CAT / "tagging"
KEY = RUN / "data" / "tagging_key.json"
SEED, SIZE = 20261012, 40
sys.path.insert(0, str(Path(__file__).resolve().parent))


def blind(stmt):
    """The statement with its theorem name replaced by X and any proof or trailing `:= by` removed."""
    s = re.sub(r"(?m)^(\s*(?:theorem|lemma))\s+[^\s(\[{⦃:]+", r"\1 X", stmt.strip(), count=1)
    s = re.sub(r"\s*:=\s*(by)?\s*(sorry)?\s*$", "", s)
    return s.strip()


def prepare():
    TAG.mkdir(parents=True, exist_ok=True)
    df = pd.read_json(CAT / "filtered.jsonl", lines=True)
    df = df[(df.fate == "kept") & (df.role == "primary")].sort_values("item").reset_index(drop=True)
    rng = random.Random(SEED)
    order = list(range(len(df)))
    rng.shuffle(order)
    key = {}
    batches = [order[i:i + SIZE] for i in range(0, len(order), SIZE)]
    for b, idx in enumerate(batches):
        lines = [f"# Tagging batch {b:02d} ({len(idx)} items)\n"]
        for j in idx:
            r = df.iloc[j]
            tid = f"t{j:03d}"
            d_is_a = rng.random() < 0.5
            key[tid] = dict(item=r["item"], A="D" if d_is_a else "C", batch=b)
            a, bb = (r["D"], r["C"]) if d_is_a else (r["C"], r["D"])
            lines.append(f"## {tid}\n\n**Informal statement**\n\n{r['nl']}\n\n**Formal statement A**\n\n```lean\n{blind(a)}\n```\n\n"
                         f"**Formal statement B**\n\n```lean\n{blind(bb)}\n```\n")
        (TAG / f"batch_{b:02d}.md").write_text("\n".join(lines))
    KEY.write_text(json.dumps(key, indent=1))
    print(len(df), "items in", len(batches), "batches")


def collect():
    key = json.loads(KEY.read_text())
    shutil.copy(KEY, TAG / "key.json")
    rows = {}
    for rater in ("A", "B"):
        for f in sorted(TAG.glob(f"rater{rater}_*.json")):
            for t in json.load(open(f)):
                k = key[t["id"]]
                d_lab = k["A"] == "D" and "A" or "B"
                c_lab = "B" if d_lab == "A" else "A"
                r = rows.setdefault(t["id"], dict(tid=t["id"], item=k["item"]))
                r[f"{rater}_D_faithful"] = t[d_lab]["faithful"]
                r[f"{rater}_C_faithful"] = t[c_lab]["faithful"]
                r[f"{rater}_D_category"] = t[d_lab].get("category")
                r[f"{rater}_C_category"] = t[c_lab].get("category")
                r[f"{rater}_D_reason"] = t[d_lab].get("reason")
                r[f"{rater}_C_reason"] = t[c_lab].get("reason")
    df = pd.DataFrame(rows.values())
    missing = set(key) - set(df.tid)
    assert not missing, f"untagged: {sorted(missing)[:10]}"
    for rater in ("A", "B"):
        df[f"{rater}_defect"] = (df[f"{rater}_D_faithful"] == False) & (df[f"{rater}_C_faithful"] == True)  # noqa: E712
    df["included"] = df.A_defect & df.B_defect
    df["one_rater"] = (df.A_defect | df.B_defect) & ~df.included
    df["category"] = df.A_D_category.where(df.A_defect, df.B_D_category)
    df.to_json(CAT / "tags.jsonl", orient="records", lines=True, force_ascii=False)
    # agreement on faithfulness of D (Cohen's kappa)
    a, b = df.A_D_faithful.astype(bool), df.B_D_faithful.astype(bool)
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    print(dict(n=len(df), included=int(df.included.sum()), one_rater=int(df.one_rater.sum()),
               kappa_D=round((po - pe) / (1 - pe), 3) if pe < 1 else None))


if __name__ == "__main__":
    {"prepare": prepare, "collect": collect}[sys.argv[1]]()
