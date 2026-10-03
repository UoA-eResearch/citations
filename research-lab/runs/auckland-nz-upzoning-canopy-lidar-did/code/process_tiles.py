"""Stream LiDAR tiles: download -> per-1 m-cell canopy / building / valid flags -> counts per 30 m grid cell -> delete.

Per tile (plan.md section 3):
- points with class 7, 12 or 18 (noise, overlap, high noise) and withheld points are dropped;
- ground model: mean elevation of class-2 points per 1 m cell; empty cells take the nearest ground cell's value;
- height above ground (HAG) = z - ground of the point's 1 m cell;
- a 1 m cell is valid if it holds any remaining point; canopy_t if it holds a vegetation point (class 3, 4 or 5) with
  HAG >= t, for t = 2, 3 (primary) and 5 m; building if it holds a class-6 point;
- counts are summed into 30 m cells on the global NZTM grid (x, y multiples of 30 m).
Output per epoch: data/cells/<epoch>/<tile>.parquet with columns cx, cy (cell lower-left), n_valid, n_c2, n_c3, n_c5, n_bld.
Usage: process_tiles.py <epoch> [n_jobs] [limit] [noov]
With "noov" (deviations.md D4), points carrying the LAS 1.4 overlap *flag* are also dropped (point formats >= 6, as in
the 2024 collection, mark overlap with a flag rather than class 12); output goes to data/cells/<epoch>_noov/.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import laspy
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy import ndimage

RUN = Path(__file__).resolve().parents[1]
BASE = "https://opentopography.s3.sdsc.edu/pc-bulk/"
DROP = (7, 12, 18)
CELL = 30
TMP = Path(os.environ.get("CANOPY_TMP", RUN / "data" / "tmp"))


def process(key, epoch, noov=False):
    out = RUN / "data" / "cells" / (epoch + ("_noov" if noov else "")) / (Path(key).stem + ".parquet")
    if out.exists():
        return "skip"
    TMP.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".laz", dir=TMP)
    os.close(fd)
    try:
        for k in range(5):
            r = subprocess.run(["curl", "-sS", "--retry", "5", "-o", tmp, BASE + key], capture_output=True)
            if r.returncode == 0 and os.path.getsize(tmp) > 0:
                break
        else:
            return f"download failed: {key}"
        las = laspy.read(tmp)
        cls = np.asarray(las.classification)
        keep = ~np.isin(cls, DROP)
        if hasattr(las, "withheld") and las.withheld is not None:
            keep &= ~np.asarray(las.withheld, bool)
        if noov and las.header.point_format.id >= 6:
            keep &= ~np.asarray(las.overlap, bool)
        x, y, z, cls = np.asarray(las.x)[keep], np.asarray(las.y)[keep], np.asarray(las.z)[keep], cls[keep]
        if len(x) == 0:
            pd.DataFrame(columns=["cx", "cy", "n_valid", "n_c2", "n_c3", "n_c5", "n_bld"]).to_parquet(out)
            return "empty"
        x0, y0 = np.floor(x.min() / CELL) * CELL, np.floor(y.min() / CELL) * CELL
        ix, iy = (x - x0).astype(np.int64), (y - y0).astype(np.int64)
        nx, ny = ix.max() + 1, iy.max() + 1
        lin = iy * nx + ix
        g = cls == 2
        gs = np.bincount(lin[g], weights=z[g], minlength=nx * ny)
        gc = np.bincount(lin[g], minlength=nx * ny)
        ground = np.full(nx * ny, np.nan)
        ground[gc > 0] = gs[gc > 0] / gc[gc > 0]
        grid = ground.reshape(ny, nx)
        if np.isnan(grid).all():
            return f"no ground: {key}"
        idx = ndimage.distance_transform_edt(np.isnan(grid), return_distances=False, return_indices=True)
        grid = grid[tuple(idx)]
        hag = z - grid.ravel()[lin]
        veg = np.isin(cls, (3, 4, 5))
        flags = {}
        flags["valid"] = np.bincount(lin, minlength=nx * ny) > 0
        for t in (2, 3, 5):
            flags[f"c{t}"] = np.bincount(lin[veg & (hag >= t)], minlength=nx * ny) > 0
        flags["bld"] = np.bincount(lin[cls == 6], minlength=nx * ny) > 0
        # 1 m cell centres -> 30 m cells
        cy_, cx_ = np.divmod(np.arange(nx * ny), nx)
        X, Y = x0 + cx_, y0 + cy_
        cxc, cyc = (np.floor(X / CELL) * CELL).astype(np.int64), (np.floor(Y / CELL) * CELL).astype(np.int64)
        v = flags["valid"]
        df = pd.DataFrame({"cx": cxc[v], "cy": cyc[v], "n_valid": 1, "n_c2": flags["c2"][v].astype(np.int32),
                           "n_c3": flags["c3"][v].astype(np.int32), "n_c5": flags["c5"][v].astype(np.int32),
                           "n_bld": flags["bld"][v].astype(np.int32)})
        df = df.groupby(["cx", "cy"], as_index=False).sum()
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out)
        return "ok"
    except Exception as e:  # noqa: BLE001
        return f"error {key}: {e}"
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def main(epoch, n_jobs=48, limit=None, noov=None):
    t = pd.read_parquet(RUN / "data" / "tiles_needed.parquet")
    keys = t[t.epoch == epoch].key.tolist()[: int(limit) if limit not in (None, "", "0") else None]
    nv = noov == "noov"
    res = Parallel(n_jobs=int(n_jobs), backend="loky", verbose=5)(delayed(process)(k, epoch, nv) for k in keys)
    s = pd.Series(res)
    print(epoch, s.str.split(":").str[0].str.split(" ").str[0].value_counts().to_dict())
    bad = [r for r in res if r not in ("ok", "skip", "empty")]
    (RUN / "data" / "cells" / f"{epoch}{'_noov' if nv else ''}_failures.txt").write_text("\n".join(bad))


if __name__ == "__main__":
    main(*sys.argv[1:])
