"""D8 (review issue 7): re-check "other" outputs that are textually close to the defective reference with a portfolio
that first normalises both sides (ring_nf, field_simp, simp only with division and commutativity lemmas). The
preregistered certifier misses some identical statements, e.g. `1 / (k + 1) / (k + 2)` against
`1 / ((k + 1) * (k + 2))`. Candidates: unique statements classed "other" (elaborate, equivalent to neither reference)
on the 59 primary items, all models and conditions, whose normalised binders and conclusion have a difflib ratio of at
least 0.8 to those of the condition's defective reference (D, or D' for twins). Each is tested O -> D and D -> O
(40 s per direction). Writes results/tables/review/recheck_near.jsonl.
Usage: VAC_TOOLCHAIN=v49 recheck_near.py <workers> [test]"""
import json
import multiprocessing as mp
import sys
from difflib import SequenceMatcher
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
CAT, OUT = RUN / "results" / "catalogue", RUN / "results" / "tables" / "review"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lean_check as L  # noqa: E402
from classify import extract, refs, verbatim_key  # noqa: E402

MODELS = ["kimina", "goedel", "herald", "dsp_v2", "qwen"]
CLOSE = ("first\n    | (apply h <;> (first | assumption | norm_num | linarith | simp_all))\n    | (simp_all; done)\n"
         "    | (ring_nf at h ⊢; first | (apply h <;> (first | assumption | (ring_nf at *; assumption) | norm_num | linarith"
         " | simp_all)) | (simp_all; done))\n"
         "    | (simp only [div_div, mul_comm, mul_assoc, mul_left_comm, ge_iff_le, gt_iff_lt] at h ⊢; first | (apply h <;>"
         " (first | assumption | norm_num | linarith | simp_all)) | (simp_all; done))\n"
         "    | (field_simp at h ⊢; first | (apply h <;> (first | assumption | norm_num | linarith)) | (simp_all; done))\n"
         "    | aesop\n    | (simp_all <;> nlinarith [h])")


def implies_norm(repl, a, b, opens_a, opens_b, timeout=40):
    cmd = (L.wrap("stmtA", a, opens_a) + L.wrap("stmtB", b, opens_b) +
           f"theorem chk : stmtA → stmtB := by\n  unfold stmtA stmtB\n  intro h\n  intros\n  {CLOSE}\n\n#print axioms chk")
    r = repl.run(cmd, timeout=timeout)
    if "timeout" in r or "dead" in r or L.errors(r) or L.uses_sorry(r):
        return False
    ax = L.axioms(r, "chk")
    return ax is not None and set(ax) <= L.ALLOWED


_repl = None


def init():
    global _repl
    _repl = L.Repl()


def work(task):
    uid, code, ref = task
    out = dict(uid=uid)
    try:
        a = implies_norm(_repl, code, ref["D"], ref["oD"], ref["oD"])
        out["copy_norm"] = bool(a and implies_norm(_repl, ref["D"], code, ref["oD"], ref["oD"]))
    except Exception as e:  # noqa: BLE001
        out["error"] = repr(e)[:300]
        try:
            _repl.restart()
        except Exception:  # noqa: BLE001
            pass
    return out


def candidates():
    fz = [json.loads(x) for x in open(CAT / "frozen.jsonl")]
    prim = {r["item"] for r in fz if r["set"] == "included" and r.get("N_twin")}
    R = refs()
    vk = {k: verbatim_key(v["D"]) for k, v in R.items()}
    tasks = []
    for m in MODELS:
        cl = {json.loads(x)["uid"]: json.loads(x) for x in open(RUN / "data" / "classified" / f"{m}.jsonl")}
        samples = {json.loads(x)["key"]: json.loads(x) for x in open(RUN / "data" / "samples" / f"{m}.jsonl")}
        seen = set()
        for o in map(json.loads, open(RUN / "data" / "classified" / f"{m}_outputs.jsonl")):
            uid, key = o.get("uid"), o["key"]
            if not uid or uid in seen or key.rsplit("|", 1)[0] not in prim:
                continue
            c = cl[uid]
            if not c.get("elab") or c.get("copy") or c.get("correct"):
                continue
            s = samples[key]
            text = (s["greedy"][0] if o["idx"] == "g" else s["outputs"][int(o["idx"])])["text"]
            code = extract(text)
            if SequenceMatcher(None, verbatim_key(code), vk[key], autojunk=False).ratio() < 0.8:
                continue
            seen.add(uid)
            tasks.append((f"{m}:{uid}", code, R[key]))
    return tasks


def main(workers, test=False):
    OUT.mkdir(parents=True, exist_ok=True)
    if test:  # review issue 7's example (induction_sum_1oktkp1): the division chain against D
        R = refs()["minif2f/induction_sum_1oktkp1|O"]
        code = ("theorem my_favorite_theorem (n : ℕ) : ∑ k in Finset.range n, (1 : ℝ) / (k + 1) / (k + 2) = n / (n + 1) "
                ":= by sorry")
        repl = L.Repl()
        print("preregistered:", L.implies(repl, code, R["D"], R["oD"], R["oD"]), L.implies(repl, R["D"], code, R["oD"], R["oD"]))
        print("normalising:", implies_norm(repl, code, R["D"], R["oD"], R["oD"]), implies_norm(repl, R["D"], code, R["oD"], R["oD"]))
        return
    tasks = candidates()
    print(len(tasks), "near-D 'other' statements to re-check", flush=True)
    with mp.Pool(workers, initializer=init) as pool, open(OUT / "recheck_near.jsonl", "w") as f:
        for o in pool.imap_unordered(work, tasks, chunksize=1):
            f.write(json.dumps(o) + "\n")
            f.flush()
    print("RECHECK DONE", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), len(sys.argv) > 2 and sys.argv[2] == "test")
