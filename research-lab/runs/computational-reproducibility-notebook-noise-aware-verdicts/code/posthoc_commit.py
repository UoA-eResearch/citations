"""Post hoc (D4, review finding 3): for the completed notebooks, was the notebook read at the dataset's own commit?
Where the AS-OF commit differs from the dataset's `commit`, compare the notebook file's blob id at the two commits
(trees only; the clones are blob-less). -> results/tables/posthoc_commit.json"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RUN / "code"))
import select_nb as SN  # noqa: E402

D, TAB = RUN / "data", RUN / "results" / "tables"


def blob(repo, commit, path):
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", f"{commit}:{path}"], capture_output=True, timeout=60,
                       env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin", "GIT_NO_LAZY_FETCH": "1"})
    return r.stdout.decode().strip() if r.returncode == 0 else None


def main():
    N = pd.read_csv(TAB / "notebooks.csv")
    comp = N[N.reps_ok]
    S = pd.read_csv(D / "interim" / "sample_ready.csv", dtype=str).set_index("nbid")
    c = sqlite3.connect(f"file:{SN.DB}?mode=ro", uri=True)
    dc = pd.read_sql('select n.id nb_id, r."commit" dcommit from notebooks n join repositories r on r.id = n.repository_id', c)
    dc["nbid"] = "nb" + dc.nb_id.astype(str)
    dc = dc.drop_duplicates("nbid").set_index("nbid").dcommit
    rows = []
    for nb in comp.nbid:
        s = S.loc[nb]
        d = dc.get(nb)
        same = (d == s.asof_commit)
        row = {"nbid": nb, "same_commit": bool(same), "masked_mismatch": bool(comp.set_index("nbid").loc[nb, "exact_mismatch"])}
        if not same:
            repo = D / "repos" / s.repo_id
            a, b = blob(repo, s.asof_commit, s.nb_path), blob(repo, d, s.nb_path)
            row["file_status"] = "dataset_commit_unavailable" if b is None else ("identical" if a == b else "differs")
        rows.append(row)
    R = pd.DataFrame(rows)
    diff = R[~R.same_commit]
    out = {"completed": int(len(R)), "read_at_dataset_commit": int(R.same_commit.sum()), "read_at_other_commit": int(len(diff)),
           "other_commit_file_status": diff.file_status.value_counts().to_dict(),
           "masked_match_among_file_differs": int((~diff[diff.file_status == "differs"].masked_mismatch).sum()) if len(diff) else 0}
    (TAB / "posthoc_commit.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
