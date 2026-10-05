"""Measure D (audit_plan.md): traceability of numbers printed in each report.md.
A number printed with k decimals is 'traced' if some numeric value in the run's results/ files (csv/json/txt/md, files
<= 25 MB), plan.md or deviations.md lies within half a unit of its last printed digit (as a proportion too, for
percentages). 'Substantive' numbers: decimals, percentages, or integers >= 100 that are not years.
Writes paper/audit/D_numbers_summary.csv, D_numbers_all.csv and D_sample_untraced.csv (seeded sample, <= 10 per report)."""
import json
import random
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
RUNS = REPO / "research-lab" / "runs"
OUT = REPO / "research-lab" / "paper" / "audit"
NUM = re.compile(r"(?<![\w.])([+\-−]?)(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?(?:[eE]([+\-−]?\d+))?(\s?%)?(?![\w])")
SRC_NUM = re.compile(r"[+\-]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d*|\.\d+|\d+)(?:[eE][+\-]?\d+)?")  # thousands separators (fix A8)
MONTHS = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*"


def scrub(text):
    """Blank out spans whose digits are not reported quantities (keeps offsets for context)."""
    pats = [r"`[^`\n]*`", r"\]\([^)]*\)", r"https?://\S+", r"\b10\.\d{4,9}/\S+", r"\b(?:arXiv:?\s?)?\d{4}\.\d{4,5}(?:v\d)?\b",
            r"\b[0-9a-f]{7,40}\b(?=[^0-9a-f])", r"\b[DEFRUCT]\d+[a-z]?\b", r"\b\d{4}-\d{2}-\d{2}\b", r"\b\d{1,2}:\d{2}\b",
            rf"\b\d{{1,2}}\s+{MONTHS}\b", rf"\b{MONTHS}\s+\d{{1,2}}\b", r"(?m)^#+\s*[\d.]+", r"\[\d+\]", r"(?i)(?:\b(?:figure|fig\.|table|section|sec\.)|§)\s*\d+(?:\.\d+)*",
            r"(?m)^\s*\d+\.\s", r"!\[[^\]]*\]"]
    for p in pats:
        text = re.sub(p, lambda m: " " * len(m.group(0)), text)
    return text


def report_numbers(text):
    s = scrub(text)
    out = []
    for m in NUM.finditer(s):
        sign, ip, dp, ex, pct = m.groups()
        ip_clean = ip.replace(",", "")
        val = float(ip_clean + (dp or ""))
        if ex:
            val *= 10 ** int(ex.replace("−", "-"))
        if sign in ("-", "−"):
            val = -val
        k = len(dp) - 1 if dp else 0
        is_year = (not dp and not pct and not ex and 1900 <= val <= 2100)
        if is_year:
            continue
        subst = bool(dp) or bool(pct) or abs(val) >= 100
        out.append(dict(value=val, decimals=k, pct=bool(pct), substantive=subst, start=m.start(), token=text[m.start():m.end()].strip()))
    return out


def source_values(run, results_only=False):
    vals = []
    files = ([] if results_only else [run / "plan.md", run / "deviations.md"]) + [p for p in (run / "results").rglob("*") if p.suffix in (".csv", ".json", ".txt", ".md", ".tsv")]
    skipped = []
    for f in files:
        if not f.exists():
            continue
        if f.stat().st_size > 25e6:
            skipped.append(f.name)
            continue
        t = f.read_text(errors="ignore").replace("−", "-")
        vals.extend(float(x.replace(",", "")) for x in SRC_NUM.findall(t) if len(x) < 40)
    a = np.unique(np.array(vals, dtype=float)) if vals else np.array([])
    return np.sort(np.concatenate([a, -a])) if len(a) else a, skipped


def traced(v, k, pct, src):
    if not len(src):
        return False
    tol = 0.5 * 10 ** (-k) + 1e-12
    cands = [(v, tol)]
    if pct:
        cands.append((v / 100, tol / 100))
    for x, t in cands:
        i = np.searchsorted(src, x - t)
        if i < len(src) and src[i] <= x + t:
            return True
    return False


def main():
    rows, summ = [], []
    for run in sorted(p for p in RUNS.iterdir() if (p / "report.md").exists()):
        text = (run / "report.md").read_text()
        src, skipped = source_values(run)
        nums = report_numbers(text)
        for n in nums:
            n.update(run=run.name, traced=traced(n["value"], n["decimals"], n["pct"], src),
                     context=text[max(0, n["start"] - 110):n["start"] + 60].replace("\n", " "))
            rows.append(n)
        d = pd.DataFrame(nums)
        sub = d[d.substantive]
        summ.append(dict(run=run.name, n_numbers=len(d), traced_all=d.traced.mean(), n_substantive=len(sub), traced_substantive=sub.traced.mean(),
                         n_source_values=len(src) // 2, skipped_large_files=";".join(skipped)))
    a = pd.DataFrame(rows)
    a.drop(columns=["start"]).to_csv(OUT / "D_numbers_all.csv", index=False)
    s = pd.DataFrame(summ)
    s.to_csv(OUT / "D_numbers_summary.csv", index=False)
    rng = random.Random(20261006)
    samp = []
    for run, g in a[a.substantive & ~a.traced].groupby("run"):
        idx = list(g.index)
        rng.shuffle(idx)
        for i in idx[:10]:
            samp.append(dict(sample_id=f"{run[:24]}-{i}", run=run, token=a.loc[i, "token"], context=a.loc[i, "context"]))
    pd.DataFrame(samp).to_csv(OUT / "D_sample_untraced_latest.csv", index=False)  # the classified sample is D_sample_untraced_v1.csv (A11)
    print(s.round(3).to_string(index=False))
    tot = a[a.substantive]
    print(f"\nall numbers {len(a)}, traced {a.traced.mean():.3f}; substantive {len(tot)}, traced {tot.traced.mean():.3f}; sample of untraced: {len(samp)}")


if __name__ == "__main__":
    main()


def null_rate():
    """Chance-match check (added after the protocol; see paper): trace each report's substantive numbers against every
    OTHER run's sources. The mean cross-run traced rate estimates how often a number 'traces' by coincidence."""
    runs = sorted(p for p in RUNS.iterdir() if (p / "report.md").exists())
    srcs = {r.name: source_values(r)[0] for r in runs}
    nums = {r.name: [n for n in report_numbers((r / "report.md").read_text()) if n["substantive"]] for r in runs}
    rows = []
    for r in runs:
        own = np.mean([traced(n["value"], n["decimals"], n["pct"], srcs[r.name]) for n in nums[r.name]])
        cross = [np.mean([traced(n["value"], n["decimals"], n["pct"], srcs[o.name]) for n in nums[r.name]]) for o in runs if o != r]
        rows.append(dict(run=r.name, traced_own=own, traced_cross_mean=float(np.mean(cross)), traced_cross_max=float(np.max(cross))))
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "D_numbers_null.csv", index=False)
    print(d.round(3).to_string(index=False))
    print(f"mean own {d.traced_own.mean():.3f} vs mean cross-run (chance) {d.traced_cross_mean.mean():.3f}")


if __name__ == "__main__" and "--null" in __import__("sys").argv:
    null_rate()


def sigdigits(tok):
    t = re.sub(r"[^\d.]", "", tok.replace(",", ""))
    t = t.lstrip("0").replace(".", "") if "." in t else t.rstrip("0") or "0"
    t = t.lstrip("0")
    return max(1, len(t))


def null_by_sig():
    """Own vs cross-run (chance) traced rates by number of significant digits printed."""
    runs = sorted(p for p in RUNS.iterdir() if (p / "report.md").exists())
    srcs = {r.name: source_values(r)[0] for r in runs}
    rows = []
    for r in runs:
        for n in report_numbers((r / "report.md").read_text()):
            if not n["substantive"]:
                continue
            sd = sigdigits(n["token"])
            own = traced(n["value"], n["decimals"], n["pct"], srcs[r.name])
            cross = np.mean([traced(n["value"], n["decimals"], n["pct"], srcs[o.name]) for o in runs if o != r])
            rows.append(dict(run=r.name, token=n["token"], sig=min(sd, 5), own=own, cross=cross))
    d = pd.DataFrame(rows)
    g = d.groupby("sig").agg(n=("own", "size"), traced_own=("own", "mean"), traced_chance=("cross", "mean"))
    g["corrected"] = (g.traced_own - g.traced_chance) / (1 - g.traced_chance)
    g.to_csv(OUT / "D_numbers_by_sigdigits.csv")
    d.to_csv(OUT / "D_numbers_sig_detail.csv", index=False)
    print(g.round(3).to_string())
    hi = d[d.sig >= 3]
    print(f">=3 significant digits: n={len(hi)} own {hi.own.mean():.3f} chance {hi.cross.mean():.3f}")


if __name__ == "__main__" and "--sig" in __import__("sys").argv:
    null_by_sig()



def perturbation_null(seeds=(1, 2, 3, 4, 5)):
    """Size-matched chance control (review M7.2): shift each printed number by 3-7 units of its last printed digit
    (random sign), keeping its precision, and test whether the shifted value 'traces' against the study's OWN sources.
    Reported for all sources and for results/ only. Writes D_numbers_perturbation.csv (per study) and
    D_numbers_perturbation_by_sig.csv."""
    rng = np.random.default_rng(20261006)
    runs = sorted(p for p in RUNS.iterdir() if (p / "report.md").exists())
    rows, det = [], []
    for r in runs:
        nums = [n for n in report_numbers((r / "report.md").read_text()) if n["substantive"]]
        for ro in (False, True):
            src = source_values(r, results_only=ro)[0]
            own = [traced(n["value"], n["decimals"], n["pct"], src) for n in nums]
            ch = []
            for _ in seeds:
                hits = []
                for n in nums:
                    u = rng.integers(3, 8) * rng.choice([-1, 1]) * 10 ** (-n["decimals"])
                    hits.append(traced(round(n["value"] + u, n["decimals"]), n["decimals"], n["pct"], src))
                ch.append(np.array(hits))
            chm = np.mean(ch, axis=0)
            rows.append(dict(run=r.name, sources="results only" if ro else "results+plan+deviations", n=len(nums),
                             traced_own=float(np.mean(own)), traced_chance=float(np.mean(chm))))
            for n, o, c in zip(nums, own, chm):
                det.append(dict(run=r.name, sources="results only" if ro else "results+plan+deviations", token=n["token"],
                                sig=min(sigdigits(n["token"]), 5), own=o, chance=c))
    d = pd.DataFrame(rows)
    d["corrected"] = (d.traced_own - d.traced_chance) / (1 - d.traced_chance)
    d.to_csv(OUT / "D_numbers_perturbation.csv", index=False)
    t = pd.DataFrame(det)
    t.to_csv(OUT / "D_numbers_perturbation_detail.csv", index=False)
    g = t.groupby(["sources", "sig"]).agg(n=("own", "size"), traced_own=("own", "mean"), traced_chance=("chance", "mean")).reset_index()
    g["corrected"] = (g.traced_own - g.traced_chance) / (1 - g.traced_chance)
    g.to_csv(OUT / "D_numbers_perturbation_by_sig.csv", index=False)
    print(g.round(3).to_string(index=False))
    for src, h in t.groupby("sources"):
        o, c = h.own.mean(), h.chance.mean()
        print(f"{src}: own {o:.3f} chance {c:.3f} corrected {(o - c) / (1 - c):.3f}")


if __name__ == "__main__" and "--perturb" in __import__("sys").argv:
    perturbation_null()
