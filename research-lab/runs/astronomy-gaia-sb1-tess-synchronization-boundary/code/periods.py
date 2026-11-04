"""Per-sector rotation-period search (plan section 1). The search never sees the orbit.

Flux: TESS-SPOC PDCSAP_FLUX; QLP SAP_FLUX (QLP's KSPSAP_FLUX is spline-detrended on sub-day scales, which would
erase rotation). Cadences with nonzero QUALITY or non-finite flux are dropped, each sector is median-normalised, and
points more than 5 sigma (MAD) from a running median of 25 points are clipped.

Search: generalised Lomb-Scargle over 0.2-13 d; a sector detects if its highest peak's Baluev false-alarm
probability is below 1e-5. Double-dip rule: the ACF of a 30-minute-binned light curve is examined for local maxima
within 15% of P and of 2P; if the 2P peak exists (2P <= 13 d and <= half the sector's span) and is higher than the P
peak by more than 0.05, or there is no P peak, 2P is used. Pulsator flag: up to five rounds of prewhitening;
the number of significant (FAP < 1e-5) peaks in 0.3-3 d that are not within 2% of an integer ratio of an earlier one.

  periods.py -> data/sector_periods.parquet
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.timeseries import LombScargle
from scipy.ndimage import median_filter
from scipy.signal import find_peaks

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
PMIN, PMAX, FAP = 0.2, 13.0, 1e-5


def load(path, product):
    with fits.open(path, memmap=False) as h:
        d = h[1].data
        col = "PDCSAP_FLUX" if product == "tess-spoc" else "SAP_FLUX"
        t, f, q = np.asarray(d["TIME"], float), np.asarray(d[col], float), np.asarray(d["QUALITY"])
    t, f = prep(t, f, q)
    if t is not None and product == "qlp" and os.environ.get("QLP_DETREND") == "1":
        t, f = detrend(t, f)                       # D1 sensitivity
    return t, f


def detrend(t, f):
    """D1 sensitivity for QLP: subtract a quadratic from each continuous segment (split at gaps over 1 d)."""
    cut = np.r_[0, np.flatnonzero(np.diff(t) > 1.0) + 1, len(t)]
    g = f.copy()
    for a, b in zip(cut[:-1], cut[1:]):
        if b - a >= 10:
            x = t[a:b] - t[a:b].mean()
            g[a:b] = f[a:b] - np.polyval(np.polyfit(x, f[a:b], 2), x)
    return t, g


def prep(t, f, q=None):
    ok = np.isfinite(t) & np.isfinite(f) & ((q == 0) if q is not None else True)
    t, f = t[ok], f[ok]
    if len(t) < 100:
        return None, None
    f = f / np.median(f) - 1.0
    r = f - median_filter(f, size=25, mode="nearest")
    s = 1.4826 * np.median(np.abs(r - np.median(r)))
    k = np.abs(r) < 5 * s if s > 0 else np.ones(len(f), bool)
    return t[k], f[k]


def grid(t):
    span = t.max() - t.min()
    return np.arange(1 / PMAX, 1 / PMIN, 1 / (10 * span))


def peak(t, f, fr):
    ls = LombScargle(t, f)
    pw = ls.power(fr, method="fast")
    i = int(np.argmax(pw))
    fap = float(ls.false_alarm_probability(pw[i], minimum_frequency=fr[0], maximum_frequency=fr[-1], method="baluev"))
    th = ls.model_parameters(fr[i])
    return fr[i], float(pw[i]), fap, float(np.hypot(th[1], th[2])), ls


def acf_choice(t, f, P):
    span = t.max() - t.min()
    if 2 * P > min(PMAX, span / 2):
        return P, False
    b = np.floor((t - t.min()) / (30 / 1440)).astype(int)
    x = np.full(b.max() + 1, np.nan); x[np.unique(b)] = pd.Series(f).groupby(b).mean().to_numpy()
    x = np.nan_to_num(x - np.nanmean(x)); n = len(x)
    a = np.correlate(x, x, "full")[n - 1:] / np.maximum(np.arange(n, 0, -1), 1)
    a = a / a[0] if a[0] > 0 else a
    lag = np.arange(n) * 30 / 1440
    pk, _ = find_peaks(a)
    def best(target):
        w = pk[(lag[pk] > 0.85 * target) & (lag[pk] < 1.15 * target)]
        return a[w].max() if len(w) else None
    h1, h2 = best(P), best(2 * P)
    if h2 is not None and (h1 is None or h2 > h1 + 0.05):
        return 2 * P, True
    return P, False


def pulsator_peaks(t, f, fr):
    found, r = [], f.copy()
    for _ in range(5):
        nu, pw, fap, amp, ls = peak(t, r, fr)
        if fap >= FAP:
            break
        found.append(nu)
        r = r - ls.model(t, nu)
    indep = []
    for nu in found:
        P = 1 / nu
        if not (0.3 <= P <= 3):
            continue
        if any(min(abs(nu / m - round(nu / m)), abs(m / nu - round(m / nu))) < 0.02 for m in indep):
            continue
        indep.append(nu)
    return len(indep)


def one(row):
    tic, sector, product, path = row
    try:
        t, f = load(D / "lc" / path, product)
    except Exception as e:
        return (tic, sector, product, 0, np.nan, np.nan, np.nan, np.nan, np.nan, False, -1, f"read error {type(e).__name__}")
    if t is None:
        return (tic, sector, product, 0, np.nan, np.nan, np.nan, np.nan, np.nan, False, -1, "too few points")
    fr = grid(t)
    nu, pw, fap, amp, _ = peak(t, f, fr)
    P = 1 / nu
    P2, dbl = acf_choice(t, f, P) if fap < FAP else (P, False)
    npul = pulsator_peaks(t, f, fr) if fap < FAP else 0
    return (tic, sector, product, len(t), P, P2, pw, fap, amp, dbl, npul, "")


def main(workers=12):
    ix = pd.read_parquet(D / "lc_index.parquet")
    if os.environ.get("ONLY_PRODUCT"):
        ix = ix[ix["product"] == os.environ["ONLY_PRODUCT"]]
    ix = ix[[(D / "lc" / p).exists() for p in ix.path]]
    rows = list(ix[["tic", "sector", "product", "path"]].itertuples(index=False, name=None))
    with ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(one, rows, chunksize=20))
    out = pd.DataFrame(res, columns=["tic", "sector", "product", "n", "p_ls", "p", "power", "fap", "amp", "doubled", "n_pulse", "note"])
    out.to_parquet(D / os.environ.get("PERIODS_OUT", "sector_periods.parquet"))
    print(len(out), "sector light curves |", int((out.fap < FAP).sum()), "detections")


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:]))
