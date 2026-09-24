#!/usr/bin/env python
"""Stage 01: data acquisition (real GWOSC/Zenodo data in both modes).

* Event lists from the GWOSC eventapi for every catalog in
  data_sources.catalogs (GWTC-4.0 = O4a, GWTC-3-confident = O3b,
  GWTC-2.1-confident = O1-O3a), FAR < 1/yr and a point-estimate BBH
  pre-filter, de-duplicated by commonName.
* Preferred ("Mixed") PE release file per event from Zenodo, downloaded with
  a small thread pool (Zenodo throughput from this host is ~1.6 MB/s in
  aggregate, so the full O1-O4a BBH set (~30 GB) takes ~5 h; the stage is
  resumable file-by-file and safe to re-run).
* The O1-O4a cumulative sensitivity-injection mixture file (625 MB).

smoke mode: the N smallest PE files per catalog (n_events_per_catalog) so
that every catalog / file-layout code path is exercised in ~5 minutes.

Outputs: data/processed/event_manifest_<mode>.json, data/raw/pe_samples/*.h5,
data/raw/injections/<mixture>.hdf
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import add_common_args, load_config, outputs_exist, setup_logging  # noqa: E402
from gwosc_client import (download_file, download_many, fetch_event_detail, fetch_event_list,  # noqa: E402
                          prefilter_candidates, remote_size, resolve_preferred_pe)
from io_utils import load_json, save_json  # noqa: E402


def pe_dest(cfg, name: str) -> Path:
    return cfg.path("raw_pe_dir") / f"{name}_PEDataRelease.h5"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(parser)
    parser.add_argument("--skip-injections", action="store_true")
    args = parser.parse_args()
    cfg = load_config(mode=args.mode)
    logger = setup_logging(cfg, "01_fetch_data")

    manifest_path = cfg.manifest_path()
    src = cfg.raw["data_sources"]
    inj_dest = cfg.path("raw_injections_dir") / src["injection_file_key"]
    if outputs_exist([manifest_path, inj_dest], args.force, logger, "01_fetch_data"):
        manifest = load_json(manifest_path)
        missing = [m for m in manifest if not Path(m["pe_file"]).exists()]
        if not missing:
            return
        logger.info("%d manifest entries have no local PE file; re-downloading those", len(missing))

    n_per_cat = cfg.mode_value("n_events_per_catalog")
    mass2_floor = float(cfg.raw["sample"]["bbh_mass2_source_floor_msun"])
    exclude = set(cfg.raw["sample"].get("exclude_events") or [])

    # ---- 0. FAR fallback table (O1/O2 events carry far=None in GWTC-2.1-confident) -------
    far_fallback = {}
    for url in src.get("far_fallback_catalogs") or []:
        for ev in fetch_event_list(url).values():
            if ev.get("far") is not None:
                far_fallback.setdefault(ev["commonName"], ev["far"])
    if far_fallback:
        logger.info("FAR fallback table: %d events from %s", len(far_fallback), src.get("far_fallback_catalogs"))

    # ---- 1. candidate events from every catalog ------------------------------------
    seen, candidates = set(), []
    for cat in src["catalogs"]:
        events = fetch_event_list(cat["eventapi"])
        cands = prefilter_candidates(events, cfg.far_threshold, mass2_floor, far_fallback)
        n_fb = sum(1 for c in cands if c.get("far_source"))
        if n_fb:
            logger.info("%s: %d candidates use a fallback-catalog FAR: %s", cat["name"], n_fb,
                        [c["commonName"] for c in cands if c.get("far_source")])
        cands = [c for c in cands if c["commonName"] not in seen and c["commonName"] not in exclude]
        logger.info("%s: %d event-versions, %d pass FAR<%.3g/yr & m2>%g pre-filter (new)",
                    cat["name"], len(events), len(cands), cfg.far_threshold, mass2_floor)
        resolved = []
        for ev in cands:
            detail = fetch_event_detail(ev)
            pe = resolve_preferred_pe(detail, cat["preferred_pe_group"])
            if pe is None:
                logger.warning("%s: no PE data_url in eventapi detail, skipping", ev["commonName"])
                continue
            resolved.append({
                "commonName": ev["commonName"], "version": ev["version"], "catalog": cat["name"],
                "far": ev.get("far"), "far_source": ev.get("far_source", cat["name"]),
                "snr": ev.get("network_matched_filter_snr"),
                "mass_1_source_point": ev.get("mass_1_source"), "mass_2_source_point": ev.get("mass_2_source"),
                "chi_eff_point": ev.get("chi_eff"), "data_url": pe["data_url"],
                "waveform_family": pe["waveform_family"], "preferred_pe_group": cat["preferred_pe_group"],
                "redshift_prior": cat["redshift_prior"],
            })
        if n_per_cat is not None:
            k = int(n_per_cat.get(cat["name"], 0)) if isinstance(n_per_cat, dict) else int(n_per_cat)
            for r in resolved:
                r["size"] = remote_size(r["data_url"])
            resolved.sort(key=lambda r: (r["size"] or 1e12, r["far"]))
            resolved = resolved[:k]
        for r in resolved:
            seen.add(r["commonName"])
        candidates.extend(resolved)
    logger.info("%d candidate events across catalogs", len(candidates))

    # ---- 2. PE file downloads (thread pool, resumable) ---------------------------
    jobs, manifest = [], []
    sample_dir = cfg.path("sample_dir") / "pe_samples"
    for r in candidates:
        dest = pe_dest(cfg, r["commonName"])
        r["pe_file"] = str(dest)
        manifest.append(r)
        if dest.exists():
            continue
        # reuse the verification sample pulled during planning, if present
        for cand in sample_dir.glob(f"{r['commonName']}*"):
            logger.info("reusing planning-stage sample file %s", cand)
            shutil.copy(cand, dest)
            break
        if not dest.exists():
            if "size" not in r:
                r["size"] = remote_size(r["data_url"])
            jobs.append((r["data_url"], dest, r.get("size")))
    total = sum((j[2] or 0) for j in jobs)
    logger.info("downloading %d PE files (~%.1f GB; ~%.0f min at 1.6 MB/s)", len(jobs), total / 1e9,
                total / 1.6e6 / 60)
    results = download_many(jobs, threads=int(src.get("download_threads", 4)))
    manifest = [m for m in manifest if Path(m["pe_file"]).exists()]
    failed = [str(d) for d, ok in results.items() if not ok]
    if failed:
        logger.error("%d downloads failed (re-run this stage to retry): %s", len(failed), failed[:5])
    save_json(manifest, manifest_path)
    logger.info("wrote event manifest: %s (%d events with PE)", manifest_path, len(manifest))

    # ---- 3. injections ----------------------------------------------------------------
    if not args.skip_injections:
        url = f"{src['zenodo_injection_record']}/files/{src['injection_file_key']}/content"
        download_file(url, inj_dest, expected_size=int(src["injection_file_size_bytes"]))
    logger.info("stage 01 (fetch_data) complete")


if __name__ == "__main__":
    main()
