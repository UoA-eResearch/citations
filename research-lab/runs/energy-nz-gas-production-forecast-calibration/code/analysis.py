"""Calibration of the forecasts and of the reserve categories (plan sections 1, 4, 5, 6).

Reads data/profiles.csv, data/realised.csv, data/national.csv, data/reserves.csv and data/gic_annual.csv.
Writes results/tables/primary.json, pairs.csv, by_horizon.csv, revisions.csv and validation.json.

Nothing here chooses a threshold: the hypotheses, the error measure (epsilon = 0.05 PJ), the horizons, the
field-cluster bootstrap and the decision rules are all as preregistered in plan.md.
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
T = RUN / "results" / "tables"
EPS, B, SEED = 0.05, 2000, 20261020
NOT_A_FIELD = {"Manufactured Production"}
H1_T1, H1_T3 = np.log(1.05), np.log(1.15)


def rows(name):
    with open(RUN / "data" / name) as fh:
        return list(csv.DictReader(fh))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    # ---- forecasts: one value per (vintage, mapped field, target year).
    # Two captures can carry the same vintage (MBIE re-published the "as at 1 January 2021" workbook); the later
    # capture is the more revised publication, so one capture per vintage year is kept.
    prof = [r for r in rows("profiles.csv") if r["field"] not in NOT_A_FIELD]
    keep = {}
    for r in prof:
        v = int(r["vintage_year"])
        if v not in keep or r["capture"] > keep[v]:
            keep[v] = r["capture"]
    fc = defaultdict(float)
    for r in prof:
        v = int(r["vintage_year"])
        if r["capture"] != keep[v]:
            continue
        fc[(v, r["field"], int(r["year"]))] += f(r["pj"]) or 0.0

    # ---- realised by field: latest capture wins (MBIE revises back years)
    best, act = {}, {}
    for r in rows("realised.csv"):
        if r["field"] in NOT_A_FIELD:
            continue
        k = (r["basis"], r["field"], int(r["year"]))
        if k not in best or r["capture"] > best[k]:
            best[k], act[k] = r["capture"], f(r["pj"]) or 0.0
    vmax = {}
    for (v, _, t) in fc:
        vmax[v] = max(vmax.get(v, t), t)                     # the last year each vintage's profile covers
    years_act = sorted({y for (_, _, y) in act})
    tmax = max(years_act)
    fields = sorted({fld for (_, fld, _) in act} | {fld for (_, fld, _) in fc})

    # ---- pairs, union rule: a field enters if it was forecast OR produced
    pairs = []
    for basis in ("net", "gross"):
        for (v, fld, t), F in fc.items():
            if t > tmax or t < v:
                continue
            A = act.get((basis, fld, t))
            if A is None:
                continue
            pairs.append(dict(basis=basis, vintage=v, field=fld, year=t, h=t - v, forecast=F, realised=A,
                              e=float(np.log((F + EPS) / (A + EPS)))))
        for (b, fld, t), A in act.items():
            if b != basis or A <= 0:
                continue
            for v in sorted({vv for (vv, _, _) in fc}):
                if not (v <= t <= tmax) or (v, fld, t) in fc:
                    continue
                if not any(k[0] == v for k in fc):
                    continue
                # The field produced in year t but the vintage gives no number for it. Either the field is absent
                # from the vintage's profile altogether, or it is listed but its cell for that year is blank. Both
                # are a zero forecast under the preregistered union rule (plan §3). The draft skipped the second
                # case, which dropped, for instance, the 2019 vintage's blank Maui cells for 2022 and 2023 (D2).
                listed = any(k[0] == v and k[1] == fld for k in fc)
                if listed and t > vmax.get(v, t):
                    continue                                    # beyond the vintage's own profile horizon
                pairs.append(dict(basis=basis, vintage=v, field=fld, year=t, h=t - v, forecast=0.0, realised=A,
                                  e=float(np.log(EPS / (A + EPS))), missing_from_profile=not listed,
                                  blank_cell=listed))
    with open(T / "pairs.csv", "w", newline="") as fh:
        cols = ["basis", "vintage", "field", "year", "h", "forecast", "realised", "e", "missing_from_profile",
                "blank_cell"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(pairs)

    rng = np.random.default_rng(SEED)

    def boot_median(sel):
        """Median of e with a field-cluster bootstrap; returns (median, lo, hi, se, n, n_fields)."""
        by = defaultdict(list)
        for p in sel:
            by[p["field"]].append(p["e"])
        ks = sorted(by)
        if not ks:
            return (None,) * 4 + (0, 0)
        allv = [x for k in ks for x in by[k]]
        draws = []
        for _ in range(B):
            pick = rng.choice(len(ks), len(ks))
            vals = [x for i in pick for x in by[ks[i]]]
            draws.append(np.median(vals))
        return (float(np.median(allv)), float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5)),
                float(np.std(draws, ddof=1)), len(allv), len(ks))

    out = {"vintages": sorted({v for (v, _, _) in fc}), "realised_years": [min(years_act), tmax],
           "fields": fields, "epsilon_pj": EPS, "bootstrap": B}
    horizon = []
    for basis in ("net", "gross"):
        for h in range(0, 6):
            sel = [p for p in pairs if p["basis"] == basis and p["h"] == h]
            m, lo, hi, se, n, nf = boot_median(sel)
            vint = sorted({p["vintage"] for p in sel})
            horizon.append(dict(basis=basis, h=h, median_e=m, lo=lo, hi=hi, se=se, n_pairs=n, n_fields=nf,
                                n_vintages=len(vint), vintages=";".join(map(str, vint)),
                                pct=None if m is None else 100 * (np.exp(m) - 1),
                                mde_pct=None if se is None else 100 * (np.exp(2.8 * se) - 1)))
    with open(T / "by_horizon.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(horizon[0])); w.writeheader(); w.writerows(horizon)

    def at(basis, h):
        return next(r for r in horizon if r["basis"] == basis and r["h"] == h)
    m1, m3 = at("net", 1), at("net", 3)
    sup = (m1["median_e"] >= H1_T1 and m3["median_e"] >= H1_T3 and m1["lo"] > 0 and m3["lo"] > 0)
    ref = (m1["hi"] < H1_T1 and m3["hi"] < H1_T3)
    out["H1"] = dict(basis="net", m1=m1, m3=m3, threshold_h1_pct=5.0, threshold_h3_pct=15.0,
                     verdict="Supported" if sup else "Refuted" if ref else "Inconclusive")

    # ---- sensitivities (plan section 4)
    sens = {}
    for nm, keep_fn in (("exclude_others", lambda q: q["field"] != "Others"),
                        ("realised_above_0p5PJ", lambda q: q["realised"] > 0.5),
                        ("exclude_others_and_small", lambda q: q["field"] != "Others" and q["realised"] > 0.5)):
        sens[nm] = {}
        for h in (1, 3):
            sel = [q for q in pairs if q["basis"] == "net" and q["h"] == h and keep_fn(q)]
            m, lo, hi, se, n, nf = boot_median(sel)
            sens[nm][h] = dict(median_e=m, lo=lo, hi=hi, n_pairs=n, n_fields=nf,
                               pct=None if m is None else 100 * (np.exp(m) - 1))
    for nm in ("cluster_by_vintage",):
        sens[nm] = {}
        for h in (1, 3):
            sel = [q for q in pairs if q["basis"] == "net" and q["h"] == h]
            by = defaultdict(list)
            for q in sel:
                by[q["vintage"]].append(q["e"])
            ks = sorted(by)
            draws = [np.median([x for i in rng.choice(len(ks), len(ks)) for x in by[ks[i]]]) for _ in range(B)]
            sens[nm][h] = dict(median_e=float(np.median([x for k in ks for x in by[k]])),
                               lo=float(np.percentile(draws, 2.5)), hi=float(np.percentile(draws, 97.5)),
                               n_vintages=len(ks))
    out["sensitivity"] = sens

    # ---- national. MBIE's energy overview series "Indigenous Production -> Natural gas" reproduces the sum of
    # the field-level NET production exactly for every overlapping year (validation below), and its 2025 value
    # matches MBIE's published 102 PJ, so it is the net series extended to 2025.
    nat = {}
    for r in rows("national.csv"):
        nat[int(r["year"])] = f(r["gross_pj"])
    natnet = defaultdict(float)
    natgross = defaultdict(float)
    for (b, fld, t), A in act.items():
        (natnet if b == "net" else natgross)[t] += A
    natsum = []
    for v in sorted({vv for (vv, _, _) in fc}):
        for t in range(v, max(nat) + 1):
            F = sum(val for (vv, _, tt), val in fc.items() if vv == v and tt == t)
            if F <= 0:
                continue
            row = dict(vintage=v, year=t, h=t - v, forecast_total=F,
                       realised_net=nat.get(t), realised_gross=natgross.get(t) or None)
            for k, a in (("gross", row["realised_gross"]), ("net", row["realised_net"])):
                row[f"e_{k}"] = float(np.log(F / a)) if a else None
            natsum.append(row)
    out["national"] = {}
    for basis in ("gross", "net"):
        byh = defaultdict(list)
        for r in natsum:
            if r[f"e_{basis}"] is not None:
                byh[r["h"]].append(r[f"e_{basis}"])
        out["national"][basis] = {h: dict(n_vintages=len(v), median_pct=100 * (np.exp(np.median(v)) - 1),
                                          min_pct=100 * (np.exp(min(v)) - 1), max_pct=100 * (np.exp(max(v)) - 1))
                                  for h, v in sorted(byh.items()) if h <= 6}
    with open(T / "national_pairs.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(natsum[0])); w.writeheader(); w.writerows(natsum)

    # ---- reserve-category calibration: ultimate recoverable revisions between consecutive vintages
    # Keyed on the harmonised field, with the raw names that map to it summed within a vintage. The draft keyed on
    # raw names, so a field renamed between vintages ("Turangi" / "Turangi and Turangi McKee Overthrust") dropped
    # out of the comparison (D2). "Others" is a changing basket of small fields, not a field, and is excluded.
    # One capture per vintage, the latest, as for the profiles.
    rkeep = {}
    for r in rows("reserves.csv"):
        v = int(r["vintage_year"])
        if v not in rkeep or r["capture"] > rkeep[v]:
            rkeep[v] = r["capture"]
    ur = defaultdict(dict)
    for r in rows("reserves.csv"):
        v = int(r["vintage_year"])
        if r["capture"] != rkeep[v] or r["field"] in NOT_A_FIELD or r["field"] in ("Others", "UNMAPPED"):
            continue
        for k in ("1", "2", "3"):
            x = f(r[f"ur{k}"])
            if x is not None:
                d = ur[k].setdefault(v, {})
                d[r["field"]] = d.get(r["field"], 0.0) + x
    revs, rev_rows = {}, []
    for k in ("1", "2", "3"):
        vs = sorted(ur[k])
        down = tot = 0
        for a, b in zip(vs, vs[1:]):
            if b - a != 1:
                continue
            for fld, va in ur[k][a].items():
                vb = ur[k][b].get(fld)
                if vb is None or va <= 0:
                    continue
                rel = vb / va - 1
                rev_rows.append(dict(category=f"{k}P", field=fld, v_from=a, v_to=b, ur_from=va, ur_to=vb,
                                     rel_change=rel))
                if abs(rel) > 0.01:
                    tot += 1
                    down += rel < 0
        if tot:
            p = down / tot
            lo, hi = (lambda c, hw: (c - hw, c + hw))(
                (p + 1.96 ** 2 / (2 * tot)) / (1 + 1.96 ** 2 / tot),
                1.96 * np.sqrt(p * (1 - p) / tot + 1.96 ** 2 / (4 * tot ** 2)) / (1 + 1.96 ** 2 / tot))
            revs[f"{k}P"] = dict(n_revised=tot, n_down=down, share_down=p, lo=float(lo), hi=float(hi))
    with open(T / "revisions.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rev_rows[0])); w.writeheader(); w.writerows(rev_rows)
    out["revisions"] = revs
    # the volume behind the sign count: net PJ revision of ultimate recoverable, by category and vintage pair
    pj = defaultdict(dict)
    for x in rev_rows:
        key = f"{x['v_from']}-{x['v_to']}"
        pj[x["category"]][key] = pj[x["category"]].get(key, 0.0) + (x["ur_to"] - x["ur_from"])
    out["revisions_pj"] = {c: {k: round(v, 1) for k, v in sorted(d.items())} for c, d in pj.items()}
    r2 = revs.get("2P")
    out["H2"] = dict(**(r2 or {}), threshold=0.50, lead_reference=0.60,
                     verdict=("Supported" if r2 and r2["lo"] > 0.50 else
                              "Refuted" if r2 and r2["hi"] <= 0.50 else "Inconclusive"))
    r1 = revs.get("1P")
    out["H3"] = dict(**(r1 or {}), threshold=0.10,
                     verdict=("Supported" if r1 and r1["lo"] > 0.10 else
                              "Refuted" if r1 and r1["hi"] <= 0.10 else "Inconclusive"))

    # ---- validation (plan section 5)
    val = {}
    for v in sorted({vv for (vv, _, _) in fc}):
        F = sum(val2 for (vv, _, tt), val2 in fc.items() if vv == v and tt == v)
        val[f"profile_total_first_year_{v}"] = round(F, 2)
    val["national_net_mbie_overview"] = {y: round(nat[y], 1) for y in sorted(nat) if y >= 2018}
    val["national_net_summed_from_fields"] = {y: round(natnet[y], 1) for y in sorted(natnet) if y >= 2018}
    val["national_gross_summed_from_fields"] = {y: round(natgross[y], 1) for y in sorted(natgross) if y >= 2018}
    val["overview_matches_field_net"] = {y: round(nat[y] - natnet[y], 3) for y in sorted(natnet) if y >= 2018}
    val["mbie_published_2025_net_pj"] = 102.0
    val["kept_capture_per_vintage"] = {str(k): v for k, v in sorted(keep.items())}
    gic = defaultdict(float)
    for r in rows("gic_annual.csv"):
        if int(r["days"]) >= 365:
            gic[int(r["year"])] += f(r["pj"]) or 0.0
    val["gic_four_group_total_by_year"] = {y: round(v, 1) for y, v in sorted(gic.items())}
    # ---- plan §5: three published MBIE statements, reproducible now that the 2025 and 2026 vintages are in hand
    # (the draft dropped them on the false premise that those releases were not archived; D2)
    def prof_total(v, t):
        return sum(F for (vv, _, tt), F in fc.items() if vv == v and tt == t)
    def rr2_total(v):
        tot = 0.0
        for r in rows("reserves.csv"):
            if int(r["vintage_year"]) == v and r["capture"] == rkeep.get(v) and f(r["rr2"]) is not None \
                    and r["field"] not in NOT_A_FIELD:
                tot += f(r["rr2"])
        return tot
    mbie = {}
    if 2025 in {k[0] for k in fc} and 2025 in nat:
        p25, a25 = prof_total(2025, 2025), nat[2025]
        mbie["1_2025_realised_vs_2025_profile"] = dict(profile=round(p25, 2), realised=round(a25, 2),
            pct=round(100 * (a25 / p25 - 1), 1), published_pct=-4.1)
    if {2025, 2026} <= {k[0] for k in fc}:
        a, b = prof_total(2025, 2026), prof_total(2026, 2026)
        mbie["2_2026_profile_vs_2025_profile_for_2026"] = dict(v2025=round(a, 2), v2026=round(b, 2),
            pct=round(100 * (b / a - 1), 1), published_pct=-15.0)
    if {2025, 2026} <= set(rkeep):
        a, b = rr2_total(2025), rr2_total(2026)
        mbie["3_2P_remaining_2026_vs_2025"] = dict(v2025=round(a, 1), v2026=round(b, 1),
            pct=round(100 * (b / a - 1), 1), published_2026_pj=731, published_pct=-23.0,
            diff_from_published_pct=round(100 * (b / 731 - 1), 1))
    val["mbie_statements"] = mbie

    # ---- plan §4, reported alongside: error by vintage, and the zero-forecast / zero-outcome shares
    byv = {}
    for v in sorted({q["vintage"] for q in pairs}):
        for h in (0, 1, 2, 3):
            es = [q["e"] for q in pairs if q["basis"] == "net" and q["vintage"] == v and q["h"] == h]
            if es:
                byv.setdefault(str(v), {})[str(h)] = dict(n=len(es), median_pct=round(100 * (np.exp(np.median(es)) - 1), 1))
    out["error_by_vintage"] = byv
    net = [q for q in pairs if q["basis"] == "net" and q["h"] >= 1]
    out["zero_shares"] = dict(
        n_pairs=len(net),
        forecast_positive_realised_zero=round(np.mean([q["forecast"] > 0 and q["realised"] <= 0 for q in net]), 3),
        forecast_zero_realised_positive=round(np.mean([q["forecast"] <= 0 and q["realised"] > 0 for q in net]), 3))

    # ---- plan §4 sensitivity omitted from the draft: trim the largest 5% of absolute errors, and the
    # union-rule pairs (the result without any zero-forecast pair added by the union rule)
    def h_summary(sel):
        med, lo, hi = boot_median(sel)[:3]            # boot_median returns a tuple
        if med is None:
            return dict(n=0)
        return dict(median_pct=round(100 * (np.exp(med) - 1), 1), lo_pct=round(100 * (np.exp(lo) - 1), 1),
                    hi_pct=round(100 * (np.exp(hi) - 1), 1), n=len(sel))
    extra = {}
    for nm, keep_fn in (("trim_largest_5pct_abs_error", None),
                        ("without_union_rule_pairs", lambda q: not q.get("missing_from_profile") and not q.get("blank_cell"))):
        extra[nm] = {}
        for h in (1, 3):
            sel = [q for q in pairs if q["basis"] == "net" and q["h"] == h]
            if keep_fn is None:
                cut = np.percentile([abs(q["e"]) for q in sel], 95)
                sel = [q for q in sel if abs(q["e"]) <= cut]
            else:
                sel = [q for q in sel if keep_fn(q)]
            extra[nm][str(h)] = h_summary(sel)
    out["sensitivity_post_review"] = extra

    out["validation"] = val
    json.dump(out, open(T / "primary.json", "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("vintages", "realised_years", "H1", "H2", "H3", "national")},
                     indent=1, default=float)[:4000])


if __name__ == "__main__":
    main()
