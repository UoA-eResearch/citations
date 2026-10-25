"""G4 error audit for validation metrics (see METHODS.md).

    python3 -I tools/error_audit.py init ERRORS.csv OUT.csv
        ERRORS.csv: one row per validation error (any columns; must include an id column); writes OUT.csv with the
        audit columns appended, to be filled in by hand: class (artefact | label_noise | genuine), note
    python3 -I tools/error_audit.py summarise OUT.csv N_EVALUATED N_CORRECT [--out audit.json]
        -> counts per class and the metric three ways: as measured; excluding artefacts (judgeable denominator);
           excluding artefacts and counting label-noise cases as correct

Classes:
  artefact     the validation set-up could not judge the item (e.g. the system's choice was not shown to the labeller,
               truncated input, a rubric that cannot express the true answer)
  label_noise  the gold label is wrong or the item is ambiguous on inspection
  genuine      a real error of the system under test
"""
import csv
import json
import sys
from collections import Counter

CLASSES = ("artefact", "label_noise", "genuine")


def init(src, out):
    rows = list(csv.DictReader(open(src)))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) + ["class", "note"])
        w.writeheader()
        for r in rows:
            w.writerow({**r, "class": "", "note": ""})
    print(len(rows), "errors to classify ->", out)


def summarise(path, n_eval, n_correct, outp=None):
    rows = list(csv.DictReader(open(path)))
    c = Counter(r["class"].strip() for r in rows)
    bad = [r for r in rows if r["class"].strip() not in CLASSES]
    if bad:
        raise SystemExit(f"{len(bad)} errors unclassified or with an unknown class (allowed: {CLASSES})")
    n_eval, n_correct = int(n_eval), int(n_correct)
    if n_eval - n_correct != len(rows):
        raise SystemExit(f"error count {len(rows)} != evaluated - correct = {n_eval - n_correct}")
    judge = n_eval - c["artefact"]
    out = {"evaluated": n_eval, "errors": len(rows), "by_class": {k: c.get(k, 0) for k in CLASSES},
           "metric_as_measured": round(n_correct / n_eval, 4),
           "metric_judgeable": round(n_correct / judge, 4) if judge else None, "judgeable_n": judge,
           "metric_judgeable_noise_as_correct": round((n_correct + c["label_noise"]) / judge, 4) if judge else None}
    if outp:
        json.dump(out, open(outp, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "init":
        init(a[1], a[2])
    else:
        summarise(a[1], a[2], a[3], a[a.index("--out") + 1] if "--out" in a else None)
