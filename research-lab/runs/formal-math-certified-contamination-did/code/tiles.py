"""Key-result tiles for report.html, rounded once from the stored tables (D9). Writes results/tables/tiles.json."""
import json
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"


def main():
    prim = json.load(open(T / "primary.json"))
    s = pd.read_csv(T / "secondary.csv").set_index("analysis")
    lr = pd.read_csv(T / "leak_rates.csv")
    any_ = lr[(lr.bench == "bench_minif2f") & (lr.corpus == "any corpus")].iloc[0]
    st = pd.read_csv(T / "leak_status_by_prover.csv")
    own = st[st.scope == "own corpora"].groupby("prover").leaked.mean()
    ps = lambda k: s.loc[k]  # noqa: E731
    tiles = [
        ["Verdict", "Refuted", f"surface rewording, pass@32: leaked problems lose {100 * prim['DiD']:+.1f} pp more (one-sided upper bound {100 * prim['upper95_one_sided']:+.1f}), not >= 10"],
        ["miniF2F leaked", f"{100 * any_.share_any:.0f}%", f"{int(any_.items_any)} of {int(any_.n_items)} have a Lean-certified identical, equivalent or stronger statement in an open corpus"],
        ["Own-corpus leaks", " / ".join(f"{100 * own[p]:.0f}%" for p in ["goedel_v2", "kimina", "dsp_v2"]), "Goedel-Prover-V2 / Kimina / DeepSeek-Prover-V2 (public lineage)"],
        ["Per sample", f"{100 * ps('per-sample, prover dsp_v2').DiD:+.1f} / {100 * ps('per-sample, prover stp').DiD:+.1f} pp",
         "extra drop on reworded leaked items for DeepSeek-Prover-V2 / STP, whose leaks are near-verbatim; pass@32 sits at a 100% ceiling"],
    ]
    json.dump(tiles, open(T / "tiles.json", "w"), indent=0)
    print(json.dumps(tiles, indent=1))


if __name__ == "__main__":
    main()
