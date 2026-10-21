"""Post-review sensitivity of H1's magnitude, on the corrected sector labels (deviations D9).

The review showed that the preregistered estimate clears its -15% bar but that several reasonable variants do not;
its table was computed on the draft labels from a cached panel. This recomputes the variants that bear on the
magnitude with the study's own loader and estimator (did.py), so they use the corrected labels. Descriptive only:
the H1 verdict is the preregistered specification's.

Writes results/tables/sensitivity_post_review.json.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import did as D  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def fmt(r):
    if r is None:
        return None
    return dict(rel_pct=round(100 * r["rel"], 1), ci_pct=[round(100 * r["ci"][0], 1), round(100 * r["ci"][1], 1)],
                n_sites=r["n_sites"], n_treated=r["n_treated_sites"],
                clears_15=bool(r["rel"] <= -0.15 and r["ci"][1] < 0))


def main():
    d, _ = D.load()
    eu = d[d.group == "eu"].copy()
    eu["dens"] = 1000 * eu.violation_nodes / eu.elements
    out = {"preregistered": fmt(D.did(eu))}

    out["drop_zero_violation_snapshots"] = fmt(D.did(eu[eu.violation_nodes > 0]))
    zero_sites = set(eu[eu.violation_nodes == 0].domain)
    out["drop_sites_ever_at_zero"] = fmt(D.did(eu[~eu.domain.isin(zero_sites)]))
    eu["y_nodes"] = np.log1p(eu.violation_nodes)
    out["unnormalised_log1p_nodes"] = fmt(D.did(eu, y="y_nodes"))
    out["treated_ecommerce_only"] = fmt(D.did(eu[(eu.inscope == 0) | (eu.sector == "ecommerce")]))
    out["treated_non_ecommerce_only"] = fmt(D.did(eu[(eu.inscope == 0) | (eu.sector != "ecommerce")]))

    # ratio of means on raw density: the change a reader of "violation density fell X%" would expect
    w = eu[eu.target.isin(D.PRE + D.POST)]
    m = w.assign(post=w.target.isin(D.POST)).groupby(["inscope", "post"]).dens.mean()
    rom = (m[(1.0, True)] / m[(1.0, False)]) / (m[(0.0, True)] / m[(0.0, False)]) - 1
    out["ratio_of_means_raw_density_pct"] = round(100 * float(rom), 1)

    out["composition"] = dict(
        inscope_sites=int(eu[eu.inscope == 1].domain.nunique()),
        inscope_ecommerce=int(eu[(eu.inscope == 1) & (eu.sector == "ecommerce")].domain.nunique()))
    json.dump(out, open(RUN / "results" / "tables" / "sensitivity_post_review.json", "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
