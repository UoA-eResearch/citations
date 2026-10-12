"""Split an input directory of YAMLs into N shards so several boltz processes can share the GPU.

Sharding is round-robin over the sorted file list, so each shard sees a similar mix of kinases and
ligands, and the shard map is recorded (results/tables/shards_<arm>.csv) because each boltz process seeds
its own RNG stream: a prediction is reproducible given the same shard layout and seed, not given the pair
alone. Diffusion sampling makes the affinity head stochastic, so this is recorded rather than hidden.

  python code/shard.py <arm> <n_shards>
"""
import csv
import shutil
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]


def main(arm, n):
    src = RUN / "data" / f"inputs_{arm}"
    files = sorted(src.glob("*.yaml"))
    rows = []
    for i in range(n):
        d = RUN / "data" / f"inputs_{arm}_s{i}"
        d.mkdir(parents=True, exist_ok=True)
    for k, f in enumerate(files):
        s = k % n
        shutil.copy(f, RUN / "data" / f"inputs_{arm}_s{s}" / f.name)
        rows.append(dict(arm=arm, pair_id=f.stem, shard=s, seed=20261013 + s))
    with open(RUN / "results" / "tables" / f"shards_{arm}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, ["arm", "pair_id", "shard", "seed"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(files)} yamls -> {n} shards of about {len(files) // n}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]))
