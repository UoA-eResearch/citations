#!/usr/bin/env python
"""D27c: a smooth estimate of the detection probability P_det(theta) in theta = (m1_src, q, chi_eff, z), from the found
injections alone (density ratio): the found injections are distributed as N_gen p_draw(theta) P_det(theta), so

    P_det(x) ~= sum_j K_h(x - x_j) / (N_gen p_draw,x(x_j))

in x = (ln Mc_det, q, chi_eff, ln z), where a PE posterior is narrow in ln Mc_det and P_det varies smoothly. The kernel
sum is a 4-d histogram smoothed by a Gaussian filter. The grid is the time-weighted O1-O4a mixture the selection term of
the likelihood uses. Only relative values within one event's posterior matter (e2_rho_scan_oracle --pdet, v3c/v3d
mocks). Independent review (deviations.md "D27c review" (b)): the 1-bin smoothing inflates the absolute P_det by ~35%
(grid alpha / injection alpha = 1.35 for a null population), which cancels within an event; changing the smoothing to
0.5 or 2 bins moves P_det-weighted event means by <= 0.02 sd typically.

Usage: ../venv/bin/python analysis/pdet_grid.py  -> data/processed/pdet_grid_full.npz
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import gaussian_filter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

EDGES = dict(lnmc=np.linspace(np.log(2.0), np.log(250.0), 43), q=np.linspace(0.0, 1.0, 21),
             chi=np.linspace(-1.0, 1.0, 41), lnz=np.linspace(np.log(0.005), np.log(3.0), 41))
SMOOTH_BINS = (1.0, 1.0, 1.0, 1.0)


def to_x(m1, q, chi, z):
    mc_det = m1 * q ** 0.6 / (1 + q) ** 0.2 * (1 + z)
    return np.stack([np.log(mc_det), q, chi, np.log(z)], axis=-1)


def build(inj):
    m1, q, chi, z = (np.asarray(inj[c], float) for c in ("mass_1", "mass_ratio", "chi_eff", "redshift"))
    ok = z > 0
    x = to_x(m1[ok], q[ok], chi[ok], z[ok])
    # draw density in x: p_theta * |d theta / d x| = p_theta * m1 * z  (d ln Mc_det / d m1 = 1/m1 at fixed q, z)
    ln_px = inj["ln_prior"][ok] + np.log(m1[ok]) + np.log(z[ok])
    w = np.exp(-ln_px) / float(inj["total_generated"])
    edges = [EDGES[k] for k in ("lnmc", "q", "chi", "lnz")]
    h, _ = np.histogramdd(x, bins=edges, weights=w)
    vol = np.prod(np.meshgrid(*[np.diff(e) for e in edges], indexing="ij"), axis=0)
    p = gaussian_filter(h / vol, SMOOTH_BINS, mode="nearest")
    n, _ = np.histogramdd(x, bins=edges)
    return p, gaussian_filter(n, SMOOTH_BINS, mode="nearest"), edges


class PdetGrid:
    def __init__(self, path):
        d = np.load(path)
        self.centres = [0.5 * (e[1:] + e[:-1]) for e in (d["e0"], d["e1"], d["e2"], d["e3"])]
        self.lnp = np.log(np.clip(d["pdet"], 1e-8, 1.0))      # sparse edge cells can exceed 1
        self.f = RegularGridInterpolator(self.centres, self.lnp, bounds_error=False, fill_value=None)

    def ln_pdet(self, m1, q, chi, z):
        x = to_x(m1, q, chi, np.clip(z, 1e-4, None))
        lo = np.array([c[0] for c in self.centres])
        hi = np.array([c[-1] for c in self.centres])
        return self.f(np.clip(x, lo, hi))


def main():
    from config import load_config
    from io_utils import read_injection_table
    cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
    inj = read_injection_table(cfg.injection_table_path())
    p, n, edges = build(inj)
    out = cfg.path("processed_dir") / "pdet_grid_full.npz"
    np.savez(out, pdet=p, n_smoothed=n, e0=edges[0], e1=edges[1], e2=edges[2], e3=edges[3])
    print("saved", out, "grid", p.shape, "max P_det", p.max().round(3), "cells with >=20 found (smoothed):", int((n >= 20).sum()))
    g = PdetGrid(out)
    # sanity: P_det along z for a 30+30 Msun, chi_eff = 0 binary, and along chi_eff at z = 0.3
    for z in (0.05, 0.1, 0.2, 0.4, 0.8, 1.2):
        print(f"  m1=30 q=1 chi=0 z={z}: P_det={np.exp(g.ln_pdet(np.array([30.0]), np.array([1.0]), np.array([0.0]), np.array([z])))[0]:.3f}")
    for c in (-0.4, -0.2, 0.0, 0.2, 0.4, 0.6):
        print(f"  m1=30 q=0.8 z=0.3 chi={c}: P_det={np.exp(g.ln_pdet(np.array([30.0]), np.array([0.8]), np.array([c]), np.array([0.3])))[0]:.3f}")
    for qq in (0.3, 0.5, 0.7, 0.9, 1.0):
        print(f"  Mc fixed (m1=30,q=0.8 equiv) z=0.3 chi=0 q={qq}: ", end="")
        mc = 30 * 0.8 ** 0.6 / 1.8 ** 0.2
        m1 = mc * (1 + qq) ** 0.2 / qq ** 0.6
        print(f"P_det={np.exp(g.ln_pdet(np.array([m1]), np.array([qq]), np.array([0.0]), np.array([0.3])))[0]:.3f}")


if __name__ == "__main__":
    main()
