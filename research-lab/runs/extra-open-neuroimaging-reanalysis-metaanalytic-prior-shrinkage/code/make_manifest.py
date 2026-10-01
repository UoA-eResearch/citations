#!/usr/bin/env python
"""Job list for first-level models (plan.md sec 2), built from the OpenNeuro S3 listing.

One row per (dataset, task, subject) with an MNI preprocessed BOLD file, in the order the domains are processed.
Output: data/manifest.tsv (dataset, task, acq, sub, bold_key, bold_size, conf_key, mask_key, events_key)
"""
import re
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
B = "https://s3.amazonaws.com/openneuro.org"
JOBS = [("ds002785", "workingmemory"), ("ds002785", "emomatching"), ("ds002785", "gstroop"),
        ("ds002785", "anticipation"), ("ds002785", "faces"), ("ds002790", "stopsignal"),
        ("ds002790", "workingmemory"), ("ds002790", "emomatching")]          # last two: replications


def ls(prefix):
    tok, out = None, []
    while True:
        u = f"{B}?list-type=2&prefix={prefix}&max-keys=1000"
        if tok:
            u += "&continuation-token=" + urllib.parse.quote(tok)
        x = urllib.request.urlopen(u, timeout=120).read().decode()
        out += re.findall(r"<Key>([^<]*)</Key>.*?<Size>(\d+)</Size>", x)
        m = re.search(r"<NextContinuationToken>([^<]*)</NextContinuationToken>", x)
        if not m:
            return out
        tok = m.group(1)


def main():
    rows = []
    for ds in sorted({d for d, _ in JOBS}):
        keys = dict(ls(f"{ds}/derivatives/fmriprep/sub-"))
        raw = dict(ls(f"{ds}/sub-"))
        for k, s in keys.items():
            m = re.match(rf"{ds}/derivatives/fmriprep/(sub-\d+)/func/\1_task-([a-z]+)_acq-([a-z0-9]+)"
                         r"_space-MNI152NLin2009cAsym_desc-preproc_bold\.nii\.gz$", k)
            if not m or (ds, m.group(2)) not in JOBS:
                continue
            sub, task, acq = m.groups()
            stem = f"{sub}_task-{task}_acq-{acq}"
            conf = f"{ds}/derivatives/fmriprep/{sub}/func/{stem}_desc-confounds_regressors.tsv"
            mask = f"{ds}/derivatives/fmriprep/{sub}/func/{stem}_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz"
            ev = f"{ds}/{sub}/func/{stem}_events.tsv"
            rows.append(dict(dataset=ds, task=task, acq=acq, sub=sub, bold_key=k, bold_size=int(s),
                             conf_key=conf if conf in keys else "", mask_key=mask if mask in keys else "",
                             events_key=ev if ev in raw else ""))
    df = pd.DataFrame(rows)
    order = {j: i for i, j in enumerate(JOBS)}
    df["o"] = [order[(d, t)] for d, t in zip(df.dataset, df.task)]
    df = df.sort_values(["o", "sub"]).drop(columns="o")
    df.to_csv(RUN / "data" / "manifest.tsv", sep="\t", index=False)
    print(df.groupby(["dataset", "task"], sort=False).agg(n=("sub", "size"), gb=("bold_size", lambda x: round(x.sum() / 1e9, 1)),
          no_conf=("conf_key", lambda x: (x == "").sum()), no_mask=("mask_key", lambda x: (x == "").sum()),
          no_events=("events_key", lambda x: (x == "").sum())).to_string())


if __name__ == "__main__":
    main()
