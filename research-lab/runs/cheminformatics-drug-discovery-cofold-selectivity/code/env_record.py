"""Record the environment the predictions were produced in: results/tables/env.json.

Written as a script rather than by hand because the first version of this table was made with ad-hoc
shell commands and was wrong twice: the affinity checkpoint was still downloading, so its size was a
partial 508 MB, and the digests were labelled sha256 but were 32 hex characters (md5). Hashing the
weights is the only check a reader has that the released checkpoints were used unmodified, so it is
worth having reproducible.
"""
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
CKPT = Path.home() / ".boltz"
PKGS = ["boltz", "torch", "rdkit", "numpy", "scipy", "pandas", "scikit-learn",
        "cuequivariance-torch", "matplotlib"]


def sha256_file(p, chunk=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def version(name):
    from importlib.metadata import PackageNotFoundError, version as v
    try:
        return v(name)
    except PackageNotFoundError:
        return None


def gpu():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version",
                              "--format=csv,noheader"], capture_output=True, text=True, timeout=30)
        return out.stdout.strip().splitlines()[0]
    except Exception as e:  # recorded rather than raised: the table is provenance, not a dependency
        return f"unavailable: {e}"


def main():
    env = dict(
        python=platform.python_version(),
        platform=platform.platform(),
        # the run spans a reboot, so both kernels it ran under are recorded
        kernels=["6.8.0-139-generic", platform.release()],
        packages={p: version(p) for p in PKGS},
        gpu=gpu(),
        checkpoints={p.name: dict(bytes=p.stat().st_size, sha256=sha256_file(p))
                     for p in sorted(CKPT.glob("*.ckpt"))},
    )
    out = RUN / "results" / "tables" / "env.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(env, open(out, "w"), indent=1)
    print(json.dumps(env, indent=1))


if __name__ == "__main__":
    sys.exit(main())
