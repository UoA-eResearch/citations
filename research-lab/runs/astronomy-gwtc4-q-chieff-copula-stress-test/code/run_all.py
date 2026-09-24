#!/usr/bin/env python
"""Pipeline driver with stage selection and resumability.

    python run_all.py --mode smoke                 # everything, fast settings
    python run_all.py --mode full                  # full run (see README for runtimes)
    python run_all.py --mode full --stages fit,mocks,mockstats,diagnostics,figures
    python run_all.py --mode full --stages fit --models copula_gauss_plp --backend gpu
    python run_all.py --mode smoke --force         # redo every stage
    python run_all.py --mode full --stages gpucheck  # optional: time the likelihood on the GPU

Each stage is a standalone script in src/ that skips itself when its outputs
exist (unless --force). Stage logs: logs/<stage>_<mode>.log
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
PY = CODE_DIR.parent / "venv" / "bin" / "python"
STAGES = [
    ("fetch", "src/fetch_data.py"),
    ("build", "src/build_sample.py"),
    ("test", "src/test_models.py"),
    ("fit", "src/fit_models.py"),
    ("mocks", "src/mock_catalogs.py"),
    ("mockstats", "src/mock_stats.py"),
    ("diagnostics", "src/diagnostics.py"),
    ("figures", "src/make_figures.py"),
]
# optional stages (never run by default): `--stages gpucheck` times the compiled
# likelihood on the GPU (stops/restarts the vllm container for ~2-3 minutes).
OPTIONAL_STAGES = [("gpucheck", "src/gpu_check.py")]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["smoke", "full"], default="smoke")
    parser.add_argument("--stages", default=",".join(s for s, _ in STAGES),
                        help="comma-separated subset of: " + ",".join(s for s, _ in STAGES + OPTIONAL_STAGES))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--backend", choices=["auto", "cpu", "gpu"], default=None)
    parser.add_argument("--models", default=None, help="passed to the fit stage")
    parser.add_argument("--skip-nuts", action="store_true")
    args = parser.parse_args()
    wanted = [s.strip() for s in args.stages.split(",") if s.strip()]
    unknown = set(wanted) - {s for s, _ in STAGES + OPTIONAL_STAGES}
    if unknown:
        sys.exit(f"unknown stages: {unknown}")
    py = PY if PY.exists() else Path(sys.executable)
    t_all = time.time()
    for name, script in STAGES + OPTIONAL_STAGES:
        if name not in wanted:
            continue
        cmd = [str(py), str(CODE_DIR / script)]
        if name == "test":
            cmd.append(args.mode)
        else:
            cmd += ["--mode", args.mode]
            if args.force:
                cmd.append("--force")
            if args.backend and name in ("fit", "mockstats", "gpucheck"):
                cmd += ["--backend", args.backend]
            if args.models and name == "fit":
                cmd += ["--models", args.models]
            if args.skip_nuts and name == "fit":
                cmd.append("--skip-nuts")
        print(f"\n===== stage {name}: {' '.join(cmd)}", flush=True)
        t0 = time.time()
        rc = subprocess.call(cmd, cwd=str(CODE_DIR))
        print(f"===== stage {name} finished rc={rc} in {(time.time() - t0) / 60:.1f} min", flush=True)
        if rc != 0:
            sys.exit(f"stage {name} failed (rc={rc}); fix and re-run -- completed stages are skipped automatically")
    print(f"\nALL REQUESTED STAGES DONE in {(time.time() - t_all) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
