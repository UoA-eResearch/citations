"""Pull the raw text of specific opinion documents from the shards (cluster_id % 32) for reading."""
import gzip, json, re, html, sys
RUN = "/mnt/citations/research-lab/runs/legal-phantom-citations-judicial-opinions"
TAG = re.compile(r"<[^>]+>")
want = {}  # opinion_id -> cluster_id
for a in sys.argv[1:]:
    o, c = a.split(":"); want[int(o)] = int(c)
by_shard = {}
for o, c in want.items(): by_shard.setdefault(c % 32, set()).add(o)
out = {}
for sh, ids in by_shard.items():
    for line in gzip.open(f"{RUN}/data/opinions/shard_{sh:02d}.jsonl.gz", "rt", encoding="utf-8"):
        if not any(f'"opinion_id": {o},' in line for o in ids): continue
        rec = json.loads(line)
        if rec["opinion_id"] in ids:
            t = rec["raw"]
            if rec["field"] != "plain_text": t = html.unescape(TAG.sub(" ", t))
            out[rec["opinion_id"]] = {"cluster_id": rec["cluster_id"], "date": rec["date"], "type": rec["type"], "ocr": rec["ocr"], "field": rec["field"], "len": len(t), "text": " ".join(t.split())}
            ids.discard(rec["opinion_id"])
            if not ids: break
json.dump(out, open(f"{RUN}/review/reviewer_checks/pulled_docs.json", "w"), indent=1)
for o, d in out.items():
    print(f"=== opinion {o} cluster {d['cluster_id']} {d['date']} type={d['type']} ocr={d['ocr']} len={d['len']}")
    print("HEAD:", d["text"][:1200]); print("TAIL:", d["text"][-700:]); print()
