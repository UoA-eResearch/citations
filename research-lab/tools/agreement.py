"""G7 two independent blind labellers: agreement and adjudication (see METHODS.md).

    python3 -I tools/agreement.py LABELS_A.json LABELS_B.json [--field match] [--out agreement.json]
        LABELS_*.json: {"item_id": {"<field>": label, ...}, ...} (labels may be strings or lists; lists are compared
        as sets, so ["A","C"] == ["C","A"])
        -> percent agreement, Cohen's kappa (nominal), per-class counts, and the list of disagreeing items to send to
           a third blind adjudication pass

    python3 -I tools/agreement.py --merge LABELS_A.json LABELS_B.json ADJUDICATED.json --out FINAL.json
        final label = the shared label where A and B agree, else the adjudicator's label
"""
import json
import sys
from collections import Counter


def norm(v):
    if isinstance(v, list):
        return "|".join(sorted(map(str, v))) or "none"
    return str(v)


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return po, (po - pe) / (1 - pe) if pe < 1 else float("nan")


def compare(pa, pb, field="match"):
    A, B = json.load(open(pa)), json.load(open(pb))
    items = sorted(set(A) & set(B))
    missing = sorted(set(A) ^ set(B))
    a = [norm(A[i][field] if isinstance(A[i], dict) else A[i]) for i in items]
    b = [norm(B[i][field] if isinstance(B[i], dict) else B[i]) for i in items]
    po, k = kappa(a, b)
    dis = [i for i, x, y in zip(items, a, b) if x != y]
    return {"items": len(items), "missing_in_one": missing, "percent_agreement": round(po, 4), "cohen_kappa": round(k, 4),
            "label_counts_a": dict(Counter(a)), "label_counts_b": dict(Counter(b)), "disagreements": dis}


def merge(pa, pb, padj, field="match"):
    A, B, J = json.load(open(pa)), json.load(open(pb)), json.load(open(padj))
    out, src = {}, Counter()
    for i in sorted(set(A) & set(B)):
        la = A[i][field] if isinstance(A[i], dict) else A[i]
        lb = B[i][field] if isinstance(B[i], dict) else B[i]
        if norm(la) == norm(lb):
            out[i] = {field: la, "source": "agreed"}; src["agreed"] += 1
        elif i in J:
            out[i] = {field: J[i][field] if isinstance(J[i], dict) else J[i], "source": "adjudicated"}; src["adjudicated"] += 1
        else:
            raise SystemExit(f"item {i}: labellers disagree and no adjudication label")
    return out, dict(src)


if __name__ == "__main__":
    a = sys.argv[1:]
    field = a[a.index("--field") + 1] if "--field" in a else "match"
    outp = a[a.index("--out") + 1] if "--out" in a else None
    if a[0] == "--merge":
        res, src = merge(a[1], a[2], a[3], field)
        json.dump(res, open(outp, "w"), indent=1)
        print("merged", src)
    else:
        r = compare(a[0], a[1], field)
        if outp:
            json.dump(r, open(outp, "w"), indent=1)
        print(json.dumps({k: v for k, v in r.items() if k != "disagreements"}, indent=1),
              f"\n{len(r['disagreements'])} disagreements -> adjudicate")
