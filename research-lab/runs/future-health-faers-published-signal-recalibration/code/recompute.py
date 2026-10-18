"""Recompute every eligible published signal and every negative-control pair under one protocol (plan sections 3-4).

Protocol: the paper's window; latest version per case (FAERS caseid by version, fda_dt; legacy CASE by ISR); the drug as
primary suspect (PS), matched on prod_ai or drugname against the RxNorm ingredient, its brand names and the paper's own
drug string; the event as an exact MedDRA PT. Report-level 2x2: a drug&event, b drug&other, c other&event, d rest.
Variants: all suspect roles (PS, SS); no deduplication; the full window (2004Q1 to the last quarter before publication).
Negative controls: the same protocol over 2004Q1-2025Q4.
Writes data/recomputed.csv and data/negative_controls_computed.csv."""
import json
import re
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rxnorm  # noqa: E402

RUN = Path(__file__).resolve().parents[1]


def qstr(y, q):
    return f"{y}Q{q}"


def terms_for(ingredient, drug_string):
    t = {ingredient} | set(rxnorm.brands(ingredient)) | {rxnorm.clean(drug_string).lower()}
    return sorted({x.upper() for x in t if x and len(x) >= 4})


def pattern(terms):
    return "(^|[^A-Z0-9])(" + "|".join(re.escape(t) for t in terms) + ")([^A-Z0-9]|$)"


class FAERS:
    def __init__(self):
        self.db = duckdb.connect(str(RUN / "data" / "faers.duckdb"), read_only=False)
        self.db.execute("SET threads TO 16")
        self.pts = {r[0] for r in self.db.execute("SELECT DISTINCT pt FROM reac").fetchall()}
        self.windows = {}

    def window(self, start, end, dedup=True):
        key = (start, end, dedup)
        if key not in self.windows:
            name = f"w{len(self.windows)}"
            if dedup:
                self.db.execute(f"""CREATE TEMP TABLE {name} AS SELECT rid FROM (SELECT rid, row_number() OVER (PARTITION BY caseid
                    ORDER BY version DESC NULLS LAST, fda_dt DESC NULLS LAST, rid DESC) AS rn FROM demo
                    WHERE quarter >= '{start}' AND quarter <= '{end}') WHERE rn = 1""")
            else:
                self.db.execute(f"CREATE TEMP TABLE {name} AS SELECT DISTINCT rid FROM demo WHERE quarter >= '{start}' AND quarter <= '{end}'")
            n = self.db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
            self.windows[key] = (name, n)
        return self.windows[key]

    def drug_table(self, key, terms):
        """Reports naming the drug, with their roles (computed once per drug)."""
        name = "d_" + re.sub(r"[^a-z0-9]", "_", key.lower())[:40]
        if not self.db.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{name}'").fetchone()[0]:
            p = pattern(terms).replace("'", "''")
            self.db.execute(f"""CREATE TEMP TABLE {name} AS SELECT DISTINCT rid, role FROM drug
                WHERE regexp_matches(coalesce(prod_ai, ''), '{p}') OR regexp_matches(coalesce(drugname, ''), '{p}')""")
        return name

    def event_table(self, pt):
        name = "e_" + re.sub(r"[^a-z0-9]", "_", pt.lower())[:40]
        if not self.db.execute(f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{name}'").fetchone()[0]:
            self.db.execute(f"CREATE TEMP TABLE {name} AS SELECT DISTINCT rid FROM reac WHERE pt = '{pt.replace(chr(39), chr(39) * 2)}'")
        return name

    def table2x2(self, dt, et, win, roles):
        w, n = win
        rl = ",".join(f"'{r}'" for r in roles)
        q = f"""WITH D AS (SELECT DISTINCT d.rid FROM {dt} d JOIN {w} USING (rid) WHERE d.role IN ({rl})),
                     E AS (SELECT DISTINCT e.rid FROM {et} e JOIN {w} USING (rid))
                SELECT (SELECT count(*) FROM D JOIN E USING (rid)), (SELECT count(*) FROM D), (SELECT count(*) FROM E)"""
        a, nd, ne = self.db.execute(q).fetchone()
        return a, nd - a, ne - a, n - nd - ne + a


def ror(a, b, c, d):
    if min(a, b, c, d) <= 0:
        return np.nan, np.nan, np.nan, np.nan
    l = np.log((a / b) / (c / d)); se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    return float(np.exp(l)), float(np.exp(l - 1.96 * se)), float(np.exp(l + 1.96 * se)), float(se)


def main(part="all"):
    """part: 'all', 'signals' or 'nc' (the negative controls do not depend on the extraction and can run first)."""
    F = FAERS()
    if part in ("all", "signals"):
        signals(F)
    if part in ("all", "nc"):
        controls(F)
    rxnorm.save()


def signals(F):
    sig = pd.read_csv(RUN / "data" / "signals_eligible.csv", dtype={"paper": str})
    pub = {}
    for l in open(RUN / "data" / "raw" / "epmc" / "records.jsonl"):
        r = json.loads(l); pub[str(r["id"])] = r.get("firstPublicationDate") or r.get("pubYear")
    rows = []
    # D3: rows already computed in the as-run pass are reused (the computation is deterministic); only new signals run
    cache = {}
    for prev in (RUN / "data" / "recomputed_asrun.csv", RUN / "data" / "recomputed.csv"):   # D4: the later file wins
        if prev.exists():
            for r in pd.read_csv(prev, dtype={"paper": str}).to_dict("records"):
                if r["status"] == "ok":
                    cache[(r["paper"], int(r["k"]), r["ingredient"], r["event_pt"], r["win"])] = r

    def faers_only(out, s, pt):
        """D4: the preregistered FAERS-only sensitivity (plan section 3): the window truncated to start at 2012Q4."""
        if isinstance(out.get("faersonly_status"), str):
            return out
        m = re.match(r"(\d{4})Q(\d)-(\d{4})Q(\d)", s.win)
        start, end = max(qstr(int(m[1]), int(m[2])), "2012Q4"), qstr(int(m[3]), int(m[4]))
        if end < "2012Q4":
            out["faersonly_status"] = "window ends before 2012Q4"; return out
        dt = F.drug_table(s.ingredient + "|" + rxnorm.clean(s.drug).lower(), terms_for(s.ingredient, s.drug))
        a, b, c, d = F.table2x2(dt, F.event_table(pt), F.window(start, end), ("PS",))
        r_, lo, hi, se = ror(a, b, c, d)
        out.update(faersonly_status="ok", faersonly_a=a, faersonly_b=b, faersonly_c=c, faersonly_d=d, faersonly_ror=r_,
                   faersonly_lo=lo, faersonly_hi=hi, faersonly_se=se)
        return out
    for s in sig.itertuples():
        pt = (s.event_uk or "").upper()
        base = dict(paper=s.paper, k=s.k, ingredient=s.ingredient, event_pt=pt, win=s.win)
        hit = cache.get((s.paper, int(s.k), s.ingredient, pt, s.win))
        if hit is not None:
            rows.append(faers_only(dict(hit), s, pt))
            if len(rows) % 25 == 0:
                print(len(rows), "signals", flush=True)
            continue
        if pt not in F.pts:
            rows.append({**base, "status": "event not a FAERS PT"}); continue
        m = re.match(r"(\d{4})Q(\d)-(\d{4})Q(\d)", s.win)
        start, end = qstr(int(m[1]), int(m[2])), qstr(int(m[3]), int(m[4]))
        dt = F.drug_table(s.ingredient + "|" + rxnorm.clean(s.drug).lower(), terms_for(s.ingredient, s.drug))
        et = F.event_table(pt)
        out = {**base, "status": "ok"}
        pdate = str(pub.get(s.paper) or "")
        py, pq = (int(pdate[:4]), (int(pdate[5:7]) - 1) // 3 + 1) if len(pdate) >= 7 else (int(pdate[:4] or 2025), 1)
        full_end = qstr(py, pq - 1) if pq > 1 else qstr(py - 1, 4)
        for vname, win, roles in [("primary", F.window(start, end), ("PS",)), ("allsuspect", F.window(start, end), ("PS", "SS")),
                                  ("nodedup", F.window(start, end, dedup=False), ("PS",)), ("fullwindow", F.window("2004Q1", full_end), ("PS",))]:
            a, b, c, d = F.table2x2(dt, et, win, roles)
            r_, lo, hi, se = ror(a, b, c, d)
            out.update({f"{vname}_a": a, f"{vname}_b": b, f"{vname}_c": c, f"{vname}_d": d, f"{vname}_ror": r_, f"{vname}_lo": lo,
                        f"{vname}_hi": hi, f"{vname}_se": se})
        rows.append(faers_only(out, s, pt))
        if len(rows) % 25 == 0:
            print(len(rows), "signals", flush=True)
    pd.DataFrame(rows).to_csv(RUN / "data" / "recomputed.csv", index=False)
    print(len(rows), "signals")


def controls(F):
    nc = pd.read_csv(RUN / "data" / "negative_controls.csv")
    win = F.window("2004Q1", "2025Q4")
    nrows = []
    for r in nc.itertuples():
        pt = r.pt.upper()
        if pt not in F.pts:
            nrows.append(dict(drug=r.drug, pt=pt, status="PT not in FAERS")); continue
        dt = F.drug_table("nc_" + r.drug, terms_for(r.drug, r.drug))
        a, b, c, d = F.table2x2(dt, F.event_table(pt), win, ("PS",))
        r_, lo, hi, se = ror(a, b, c, d)
        nrows.append(dict(drug=r.drug, pt=pt, status="ok", a=a, b=b, c=c, d=d, ror=r_, lo=lo, hi=hi, se=se))
    pd.DataFrame(nrows).to_csv(RUN / "data" / "negative_controls_computed.csv", index=False)
    print(len(nrows), "negative controls")


if __name__ == "__main__":
    main(*sys.argv[1:2])
