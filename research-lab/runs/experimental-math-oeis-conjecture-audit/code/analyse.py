"""Summary tables (plan sections 0 and 4) -> results/tables/primary.json, falsifications.csv."""
import json
import math
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
INT, TAB = RUN / "data" / "interim", RUN / "results" / "tables"
TAB.mkdir(parents=True, exist_ok=True)


def wilson(k, n, z=1.96):
    if n == 0:
        return [None, None]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 6), round(c + h, 6)]


if __name__ == "__main__":
    C = pd.read_parquet(INT / "conjectures.parquet")
    S = pd.read_parquet(INT / "screen.parquet")
    F = pd.read_parquet(INT / "confirm.parquet")
    out = {"candidate_lines": int(len(C)), "entries_with_candidates": int(C.anum.nunique()),
           "status": C.status.value_counts().to_dict(),
           "parsed_by_class": C[C.status == "parsed"].cls.value_counts().to_dict(),
           "data_consistent": int((C.data_ok == True).sum()), "contradicted_by_own_data": int((C.data_ok == False).sum()),  # noqa: E712
           "contradicted_by_own_data_by_class": C[C.data_ok == False].cls.value_counts().to_dict(),  # noqa: E712
           "in_block_lines": int(C.in_block.sum()) if "in_block" in C else None,
           "screen": S.screen.value_counts().to_dict()}
    scr = S[S.screen.isin(["agree", "disagree"])]
    out["screened"] = int(len(scr))
    out["screened_disagree"] = int((scr.screen == "disagree").sum())
    out["screened_disagree_rate"] = round(out["screened_disagree"] / len(scr), 6)
    out["screened_disagree_rate_wilson"] = wilson(out["screened_disagree"], len(scr))
    out["by_class"] = {c: {"screened": int((scr.cls == c).sum()), "disagree": int(((scr.cls == c) & (scr.screen == "disagree")).sum()),
                           "wilson": wilson(int(((scr.cls == c) & (scr.screen == "disagree")).sum()), int((scr.cls == c).sum()))}
                       for c in ("C", "G", "D")}
    out["beyond_data_terms_checked"] = {"median": float(scr.beyond_data_checked.median()), "p10": float(scr.beyond_data_checked.quantile(.1)),
                                        "p90": float(scr.beyond_data_checked.quantile(.9))}
    out["confirm"] = F.confirm.value_counts().to_dict()
    conf = F[F.confirm.str.startswith("confirmed")]
    out["confirmed_falsifications"] = int(len(conf))
    out["H1"] = "Supported" if len(conf) >= 100 else "Refuted"
    F.merge(S[["anum", "line_no", "nterms", "beyond_data_checked"]], on=["anum", "line_no"], how="left").to_csv(TAB / "falsifications.csv", index=False)
    (TAB / "primary.json").write_text(json.dumps(out, indent=1, default=str) + "\n")
    print(json.dumps(out, indent=1, default=str))
