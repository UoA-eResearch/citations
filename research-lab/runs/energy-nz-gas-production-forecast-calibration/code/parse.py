"""Parse the recovered workbooks into tidy tables (plan sections 2 and 3). No forecast is paired with an outcome here.

From each reserves vintage:
  * the vintage year, read from the text inside the workbook ("as at 1 January YYYY"), never from the capture date;
  * the gas production profile by field and year (PJ), from the gas block of "Gas LPG Production Profile", which
    is followed in the same sheet by an LPG block that must not be read as gas;
  * ultimate recoverable and remaining reserves by field for 1P, 2P and 3P (PJ), from the "Gas"/"GAS" sheet.

From MBIE's gas data tables ("Annual_PJ"): gross and net production by field and calendar year (PJ).

Layouts drift across vintages (sheet case, a leading blank column, header wording), so every block is located by
searching for its header rather than by fixed cell references. FIELD_MAP below is written from the two name lists
alone, as plan section 3 requires, and maps the finer reserves names onto MBIE's coarser published fields.

Writes data/profiles.csv, data/reserves.csv, data/realised.csv and results/tables/vintages.csv.
"""
import csv
import json
import re
from pathlib import Path

import openpyxl

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"

# reserves-workbook field name (normalised) -> MBIE published field. Built from the name lists only.
FIELD_MAP = {
    "pohokura": "Pohokura", "mangahewa": "Mangahewa", "maui": "Maui", "kupe": "Kupe", "kapuni": "Kapuni",
    "turangi": "Turangi", "turangiohangaonearourenui": "Turangi", "maari": "Maari", "maarimanaia": "Maari",
    "kowhai": "Kowhai", "ngatoro": "Ngatoro", "ngatorokaimirowinsorgoldie": "Ngatoro", "mckee": "McKee",
    "tui": "Tui", "rimu": "Rimu", "rimukauri": "Rimu", "cheal": "Cheal", "chealeast": "Cheal", "cheale": "Cheal",
    "chealandcardiff": "Cheal", "chealcardiff": "Cheal", "waihapangaere": "Waihapa", "waihapa": "Waihapa",
    "sidewinder": "Sidewinder", "coppermoki": "Coppermoki", "surrey": "Surrey",
    "tariki": "TarikiAhuroa", "tarikiahuroa": "TarikiAhuroa",
    # named in the reserves workbooks but not published separately by MBIE
    "kauri": "Others", "kaurimanutahi": "Others", "radnor": "Others", "supplejack": "Others",
    "hanmersprings": "Others", "ngaere": "Others", "goldie": "Others", "kaimiro": "Others",
}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def num(v):
    if v is None or (isinstance(v, str) and v.strip() in ("", "-", "n/a", "na")):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def grid(ws):
    return [list(r) for r in ws.iter_rows(values_only=True)]


def find(rows, pred, start=0):
    for i in range(start, len(rows)):
        if pred(rows[i]):
            return i
    return None


def vintage_year(wb):
    for nm in wb.sheetnames:
        for row in wb[nm].iter_rows(values_only=True):
            for c in row:
                m = re.search(r"as at 1 January (\d{4})", str(c or ""), re.I)
                if m:
                    return int(m.group(1))
    return None


def parse_profile(rows):
    """The gas block of the production-profile sheet: (field_raw, year, pj)."""
    h = find(rows, lambda r: any(norm(c) == "field" for c in r) and sum(isinstance(c, int) and 1900 < c < 2100 for c in r) >= 3)
    if h is None:
        return []
    fc = next(i for i, c in enumerate(rows[h]) if norm(c) == "field")
    years = {i: c for i, c in enumerate(rows[h]) if isinstance(c, int) and 1900 < c < 2100}
    out = []
    for r in rows[h + 1:]:
        name = str(r[fc]).strip() if fc < len(r) and r[fc] is not None else ""
        if not name:
            continue
        if norm(name) == "total":
            break                                  # the LPG block follows; it must not be read as gas
        for i, y in years.items():
            v = num(r[i]) if i < len(r) else None
            if v is not None:
                out.append((name, y, v))
    return out


def parse_reserves(rows):
    """Ultimate recoverable and remaining reserves in PJ, by field, for 1P/2P/3P.

    Two layouts occur: the block labels and "Field" share one row, or the labels sit one row above the units row
    that carries "Field". The field column is therefore searched for in the label row and the one below it."""
    h = find(rows, lambda r: any("ultimaterecoverable" in norm(c) for c in r))
    if h is None:
        return []
    fc = None
    for r in (rows[h], rows[h + 1] if h + 1 < len(rows) else []):
        for i, c in enumerate(r):
            if norm(c) == "field":
                fc = i
                break
        if fc is not None:
            break
    if fc is None:
        return []
    blocks, cur = [], None
    for i, c in enumerate(rows[h]):
        n = norm(c)
        if "ultimaterecoverable" in n or "remainingreserve" in n:
            cur = ("ur" if "ultimate" in n else "rr") + re.search(r"([123])p", n).group(1)
            blocks.append((i, cur))
    units = rows[h + 1]
    cols = {}
    for k, (start, name) in enumerate(blocks):
        end = blocks[k + 1][0] if k + 1 < len(blocks) else len(units)
        for i in range(start, min(end, len(units))):
            if norm(units[i]) == "pj":
                cols[name] = i
                break
    out = []
    for r in rows[h + 2:]:
        name = str(r[fc]).strip() if fc < len(r) and r[fc] is not None else ""
        n = norm(name)
        if not name or n.startswith(("total", "arithmetictotal", "probabilistictotal", "allfields", "note")):
            continue
        rec = {k: num(r[i]) if i < len(r) else None for k, i in cols.items()}
        if any(v is not None for v in rec.values()):
            out.append((name, rec))
    return out


def parse_realised(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[[s for s in wb.sheetnames if norm(s) == "annualpj"][0]]
    rows = grid(ws)
    hy = find(rows, lambda r: norm(r[0]) == "calendaryear" and sum(isinstance(c, int) for c in r) > 10)
    years = {i: c for i, c in enumerate(rows[hy]) if isinstance(c, int) and 1900 < c < 2100}
    out = []
    for basis, key in (("gross", "grossproduction"), ("net", "netproduction")):
        s = find(rows, lambda r: norm(r[0]).startswith(key), hy)
        if s is None:
            continue
        for r in rows[s + 1:]:
            name = str(r[0]).strip() if r[0] is not None else ""
            if not name:
                continue
            n = norm(name)
            if n.startswith(("gasreinjected", "lpgextracted", "gasflared", "netproduction", "grossproduction",
                             "consumption", "supply", "stock")):
                break
            for i, y in years.items():
                v = num(r[i]) if i < len(r) else None
                if v is not None:
                    out.append((basis, name, y, v))
    wb.close()
    return out


def parse_national(path):
    """National gross gas production (PJ) from MBIE's energy overview: Indigenous Production -> Natural gas."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[[s for s in wb.sheetnames if norm(s) == "annualpj"][0]]
    rows = grid(ws)
    hy = find(rows, lambda r: norm(r[0]).startswith("calendaryear") and sum(isinstance(c, int) for c in r) > 10)
    years = {i: c for i, c in enumerate(rows[hy]) if isinstance(c, int) and 1900 < c < 2100}
    ip = find(rows, lambda r: norm(r[0]) == "indigenousproduction", hy)
    g = find(rows, lambda r: norm(r[0]) == "naturalgas", ip)
    out = [(years[i], num(rows[g][i])) for i in years if num(rows[g][i]) is not None]
    wb.close()
    return out


def parse_gic(path):
    """Gas Industry Co daily production (TJ/day) for the four published field groups -> annual PJ."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Prod_Cons"]
    rows = grid(ws)
    hdr = rows[0]
    cols = {i: str(c).strip() for i, c in enumerate(hdr)
            if c and str(c).strip() in ("Pohokura", "Maui", "McKee/Mangahewa", "Turangi and Kowhai")}
    agg, days = {}, {}
    for r in rows[1:]:
        d = r[0]
        if not hasattr(d, "year"):
            continue
        days[d.year] = days.get(d.year, 0) + 1
        for i, nm in cols.items():
            v = num(r[i]) if i < len(r) else None
            if v is not None:
                agg[(d.year, nm)] = agg.get((d.year, nm), 0.0) + v / 1000.0     # TJ -> PJ
    wb.close()
    return [(y, nm, v, days.get(y, 0)) for (y, nm), v in sorted(agg.items())]


def main():
    man = json.load(open(RAW / "MANIFEST.json"))
    vint, prof, res = [], [], []
    for ts, rec in sorted(man.get("reserves", {}).items()):
        if rec["duplicate_of_earlier"] or not rec.get("file"):
            continue
        f = RAW / rec["file"]
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        vy = vintage_year(wb)
        pn = [s for s in wb.sheetnames if "production profile" in s.lower() and "gas" in s.lower()]
        gn = [s for s in wb.sheetnames if norm(s) == "gas"]
        p = parse_profile(grid(wb[pn[0]])) if pn else []
        r = parse_reserves(grid(wb[gn[0]])) if gn else []
        vint.append(dict(capture=ts, vintage_year=vy, file=rec["file"], sha256=rec["sha256"][:16],
                         profile_rows=len(p), profile_fields=len({x[0] for x in p}),
                         profile_years=f"{min((x[1] for x in p), default='')}-{max((x[1] for x in p), default='')}",
                         reserve_fields=len(r)))
        for name, y, v in p:
            prof.append(dict(vintage_year=vy, capture=ts, field_raw=name, field=FIELD_MAP.get(norm(name), "UNMAPPED"),
                             year=y, pj=v))
        for name, rec2 in r:
            res.append(dict(vintage_year=vy, capture=ts, field_raw=name, field=FIELD_MAP.get(norm(name), "UNMAPPED"),
                            **{k: rec2.get(k) for k in ("ur1", "ur2", "ur3", "rr1", "rr2", "rr3")}))
        wb.close()
        print(f"{ts}: vintage {vy}, {len(p)} profile cells, {len(r)} reserve fields", flush=True)

    real = []
    gas = sorted((k for k, v in man.get("gas", {}).items() if not v["duplicate_of_earlier"] and v.get("file")))
    for ts in gas:
        try:
            rows = parse_realised(RAW / man["gas"][ts]["file"])
        except Exception as e:                                        # noqa: BLE001
            print(f"  gas {ts}: {type(e).__name__}"); continue
        for basis, name, y, v in rows:
            real.append(dict(capture=ts, basis=basis, field_raw=name,
                             field=FIELD_MAP.get(norm(name), name.strip()), year=y, pj=v))
        print(f"  gas {ts}: {len(rows)} cells", flush=True)

    def write(path, rows, cols):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader(); w.writerows(rows)
    write(RUN / "data" / "profiles.csv", prof, ["vintage_year", "capture", "field_raw", "field", "year", "pj"])
    write(RUN / "data" / "reserves.csv", res, ["vintage_year", "capture", "field_raw", "field",
                                               "ur1", "ur2", "ur3", "rr1", "rr2", "rr3"])
    write(RUN / "data" / "realised.csv", real, ["capture", "basis", "field_raw", "field", "year", "pj"])
    nat = []
    for f in sorted((RAW / "mbie_other").glob("energy-overview_*.xlsx")):
        for y, v in parse_national(f):
            nat.append(dict(capture=f.stem.split("_")[-1], year=y, gross_pj=v))
        print(f"  national {f.name}: {len(nat)} years", flush=True)
    write(RUN / "data" / "national.csv", nat, ["capture", "year", "gross_pj"])
    gic = []
    gp = RAW / "gic" / "ProductionConsumption.xlsx"
    if gp.exists():
        for y, nm, v, nd in parse_gic(gp):
            gic.append(dict(year=y, field_group=nm, pj=round(v, 4), days=nd))
        print(f"  gic: {len(gic)} field-years", flush=True)
    write(RUN / "data" / "gic_annual.csv", gic, ["year", "field_group", "pj", "days"])
    write(RUN / "results" / "tables" / "vintages.csv", vint, list(vint[0]) if vint else ["capture"])
    un = sorted({r["field_raw"] for r in prof + res if r["field"] == "UNMAPPED"})
    print(f"\n{len(vint)} vintages, {len(prof)} profile cells, {len(res)} reserve rows, {len(real)} realised cells")
    print("UNMAPPED reserves-side names:", un if un else "none")


if __name__ == "__main__":
    main()
