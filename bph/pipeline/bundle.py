"""Step 8: merge landscape, SciVal placement, probes and world context into data/bph.json for the page."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("BPH_WORK", "/mnt/data/ubuntu/bph-work"))


def main():
    d = json.loads((ROOT / "data" / "landscape.json").read_text())
    live = json.loads((ROOT / "data" / "scival_live.json").read_text())
    pr = json.loads((ROOT / "data" / "probes.json").read_text())
    wo = json.loads((ROOT / "data" / "world.json").read_text())
    meta = json.loads((WORK / "els_meta.json").read_text())
    sra = json.loads((ROOT / "data" / "scival_sra3.json").read_text())
    assert len(live["works"]) == len(d["works"]), "SciVal placement is stale: rerun scival_topics.py"
    for w, s in zip(d["works"], live["works"]):
        w["sv"] = s    # [Scopus ID, SciVal Topic index, status c/s/n/x, SciVal FWCI, top-10% flag, match doi/title]
    d["scival"] = [dict(kind=r["kind"], name=r["name"], rs=r["rs"], sme=r["sme"], final=r["final"]) for r in sra]
    d["svlive"] = {k: v for k, v in live.items() if k != "works"}
    src = meta.get("source") or {}
    # Dates the Elsevier data was retrieved (for the attribution Elsevier asks for): the span of the
    # response cache's file dates, since every response is cached when first fetched.
    import datetime
    cache = Path(os.environ.get("BPH_CACHE", "/mnt/data/ubuntu/bph-cache")) / "els"
    days = sorted({datetime.date.fromtimestamp(f.stat().st_mtime).isoformat() for f in cache.rglob("*.json")})
    d["svmeta"] = dict(release=src.get("lastUpdated"), start=src.get("metricStartYear"), end=src.get("metricEndYear"),
                       retrieved=[days[0], days[-1]] if days else None)
    d["probes"] = pr
    d["world"] = wo
    # Engagement data (internal; git-ignored): people engaged in developing the SRA, and the Workshop 2 maps.
    eng_f = ROOT / "data" / "engaged.json"
    d["engaged"] = json.loads(eng_f.read_text()) if eng_f.exists() else []
    for k, e in enumerate(d["engaged"]):
        for i in e["atlas"]:
            d["authors"][i]["eng"] = k
    # Links to the shared pages (internal; the public code never names them): <WORK>/links.json {"page", "va"}
    links_f = WORK / "links.json"
    d["links"] = json.loads(links_f.read_text()) if links_f.exists() else {}
    ws_f = WORK / "engagement" / "workshop2_maps.json"
    d["workshop"] = json.loads(ws_f.read_text()) if ws_f.exists() else None
    if d["workshop"]:
        import shutil
        (ROOT / "data" / "ws").mkdir(exist_ok=True)
        for m in d["workshop"]["maps"]:
            src = WORK / "engagement" / "photos" / (m["photo"] + ".jpg")
            if src.exists():
                shutil.copy(src, ROOT / "data" / "ws" / src.name)
    out = ROOT / "data" / "bph.json"
    out.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
