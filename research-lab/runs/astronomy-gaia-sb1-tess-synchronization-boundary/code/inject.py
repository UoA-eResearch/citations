"""Injection-recovery completeness C(P, A, T) (plan section 1).

Host light curves: one randomly chosen sector of each sample binary with no detecting sector (at least 2,000
hosts; all of them if fewer). Into each, 20 spot-like signals are injected: A sin(2 pi t/P + phi1) + h A
sin(4 pi t/P + phi2), with P log-uniform on 0.3-13 d, semi-amplitude A log-uniform on 0.005-2%, h uniform on 0-0.5,
random phases. Recovery: the sector's highest peak has FAP < 1e-5 and the pipeline's period (after the ACF
double-dip rule) is within 10% of P. C is tabulated on 8 log P x 8 log A bins x 3 TESS-magnitude bins (sample
tertiles).

  inject.py -> data/injections.parquet, results/tables/completeness.csv
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import periods as PS  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
D, T = RUN / "data", RUN / "results" / "tables"
N_HOSTS, N_INJ, SEED = 2000, 20, 20261103
PB = np.logspace(np.log10(0.3), np.log10(13), 9)
AB = np.logspace(np.log10(5e-5), np.log10(2e-2), 9)


def one(args):
    tic, sector, product, path, seed = args
    rng = np.random.default_rng(seed)
    t, f = PS.load(D / "lc" / path, product)
    if t is None:
        return []
    fr = PS.grid(t); out = []
    for _ in range(N_INJ):
        P = float(np.exp(rng.uniform(np.log(0.3), np.log(13)))); A = float(np.exp(rng.uniform(np.log(5e-5), np.log(2e-2))))
        h, p1, p2 = rng.uniform(0, 0.5), rng.uniform(0, 2 * np.pi), rng.uniform(0, 2 * np.pi)
        g = f + A * np.sin(2 * np.pi * t / P + p1) + h * A * np.sin(4 * np.pi * t / P + p2)
        nu, pw, fap, amp, _ = PS.peak(t, g, fr)
        Pr = PS.acf_choice(t, g, 1 / nu)[0] if fap < PS.FAP else np.nan
        out.append((tic, sector, P, A, h, fap, Pr, bool(fap < PS.FAP and abs(Pr - P) / P < 0.10)))
    return out


def main(workers=12):
    sp = pd.read_parquet(D / "sector_periods.parquet")
    st = pd.read_parquet(D / "stars.parquet")
    quiet = set(st.loc[st.cls == "no_detection", "tic"].dropna().astype("int64"))
    ix = pd.read_parquet(D / "lc_index.parquet")
    ok = sp[(sp.n > 0) & sp.tic.isin(quiet)][["tic", "sector", "product"]]
    hosts = ok.merge(ix, on=["tic", "sector", "product"]).sample(frac=1, random_state=SEED).drop_duplicates("tic")
    hosts = hosts.head(N_HOSTS)
    jobs = [(int(r.tic), int(r.sector), r.product, r.path, SEED + i) for i, r in enumerate(hosts.itertuples())]
    with ProcessPoolExecutor(workers) as ex:
        rows = [x for res in ex.map(one, jobs, chunksize=4) for x in res]
    inj = pd.DataFrame(rows, columns=["tic", "sector", "P", "A", "h", "fap", "P_rec", "recovered"])
    inj = inj.merge(st[["tic", "Tmag"]].drop_duplicates("tic"), on="tic", how="left")
    tb = np.r_[-np.inf, st.Tmag.quantile([1 / 3, 2 / 3]).to_numpy(), np.inf]
    inj["pb"] = np.digitize(inj.P, PB) - 1; inj["ab"] = np.digitize(inj.A, AB) - 1; inj["tb"] = np.digitize(inj.Tmag, tb) - 1
    inj.to_parquet(D / "injections.parquet")
    C = inj.groupby(["tb", "pb", "ab"]).recovered.agg(["mean", "size"]).reset_index()
    C.to_csv(T / "completeness.csv", index=False)
    pd.DataFrame({"edge": ["T"] * 4 + ["P"] * 9 + ["A"] * 9, "value": list(tb) + list(PB) + list(AB)}).to_csv(T / "completeness_edges.csv", index=False)
    print(len(hosts), "hosts,", len(inj), "injections; recovered", round(inj.recovered.mean(), 3))


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:]))
