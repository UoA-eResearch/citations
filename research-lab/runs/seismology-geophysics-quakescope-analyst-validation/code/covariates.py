"""Station covariates (plan section 4; D1 clarifications). Uses metadata and waveforms only, never picks or matches.
Writes data/covariates.parquet: netsta, band, instrument, sample_rate, log_noise, network, elevation, latitude, longitude.

Stations: those with >= 30 reference P picks in the denominator (loaded station-day, station in the catalogue).
band / instrument: letters 1 and 2 of the station's modal QuakeScope read band over its denominator days.
sample_rate: modal FDSN channel-table sample rate of <read band>Z at those days.
log_noise: 3 random loaded days in the sampled months (seed 20261011); 09:00-10:00 UTC of the vertical channel of that
day's read band, byte-range read from SCEDC / NCEDC continuous miniSEED on S3; response removed to velocity; band-pass
1-10 Hz; RMS over 60 s windows; log10 of the median over all windows and days."""
import concurrent.futures as cf
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
SCEDC = "https://s3.us-west-2.amazonaws.com/scedc-pds"
NCEDC = "https://s3.us-east-2.amazonaws.com/ncedc-pds"
FDSN = {"CI": "https://service.scedc.caltech.edu/fdsnws", "NC": "https://service.ncedc.org/fdsnws", "BK": "https://service.ncedc.org/fdsnws"}
SEED = 20261011
H0, H1 = 9, 10


def channel_table():
    out = []
    for f in ("scedc_channels.txt", "ncedc_channels.txt"):
        c = pd.read_csv(RAW / "channels" / f, sep="|", comment=None, dtype=str)
        c.columns = [x.strip().lstrip("#").strip() for x in c.columns]
        out.append(c)
    c = pd.concat(out)
    c["SampleRate"] = c.SampleRate.astype(float)
    c["start"] = pd.to_datetime(c.StartTime, errors="coerce")
    c["end"] = pd.to_datetime(c.EndTime.fillna("2599-01-01"), errors="coerce").fillna(pd.Timestamp("2599-01-01"))
    return c


def denominator():
    ref = pd.read_parquet(RUN / "data" / "reference_picks.parquet")
    ref["netsta"] = ref.net + "." + ref.sta
    ref["date"] = ref.t_ref.dt.floor("D")
    a = []
    for n in ("CI", "NC", "BK"):
        x = pd.read_parquet(RAW / "availability" / f"{n}.parquet", columns=["tid", "date", "status", "cha"])
        a.append(x[x.status == "loaded"])
    a = pd.concat(a)
    a["netsta"] = a.tid.str.rsplit(".", n=1).str[0]
    a["loc"] = a.tid.str.rsplit(".", n=1).str[1]
    a["date"] = pd.to_datetime(a.date)
    st = pd.read_parquet(RAW / "stations.parquet")
    st["netsta"] = st.network_code + "." + st.station_code
    ref = ref[(ref.phase == "P") & ref.netsta.isin(set(st.netsta))]
    ref = ref.merge(a[["netsta", "date"]].drop_duplicates(), on=["netsta", "date"])
    return ref, a, st


def record_length(url):
    r = requests.get(url, headers={"Range": "bytes=0-4095"}, timeout=120)
    if r.status_code not in (200, 206):
        return None, None
    b = r.content
    # blockette 1000 (data-only SEED): record length exponent; fall back to 4096
    off = struct.unpack(">H", b[46:48])[0]
    while 48 <= off < len(b) - 8:
        btype, nxt = struct.unpack(">HH", b[off:off + 4])
        if btype == 1000:
            return 2 ** b[off + 6], int(r.headers.get("Content-Range", "/0").split("/")[-1] or 0)
        if nxt == 0:
            break
        off = nxt
    return 4096, int(r.headers.get("Content-Range", "/0").split("/")[-1] or 0)


def hour_bytes(url):
    """Bytes covering roughly 08:30-10:30 UTC of a day-long miniSEED file, aligned to record boundaries."""
    rl, size = record_length(url)
    if not rl or not size:
        return None
    a = int(size * (H0 - 0.5) / 24) // rl * rl
    b = min(size, (int(size * (H1 + 0.5) / 24) // rl + 1) * rl)
    r = requests.get(url, headers={"Range": f"bytes={a}-{b - 1}"}, timeout=300)
    return r.content if r.status_code in (200, 206) else None


def waveform_url(net, sta, loc, cha, day):
    y, j = day.year, day.dayofyear
    if net == "CI":
        return f"{SCEDC}/continuous_waveforms/{y}/{y}_{j:03d}/{net}{sta:_<5}{cha}{(loc or ''):_<3}{y}{j:03d}.ms"
    return f"{NCEDC}/continuous_waveforms/{net}/{y}/{y}.{j:03d}/{sta}.{net}.{cha}.{loc or ''}.D.{y}.{j:03d}"


def noise_one(job):
    from obspy import UTCDateTime, read, read_inventory
    netsta, loc, days_bands = job
    net, sta = netsta.split(".")
    vals = []
    try:
        inv = read_inventory(io.BytesIO(requests.get(f"{FDSN[net]}/station/1/query", params=dict(
            network=net, station=sta, level="response", format="xml"), timeout=300).content))
    except Exception:  # noqa: BLE001
        return netsta, np.nan, "no response"
    for day, band in days_bands:
        cha = band + "Z"
        try:
            raw = hour_bytes(waveform_url(net, sta, loc, cha, day))
            if raw is None:
                continue
            stream = read(io.BytesIO(raw), format="MSEED")
            t0 = UTCDateTime(day.year, day.month, day.day, H0)
            stream = stream.select(channel=cha)
            stream.trim(t0, t0 + 3600)
            stream.merge(fill_value=None)
            for tr in stream.split():
                if tr.stats.npts < 60 * tr.stats.sampling_rate:
                    continue
                tr.detrend("demean")
                tr.remove_response(inventory=inv, output="VEL", pre_filt=(0.3, 0.5, 0.4 * tr.stats.sampling_rate, 0.45 * tr.stats.sampling_rate), water_level=None)
                tr.filter("bandpass", freqmin=1.0, freqmax=10.0, corners=4, zerophase=True)
                n = int(60 * tr.stats.sampling_rate)
                x = tr.data[: len(tr.data) // n * n].reshape(-1, n)
                vals += list(np.sqrt(np.mean(x ** 2, axis=1)))
        except Exception:  # noqa: BLE001
            continue
    if not vals:
        return netsta, np.nan, "no data"
    return netsta, float(np.log10(np.median(vals))), f"{len(vals)} windows"


def main(workers=12):
    ms = json.load(open(RUN / "data" / "months.json"))
    ref, a, st = denominator()
    n = ref.groupby("netsta").size()
    stations = sorted(n[n >= 30].index)
    print(len(stations), "stations with >= 30 denominator P picks", flush=True)
    days = ref.groupby("netsta").date.apply(set)
    a = a.join(days.rename("refdays"), on="netsta")
    a_ref = a[a.apply(lambda r: isinstance(r.refdays, set) and r.date in r.refdays, axis=1)]
    band = a_ref.groupby("netsta").cha.agg(lambda s: s.mode().iloc[0] if len(s.dropna()) else None)
    loc = a_ref.groupby("netsta")["loc"].agg(lambda s: s.mode().iloc[0])
    ch = channel_table()
    ch["netsta"] = ch.Network + "." + ch.Station
    rates = {}
    for s in stations:
        b = band.get(s)
        c = ch[(ch.netsta == s) & (ch.Channel == f"{b}Z")] if b else ch.iloc[0:0]
        ds = a_ref[a_ref.netsta == s].date
        r = [c[(c.start <= d) & (c.end > d)].SampleRate.iloc[0] for d in ds if len(c[(c.start <= d) & (c.end > d)])]
        rates[s] = float(pd.Series(r).mode().iloc[0]) if r else np.nan
    # noise days: 3 random loaded days in the sampled months
    rng = np.random.default_rng(SEED)
    ym = {(y, m) for y, m in ms}
    a_m = a[[(d.year, d.month) in ym for d in a.date]]
    jobs = []
    for s in stations:
        x = a_m[a_m.netsta == s].sort_values("date")
        if x.empty:
            continue
        pick = x.iloc[sorted(rng.choice(len(x), size=min(3, len(x)), replace=False))]
        jobs.append((s, loc.get(s, ""), [(d, b) for d, b in zip(pick.date, pick.cha)]))
    with cf.ProcessPoolExecutor(workers) as ex:
        res = list(ex.map(noise_one, jobs))
    noise = {s: v for s, v, _ in res}
    notes = {s: m for s, _, m in res}
    sti = st.drop_duplicates("netsta").set_index("netsta")
    out = pd.DataFrame({"netsta": stations})
    out["band"] = [(band.get(s) or "?")[0] for s in stations]
    out["instrument"] = [(band.get(s) or "??")[1] for s in stations]
    out["read_band"] = [band.get(s) for s in stations]
    out["sample_rate"] = [rates.get(s, np.nan) for s in stations]
    out["log_noise"] = [noise.get(s, np.nan) for s in stations]
    out["noise_note"] = [notes.get(s, "not attempted") for s in stations]
    out["network"] = [s.split(".")[0] for s in stations]
    for c in ("elevation", "latitude", "longitude"):
        out[c] = [sti[c].get(s, np.nan) for s in stations]
    out.to_parquet(RUN / "data" / "covariates.parquet", index=False)
    print(out.describe(include="all").T.to_string())


if __name__ == "__main__":
    main(*(int(x) for x in sys.argv[1:]))
