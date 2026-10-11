"""Reference (analyst-reviewed) picks from SCEDC per-event phase files and NCEDC Hypoinverse Y2000 archive files
(plan section 3), plus the NCEDC catalogue's event type and review status. Writes data/reference_picks.parquet.

Filters (plan section 3; D1 adds the NCEDC review status): CI picks from SCEDC; NC and BK picks from NCEDC; event type
`eq`; magnitude >= 1.5; NCEDC status F (final, analyst-reviewed); epicentral distance <= 100 km; weight > 0. One pick per
(event, network, station, phase): highest weight, then earliest time."""
import gzip
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
Y2K_WEIGHT = {0: 1.0, 1: 0.75, 2: 0.5, 3: 0.25}


def scedc_file(path):
    rows = []
    lines = Path(path).read_text(errors="replace").splitlines()
    if not lines:
        return rows
    h = lines[0].split()
    evid, etype = h[0], h[1]
    ot = pd.Timestamp(h[3].replace("/", "-").replace(",", " "))
    mag = float(h[7])
    for l in lines[1:]:
        f = l.split()
        if len(f) < 12:
            continue
        net, sta, cha, loc = f[0], f[1], f[2], f[3]
        phase, onset = f[7], f[9]
        weight, dist, tt = float(f[10]), float(f[11]), float(f[12])
        rows.append(dict(source="scedc", evid=evid, etype=etype, mag=mag, origin=ot, net=net, sta=sta, cha=cha,
                         loc="" if loc == "--" else loc, phase=phase, onset=onset, weight=weight, dist_km=dist,
                         t_ref=ot + pd.Timedelta(seconds=tt)))
    return rows


def _num(s, scale):
    s = s.strip()
    return float(s) / scale if s and s.lstrip("-").isdigit() else np.nan


def ncedc_file(path):
    """Hypoinverse Y2000 archive: header line, phase lines, terminator line (event id)."""
    raw = subprocess.run(["uncompress", "-c", str(path)], capture_output=True).stdout
    lines = raw.decode("latin-1").splitlines()
    rows, cur = [], None
    for l in lines:
        if not l.strip():
            continue
        if l[:4].isdigit() and len(l) > 140:  # event header
            cur = dict(evid=l[136:146].strip(), mag=_num(l[147:150], 100), origin=pd.Timestamp(
                f"{l[0:4]}-{l[4:6]}-{l[6:8]} {l[8:10]}:{l[10:12]}") + pd.Timedelta(seconds=_num(l[12:16], 100)), picks=[])
            continue
        if l[:5].strip() == "":  # terminator
            if cur:
                rows += cur["picks"]
            cur = None
            continue
        if cur is None:
            continue
        sta, net, cha, loc = l[0:5].strip(), l[5:7].strip(), l[9:12].strip(), l[111:113].strip() if len(l) >= 113 else ""
        minute = pd.Timestamp(f"{l[17:21]}-{l[21:23]}-{l[23:25]} {l[25:27]}:{l[27:29]}")
        dist = _num(l[74:78], 10)
        for phase, rem, wcode, sec in (("P", l[13:15], l[16:17], l[29:34]), ("S", l[46:48], l[49:50], l[41:46])):
            if rem.strip()[-1:] != phase or not sec.strip():
                continue
            w = Y2K_WEIGHT.get(int(wcode) if wcode.strip().isdigit() else 0 if not wcode.strip() else 9, 0.0)
            cur["picks"].append(dict(source="ncedc", evid=cur["evid"], mag=cur["mag"], origin=cur["origin"], net=net, sta=sta,
                                     cha=cha, loc="" if loc == "--" else loc, phase=phase, onset=rem.strip()[:-1].lower(),
                                     weight=w, dist_km=dist, t_ref=minute + pd.Timedelta(seconds=_num(sec, 100))))
    return rows


def ncedc_catalogue(years):
    out = []
    for y in years:
        f = RAW / "catalogues" / f"ncedc_{y}.ehpcsv"
        c = pd.read_csv(f, dtype={"id": str})
        out.append(c[["id", "type", "status", "mag", "magType"]])
    return pd.concat(out).drop_duplicates("id").set_index("id")


def main():
    ms = json.load(open(RUN / "data" / "months.json"))
    rows = []
    for y, m in ms:
        for p in sorted((RAW / "phases" / "scedc" / f"{y}_{m:02d}").glob("*.phase")):
            rows += scedc_file(p)
        f = RAW / "phases" / "ncedc" / f"{y}.{m:02d}.phase.Z"
        if f.exists():
            rows += ncedc_file(f)
    d = pd.DataFrame(rows)
    cat = ncedc_catalogue(sorted({y for y, _ in ms}))
    nc = d.source == "ncedc"
    d.loc[nc, "etype"] = d.loc[nc, "evid"].map(cat["type"])
    d["status"] = np.where(nc, d.evid.map(cat["status"]), "scedc")
    n0 = len(d)
    keep = (((d.source == "scedc") & (d.net == "CI")) | (nc & d.net.isin(["NC", "BK"]))) & (d.etype == "eq") & \
        (d.mag >= 1.5) & ((d.source == "scedc") | (d.status == "F")) & (d.dist_km <= 100) & (d.weight > 0)
    d = d[keep].sort_values(["evid", "net", "sta", "phase", "weight", "t_ref"], ascending=[True, True, True, True, False, True])
    d = d.drop_duplicates(["source", "evid", "net", "sta", "phase"])
    d.to_parquet(RUN / "data" / "reference_picks.parquet", index=False)
    print(f"{n0} picks parsed; {len(d)} reference picks kept;", d.groupby(["source", "phase"]).size().to_dict())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "probe":
        a = pd.DataFrame(scedc_file(sys.argv[2]))
        b = pd.DataFrame(ncedc_file(sys.argv[3]))
        for x in (a, b):
            print(len(x), x.phase.value_counts().to_dict(), x.dist_km.describe().round(1).to_dict(), x.weight.value_counts().to_dict())
            print(x.head(3).T)
    else:
        main()
