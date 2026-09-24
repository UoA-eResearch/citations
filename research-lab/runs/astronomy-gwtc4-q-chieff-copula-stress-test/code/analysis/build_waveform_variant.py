#!/usr/bin/env python
"""D25: the plan's waveform-systematics control (plan sec 5-6). Builds an alternative standardized sample table
for the SAME 153 events from a single waveform family instead of the preferred "Mixed" release:

  phenom : IMRPhenomXPHM (O1-O3, all 69 events) + IMRPhenomXPHM-SpinTaylor (O4a, all 84)
  eob    : SEOBNRv4PHM (O1-O3, 57 of 69; the other 12 fall back to IMRPhenomXPHM) + SEOBNRv5PHM (O4a, all 84)

Everything else mirrors stage 02 (build_sample.py): source-frame masses and redshift as stored, at most 10 000 samples
per event, and the analytic PE prior evaluated at every sample with each event's redshift-prior kind and spin bound
from the main table (the per-waveform groups share their file's prior conventions).

Output: data/processed/sample_table_full_wf-<family>.h5 and a per-event group list (json).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from config import load_config  # noqa: E402
from io_utils import POSTERIOR_COLUMNS, list_pe_groups, load_json, load_posterior, read_sample_table, write_sample_table  # noqa: E402
from pe_priors import ChiEffPriorTable, ln_pe_prior, redshift_from_dl  # noqa: E402

FAMILIES = {"phenom": ["IMRPhenomXPHM", "IMRPhenomXPHM-SpinTaylor"],
            "eob": ["SEOBNRv4PHM", "SEOBNRv5PHM", "IMRPhenomXPHM", "IMRPhenomXPHM-SpinTaylor"]}


def pick_group(path, family):
    groups = list_pe_groups(path)
    by_tail = {g.split(":")[-1]: g for g in groups}
    for tail in FAMILIES[family]:
        if tail in by_tail:
            return by_tail[tail]
    raise ValueError(f"{path}: no {family} group among {groups}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(FAMILIES), required=True)
    ap.add_argument("--mode", default="full")
    args = ap.parse_args()
    cfg = load_config(mode=args.mode, config_path=str(HERE.parent / "config.yaml"))
    _, meta = read_sample_table(cfg.sample_table_path())
    manifest = {m["commonName"]: m for m in load_json(cfg.manifest_path())}
    s = cfg.raw["sample"]
    table = ChiEffPriorTable(0.99, cfg.path("processed_dir") / "chieff_prior_cache", n_mc=int(s["chieff_prior_mc_samples"]),
                             n_q=int(s["chieff_prior_q_grid"]), n_chi=int(s["chieff_prior_chi_grid"]),
                             seed=cfg.seed_for("chieff_prior"))
    rng = np.random.default_rng(cfg.seed_for(f"wf_{args.family}"))
    events, used = {}, {}
    for name in sorted(meta):
        path = Path(manifest[name]["pe_file"])
        group = pick_group(path, args.family)
        df = load_posterior(path, group, POSTERIOR_COLUMNS + ["mass_1", "mass_2"])
        if "redshift" not in df:
            df["redshift"] = redshift_from_dl(df["luminosity_distance"].values)
        if "mass_1_source" not in df:
            df["mass_1_source"] = df["mass_1"] / (1 + df["redshift"])
        if "mass_2_source" not in df:
            df["mass_2_source"] = df["mass_2"] / (1 + df["redshift"])
        if "mass_ratio" not in df:
            df["mass_ratio"] = df["mass_2_source"] / df["mass_1_source"]
        if len(df) > 10000:
            df = df.iloc[np.sort(rng.choice(len(df), 10000, replace=False))]
        m1, q, z, chi = (df["mass_1_source"].values, df["mass_ratio"].values, df["redshift"].values,
                         df[cfg.chi_eff_column].values)
        ok = np.isfinite(m1) & np.isfinite(q) & np.isfinite(z) & np.isfinite(chi) & (q > 0) & (q <= 1)
        zprior = meta[name]["redshift_prior"]
        assert float(meta[name]["spin_amax"]) == 0.99, name
        events[name] = {"mass_1": m1[ok], "mass_ratio": q[ok], "chi_eff": chi[ok], "redshift": z[ok],
                        "ln_prior": ln_pe_prior(m1[ok], q[ok], z[ok], chi[ok], zprior, table),
                        "attrs": {**{k: v for k, v in meta[name].items()}, "pe_group": group}}
        used[name] = group
        print(f"{name:<20} {group:<34} n={int(ok.sum())}", flush=True)
    out = cfg.path("processed_dir") / f"sample_table_{args.mode}_wf-{args.family}.h5"
    write_sample_table(out, events)
    json.dump(used, open(out.with_suffix(".groups.json"), "w"), indent=1)
    from collections import Counter
    print("groups used:", dict(Counter(g.split(':')[-1] for g in used.values())), "->", out)


if __name__ == "__main__":
    main()
