"""Stream one subject's files for one task into a local BIDS mirror (plan section 5; D1).

  /mnt/data/omv/<ds>/raw/                 dataset_description.json, sub-*/func/*_events.tsv, *_bold.json,
                                          *_bold.nii.gz (a symlink to the derivative BOLD: pybids needs only its
                                          length and TR)
  /mnt/data/omv/<ds>/deriv/fmriprep/      sub-*/func/*space-MNI152NLin2009cAsym_res-2_desc-{preproc_bold,brain_mask}
                                          and *desc-confounds_timeseries.tsv/.json

Raw events and sidecars come from s3://openneuro.org/<ds>/ (top-level task-<task>_events.tsv / _bold.json are
inherited if per-run files are missing); derivatives from s3://openneuro-derivatives/fmriprep/<ds>-fmriprep/.
`drop_subject` deletes the subject's images after processing.
"""
import json
import re
import shutil
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path("/mnt/data/omv")
UA = {"User-Agent": "research-lab openneuro-multiverse study (open-data research; github.com/UoA-eResearch/citations)"}
DERIV, RAW = "https://openneuro-derivatives.s3.amazonaws.com", "https://s3.amazonaws.com/openneuro.org"
SPACE = "space-MNI152NLin2009cAsym_res-2"


CHUNK, CONN = 8 << 20, 32          # the VM's link to AWS is limited to ~85 KB/s per connection, so files are fetched
                                    # as parallel byte ranges (32 connections ~2.7 MB/s per file)


def get(url, dest=None, tries=5):
    """Small objects (or dest=None): one request. Large files: parallel ranges into a preallocated file."""
    if dest is not None:
        size = head_size(url)
        if size and size > 2 * CHUNK:
            return get_ranges(url, dest, size)
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=600) as r:
                if dest is None:
                    return r.read()
                tmp = Path(str(dest) + ".part")
                with open(tmp, "wb") as f:
                    shutil.copyfileobj(r, f, 1 << 22)
                tmp.rename(dest)
                return dest
        except Exception:
            time.sleep(10 * (k + 1))
    return None


def head_size(url):
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=120) as r:
            return int(r.headers.get("Content-Length") or 0)
    except Exception:
        return 0


def get_ranges(url, dest, size, tries=6):
    import os
    from concurrent.futures import ThreadPoolExecutor
    tmp = Path(str(dest) + ".part")
    fd = os.open(tmp, os.O_RDWR | os.O_CREAT, 0o644)
    os.ftruncate(fd, size)

    def chunk(start):
        end = min(start + CHUNK, size) - 1
        for k in range(tries):
            try:
                req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={start}-{end}"})
                with urllib.request.urlopen(req, timeout=300) as r:
                    data = r.read()
                if len(data) == end - start + 1:
                    os.pwrite(fd, data, start)
                    return True
            except Exception:
                pass
            time.sleep(5 * (k + 1))
        return False
    try:
        with ThreadPoolExecutor(CONN) as ex:
            ok = all(ex.map(chunk, range(0, size, CHUNK)))
    finally:
        os.close(fd)
    if not ok:
        tmp.unlink(missing_ok=True)
        return None
    tmp.rename(dest)
    return dest


def keys(base, prefix):
    out, token = [], None
    while True:
        q = {"list-type": "2", "prefix": prefix, "max-keys": "1000"}
        if token:
            q["continuation-token"] = token
        t = (get(f"{base}/?{urllib.parse.urlencode(q)}") or b"").decode()
        out += re.findall(r"<Key>([^<]+)</Key>", t)
        m = re.search(r"<NextContinuationToken>([^<]+)</NextContinuationToken>", t)
        if not m:
            return out
        token = m.group(1)


def ents(name):
    """Entities of a BIDS file name, with run as an integer (raw files say run-01, fMRIPrep says run-1)."""
    e = dict(re.findall(r"(sub|ses|task|acq|ce|dir|rec|run|echo)-([A-Za-z0-9]+)", name.split("/")[-1]))
    if "run" in e:
        e["run"] = str(int(e["run"]))
    return tuple(sorted((k, v) for k, v in e.items() if k in ("sub", "ses", "task", "acq", "run", "echo")))


def ensure_dataset(ds):
    raw, der = ROOT / ds / "raw", ROOT / ds / "deriv" / "fmriprep"
    raw.mkdir(parents=True, exist_ok=True)
    der.mkdir(parents=True, exist_ok=True)
    if not (raw / "dataset_description.json").exists():
        b = get(f"{RAW}/{ds}/dataset_description.json") or json.dumps({"Name": ds, "BIDSVersion": "1.8.0"}).encode()
        (raw / "dataset_description.json").write_bytes(b)
    if not (der / "dataset_description.json").exists():
        (der / "dataset_description.json").write_text(json.dumps(
            {"Name": f"{ds} fMRIPrep (openneuro-derivatives)", "BIDSVersion": "1.8.0", "DatasetType": "derivative",
             "GeneratedBy": [{"Name": "fMRIPrep"}]}))
    return raw, der


def fetch_subject(ds, sub, task):
    """-> list of run dicts {entities, bold, mask, confounds, events, tr} (empty if nothing usable)."""
    raw, der = ensure_dataset(ds)
    dk = [k for k in keys(DERIV, f"fmriprep/{ds}-fmriprep/sub-{sub}/") if f"_task-{task}_" in k and "/func/" in k]
    rk = [k for k in keys(RAW, f"{ds}/sub-{sub}/") if f"_task-{task}_" in k and "/func/" in k]
    top = {n: f"{ds}/{n}" for n in (f"task-{task}_events.tsv", f"task-{task}_bold.json")}
    for name in (f"task-{task}_bold.json", f"task-{task}_events.json"):   # dataset-level sidecars (BIDS inheritance)
        dest = raw / name
        if not dest.exists():
            b = get(f"{RAW}/{ds}/{name}")
            if b:
                dest.write_bytes(b)
    runs = []
    for k in sorted(x for x in dk if x.endswith(f"_{SPACE}_desc-preproc_bold.nii.gz")):
        stem = k.split("/")[-1].split(f"_{SPACE}")[0]                    # sub-X[_ses-Y]_task-T[_run-R]
        sub_path = "/".join(k.split("/")[2:-1])                            # sub-X[/ses-Y]/func
        conf = next((x for x in dk if x.endswith(f"{stem}_desc-confounds_timeseries.tsv")), None)
        mask = next((x for x in dk if x.endswith(f"{stem}_{SPACE}_desc-brain_mask.nii.gz")), None)
        ev = next((x for x in rk if x.endswith("_events.tsv") and ents(x) == ents(stem)), None)
        js = next((x for x in rk if x.endswith("_bold.json") and ents(x) == ents(stem)), None)
        if not (conf and mask):
            continue
        ddir, rdir = der / sub_path, raw / sub_path
        ddir.mkdir(parents=True, exist_ok=True)
        rdir.mkdir(parents=True, exist_ok=True)
        files = {}
        for key, base in ((k, DERIV), (k[:-7] + ".json", DERIV), (mask, DERIV), (conf, DERIV), (conf[:-4] + ".json", DERIV)):
            dest = ddir / key.split("/")[-1]
            if not dest.exists():
                get(f"{base}/{key}", dest)
            files[key] = dest
        ev_dest = rdir / f"{stem}_events.tsv"
        if not ev_dest.exists():
            b = get(f"{RAW}/{ev}") if ev else get(f"{RAW}/{top[f'task-{task}_events.tsv']}")
            if b:
                ev_dest.write_bytes(b)
        js_dest = rdir / f"{stem}_bold.json"
        if not js_dest.exists():
            b = get(f"{RAW}/{js}") if js else get(f"{RAW}/{top[f'task-{task}_bold.json']}")
            if b is None:
                b = get(f"{DERIV}/{k[:-7]}.json")
            if b:
                js_dest.write_bytes(b)
        bold_link = rdir / f"{stem}_bold.nii.gz"
        if not bold_link.exists():
            bold_link.symlink_to(files[k])
        if not ev_dest.exists() or not js_dest.exists() or not files[k].exists():
            continue
        tr = json.loads(js_dest.read_text()).get("RepetitionTime")
        for side in (files.get(k[:-7] + ".json"), raw / f"task-{task}_bold.json"):   # inherited or derivative TR
            if tr is None and side is not None and Path(side).exists():
                tr = json.loads(Path(side).read_text()).get("RepetitionTime")
        if tr is None:
            continue
        runs.append({"stem": stem, "bold": files[k], "mask": files[mask], "confounds": files[conf], "events": ev_dest,
                     "tr": float(tr)})
    return runs


def subject_bytes(ds, sub, task):
    """Bytes of the subject's MNI res-2 BOLD files for the task (from the bucket listing), for disk budgeting."""
    q = {"list-type": "2", "prefix": f"fmriprep/{ds}-fmriprep/sub-{sub}/", "max-keys": "1000"}
    t = (get(f"{DERIV}/?{urllib.parse.urlencode(q)}") or b"").decode()
    tot = 0
    for k, z in zip(re.findall(r"<Key>([^<]+)</Key>", t), re.findall(r"<Size>(\d+)</Size>", t)):
        if f"_task-{task}_" in k and k.endswith(f"_{SPACE}_desc-preproc_bold.nii.gz"):
            tot += int(z)
    return tot


def drop_subject(ds, sub):
    for base in (ROOT / ds / "raw", ROOT / ds / "deriv" / "fmriprep"):
        d = base / f"sub-{sub}"
        if d.exists():
            for f in d.rglob("*.nii.gz"):
                f.unlink()
