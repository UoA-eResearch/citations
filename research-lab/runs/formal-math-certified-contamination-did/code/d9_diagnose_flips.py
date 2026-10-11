import json, sys, multiprocessing as mp
import pandas as pd
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import certify as C, recheck as R
RUN = str(__import__("pathlib").Path(__file__).resolve().parents[1])

def status(r):
    if "timeout" in r or "dead" in r: return "timeout"
    return "proved" if (not C.errors(r) and not C.uses_sorry(r) and C.axioms(r, "chk") is not None) else "failed"

def neg(repl, a, b, t):
    bb, cb = C.split(b); pa = C.prop(a)
    nb = f"(∀ {bb}, ¬ ({cb}))" if bb else f"(¬ ({cb}))"
    return status(repl.run(f"{C.HDR}theorem chk : {pa} → {nb} := by\n  intro h\n  intros\n  {C.PORTFOLIO}\n\n#print axioms chk", timeout=t))

def wit(repl, a, t):
    pa = C.prop(a)
    return status(repl.run(f"{C.HDR}theorem chk : ¬ {pa} := by\n  intro h\n  {R.WITNESS}\n\n#print axioms chk", timeout=t))

def work(x):
    key, a, b = x
    try:
        return dict(key=key, informative=R.informative(C._repl, b), refutable=R.refutable(C._repl, a),
                    witness=wit(C._repl, a, 60), negation=neg(C._repl, a, b, 60), negation_300s=neg(C._repl, a, b, 300))
    except Exception as e:
        return dict(key=key, error=repr(e)[:200])

if __name__ == "__main__":
    f = pd.read_csv(sys.argv[1])
    bench = pd.read_parquet(f"{RUN}/data/statements/bench_minif2f.parquet").drop_duplicates("id").set_index("id").stmt
    corp = {}
    items = []
    for r in f.itertuples():
        it, c, cid = r.key.rsplit("|", 2)
        if c not in corp:
            corp[c] = pd.read_parquet(f"{RUN}/data/statements/{c}.parquet", columns=["id", "stmt"]).drop_duplicates("id").set_index("id").stmt
        tr, te = corp[c][cid], bench[it]
        a, b = (tr, te) if r.dir == "ab_inf" else (te, tr)   # ab: train => test; ba: test => train
        items.append((f"{r.key}|{r.dir}", a, b))
    with mp.Pool(int(sys.argv[2]), initializer=C.init) as pool:
        for o in pool.imap_unordered(work, items, chunksize=1):
            print(json.dumps(o), flush=True)
