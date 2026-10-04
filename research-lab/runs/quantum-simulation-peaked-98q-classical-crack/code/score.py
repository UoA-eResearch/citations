"""Score the committed final candidates against the sealed Helios-1 strings (plan.md section 4). Refuses to run unless
results/final_candidates.json is committed and unmodified in git, and refuses a second run (answers are read once).
Writes results/score.json."""
import json
import subprocess
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
FC = RUN / "results" / "final_candidates.json"
OUT = RUN / "results" / "score.json"


def main():
    if OUT.exists():
        raise SystemExit("score.json exists: the sealed answers have already been read once")
    rel = FC.relative_to(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=RUN, text=True).strip())
    st = subprocess.check_output(["git", "status", "--porcelain", str(FC)], cwd=RUN, text=True).strip()
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(FC)], cwd=RUN, capture_output=True).returncode == 0
    if st or not tracked:
        raise SystemExit(f"{rel} must be committed and unmodified before scoring")
    commit = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", str(FC)], cwd=RUN, text=True).strip()
    fc = json.load(open(FC))
    ans = json.load(open(RUN / "data" / "sealed" / "answers.json"))
    res = dict(candidates_commit=commit)
    for inst in ("P11", "P12"):
        a = ans.get(inst) or []
        c = (fc.get(inst) or {}).get("candidate")
        if not a or not c:
            res[inst] = dict(hamming=None, note="no candidate" if not c else "no sealed answer")
            continue
        h = min(sum(x != y for x, y in zip(c, s)) for s in a)
        v = "Supported" if h == 0 else ("Inconclusive" if h <= 4 else "Contradicted")
        res[inst] = dict(hamming=h, verdict_rule=v, source=fc[inst]["source"])
    json.dump(res, open(OUT, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
