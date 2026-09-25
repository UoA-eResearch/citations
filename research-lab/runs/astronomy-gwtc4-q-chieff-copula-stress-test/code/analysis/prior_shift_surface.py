#!/usr/bin/env python
"""D29d: is the real catalog's larger PE-prior shift a per-event response difference or an occupancy difference?

Pools per-event (q_flat, chi_flat, dq = q_post - q_flat) over the real catalog and 100 v3c null mocks, compares the mean
shift in bins of (chi_flat, q_flat) (the response surface), and the number of events per catalog in the corner where
the isotropic-spin prior pulls hardest (chi_flat > 0.3 and q_flat > 0.65), real vs the mock distribution.
Output: results/tables/prior_shift_surface_v3c.json
"""
import json, os, sys
from pathlib import Path
os.environ.setdefault("JAX_PLATFORMS", "cpu")
import h5py, numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src")); sys.path.insert(0, str(HERE))
from config import load_config
from e2_tau import clipped_weights, tau, wmedian
from fit_models import load_event_arrays

cfg = load_config(mode="full", config_path=str(HERE.parent / "config.yaml"))
clip_q = float(cfg.raw["mocks"]["kernel_weight_clip_quantile"])


def per_event(q, chi, lp):
    wf = clipped_weights(-lp, clip_q)
    qf, cf = wmedian(q, wf), wmedian(chi, wf)
    qp, cp = wmedian(q, np.ones_like(q)), wmedian(chi, np.ones_like(q))
    return pd.DataFrame(dict(q_flat=qf, chi_flat=cf, q_post=qp, chi_post=cp, dq=qp - qf))


ev, names, _ = load_event_arrays(cfg, np.random.default_rng(1000), max_samples=2000)
real = per_event(ev["mass_ratio"], ev["chi_eff"], ev["ln_prior"]); real["event"] = names
mocks = []
TAG = os.environ.get("MOCK_TAG", "v3c")
with h5py.File(cfg.path("mocks_dir") / TAG / "mocks_full_rho+0.00.h5", "r") as fh:
    for k in sorted(k for k in fh if k.startswith("mock_"))[:100]:
        g = fh[k]
        d = per_event(np.asarray(g["mass_ratio"]), np.asarray(g["chi_eff"]), np.asarray(g["ln_prior"])); d["mock"] = k
        mocks.append(d)
M = pd.concat(mocks)
cb, qb = [-1, 0.0, 0.15, 0.3, 1], [0, 0.55, 0.65, 0.75, 1.01]
out = {"surface": []}
print("mean dq by (chi_flat, q_flat) bin: real (n) | mocks pooled (n per catalog)")
for c0, c1 in zip(cb[:-1], cb[1:]):
    for q0, q1 in zip(qb[:-1], qb[1:]):
        r = real[(real.chi_flat >= c0) & (real.chi_flat < c1) & (real.q_flat >= q0) & (real.q_flat < q1)]
        m = M[(M.chi_flat >= c0) & (M.chi_flat < c1) & (M.q_flat >= q0) & (M.q_flat < q1)]
        out["surface"].append(dict(chi=[c0, c1], q=[q0, q1], real_n=int(len(r)), real_dq=float(r.dq.mean()) if len(r) else None,
                                   mock_n_per_cat=float(len(m) / 100), mock_dq=float(m.dq.mean()) if len(m) else None))
        print(f"  chi [{c0:+.2f},{c1:+.2f}) q [{q0:.2f},{q1:.2f}): real {r.dq.mean() if len(r) else np.nan:+.3f} ({len(r):3d}) | "
              f"mocks {m.dq.mean() if len(m) else np.nan:+.3f} ({len(m)/100:5.1f})")
corner = lambda d: int(((d.chi_flat > 0.3) & (d.q_flat > 0.65)).sum())
nc = np.array([corner(d) for d in mocks])
out["corner_chi_gt_0p3_q_gt_0p65"] = dict(real=corner(real), mock_median=float(np.median(nc)), mock_p2p5=float(np.quantile(nc, 0.025)),
                                          mock_p97p5=float(np.quantile(nc, 0.975)), frac_mock_ge_real=float(np.mean(nc >= corner(real))))
hc = lambda d: int((d.chi_flat > 0.3).sum())
nh = np.array([hc(d) for d in mocks])
out["high_chi_gt_0p3"] = dict(real=hc(real), mock_median=float(np.median(nh)), frac_mock_ge_real=float(np.mean(nh >= hc(real))))
# among high-chi events, how high are their flat q medians?
qh = lambda d: float(d[d.chi_flat > 0.3].q_flat.median())
out["q_flat_median_of_high_chi_events"] = dict(real=qh(real), mock_median=float(np.median([qh(d) for d in mocks])),
                                               frac_mock_ge_real=float(np.mean([qh(d) >= qh(real) for d in mocks])))
out["dq_of_high_chi_events"] = dict(real=float(real[real.chi_flat > 0.3].dq.mean()),
                                    mock_median=float(np.median([d[d.chi_flat > 0.3].dq.mean() for d in mocks])))
out["corner_events_real"] = real[(real.chi_flat > 0.3) & (real.q_flat > 0.65)].sort_values("dq")[["event", "chi_flat", "q_flat", "dq"]].round(3).to_dict(orient="records")
json.dump(out, open(cfg.path("tables_dir") / f"prior_shift_surface_{TAG}.json", "w"), indent=2)
for k in ("corner_chi_gt_0p3_q_gt_0p65", "high_chi_gt_0p3", "q_flat_median_of_high_chi_events", "dq_of_high_chi_events"):
    print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in out[k].items()})
print("corner events (real):", [(e["event"], e["chi_flat"], e["q_flat"], e["dq"]) for e in out["corner_events_real"]])
