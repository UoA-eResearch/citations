"""Accessibility metrics for every fetched snapshot (axe_run.js, frozen rule subset, jsdom, no scripts), in parallel,
plus overlay-vendor detection in the raw HTML. Writes data/metrics.jsonl."""
import gzip
import json
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
NODE = "/mnt/research-lab-tools/node-v20.18.0-linux-x64/bin/node"
OVERLAY = re.compile(r"acsbapp|accessibe|userway|equalweb|audioeye|recite\.?me|reciteme|eye-able|eyeable|"
                     r"max-?access|allyable|enable\.co\.il|truabilities|userway\.org", re.I)


def run_axe(files, timeout):
    try:
        r = subprocess.run([NODE, str(RUN / "code" / "axe_run.js")], input="\n".join(files), capture_output=True, text=True,
                           timeout=timeout, cwd=RUN)
    except subprocess.TimeoutExpired:
        return None
    return {json.loads(l)["path"]: json.loads(l) for l in r.stdout.splitlines() if l.strip()}


def batch(paths):
    with tempfile.TemporaryDirectory() as td:
        files = []
        for p in paths:
            raw = gzip.decompress(Path(p).read_bytes()).decode("utf-8", "ignore")
            f = Path(td) / (Path(p).parent.name + "__" + Path(p).name.replace(".gz", ""))
            f.write_text(raw); files.append((p, f, bool(OVERLAY.search(raw))))
        res = run_axe([str(f) for _, f, _ in files], 900)
        if res is None:   # D7: the batch timed out; run its pages one at a time, a page still timing out is an axe error
            res = {}
            for _, f, _ in files:
                one = run_axe([str(f)], 120)
                res.update(one if one is not None else {str(f): dict(error="axe timeout")})
        out = []
        for p, f, ov in files:
            x = res.get(str(f), dict(error="no output"))
            d, t = Path(p).parent.name, Path(p).name.split(".")[0]
            out.append(dict(domain=d, target=t, overlay=ov, **{k: v for k, v in x.items() if k != "path"}))
        return out


def main():
    out = RUN / "data" / "metrics.jsonl"
    done = set()
    if out.exists():   # D7: resumable; snapshots already measured are kept
        for l in open(out):
            x = json.loads(l); done.add((x["domain"], x["target"]))
    paths = sorted(str(p) for p in (RUN / "data" / "html").glob("*/*.html.gz")
                   if (p.parent.name, p.name.split(".")[0]) not in done)
    chunks = [paths[i:i + 25] for i in range(0, len(paths), 25)]
    print(len(done), "already measured;", len(paths), "to go", flush=True)
    with open(out, "a") as fh, ProcessPoolExecutor(24) as ex:
        futs = [ex.submit(batch, c) for c in chunks]
        for k, f in enumerate(as_completed(futs)):
            for r in f.result():
                fh.write(json.dumps(r) + "\n")
            fh.flush()
            if k % 40 == 0:
                print("metrics", k * 25, "/", len(paths), flush=True)
    print("metrics done", len(paths))


if __name__ == "__main__":
    sys.exit(main())
