"""Choose the final candidate per instance (plan.md section 3; tie rule in deviations D4) from results/*_A*.json and
write results/final_candidates.json with each candidate's SHA-256. Does NOT read the sealed answers. The output must be
committed to git before code/score.py is run."""
import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
RANK = {"A1": 0, "A2": 1, "A3": 2}


def conf(r):
    return {"A1": r.get("top_frequency"), "A2": r.get("mean_margin"), "A3": r.get("mean_abs_z")}[r["attack"]]


def main():
    final = {}
    for inst in ("P11", "P12"):
        rs = [json.load(open(f)) for f in sorted(RUN.glob(f"results/{inst}_A*.json")) if "_subset" not in f.name]
        rs = [r for r in rs if r.get("candidate") and len(r["candidate"]) == 98]
        if not rs:
            final[inst] = None
            continue
        # A1 > A2 > A3; within an attack, highest confidence; ties -> smaller cutoff (more accurate), then larger max_bond
        rs.sort(key=lambda r: (RANK[r["attack"]], -(conf(r) or 0), r.get("cutoff", 1.0), -r.get("max_bond", 0)))
        b = rs[0]
        final[inst] = dict(candidate=b["candidate"], sha256=hashlib.sha256(b["candidate"].encode()).hexdigest(), attack=b["attack"],
                           source=f"{inst}_{b['attack']}_mb{b.get('max_bond')}_c{b.get('cutoff')}_s{b.get('seed')}", confidence=conf(b),
                           considered=[dict(attack=r["attack"], cutoff=r.get("cutoff"), max_bond=r.get("max_bond"), confidence=conf(r)) for r in rs])
    json.dump(final, open(RUN / "results" / "final_candidates.json", "w"), indent=1)
    print({k: (v and {kk: v[kk] for kk in ("sha256", "attack", "source", "confidence")}) for k, v in final.items()})


if __name__ == "__main__":
    main()
