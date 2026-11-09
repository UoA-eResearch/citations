"""SBSS 1232+563 like-for-like epoch counts (D3, confirmation pass item 2): good g and r epochs at MJD >= 60068 in the
stored light curve against a fresh IRSA query keeping every ZTF object, and where the difference comes from.
-> merged into results/tables/posthoc_d3.json under "sbss_like_for_like" """
import io
import json
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
T, D = RUN / "results" / "tables", RUN / "data"
k = pd.read_csv(T / "known_systems.csv")
sid = int(k[k.name == "SBSS 1232+563"].gaia_dr3_source_id_in_sample.iloc[0])
st = pd.concat(pd.read_parquet(f, filters=[("source_id", "==", sid)]) for f in sorted((D / "lc_v2").glob("shard_*.parquet")))
st = st[st.filt.isin(["zg", "zr"]) & (st.mjd >= 60068)]
s = pd.read_parquet(D / "sample.parquet").set_index("source_id").loc[sid]
url = f"https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE%20{s.ra2019:.6f}%20{s.dec2019:.6f}%200.000556&FORMAT=csv"
x = pd.read_csv(io.StringIO(urllib.request.urlopen(url, timeout=300).read().decode()))
x = x[(x.mjd >= 60068) & (x.catflags == 0) & (x.magerr < 0.25) & x.filtercode.isin(["zg", "zr"])]
stored = set(zip(st.filt, st.mjd.round(5)))
x["stored"] = [(f, round(m, 5)) in stored for f, m in zip(x.filtercode, x.mjd)]
out = {"stored_good_gr_epochs_mjd_ge_60068": int(len(st)), "stored_by_filter": st.filt.value_counts().to_dict(),
       "irsa_good_gr_epochs_mjd_ge_60068": int(len(x)), "irsa_by_filter": x.filtercode.value_counts().to_dict(),
       "irsa_not_stored": x[~x.stored][["oid", "filtercode", "mjd"]].assign(oid=lambda d: d.oid.astype(str)).to_dict("records")}
p = T / "posthoc_d3.json"
j = json.loads(p.read_text()); j["sbss_like_for_like"] = out
p.write_text(json.dumps(j, indent=1, default=float) + "\n")
print(json.dumps(out, indent=1, default=float))
