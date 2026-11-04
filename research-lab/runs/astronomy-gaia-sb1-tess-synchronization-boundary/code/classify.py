"""Per-star rotation period and synchronization class (plan sections 0-1).

A star's detecting sectors are those with FAP < 1e-5. Its period is the median of their periodogram periods,
doubled if its best sector (highest power) chose 2P by the ACF rule; it is *inconsistent* if those periods span more
than 10% (max/min > 1.10). Amplitude: median semi-amplitude over detecting sectors. Pulsator: the best sector has
three or more independent significant peaks in 0.3-3 d.

Ambiguous classes (excluded from the primary):
- ellipsoidal_or_double_spot: the undoubled periodogram period is within 5% of P_orb/2 (applied before doubling, so an
  ellipsoidal signal doubled by the ACF rule cannot pass as synchronized; implementation note in D1);
- possible_beaming: period within 10% of P_orb and amplitude below twice 4K/c;
- pulsator.
Synchronized: |P_rot - P_ps| / P_ps < 0.10, P_ps = P_orb for e < 0.05 or SB1C, else Hut (1981) pseudo-synchronous.

  classify.py -> data/stars.parquet
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
FAP, C_KMS = 1e-5, 299792.458


def hut_ratio(e):
    e2 = e * e
    return (1 + 7.5 * e2 + 45 / 8 * e2 ** 2 + 5 / 16 * e2 ** 3) / ((1 + 3 * e2 + 3 / 8 * e2 ** 2) * (1 - e2) ** 1.5)


def star_periods(sp):
    det = sp[sp.fap < FAP]
    if det.empty:
        return pd.DataFrame(columns=["tic", "n_sectors_det", "p_ls_med", "span", "amp", "doubled", "n_pulse", "p_rot"])
    best = det.sort_values("power", ascending=False).drop_duplicates("tic").set_index("tic")
    g = det.groupby("tic")
    out = pd.DataFrame({"n_sectors_det": g.size(), "p_ls_med": g.p_ls.median(), "span": g.p_ls.max() / g.p_ls.min(),
                        "amp": g.amp.median()})
    out["doubled"] = best.doubled.reindex(out.index).fillna(False).astype(bool)
    out["n_pulse"] = best.n_pulse.reindex(out.index)
    out["p_rot"] = np.where(out.doubled, 2 * out.p_ls_med, out.p_ls_med)
    return out.reset_index()


def main():
    s = pd.read_parquet(D / "sample.parquet")
    s = s[s.period < 12].merge(pd.read_parquet(D / "tic.parquet")[["source_id", "tic", "Tmag"]], on="source_id", how="left")
    sp = pd.read_parquet(D / os.environ.get("SECTOR_IN", "sector_periods.parquet"))
    prods = os.environ.get("LC_PRODUCTS", "tess-spoc").split(",")      # D1: TESS-SPOC only in the primary
    sp = sp[sp["product"].isin(prods)]
    n_lc = sp[sp.n > 0].groupby("tic").size()
    st = s.merge(star_periods(sp), on="tic", how="left")
    st["n_sectors_lc"] = st.tic.map(n_lc).fillna(0).astype(int)
    e = np.where((st.nss_solution_type == "SB1C") | (st.eccentricity.fillna(0) < 0.05), 0.0, st.eccentricity.fillna(0))
    st["p_ps"] = st.period / hut_ratio(e)
    st["beam_amp"] = 4 * st.semi_amplitude_primary / C_KMS
    near_half = (np.abs(st.p_ls_med - st.period / 2) / (st.period / 2)) < 0.05
    near_orb = (np.abs(st.p_rot - st.period) / st.period) < 0.10
    cls = np.select(
        [st.tic.isna(), st.n_sectors_lc == 0, st.p_rot.isna(), st.span > 1.10, st.n_pulse >= 3, near_half,
         near_orb & (st.amp < 2 * st.beam_amp)],
        ["no_tic", "no_light_curve", "no_detection", "inconsistent", "pulsator", "ellipsoidal_or_double_spot", "possible_beaming"],
        default="detected")
    st["cls"] = cls
    r = st.p_rot / st.p_ps
    st["sync"] = np.where(st.cls == "detected", np.abs(r - 1) < 0.10, np.nan)
    st["sync_state"] = np.where(st.cls != "detected", "", np.where(np.abs(r - 1) < 0.10, "synchronized", np.where(r > 1, "sub", "super")))
    st.to_parquet(D / os.environ.get("STARS_OUT", "stars.parquet"))
    print(st.cls.value_counts().to_dict()); print(st[st.cls == "detected"].sync_state.value_counts().to_dict())


if __name__ == "__main__":
    main()
