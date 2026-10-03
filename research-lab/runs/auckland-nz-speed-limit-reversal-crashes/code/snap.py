"""Snap CAS crash points to OSM road segments.

Rule (fixed in plan.md): candidates are segments within 30 m of the crash point. Among them, prefer segments whose
normalised OSM name equals the normalised CAS crashLocation1, or, for state-highway crashes, whose OSM ref carries the
same SH number; take the nearest preferred candidate, else the nearest candidate. Crashes with no segment within 30 m
are left unsnapped (seg = -1) and counted.
"""
import re

import numpy as np
import pandas as pd
import shapely

ABBR = {"RD": "ROAD", "ST": "STREET", "AVE": "AVENUE", "AV": "AVENUE", "DR": "DRIVE", "CRES": "CRESCENT",
        "PL": "PLACE", "TCE": "TERRACE", "HWY": "HIGHWAY", "PDE": "PARADE", "LN": "LANE", "CRT": "COURT",
        "CT": "COURT", "GR": "GROVE", "MT": "MOUNT", "BLVD": "BOULEVARD", "HTS": "HEIGHTS", "ESP": "ESPLANADE",
        "SQ": "SQUARE", "CL": "CLOSE", "PKWY": "PARKWAY", "HWAY": "HIGHWAY"}
SH = re.compile(r"\bSH\s*0*(\d+)")


def norm_name(s):
    if not isinstance(s, str) or not s:
        return ""
    s = s.upper()
    s = re.sub(r"\(.*?\)", " ", s)
    s = s.replace("'", "").replace("’", "").replace("Ā", "A").replace("Ē", "E").replace("Ī", "I").replace("Ō", "O").replace("Ū", "U")
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    toks = [ABBR.get(t, t) for t in s.split()]
    return " ".join(toks)


def sh_numbers(s):
    return set(SH.findall(s.upper())) if isinstance(s, str) else set()


def snap(crash_xy, crash_loc1, segs, tol=30.0):
    """crash_xy: GeoSeries of points (NZTM); crash_loc1: array of CAS crashLocation1; segs: GeoDataFrame with
    seg, name, ref. Returns (seg id array, distance array, name_match bool array)."""
    pi, si = segs.sindex.query(crash_xy.values, predicate="dwithin", distance=tol)
    segg = segs.geometry.values
    d = shapely.distance(np.asarray(crash_xy.values)[pi], np.asarray(segg)[si])
    cn = np.array([norm_name(x) for x in crash_loc1])
    csh = [sh_numbers(x) for x in crash_loc1]
    sn = segs["_norm"].values if "_norm" in segs else np.array([norm_name(x) for x in segs.name])
    ssh = segs["_sh"].values if "_sh" in segs else np.array([sh_numbers(x) for x in segs.ref])
    match = np.array([(cn[a] != "" and cn[a] == sn[b]) or bool(csh[a] & ssh[b]) for a, b in zip(pi, si)])
    cand = pd.DataFrame({"p": pi, "s": si, "d": d, "m": match})
    cand = cand.sort_values(["p", "m", "d"], ascending=[True, False, True]).drop_duplicates("p")
    out = np.full(len(crash_xy), -1)
    dist = np.full(len(crash_xy), np.nan)
    mm = np.zeros(len(crash_xy), bool)
    out[cand.p.values] = segs.seg.values[cand.s.values]
    dist[cand.p.values] = cand.d.values
    mm[cand.p.values] = cand.m.values
    return out, dist, mm
