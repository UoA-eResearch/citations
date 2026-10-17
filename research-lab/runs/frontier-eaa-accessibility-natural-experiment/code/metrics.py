"""Accessibility metrics for every fetched snapshot (axe_run.js, frozen rule subset, jsdom, no scripts), in parallel,
plus overlay-vendor detection in the raw HTML. Writes data/metrics.jsonl."""
import gzip
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
NODE = "/mnt/research-lab-tools/node-v20.18.0-linux-x64/bin/node"
OVERLAY = re.compile(r"acsbapp|accessibe|userway|equalweb|audioeye|recite\.?me|reciteme|eye-able|eyeable|"
                     r"max-?access|allyable|enable\.co\.il|truabilities|userway\.org", re.I)


def batch(paths):
    with tempfile.TemporaryDirectory() as td:
        files = []
        for p in paths:
            raw = gzip.decompress(Path(p).read_bytes()).decode("utf-8", "ignore")
            f = Path(td) / (Path(p).parent.name + "__" + Path(p).name.replace(".gz", ""))
            f.write_text(raw); files.append((p, f, bool(OVERLAY.search(raw))))
        r = subprocess.run([NODE, str(RUN / "code" / "axe_run.js")], input="\n".join(str(f) for _, f, _ in files),
                           capture_output=True, text=True, timeout=1800, cwd=RUN)
        res = {json.loads(l)["path"]: json.loads(l) for l in r.stdout.splitlines() if l.strip()}
        out = []
        for p, f, ov in files:
            x = res.get(str(f), dict(error="no output"))
            d, t = Path(p).parent.name, Path(p).name.split(".")[0]
            out.append(dict(domain=d, target=t, overlay=ov, **{k: v for k, v in x.items() if k != "path"}))
        return out


def main():
    paths = sorted(str(p) for p in (RUN / "data" / "html").glob("*/*.html.gz"))
    chunks = [paths[i:i + 25] for i in range(0, len(paths), 25)]
    with open(RUN / "data" / "metrics.jsonl", "w") as fh, ProcessPoolExecutor(24) as ex:
        for k, rows in enumerate(ex.map(batch, chunks)):
            for r in rows:
                fh.write(json.dumps(r) + "\n")
            if k % 40 == 0:
                print("metrics", k * 25, "/", len(paths), flush=True)
    print("metrics done", len(paths))


if __name__ == "__main__":
    sys.exit(main())
