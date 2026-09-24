#!/usr/bin/env python
"""Stage 02: build the standardized sample-and-prior table and injection table.

* Reads each event's preferred PE group, applies the BBH control (the LVK
  GWTC-4.0 population-paper criterion, arXiv:2508.18083 sec 3.2.2 / sec 6:
  the 1% lower limit of both component-mass posteriors > 3 Msun) and the
  explicit exclusion list, converts to the
  population parameterization (mass_1 source, mass_ratio, redshift, chi_eff)
  and evaluates the analytic PE sampling prior at every sample (pe_priors.py).
* Parses the real O1-O4a injection mixture file (selection.py); in smoke mode
  a random slice of the found injections is kept (total_generated rescaled).
* Writes a QC table with per-event medians, sample counts and prior settings,
  and the observed correlation statistics (Kendall tau of posterior medians).

Outputs: data/processed/sample_table_<mode>.h5, injection_table_<mode>.h5,
sample_qc_<mode>.csv, injection_check_<mode>.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import add_common_args, load_config, outputs_exist, setup_logging  # noqa: E402
from io_utils import (POSTERIOR_COLUMNS, find_pe_group, list_pe_groups, load_json, load_posterior,  # noqa: E402
                      read_analytic_priors, save_json, write_injection_table, write_sample_table)
from pe_priors import (ChiEffPriorTable, classify_distance_prior_string, ln_pe_prior, parse_spin_amax,  # noqa: E402
                       redshift_from_dl)
from selection import standardize_real_injections  # noqa: E402

MAX_STORED_SAMPLES = 10000


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_common_args(parser)
    args = parser.parse_args()
    cfg = load_config(mode=args.mode)
    logger = setup_logging(cfg, "02_build_sample")
    processed = cfg.path("processed_dir")
    sample_path, inj_path = cfg.sample_table_path(), cfg.injection_table_path()
    qc_path = processed / f"sample_qc_{cfg.mode}.csv"
    check_path = processed / f"injection_check_{cfg.mode}.json"
    if outputs_exist([sample_path, inj_path, qc_path, check_path], args.force, logger, "02_build_sample"):
        return

    scfg = cfg.raw["sample"]
    chieff_cache = processed / "chieff_prior_cache"
    chieff_kwargs = dict(n_mc=int(scfg["chieff_prior_mc_samples"]), n_q=int(scfg["chieff_prior_q_grid"]),
                         n_chi=int(scfg["chieff_prior_chi_grid"]), seed=cfg.seed_for("chieff_prior"))
    tables: dict[float, ChiEffPriorTable] = {}
    rng = cfg.rng("build_sample")

    # ---- events ----------------------------------------------------------------------
    manifest = load_json(cfg.manifest_path())
    exclude = set(scfg.get("exclude_events") or [])
    force_include = set(scfg.get("force_include_events") or [])
    floor = float(scfg["bbh_mass2_source_floor_msun"])
    mass_q = float(scfg.get("bbh_mass_quantile", 0.01))
    events, qc = {}, []
    for m in manifest:
        name, path = m["commonName"], Path(m["pe_file"])
        row = {k: m.get(k) for k in ("commonName", "catalog", "far", "snr")}
        try:
            group = find_pe_group(path, m["preferred_pe_group"])
            df = load_posterior(path, group, POSTERIOR_COLUMNS + ["mass_1", "mass_2"])
            if "redshift" not in df:
                df["redshift"] = redshift_from_dl(df["luminosity_distance"].values)
            if "mass_1_source" not in df:
                df["mass_1_source"] = df["mass_1"] / (1 + df["redshift"])
            if "mass_2_source" not in df:
                df["mass_2_source"] = df["mass_2"] / (1 + df["redshift"])
            if "mass_ratio" not in df:
                df["mass_ratio"] = df["mass_2_source"] / df["mass_1_source"]
            chi_col = cfg.chi_eff_column
            if chi_col not in df:
                raise KeyError(f"{chi_col} not in posterior table")
        except Exception as e:  # noqa: BLE001
            logger.error("%s: cannot read PE (%s); excluded", name, e)
            row.update(included=False, reason=f"read error: {e}")
            qc.append(row)
            continue
        m2_med = float(np.median(df["mass_2_source"]))
        # LVK GWTC-4.0 population-paper BBH criterion (arXiv:2508.18083 sec 3.2.2 / sec 6): the 1% lower
        # limit of BOTH component-mass posteriors (under the PE prior) must exceed 3 Msun
        m1_lo = float(np.quantile(df["mass_1_source"], mass_q))
        m2_lo = float(np.quantile(df["mass_2_source"], mass_q))
        row.update(pe_group=group, n_raw_samples=len(df), m1_median=float(np.median(df["mass_1_source"])),
                   m2_median=m2_med, m1_lower=m1_lo, m2_lower=m2_lo, q_median=float(np.median(df["mass_ratio"])),
                   chi_eff_median=float(np.median(df[chi_col])), z_median=float(np.median(df["redshift"])))
        if name in exclude:
            row.update(included=False, reason="explicit exclusion list (config sample.exclude_events)")
            qc.append(row)
            logger.info("%s excluded: %s", name, row["reason"])
            continue
        if min(m1_lo, m2_lo) <= floor:
            if name in force_include:
                row.update(reason=f"kept: {mass_q:.0%} lower limit m2_source {m2_lo:.2f} <= {floor} Msun but the event "
                                  "is in the LVK GWTC-3.0-inherited BBH sample (config sample.force_include_events)")
                logger.info("%s %s", name, row["reason"])
            else:
                row.update(included=False, reason=f"{mass_q:.0%} lower limit m2_source {m2_lo:.2f} <= {floor} Msun "
                                                  "(LVK BBH criterion, arXiv:2508.18083 sec 3.2.2)")
                qc.append(row)
                logger.info("%s excluded: %s", name, row["reason"])
                continue
        # PE prior settings
        ref_groups = [g for g in list_pe_groups(path) if not g.endswith("Mixed")] + [group]
        analytic = read_analytic_priors(path, ref_groups)
        amax = parse_spin_amax(analytic.get("a_1", ""), float(scfg["default_spin_amax"]))
        if m["redshift_prior"] == "from_file":
            if "luminosity_distance" in analytic:
                zprior = classify_distance_prior_string(analytic["luminosity_distance"])
            else:
                zprior = "uniform_comoving_source_frame"
                logger.warning("%s: no analytic distance prior in file; assuming %s", name, zprior)
        else:
            zprior = m["redshift_prior"]
        if amax not in tables:
            tables[amax] = ChiEffPriorTable(amax, chieff_cache, **chieff_kwargs)
        if len(df) > MAX_STORED_SAMPLES:
            df = df.iloc[np.sort(rng.choice(len(df), MAX_STORED_SAMPLES, replace=False))]
        m1, q, z, chi = (df["mass_1_source"].values, df["mass_ratio"].values, df["redshift"].values,
                         df[chi_col].values)
        ok = np.isfinite(m1) & np.isfinite(q) & np.isfinite(z) & np.isfinite(chi) & (q > 0) & (q <= 1)
        ln_prior = ln_pe_prior(m1[ok], q[ok], z[ok], chi[ok], zprior, tables[amax])
        events[name] = {"mass_1": m1[ok], "mass_ratio": q[ok], "chi_eff": chi[ok], "redshift": z[ok],
                        "ln_prior": ln_prior,
                        "attrs": {"catalog": m["catalog"], "far": float(m["far"] or np.nan),
                                  "snr": float(m["snr"] or np.nan), "pe_group": group, "redshift_prior": zprior,
                                  "spin_amax": amax, "n_raw_samples": int(row["n_raw_samples"]),
                                  "m2_median": m2_med}}
        row.update(included=True, reason="", spin_amax=amax, redshift_prior=zprior, n_stored=int(ok.sum()))
        qc.append(row)
    if not events:
        raise RuntimeError("no events survived the sample cuts")
    write_sample_table(sample_path, events)
    qc_df = pd.DataFrame(qc)
    qc_df.to_csv(qc_path, index=False)
    inc = qc_df[qc_df["included"] == True]  # noqa: E712
    tau, p = kendalltau(inc["q_median"], inc["chi_eff_median"]) if len(inc) > 2 else (np.nan, np.nan)
    logger.info("sample: %d events included, %d excluded; observed Kendall tau(q_med, chi_eff_med) = %.3f (p=%.3g)",
                len(inc), len(qc_df) - len(inc), tau, p)
    save_json({"n_included": int(len(inc)), "kendall_tau_medians": float(tau), "kendall_p": float(p),
               "catalog_counts": inc["catalog"].value_counts().to_dict()},
              processed / f"sample_summary_{cfg.mode}.json")

    # ---- injections --------------------------------------------------------------------
    raw_inj = cfg.path("raw_injections_dir") / cfg.raw["data_sources"]["injection_file_key"]
    slice_n = cfg.mode_value("injection_slice")
    table, check = standardize_real_injections(
        raw_inj, cfg.far_threshold, float(scfg["semianalytic_snr_threshold"]), chieff_cache, chieff_kwargs,
        slice_n=slice_n, rng=cfg.rng("injection_slice"),
        spin_families=cfg.raw["data_sources"].get("injection_spin_families"))
    write_injection_table(inj_path, table)
    save_json(check, check_path)
    logger.info("stage 02 (build_sample) complete")


if __name__ == "__main__":
    main()
