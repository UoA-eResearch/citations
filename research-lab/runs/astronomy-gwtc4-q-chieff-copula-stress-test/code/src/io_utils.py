"""HDF5 I/O: reading PESummary-format GWTC PE releases, and reading/writing
the pipeline's standardized tables.

Standardized sample table (data/processed/sample_table_<mode>.h5)
-----------------------------------------------------------------
One group per event (name = commonName). Equal-length float64 datasets:
    mass_1      source-frame primary mass (Msun)
    mass_ratio  q = m2/m1
    chi_eff     effective aligned spin (chi_eff, not chi_eff_infinity)
    redshift
    ln_prior    ln PE sampling prior at each sample in (mass_1, mass_ratio,
                redshift, chi_eff) -- see pe_priors.py
Group attrs: catalog, far, snr, pe_group, redshift_prior, spin_amax,
n_raw_samples, m2_median.

Standardized injection table (data/processed/injection_table_<mode>.h5)
-----------------------------------------------------------------------
Datasets mass_1, mass_ratio, chi_eff, redshift, ln_prior (draw density in the
same parameterization divided by the mixture weight; see selection.py) and
attrs total_generated, analysis_time_yr, n_found_total, amax_inj.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

logger = logging.getLogger("q_chieff_copula")

POSTERIOR_COLUMNS = ["mass_1_source", "mass_2_source", "mass_ratio", "redshift", "chi_eff",
                     "luminosity_distance", "network_matched_filter_snr"]


def list_pe_groups(h5_path: Path) -> list[str]:
    with h5py.File(h5_path, "r") as f:
        return [k for k in f.keys() if k not in ("history", "version") and "posterior_samples" in f[k]]


def find_pe_group(h5_path: Path, preferred: str) -> str:
    groups = list_pe_groups(h5_path)
    if preferred in groups:
        return preferred
    for g in groups:
        if g.endswith("Mixed"):
            logger.warning("%s: %s not found, using %s", Path(h5_path).name, preferred, g)
            return g
    if groups:
        logger.warning("%s: %s not found, using %s", Path(h5_path).name, preferred, groups[0])
        return groups[0]
    raise ValueError(f"{h5_path}: no usable PE group found")


def load_posterior(h5_path: Path, group: str, columns=None) -> pd.DataFrame:
    with h5py.File(h5_path, "r") as f:
        ds = f[group]["posterior_samples"]
        names = ds.dtype.names
        cols = [c for c in (columns or names) if c in names]
        data = ds[()]
        out = {c: np.asarray(data[c], dtype=float) for c in cols}
    df = pd.DataFrame(out)
    if "chi_eff" not in df and {"mass_1", "mass_2", "spin_1z", "spin_2z"} <= set(names):
        raise ValueError("chi_eff column missing")
    return df


def read_analytic_priors(h5_path: Path, groups: list[str]) -> dict[str, str]:
    """Return {param: prior-string} from the first group with priors/analytic."""
    with h5py.File(h5_path, "r") as f:
        for g in groups:
            if g in f and "priors" in f[g] and "analytic" in f[g]["priors"]:
                an = f[g]["priors"]["analytic"]
                out = {}
                for k in an.keys():
                    v = an[k][()]
                    v = v[0] if getattr(v, "shape", ()) else v
                    out[k] = v.decode() if isinstance(v, bytes) else str(v)
                return out
    return {}


def write_sample_table(path: Path, events: dict[str, dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as f:
        for name, d in events.items():
            g = f.create_group(name)
            for col in ("mass_1", "mass_ratio", "chi_eff", "redshift", "ln_prior"):
                g.create_dataset(col, data=np.asarray(d[col], dtype=np.float64))
            for k, v in d.get("attrs", {}).items():
                g.attrs[k] = v if isinstance(v, (int, float, str, np.number)) else str(v)
    logger.info("wrote standardized sample table: %s (%d events)", path, len(events))


def read_sample_table(path: Path) -> tuple[dict[str, pd.DataFrame], dict[str, dict]]:
    posteriors, meta = {}, {}
    with h5py.File(path, "r") as f:
        for name in sorted(f.keys()):
            g = f[name]
            posteriors[name] = pd.DataFrame({c: np.asarray(g[c]) for c in
                                             ("mass_1", "mass_ratio", "chi_eff", "redshift", "ln_prior")})
            meta[name] = dict(g.attrs)
    return posteriors, meta


def write_injection_table(path: Path, table: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as f:
        for k in ("total_generated", "analysis_time_yr", "n_found_total", "amax_inj"):
            f.attrs[k] = table[k]
        for k in ("mass_1", "mass_ratio", "chi_eff", "redshift", "ln_prior"):
            f.create_dataset(k, data=np.asarray(table[k], dtype=np.float64))
        if "component" in table:
            f.create_dataset("component", data=np.asarray(table["component"], dtype=np.int8))
    logger.info("wrote standardized injection table: %s (%d found injections, total_generated=%d)",
                path, len(table["mass_1"]), table["total_generated"])


def read_injection_table(path: Path) -> dict:
    with h5py.File(path, "r") as f:
        out = {k: np.asarray(f[k]) for k in ("mass_1", "mass_ratio", "chi_eff", "redshift", "ln_prior")}
        if "component" in f:
            out["component"] = np.asarray(f["component"])
        out.update({k: f.attrs[k] for k in f.attrs})
    out["total_generated"] = float(out["total_generated"])
    return out


def save_json(obj, path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    def _default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        if isinstance(o, Path):
            return str(o)
        return str(o)

    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=_default)


def load_json(path: Path):
    with open(path) as f:
        return json.load(f)
