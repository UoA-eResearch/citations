"""AVN catalog and Stockman et al. (2023) protocol: times in hours from the first event, input events mw > cutoff,
train/test split at hours 1200 (Visso), 1800 (Norcia), 3600 (Campotosto), test history = last 19 training events
(burn-in) + test events, target events M >= 3."""
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
NPP = RUN / "data" / "raw" / "Neural-Point-Process" / "data"
SPLIT = {"Visso": 1200, "Norcia": 1800, "Campotosto": 3600}
CUTOFF = {"Visso": 1.2, "Norcia": 1.2, "Campotosto": 1.3}
TIME_STEP = 20
M0PRED = 3.0


def catalog():
    c = pd.read_csv(NPP / "Catalogs" / "Amatrice_CAT5.v20210504_reduced_cols.csv")
    c["datetime"] = pd.to_datetime(c[["year", "month", "day", "hour", "minute", "second"]])
    c["time"] = (c["datetime"] - c["datetime"][0]) / pd.to_timedelta(1, unit="h")
    return c.dropna()


def split(seq, cutoff=None, cat=None):
    cutoff = CUTOFF[seq] if cutoff is None else cutoff
    c = catalog() if cat is None else cat
    s = c[c.mw > cutoff]
    T, M = s.time.to_numpy(float), s.mw.to_numpy(float)
    up = SPLIT[seq]
    tr = T < up
    T_tr, M_tr, T_te, M_te = T[tr], M[tr], T[~tr], M[~tr]
    T_te_b = np.append(T_tr[-TIME_STEP + 1:], T_te)
    M_te_b = np.append(M_tr[-TIME_STEP + 1:], M_te)
    return dict(T_all=T, M_all=M, T_train=T_tr, M_train=M_tr, T_test=T_te_b, M_test=M_te_b, split=up, cutoff=cutoff)


def released(seq, cutoff=None):
    cutoff = CUTOFF[seq] if cutoff is None else cutoff
    r = pd.read_csv(NPP / "Results" / f"resultsMcut-{cutoff}_partition:{seq}_M0pred:3.csv")
    p = pd.read_csv(NPP / "ETAS_parameters" / f"paramsMcut-{cutoff}_partition:{seq}.csv", header=None, index_col=0)[1]
    params = {k: float(v) for k, v in p.items() if k != "train_time"}
    return r, params
