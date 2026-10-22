"""D3 (added secondary analysis): exposure from slip-sized newly bare patches only. Reads no outcome.

Newly bare 20 m cells (bare20.tif band 1 > 0) are labelled into 8-connected patches; patches of at most 25 cells
(1 ha) count. E_slip = newly bare 10 m pixels in those patches / valid pixels, over each site's C(5 km).
Writes results/tables/exposure_slips.csv (E_slip and its tercile) and results/tables/exposure_slips_summary.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy import ndimage

RUN = Path(__file__).resolve().parents[1]
MAX_CELLS = 25


def main():
    with rasterio.open(RUN / "data" / "bare20.tif") as ds:
        bare, valid = ds.read(1).astype(np.int64), ds.read(2).astype(np.int64)
    lab, n = ndimage.label(bare > 0, structure=np.ones((3, 3), bool))
    size = np.bincount(lab.ravel())
    small = (lab > 0) & (size[lab] <= MAX_CELLS)
    large5 = (lab > 0) & (size[lab] > 125)
    bs = np.where(small, bare, 0).ravel()
    v = valid.ravel()
    z = np.load(RUN / "data" / "contrib.npz")
    s = pd.read_csv(RUN / "results" / "tables" / "sites.csv")
    rows = []
    for site in s.site_id:
        c = z[f"{site}|route|5"]
        rows.append({"site_id": site, "E_slip_route_5": float(bs[c].sum() / v[c].sum()) if v[c].sum() else np.nan})
    x = pd.DataFrame(rows)
    o = x.E_slip_route_5.rank(method="first")
    x["tercile_slip"] = pd.cut(o, [0, len(x) / 3, 2 * len(x) / 3, len(x)], labels=["bottom", "middle", "top"]).astype(str)
    x.to_csv(RUN / "results" / "tables" / "exposure_slips.csv", index=False)
    ex = pd.read_csv(RUN / "results" / "tables" / "exposure.csv")
    summ = {"patches": int(n), "patches_le_1ha": int((size[1:] <= MAX_CELLS).sum()),
            "share_of_bare_px_in_patches_le_1ha": round(float(bare[small].sum() / bare.sum()), 4),
            "share_of_bare_px_in_patches_gt_5ha": round(float(bare[large5].sum() / bare.sum()), 4),
            "E_slip_quantiles": {str(q): round(float(x.E_slip_route_5.quantile(q)), 6) for q in (0, 0.25, 0.5, 0.75, 1)},
            "spearman_with_primary_E": round(float(x.E_slip_route_5.corr(ex.E_route_5, method="spearman")), 3)}
    json.dump(summ, open(RUN / "results" / "tables" / "exposure_slips_summary.json", "w"), indent=1)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
