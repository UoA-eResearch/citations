"""Reviewer's Lean re-checks. Usage: VAC_TOOLCHAIN=v49|v415 review_lean.py <mode> <workers> <out.jsonl>
Modes:
  neg      - for every L1/L2 pair in leak_pairs_bench_minif2f.csv in this toolchain: re-run certify.check(train, test) and
             certify.check(test, train); then the explosion test check(train, NOT test) and (for L1) check(test, NOT train).
             Also run recheck.refutable on the train statement with the study's guard and with a stronger witness-based guard.
  free     - for all 488 miniF2F items: is the statement provable alone by recheck.FREE (60 s)? (study: 69 automation-provable)
  rejected - random sample of 60 rejected candidate pairs (checked, ab False, ba False) and 30 pairs rejected only by the
             recheck (ab True but ab_inf False): re-run the certification, and for recheck-rejected pairs rerun informative/refutable
"""
import json, os, sys, random, time
import multiprocessing as mp
from pathlib import Path
import pandas as pd

RUN = Path("/mnt/citations/research-lab/runs/formal-math-certified-contamination-did")
sys.path.insert(0, str(RUN / "code"))
import certify as C  # noqa
import recheck as R  # noqa

TC = os.environ.get("VAC_TOOLCHAIN", "v49")
mode, workers, out_path = sys.argv[1], int(sys.argv[2]), Path(sys.argv[3])


def prop_neg(stmt):
    b, c = C.split(stmt)
    return f"(∀ {b}, ¬ ({c}))" if b else f"(¬ ({c}))"


def check_neg(repl, a, b, timeout=20):
    """(forall a) -> (forall B_b, not C_b) with the certification portfolio: provable only if a is inconsistent with B_b."""
    try:
        pa, pb = C.prop(a), prop_neg(b)
    except Exception:
        return None
    cmd = f"{C.HDR}theorem chk : {pa} → {pb} := by\n  intro h\n  intros\n  {C.PORTFOLIO}\n\n#print axioms chk"
    r = repl.run(cmd, timeout=timeout)
    if "timeout" in r or "dead" in r:
        return False
    if C.errors(r) or C.uses_sorry(r):
        return False
    ax = C.axioms(r, "chk")
    return ax is not None and set(ax) <= C.ALLOWED


WITNESS = ("first\n    | (simp_all; done)\n    | aesop\n"
           "    | (exact absurd (h 0) (by norm_num))\n    | (exact absurd (h 1) (by norm_num))\n    | (exact absurd (h 2) (by norm_num))\n"
           "    | (exact absurd (h 3) (by norm_num))\n    | (exact absurd (h 0 (by norm_num)) (by norm_num))\n"
           "    | (exact absurd (h 1 (by norm_num)) (by norm_num))\n    | (exact absurd (h 2 (by norm_num)) (by norm_num))\n"
           "    | (exact absurd (h 2 (by norm_num) (by norm_num)) (by norm_num))\n    | (exact absurd (h 3 (by norm_num) (by norm_num)) (by norm_num))\n"
           "    | (exact absurd (h 0 0) (by norm_num))\n    | (exact absurd (h 1 1) (by norm_num))\n    | (exact absurd (h 1 2) (by norm_num))\n"
           "    | (exact absurd (h 0 1) (by norm_num))\n    | (exact absurd (h 2 3) (by norm_num))\n    | (exact absurd (h 0 0 0) (by norm_num))\n"
           "    | (exact absurd (h 1 2 3) (by norm_num))\n    | (exact absurd (h (-1)) (by norm_num))\n    | (exact absurd (h (1/2)) (by norm_num))\n"
           "    | (exact absurd (h 0 (by norm_num) (by norm_num)) (by norm_num))\n    | (exact absurd (h 1 (by norm_num) (by norm_num)) (by norm_num))\n"
           "    | (exact absurd (h 10) (by norm_num))\n    | (exact absurd (h 100) (by norm_num))\n    | (exact absurd (h 2 (by norm_num)) (by decide))\n"
           "    | (exact absurd (h 2 (by norm_num) (by decide)) (by decide))\n    | (exact absurd (h 3 (by norm_num) (by decide)) (by decide))")


def refutable_witness(repl, a, timeout=60):
    """A stronger refutation: small-witness instantiations of the training statement."""
    try:
        pa = C.prop(a)
    except Exception:
        return None
    r = repl.run(f"{C.HDR}theorem chk : {pa} → False := by\n  intro h\n  {WITNESS}\n\n#print axioms chk", timeout=timeout)
    if "timeout" in r or "dead" in r:
        return None
    return not C.errors(r) and not C.uses_sorry(r) and (C.axioms(r, "chk") is not None)


def free_provable(repl, stmt, timeout=60):
    try:
        pb = C.prop(stmt)
    except Exception:
        return "parse_error"
    r = repl.run(f"{C.HDR}theorem chk : {pb} := by\n  intros\n  {R.FREE}\n\n#print axioms chk", timeout=timeout)
    if "timeout" in r or "dead" in r:
        return "timeout"
    if C.errors(r) or C.uses_sorry(r):
        return "not_proved"
    ax = C.axioms(r, "chk")
    return "proved" if ax is not None and set(ax) <= C.ALLOWED else "bad_axioms"


def work_neg(item):
    key, tier, train, test = item
    t0 = time.time()
    out = dict(key=key, tier=tier)
    try:
        out["ab"] = C.check(C._repl, train, test)
        out["ba"] = C.check(C._repl, test, train)
        out["a_implies_not_b"] = check_neg(C._repl, train, test)
        out["b_implies_not_a"] = check_neg(C._repl, test, train) if tier == "L1" else None
        out["train_refutable_study"] = R.refutable(C._repl, train)
        out["train_refutable_witness"] = refutable_witness(C._repl, train)
        out["test_free_provable"] = free_provable(C._repl, test)
    except Exception as e:
        out["error"] = repr(e)[:200]
        try:
            C._repl.restart()
        except Exception:
            pass
    out["s"] = time.time() - t0
    return out


def work_free(item):
    key, stmt = item
    try:
        return dict(key=key, free=free_provable(C._repl, stmt))
    except Exception as e:
        try:
            C._repl.restart()
        except Exception:
            pass
        return dict(key=key, error=repr(e)[:200])


def work_rej(item):
    key, kind, train, test, orig = item
    out = dict(key=key, kind=kind, orig=orig)
    try:
        out["ab"] = C.check(C._repl, train, test)
        out["ba"] = C.check(C._repl, test, train)
        if kind == "recheck_rejected":
            out["test_informative"] = R.informative(C._repl, test)
            out["train_refutable"] = R.refutable(C._repl, train)
            out["test_free"] = free_provable(C._repl, test)
    except Exception as e:
        out["error"] = repr(e)[:200]
        try:
            C._repl.restart()
        except Exception:
            pass
    return out


def main():
    b = pd.read_parquet(RUN / "data/statements/bench_minif2f.parquet").set_index("id").stmt
    corpora = {}

    def cstmt(corp):
        if corp not in corpora:
            corpora[corp] = pd.read_parquet(RUN / f"data/statements/{corp}.parquet", columns=["id", "stmt"]).drop_duplicates("id").set_index("id").stmt
        return corpora[corp]
    items = []
    if mode == "neg":
        p = pd.read_csv(RUN / "results/tables/leak_pairs_bench_minif2f.csv")
        p = p[p.tier != "L0"]
        for r in p.itertuples():
            if ("v415" if r.corpus in C.LEAN415 else "v49") != TC:
                continue
            items.append((f"{r.item}|{r.corpus}|{r.corpus_id}", r.tier, cstmt(r.corpus)[r.corpus_id], b[r.item]))
        fn = work_neg
    elif mode == "free":
        if TC == "v49":
            items = [(k, s) for k, s in b.items()]
        fn = work_free
    elif mode == "rejected":
        rng = random.Random(2026)
        cands = []
        for f in sorted((RUN / "data/certify").glob("bench_minif2f__*.jsonl")):
            corp = f.stem.split("__")[1]
            if ("v415" if corp in C.LEAN415 else "v49") != TC:
                continue
            rc = {json.loads(l)["key"]: json.loads(l) for l in open(RUN / f"data/certify/recheck_bench_minif2f__{corp}.jsonl")}
            for line in open(f):
                r = json.loads(line)
                if r.get("status") != "checked":
                    continue
                it, _, cid = r["key"].rsplit("|", 2)
                if not r.get("ab") and not r.get("ba"):
                    cands.append((r["key"], "cert_rejected", cstmt(corp)[cid], b[it], dict(ab=r.get("ab"), ba=r.get("ba"))))
                elif r.get("ab") and rc.get(r["key"], {}).get("ab_inf") is False:
                    cands.append((r["key"], "recheck_rejected", cstmt(corp)[cid], b[it], dict(ab=r.get("ab"), ba=r.get("ba"), ab_inf=False, ba_inf=rc[r["key"]].get("ba_inf"))))
        rej = [c for c in cands if c[1] == "cert_rejected"]
        rrj = [c for c in cands if c[1] == "recheck_rejected"]
        n1, n2 = (60, 30) if TC == "v49" else (20, 10)
        items = rng.sample(rej, min(n1, len(rej))) + rng.sample(rrj, min(n2, len(rrj)))
        fn = work_rej
    done = set()
    if out_path.exists():
        done = {json.loads(l)["key"] for l in open(out_path)}
    todo = [it for it in items if it[0] not in done]
    print(f"{mode} {TC}: {len(items)} items, {len(todo)} to run", flush=True)
    with mp.Pool(workers, initializer=C.init) as pool, open(out_path, "a") as f:
        for i, o in enumerate(pool.imap_unordered(fn, todo, chunksize=1)):
            f.write(json.dumps(o) + "\n"); f.flush()
            if (i + 1) % 25 == 0:
                print(i + 1, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
