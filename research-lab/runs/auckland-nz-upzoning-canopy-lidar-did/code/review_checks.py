"""Checks added after independent review (deviations.md D4-D7). The preregistered verdict comes from analysis.py.

Regression to the mean: the preregistered strata condition on E1 canopy while both outcomes are differences from E1.
This script re-estimates post (E1->E2), pre (E0->E1) and long (E0->E2) differences under alternative strata:
  E1 band (preregistered) | no canopy band | E0 band | E2 band (placebo) | endpoint-mean band (Oldham: band of the mean
  of the two epochs being differenced) | endpoint-mean band + change in raw point density (pts/m2, tile headers).
Data versions: E2 as originally processed, and E2 with the 2024 overlap flag dropped (D4); both with tile-seam
counts capped (D6).
Also: decision rule applied to the RTM-free specs (post hoc); mechanism split under endpoint-mean strata; Kitagawa
decomposition of the raw high-SH post gap; density by epoch and zone.
Outputs: results/tables/review_specs.csv, review_mechanism.csv, review_density.csv
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analysis as A  # noqa: E402

TAB = A.TAB
BANDS = [-0.1, 5, 15, 30, 50, 100.1]
LAB = ["0-5", "5-15", "15-30", "30-50", ">50"]


def band(x):
    return pd.cut(x, BANDS, labels=LAB).astype(str)


def density(m):
    t = pd.read_parquet(A.RUN / "data" / "tiles_needed.parquet")
    t["dens"] = t.npts / ((t.maxx - t.minx) * (t.maxy - t.miny))
    x, y = m.cx.values + 15, m.cy.values + 15
    for ep, col in [("2013", "dens_e0"), ("2016", "dens_e1"), ("2024", "dens_e2")]:
        tt = t[t.epoch == ep]
        if ep == "2016":
            out = np.full(len(m), np.nan)
            for c in ("N", "S"):
                sub = tt[tt.key.str.startswith("NZ16_N" if c == "N" else "NZ16_S")]
                v = _lookup(sub, x, y)
                out = np.where(m.coll.values == c, v, out)
            m[col] = out
        else:
            m[col] = _lookup(tt, x, y)
    return m


def _lookup(tt, x, y):
    out = np.full(len(x), np.nan)
    for r in tt.itertuples():
        msk = (x >= r.minx) & (x < r.maxx) & (y >= r.miny) & (y < r.maxy)
        out[msk] = r.dens
    return out


def specs(m, version):
    m = m.copy()
    m["d_post"], m["d_pre"], m["d_long"] = m.c3_e2 - m.c3_e1, m.c3_e1 - m.c3_e0, m.c3_e2 - m.c3_e0
    base = m.talb.astype(str) + "|" + m.dband + "|" + m.coll.astype(str)
    m["s_e1"] = base + "|" + band(m.c3_e1)
    m["s_none"] = base
    m["s_e0"] = base + "|" + band(m.c3_e0)
    m["s_e2"] = base + "|" + band(m.c3_e2)
    m["s_post_mean"] = base + "|" + band((m.c3_e1 + m.c3_e2) / 2)
    m["s_pre_mean"] = base + "|" + band((m.c3_e0 + m.c3_e1) / 2)
    m["s_long_mean"] = base + "|" + band((m.c3_e0 + m.c3_e2) / 2)
    m["dd_post"], m["dd_pre"], m["dd_long"] = m.dens_e2 - m.dens_e1, m.dens_e1 - m.dens_e0, m.dens_e2 - m.dens_e0
    rows = []
    for lab, fe in [("E1 band (preregistered)", "s_e1"), ("no canopy band", "s_none"), ("E0 band", "s_e0"),
                    ("E2 band (placebo)", "s_e2"), ("endpoint-mean band (Oldham)", "mean"),
                    ("endpoint-mean band + density change", "mean+d")]:
        for out in ("post", "pre", "long"):
            f = {"mean": f"s_{out}_mean", "mean+d": f"s_{out}_mean"}.get(fe, fe)
            extra = f"dd_{out}" if fe == "mean+d" else None
            q = m.dropna(subset=[f"dd_{out}"]) if extra else m
            for r in A.fit(q, f"d_{out}", lab, extra=extra, fe=f):
                r.update(version=version, difference=out)
                rows.append(r)
    return pd.DataFrame(rows)


def verdict(post, pre):
    pre_ok = abs(pre.est) <= 0.5
    if pre_ok and post.est <= -1 and post.hi < 0:
        return "Supported"
    if pre_ok and post.lo > -1:
        return "Contradicted"
    return "Inconclusive"


def main():
    out = []
    versions = [("E2 as processed (overlap flag kept)", None, "units_review_orig.parquet")]
    if (A.RUN / "data" / "cells" / "2024_noov").exists() and len(list((A.RUN / "data" / "cells" / "2024_noov").glob("*.parquet"))) >= 2200:
        versions.append(("E2 with overlap flag dropped (D4)", "2024_noov", "units_review_noov.parquet"))
    mech_rows, dens_rows = [], []
    for vlab, sub, fn in versions:
        A.build_units(e2_sub=sub, out_name=fn, seam_cap=True)
        m = density(pd.read_parquet(A.RUN / "data" / fn))
        sp = specs(m, vlab)
        out.append(sp)
        # post hoc decision rule on RTM-free specs
        for lab in ("no canopy band", "endpoint-mean band (Oldham)", "endpoint-mean band + density change"):
            h = sp[(sp.term == "high") & (sp.analysis == lab)].set_index("difference")
            mech_rows.append(dict(version=vlab, analysis=f"decision rule applied post hoc: {lab}",
                                  value=verdict(h.loc["post"], h.loc["pre"])))
        # mechanism under endpoint-mean strata
        m["d_post"] = m.c3_e2 - m.c3_e1
        m["s_post_mean"] = m.talb.astype(str) + "|" + m.dband + "|" + m.coll.astype(str) + "|" + band((m.c3_e1 + m.c3_e2) / 2)
        m["redev"] = (m.bld_e2 - m.bld_e1).abs() >= 10
        for lab, msk in [("not redeveloped", ~m.redev), ("redeveloped", m.redev)]:
            r = A.fit(m[msk], "d_post", lab, fe="s_post_mean")[0]
            mech_rows.append(dict(version=vlab, analysis=f"mechanism (endpoint-mean strata): {lab}", value=r["est"], lo=r["lo"], hi=r["hi"]))
        g = m.groupby(["group", "redev"]).d_post.mean().unstack()
        share = m.groupby("group").redev.mean()
        gap = (m[m.group == "high"].d_post.mean() - m[m.group == "SH"].d_post.mean())
        comp = (share["high"] - share["SH"]) * ((g.loc["SH", True] + g.loc["high", True]) / 2 - (g.loc["SH", False] + g.loc["high", False]) / 2)
        mech_rows += [dict(version=vlab, analysis="raw high - SH post gap (pp)", value=gap),
                      dict(version=vlab, analysis="Kitagawa: composition (more redevelopment)", value=comp),
                      dict(version=vlab, analysis="Kitagawa: within redevelopment status", value=gap - comp),
                      dict(version=vlab, analysis="redevelopment share high / SH", value=f"{share['high']:.3f} / {share['SH']:.3f}"),
                      dict(version=vlab, analysis="mean canopy change of redeveloped cells SH / high / low",
                           value=f"{g.loc['SH', True]:.2f} / {g.loc['high', True]:.2f} / {g.loc['low', True]:.2f}")]
        dd = m.groupby("group")[["dens_e0", "dens_e1", "dens_e2", "c3_e0", "c3_e1", "c3_e2"]].mean().assign(version=vlab)
        dens_rows.append(dd)
    res = pd.concat(out)
    res.to_csv(TAB / "review_specs.csv", index=False)
    show = res[res.term == "high"].pivot_table(index=["version", "analysis"], columns="difference", values="est", sort=False)
    print(show.round(2).to_string())
    pd.DataFrame(mech_rows).to_csv(TAB / "review_mechanism.csv", index=False)
    print(pd.DataFrame(mech_rows).to_string(index=False))
    pd.concat(dens_rows).to_csv(TAB / "review_density.csv")
    print(pd.concat(dens_rows).round(2).to_string())


if __name__ == "__main__":
    main()
