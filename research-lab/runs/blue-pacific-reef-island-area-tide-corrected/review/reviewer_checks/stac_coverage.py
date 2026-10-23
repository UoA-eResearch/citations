"""Reviewer check 6: is the late start of Sentinel-2 at Kanton, Kapingamarangi, Funafuti and Tarawa a property of the
archive or of scenes.py's search? Counts items per year, 2015-2022, in three Earth Search collections for each bbox."""
import json, sys, urllib.request
ES = "https://earth-search.aws.element84.com/v1/search"
BB = {"kanton": (-2.88, -171.76, -2.75, -171.62), "kapingamarangi": (0.95, 154.70, 1.15, 154.86),
      "funafuti": (-8.72, 179.03, -8.43, 179.27), "tarawa": (1.30, 172.85, 1.75, 173.25), "majuro": (7.02, 171.00, 7.25, 171.42)}
def count(coll, bbox, y):
    body = {"collections": [coll], "bbox": bbox, "limit": 1, "datetime": f"{y}-01-01T00:00:00Z/{y}-12-31T23:59:59Z"}
    req = urllib.request.Request(ES, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": "research-lab-review"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    return d.get("numberMatched", d.get("context", {}).get("matched"))
for name, (s, w, n, e) in BB.items():
    for coll in ("sentinel-2-l2a", "sentinel-2-c1-l2a", "sentinel-2-l1c"):
        try:
            print(name, coll, {y: count(coll, [w, s, e, n], y) for y in range(2015, 2023)}, flush=True)
        except Exception as ex:
            print(name, coll, "ERR", repr(ex)[:80], flush=True)
