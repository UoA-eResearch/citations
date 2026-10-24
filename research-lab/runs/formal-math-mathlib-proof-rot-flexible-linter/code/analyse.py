"""H1 GEE and secondaries (plan sections 4-5) -> results/tables/primary.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

RUN = Path(__file__).resolve().parents[1]
WORK, TAB = RUN / "data" / "work", RUN / "results" / "tables"
TAB.mkdir(parents=True, exist_ok=True)


def frame(o, n):
    P = pd.read_parquet(WORK / f"pop_{o}_{n}.parquet")
    L = pd.read_parquet(WORK / f"label_{o}.parquet")
    R = pd.read_parquet(WORK / f"replay_{o}_{n}.parquet")
    d = P.merge(L, on=["file", "name"]).merge(R, on=["file", "name"])
    d = d[(d.o_errors == 0) & ~d.o_timeout]                 # validation: declarations that compile in O
    d["fail_i"] = d.fail.astype(int)
    d["flag_i"] = d.flagged.astype(int)
    d["log_tac"] = np.log(d.tactics)
    return d


def gee(d, y="fail_i"):
    if d[y].sum() < 5 or d.flag_i.sum() < 5:
        return None
    m = smf.gee(f"{y} ~ flag_i + log_tac + n_simp", groups="file", data=d, family=sm.families.Binomial(),
                cov_struct=sm.cov_struct.Exchangeable()).fit()
    b, se = m.params["flag_i"], m.bse["flag_i"]
    return {"or": round(float(np.exp(b)), 4), "ci": [round(float(np.exp(b - 1.96 * se)), 4), round(float(np.exp(b + 1.96 * se)), 4)],
            "p": round(float(m.pvalues["flag_i"]), 5), "n": int(len(d)), "files": int(d.file.nunique()),
            "fail_flagged": round(float(d[d.flag_i == 1][y].mean()), 4), "fail_unflagged": round(float(d[d.flag_i == 0][y].mean()), 4),
            "n_flagged": int(d.flag_i.sum())}


def verdict(r):
    if r is None:
        return "not testable"
    lo, hi = r["ci"]
    return "Supported" if (r["or"] >= 1.5 and lo > 1.0) else "Refuted" if hi < 1.5 else "Inconclusive"


if __name__ == "__main__":
    out = {}
    d = frame("O_2504", "N_2604")
    out["primary"] = gee(d)
    out["H1"] = verdict(out["primary"])
    out["primary_population"] = {"declarations": int(len(d)), "flagged": int(d.flag_i.sum()), "fail_rate": round(float(d.fail_i.mean()), 4),
                                 "same_body_fail_rate": round(float(d[d.same_body].fail_i.mean()), 4) if d.same_body.any() else None,
                                 "changed_body_fail_rate": round(float(d[~d.same_body].fail_i.mean()), 4)}
    out["error_classes"] = d[d.fail].eclass.value_counts().to_dict()
    d2 = d.copy()
    d2["fail_nounk"] = (d2.fail & ~d2.only_unknown_id.fillna(False)).astype(int)
    out["excluding_unknown_identifier_only"] = gee(d2, "fail_nounk")
    d6 = frame("O_2504", "O_2510")
    out["decay"] = {"O+6": {"fail_flagged": round(float(d6[d6.flag_i == 1].fail_i.mean()), 4), "fail_unflagged": round(float(d6[d6.flag_i == 0].fail_i.mean()), 4), "n": int(len(d6))},
                    "O+12": {"fail_flagged": out["primary"]["fail_flagged"] if out["primary"] else None,
                             "fail_unflagged": out["primary"]["fail_unflagged"] if out["primary"] else None, "n": int(len(d))},
                    "O+6_gee": gee(d6)}
    dS = frame("O_2510", "N_2610")
    out["secondary_pair"] = gee(dS)
    pooled = pd.concat([d.assign(file="A:" + d.file), dS.assign(file="B:" + dS.file)])
    out["pooled"] = gee(pooled)
    out["secondary_error_classes"] = dS[dS.fail].eclass.value_counts().to_dict()
    (TAB / "primary.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
