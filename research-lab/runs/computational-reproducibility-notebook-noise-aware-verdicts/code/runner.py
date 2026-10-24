"""Environment builds and executions inside Docker (plan section 2).

  runner.py runners          one nbclient runner environment per Python version (host dir, mounted read-only)
  runner.py run [N]          build AS-OF and LATEST environments and execute every sampled notebook
                             (3 AS-OF runs + 1 LATEST run) -> data/runs/<nbid>/...
Third-party code never runs on the host: builds run in containers with network but without host credentials or home;
executions run with --network none.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
D = RUN / "data"
UV = D / "bin" / "uv-x86_64-unknown-linux-musl"
RUNNERS, ENVS, OUT, CACHE = D / "runners", D / "envs", D / "runs", D / "uvcache"
VERSIONS = ["3.8", "3.9", "3.10", "3.11", "3.12"]
FLAVOR = os.environ.get("NB_IMAGE_FLAVOR", "-slim")     # D2: "" = full image with build tools, for failed slim builds
EXEC = '''
import sys, json, nbformat, os
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
nb = nbformat.read(sys.argv[1], as_version=4)
c = NotebookClient(nb, timeout=1200, kernel_name="nbenv", allow_errors=False, resources={"metadata": {"path": sys.argv[3]}})
st, err = "ok", ""
try:
    c.execute()
except CellExecutionError as e:
    st, err = "cell_error", str(e)[-600:]
except Exception as e:
    st, err = "error", (type(e).__name__ + ": " + str(e))[:400]
nbformat.write(nb, sys.argv[2])
json.dump({"status": st, "err": err}, open(sys.argv[2] + ".json", "w"))
'''
KERNEL = {"argv": ["/env/bin/python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
          "display_name": "nbenv", "language": "python"}


def docker(args, timeout):
    try:
        r = subprocess.run(["docker", "run", "--rm"] + args, capture_output=True, timeout=timeout)
        return r.returncode, r.stdout.decode("utf-8", "replace")[-3000:], r.stderr.decode("utf-8", "replace")[-3000:]
    except subprocess.TimeoutExpired:
        return -9, "", "timeout"


def runners():
    for v in VERSIONS:
        dst = RUNNERS / v
        if (dst / "bin" / "python").exists():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        code, o, e = docker(["--user", f"{os.getuid()}:{os.getgid()}", "-e", "UV_CACHE_DIR=/cache", "-v", f"{CACHE}:/cache",
                             "-v", f"{UV}:/opt/uv:ro", "-v", f"{dst}:/runner", f"python:{v}-slim", "sh", "-c",
                             "/opt/uv/uv venv /runner --python /usr/local/bin/python -q --allow-existing && "
                             "/opt/uv/uv pip install --python /runner/bin/python -q nbclient nbformat jupyter_client"], 1800)
        ks = dst / "share" / "jupyter" / "kernels" / "nbenv"
        ks.mkdir(parents=True, exist_ok=True)
        (ks / "kernel.json").write_text(json.dumps(KERNEL))
        print(v, code, e[-300:], flush=True)


def build(nb, arm):
    env = ENVS / f"{nb.nbid}_{arm}"
    log = OUT / nb.nbid / f"build_{arm}.json"
    image = f"python:{nb.pyver}{FLAVOR if arm == 'asof' else '-slim'}"
    if log.exists():
        return json.loads(log.read_text())
    env.mkdir(parents=True, exist_ok=True)
    excl = f"--exclude-newer {nb.asof_date}T00:00:00Z" if arm == "asof" else ""
    req = nb.req_path if isinstance(nb.req_path, str) and nb.req_path else ""
    pkgs = nb.pkgs if isinstance(nb.pkgs, str) else ""
    inst = f"/opt/uv/uv pip install --python /env/bin/python {excl} -r /repo/{req}" if req else \
           (f"/opt/uv/uv pip install --python /env/bin/python {excl} {pkgs}" if pkgs else "true")
    cmd = (f"/opt/uv/uv venv /env --python /usr/local/bin/python -q --allow-existing && {inst} && "
           f"/opt/uv/uv pip install --python /env/bin/python {excl} ipykernel")
    t0 = time.time()
    code, o, e = docker(["--user", f"{os.getuid()}:{os.getgid()}", "-e", "UV_CACHE_DIR=/cache", "-e", "HOME=/tmp",
                         "-v", f"{CACHE}:/cache", "-v", f"{UV}:/opt/uv:ro", "-v", f"{env}:/env",
                         "-v", f"{D / 'repos' / nb.repo_id}:/repo:ro", "--cpus", "2", "--memory", "6g",
                         image, "sh", "-c", cmd], 1800)
    res = {"code": code, "secs": round(time.time() - t0, 1), "err": e[-1200:] if code else "", "image": image}
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps(res))
    return res


def execute(nb, arm, rep):
    out = OUT / nb.nbid / f"{arm}_{rep}.ipynb"
    if (out.parent / (out.name + ".json")).exists():
        return json.loads((out.parent / (out.name + ".json")).read_text())
    work = OUT / nb.nbid / f"work_{arm}_{rep}"
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(D / "repos" / nb.repo_id, work, symlinks=True, ignore=shutil.ignore_patterns(".git"))
    nbdir = str(Path("/work") / Path(nb.nb_path).parent)
    (OUT / nb.nbid / "exec.py").write_text(EXEC)
    t0 = time.time()
    bj = json.loads((OUT / nb.nbid / f"build_{arm}.json").read_text())
    image = bj.get("image", f"python:{nb.pyver}-slim")
    code, o, e = docker(["--network", "none", "--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp",
                         "-e", "JUPYTER_PATH=/runner/share/jupyter",
                         "-v", f"{ENVS / (nb.nbid + '_' + arm)}:/env:ro", "-v", f"{RUNNERS / nb.pyver}:/runner:ro",
                         "-v", f"{work}:/work", "-v", f"{OUT / nb.nbid}:/out", "--cpus", "2", "--memory", "6g",
                         "-w", nbdir, image, "/runner/bin/python", "/out/exec.py",
                         f"/work/{nb.nb_path}", f"/out/{arm}_{rep}.ipynb", nbdir], 1500)
    shutil.rmtree(work, ignore_errors=True)
    j = out.parent / (out.name + ".json")
    res = json.loads(j.read_text()) if j.exists() else {"status": "container_failed", "err": (e or o)[-600:]}
    res["secs"] = round(time.time() - t0, 1)
    j.write_text(json.dumps(res))
    return res


def one(nb):
    rec = {"nbid": nb.nbid}
    for arm in ("asof", "latest"):
        b = build(nb, arm)
        rec[f"build_{arm}"] = b["code"]
    if rec["build_asof"] == 0:
        r1 = execute(nb, "asof", 1)
        rec["asof_1"] = r1["status"]
        if r1["status"] == "ok":
            for rep in (2, 3):
                rec[f"asof_{rep}"] = execute(nb, "asof", rep)["status"]
    if rec["build_latest"] == 0 and rec.get("asof_1") == "ok":
        rec["latest_1"] = execute(nb, "latest", 1)["status"]
    for arm in ("asof", "latest"):          # environments are large; executions are kept
        shutil.rmtree(ENVS / f"{nb.nbid}_{arm}", ignore_errors=True)
    return rec


def run(n=None):
    S = pd.read_csv(D / "interim" / os.environ.get("SAMPLE", "sample_ready.csv"), dtype=str)
    if n:
        S = S.head(int(n))
    rows = []
    with ThreadPoolExecutor(int(os.environ.get("WORKERS", "6"))) as ex:
        for k, r in enumerate(ex.map(one, S.itertuples()), 1):
            rows.append(r)
            if k % 10 == 0:
                print(k, "of", len(S), flush=True)
                pd.DataFrame(rows).to_csv(D / "interim" / "run_status.csv", index=False)
    pd.DataFrame(rows).to_csv(D / "interim" / os.environ.get("STATUS", "run_status.csv"), index=False)
    print(pd.DataFrame(rows).drop(columns="nbid").apply(lambda c: c.value_counts(dropna=False).to_dict()).to_string())


if __name__ == "__main__":
    {"runners": runners, "run": lambda: run(sys.argv[2] if len(sys.argv) > 2 else None)}[sys.argv[1]]()
