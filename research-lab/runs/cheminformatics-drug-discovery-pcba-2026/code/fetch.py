"""Data acquisition (plan sections 1 and 3). PubChem E-utilities and PUG REST (rate-limited to < 5 requests/s);
LIT-PCBA archive.

  fetch.py assays    -> data/raw/assays.json (qualifying AIDs, metadata, gene targets), data/raw/chosen.json
  fetch.py outcomes  -> data/raw/cids/<aid>_{active,inactive,all}.json
  fetch.py smiles    -> data/raw/cid_smiles.csv (CID, SMILES, InChIKey)
  fetch.py lit       -> data/raw/LIT-PCBA/full_data.tgz
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/"
TERM = "2021/01/01:2026/12/31[DDAT] AND confirmatory[ACMD] AND 50:100000000[AC] AND 5050:1000000000[TSC] AND 1[TCNT]"


def get(url, data=None, tries=6, as_json=True):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data)
            r = urllib.request.urlopen(req, timeout=300).read()
            time.sleep(0.25)
            return json.loads(r) if as_json else r.decode()
        except Exception as e:  # rate limits and timeouts are retried
            err = e
            time.sleep(2 + 4 * i)
    raise RuntimeError(f"{url[:120]}: {err}")


def assays():
    RAW.mkdir(parents=True, exist_ok=True)
    ids = get(EU + "esearch.fcgi?" + urllib.parse.urlencode({"db": "pcassay", "retmode": "json", "retmax": 500, "term": TERM}))["esearchresult"]["idlist"]
    summ = get(EU + "esummary.fcgi?" + urllib.parse.urlencode({"db": "pcassay", "retmode": "json", "id": ",".join(ids)}))["result"]
    tg = get(PUG + f"assay/aid/{','.join(ids)}/targets/GeneSymbol/JSON")
    genes = {str(x["AID"]): x.get("GeneSymbol", []) for x in tg.get("InformationList", {}).get("Information", [])}
    rows = []
    for a in ids:
        s = summ[a]
        rows.append({"aid": int(a), "name": s.get("name", ""), "source": (s.get("sourcenamelist") or [""])[0] if isinstance(s.get("sourcenamelist"), list) else s.get("sourcename", ""),
                     "deposit_date": s.get("depositdate", ""), "active_sids": int(s.get("activesidcount") or 0),
                     "total_sids": int(s.get("sidcount") or s.get("totalsidcount") or 0), "genes": genes.get(a, [])})
    (RAW / "assays.json").write_text(json.dumps(rows, indent=1))
    by_gene = {}
    for r in rows:
        if len(r["genes"]) != 1:
            continue                                   # no or several gene symbols: not a single protein target
        g = r["genes"][0]
        best = by_gene.get(g)
        key = (r["active_sids"], r["total_sids"], -r["aid"])
        if best is None or key > (best["active_sids"], best["total_sids"], -best["aid"]):
            by_gene[g] = r
    chosen = sorted(by_gene.values(), key=lambda r: r["aid"])
    (RAW / "chosen.json").write_text(json.dumps(chosen, indent=1))
    print(len(rows), "qualifying assays;", sum(len(r["genes"]) != 1 for r in rows), "without exactly one gene symbol;",
          len(chosen), "targets chosen")


def outcomes():
    chosen = json.loads((RAW / "chosen.json").read_text())
    d = RAW / "cids"
    d.mkdir(exist_ok=True)
    for r in chosen:
        for kind in ("active", "inactive", "all"):   # "inconclusive" is not a valid cids_type; derived as all - active - inactive
            f = d / f"{r['aid']}_{kind}.json"
            if f.exists():
                continue
            try:
                j = get(PUG + f"assay/aid/{r['aid']}/cids/JSON?cids_type={kind}")
                cids = j.get("InformationList", {}).get("Information", [{}])[0].get("CID", [])
            except RuntimeError as e:
                if "404" in str(e):
                    cids = []
                else:
                    raise
            f.write_text(json.dumps(cids))
        print(r["aid"], r["genes"], flush=True)


def smiles():
    cids = set()
    for f in (RAW / "cids").glob("*.json"):
        cids |= set(json.loads(f.read_text()))
    out = RAW / "cid_smiles.csv"
    have = set()
    if out.exists():
        have = {int(r["CID"]) for r in csv.DictReader(open(out))}
    todo = sorted(cids - have)
    print(len(cids), "CIDs;", len(todo), "to fetch", flush=True)
    w = open(out, "a", newline="")
    wr = csv.writer(w)
    if not have:
        wr.writerow(["CID", "SMILES", "InChIKey"])
    for i in range(0, len(todo), 500):
        batch = todo[i:i + 500]
        txt = get(PUG + "compound/cid/property/SMILES,InChIKey/CSV", data=urllib.parse.urlencode({"cid": ",".join(map(str, batch))}).encode(),
                  as_json=False)
        rows = list(csv.DictReader(txt.splitlines()))
        for r in rows:
            wr.writerow([r["CID"], r.get("SMILES", ""), r.get("InChIKey", "")])
        w.flush()
        if (i // 500) % 50 == 0:
            print(i + len(batch), "/", len(todo), flush=True)
    w.close()


def lit():
    d = RAW / "LIT-PCBA"
    d.mkdir(parents=True, exist_ok=True)
    f = d / "full_data.tgz"
    if not f.exists():
        import subprocess
        subprocess.run(["curl", "-fsSL", "-m", "1800", "-o", str(f), "https://drugdesign.unistra.fr/LIT-PCBA/Files/full_data.tgz"], check=True)
    print(f, f.stat().st_size)


if __name__ == "__main__":
    {"assays": assays, "outcomes": outcomes, "smiles": smiles, "lit": lit}[sys.argv[1]]()
