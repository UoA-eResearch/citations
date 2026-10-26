"""G3 hand trace: three population station x trigger pairs (seed 20261026), recomputed from the raw extracted picks with
an independent, plain implementation of the proxy (no teleseismic masking, which the trace reports separately as the
pipeline's masked fraction), and compared with N_post and N_base in pairs_primary.parquet.
-> results/tables/handtrace.json
"""
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
sys.path.insert(0, str(RUN / "code"))
from windows import gc_km  # noqa: E402

H = 3_600_000


def pairs_for(pk):
    """P-S pairs per station: first S 0.8-8 s after each P with no P between; t0 = tP - 1.37 (tS - tP)."""
    out = []
    for tid, g in pk.sort_values(["tid", "peak_ms"]).groupby("tid"):
        ph, t = g.pha.to_numpy(), g.peak_ms.to_numpy()
        for i in np.flatnonzero(ph == "P"):
            for j in range(i + 1, min(i + 4, len(t))):
                if ph[j] == "P":
                    break
                dt = t[j] - t[i]
                if 800 <= dt <= 8000:
                    out.append((tid, t[i], t[i] - 1.37 * dt))
                    break
    return pd.DataFrame(out, columns=["tid", "tp", "t0"])


def main():
    pr = pd.read_parquet(T / "pairs_primary.parquet")
    pop = pr[pr.in_population & (pr.n_post + pr.n_base > 0)].sample(3, random_state=20261026)
    tr = pd.read_csv(D / "cat" / "triggers_m7.csv", parse_dates=["time"]).set_index("id")
    st = pd.read_parquet(D / "raw" / "stations.parquet", columns=["id", "latitude", "longitude"]).groupby("id").median()
    con = duckdb.connect()
    res = []
    for r in pop.itertuples():
        o = int(tr.loc[r.trigger, "time"].value // 10**6)
        post0 = int(np.ceil((o + r.dist_km / 2.5 * 1000 + 2 * H) / H)); post1 = post0 + 24
        base1 = o // H; base0 = base1 - 168
        lat, lon = st.loc[r.tid]
        dk = gc_km(lat, lon, st.latitude.to_numpy(), st.longitude.to_numpy())
        near = list(st.index[dk <= 50])
        months = sorted({pd.Timestamp(base0 * H, unit="ms").strftime("%Y-%m"), pd.Timestamp(post1 * H, unit="ms").strftime("%Y-%m")})
        files = [str(f) for m in months for f in D.glob(f"picks/network=*/year={int(m[:4])}/month={int(m[5:])}.parquet")]
        pk = con.execute(f"""SELECT tid, pha, peak_ms, conf FROM read_parquet({files})
                             WHERE peak_ms >= {base0 * H - 60000} AND peak_ms < {post1 * H + 60000}
                             AND tid IN ({','.join(repr(t) for t in near)})""").df()
        pk = pk.sort_values(["tid", "pha", "peak_ms"])
        g = ((pk.tid != pk.tid.shift()) | (pk.pha != pk.pha.shift()) | (pk.peak_ms.diff() > 500)).cumsum()
        pk = pk.loc[pk.groupby(g).conf.idxmax()]
        pp = pairs_for(pk)
        mine = pp[pp.tid == r.tid].copy()
        others = pp[pp.tid != r.tid]
        ot, otid = others.t0.to_numpy(), others.tid.to_numpy()
        mine["k"] = [len(set(otid[np.abs(ot - x) <= 2500])) for x in mine.t0]
        loc = mine[mine.k >= 2]
        n_post = int(((loc.tp // H >= post0) & (loc.tp // H < post1)).sum())
        n_base = int(((loc.tp // H >= base0) & (loc.tp // H < base1)).sum())
        res.append({"tid": r.tid, "trigger": r.trigger, "mag": float(r.mag), "dist_km": round(float(r.dist_km), 1),
                    "trace_n_post": n_post, "table_n_post": int(r.n_post), "trace_n_base": n_base, "table_n_base": int(r.n_base),
                    "neighbours_within_50km": len(near) - 1, "note": "trace omits teleseismic masking, so table counts are usually equal or slightly lower"})
        print(res[-1], flush=True)
    (T / "handtrace.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
