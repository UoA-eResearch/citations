"""Secondary analyses added after independent review (deviations.md D4).

1. Per-target A - NPP and A - S0 with 24-h block-bootstrap CIs (primary configurations).
2. Concentration: share of the A - S0 gain carried by the top 1 and top 3 24-h blocks.
3. Information asymmetry: model A evaluated with S0's truncated history (test events + 19 burn-in events).
4. Cutoff sweep as log-likelihood differences (A - S0, A - NPP, NPP - S0 = G), flagging G <= 0, where R is undefined.
5. Synthetic incomplete catalog (cutoff 2.0): the same quantities.
Outputs: results/tables/secondary_ab.csv, secondary_sweep.csv, secondary_truncated.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data as D  # noqa: E402
import etas_lib as E  # noqa: E402
from run_config import load  # noqa: E402
from s0_check import windows  # noqa: E402

RUN = D.RUN
TAB = RUN / "results" / "tables"
RNG = np.random.default_rng(4)


def boot_diff(pw, a, b, n=2000):
    g = pw.groupby("block")
    sa, sb, cnt = g[a].sum(), g[b].sum(), g.size()
    blocks = cnt.index.values
    out = []
    for _ in range(n):
        bs = RNG.choice(blocks, len(blocks), replace=True)
        out.append((sa.loc[bs].sum() - sb.loc[bs].sum()) / cnt.loc[bs].sum())
    return np.percentile(out, [2.5, 97.5])


def main():
    rows, trunc = [], []
    for seq, cut in [("Visso", 1.2), ("Norcia", 1.2), ("Campotosto", 1.3), ("synthetic", 2.0)]:
        pw = pd.read_parquet(RUN / "results" / "pointwise" / f"{seq}_{cut}.parquet")
        f = json.load(open(RUN / "results" / "fits" / f"{seq}_{cut}.json"))
        d_an = pw.A - pw.NPP
        lo, hi = boot_diff(pw, "A", "NPP")
        gain = (pw.A - pw.S0).groupby(pw.block).sum().sort_values(ascending=False)
        rows.append(dict(config=seq, cutoff=cut, n_targets=len(pw), A_minus_NPP=d_an.mean(), lo=lo, hi=hi,
                         A_minus_S0=(pw.A - pw.S0).mean(), share_top1_block=gain.iloc[0] / gain.sum(),
                         share_top3_blocks=gain.iloc[:3].sum() / gain.sum(), top_block_start=float(gain.index[0] * (24 if seq != "synthetic" else 1))))
        # truncated-history evaluation of A
        d, r, params = load(seq, cut)
        T, M = d["T_test"], d["M_test"]
        idx, prev = windows(T, M, D.TIME_STEP)
        ll_tr, _ = E.target_ll(f["A"], "A", T, M, T[idx], prev, cut)
        G = pw.NPP.mean() - pw.S0.mean()
        trunc.append(dict(config=seq, cutoff=cut, A_full_history=pw.A.mean(), A_truncated_history=ll_tr.mean(),
                          R_full=(pw.A.mean() - pw.S0.mean()) / G, R_truncated=(ll_tr.mean() - pw.S0.mean()) / G))
    ab = pd.DataFrame(rows)
    ab.to_csv(TAB / "secondary_ab.csv", index=False)
    pd.DataFrame(trunc).to_csv(TAB / "secondary_truncated.csv", index=False)
    print(ab.round(3).to_string(index=False))
    print(pd.DataFrame(trunc).round(3).to_string(index=False))
    sw = []
    for fpath in sorted((RUN / "results" / "fits").glob("*.json")):
        tag = fpath.stem
        if tag.startswith("synthetic"):
            continue
        j = json.load(open(fpath))
        pw = pd.read_parquet(RUN / "results" / "pointwise" / f"{tag}.parquet")
        m = pw[["S0", "NPP", "S2", "A", "B"]].mean()
        lo, hi = boot_diff(pw, "A", "NPP", n=1000)
        G = m.NPP - m.S0
        sw.append(dict(config=j["config"], cutoff=j["cutoff"], G=G, gap_defined=G > 0, A_minus_S0=m.A - m.S0, A_minus_NPP=m.A - m.NPP,
                       A_minus_NPP_lo=lo, A_minus_NPP_hi=hi, best_model=m.idxmax(), R=(m.A - m.S0) / G if G > 0 else np.nan,
                       Tb=j["A"]["Tb"], alpha=j["A"]["alpha"], beta=j["A"]["beta"],
                       branching=j["A"]["K"] * j["A"]["beta"] / (j["A"]["beta"] - j["A"]["alpha"]) if j["A"]["beta"] > j["A"]["alpha"] else np.inf))
    s = pd.DataFrame(sw).sort_values(["config", "cutoff"])
    s.to_csv(TAB / "secondary_sweep.csv", index=False)
    print(s.round(3).to_string(index=False))
    print("A > NPP in", int((s.A_minus_NPP > 0).sum()), "of", len(s), "| A > NPP with CI above 0 in", int((s.A_minus_NPP_lo > 0).sum()),
          "| A best of all five in", int((s.best_model == "A").sum()))


if __name__ == "__main__":
    main()
