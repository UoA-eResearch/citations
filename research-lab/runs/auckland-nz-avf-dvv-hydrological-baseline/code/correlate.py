"""Daily ambient-noise cross-correlations for the 11 AVF stations (plan section 2). Resumable by day.

  correlate.py run [--start 2013-01-01] [--end 2026-09-30] [--workers 8]
  correlate.py test YYYY-MM-DD

Per station-day (vertical, location 10; EHZ, MKAZ HHZ): stream the day file from GeoNet's open S3 bucket, merge, skip
if under 20 h of data; demean, detrend, low-pass 8 Hz and decimate to 20 Hz; bandpass 0.3-5 Hz. 48 windows of 30
minutes; a window is invalid if it holds a gap or if its RMS exceeds 5x the day's median window RMS (transient mask).
Each window is spectrally whitened over 0.3-5 Hz (cosine-tapered edges) and then normalised by its 2 s running
absolute mean. Pair cross-correlations (lags +/-100 s) are averaged over windows valid at both stations; a pair-day
needs at least 24. Writes data/ccf/<year>/<date>.npz: ccf (55 x 4001 float32), nwin (55), and the station list.
"""
import argparse
import io
import itertools
import sys
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / "data" / "ccf"
S3 = "https://geonet-open-data.s3-ap-southeast-2.amazonaws.com/waveforms/miniseed"
STATIONS = ["ABAZ", "AWAZ", "EPAZ", "ETAZ", "HBAZ", "KBAZ", "MBAZ", "MKAZ", "RVAZ", "WIAZ", "WTAZ"]
CHAN = {s: "EHZ" for s in STATIONS} | {"MKAZ": "HHZ"}
PAIRS = list(itertools.combinations(range(len(STATIONS)), 2))
FS, WIN, NWIN, MAXLAG = 20.0, 1800, 48, 100
NS = int(WIN * FS)
NFFT = 2 * NS
FREQ = np.fft.rfftfreq(NFFT, 1 / FS)


def fetch(day, sta):
    doy = day.timetuple().tm_yday
    url = f"{S3}/{day.year}/{day.year}.{doy:03d}/{sta}.NZ/{day.year}.{doy:03d}.{sta}.10-{CHAN[sta]}.NZ.D"
    for k in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            time.sleep(5 * (k + 1))
        except Exception:
            time.sleep(5 * (k + 1))
    return None


def whiten_taper():
    w = np.zeros_like(FREQ)
    lo1, lo2, hi1, hi2 = 0.25, 0.35, 4.5, 5.5
    m = (FREQ >= lo2) & (FREQ <= hi1)
    w[m] = 1.0
    a = (FREQ > lo1) & (FREQ < lo2)
    w[a] = 0.5 * (1 - np.cos(np.pi * (FREQ[a] - lo1) / (lo2 - lo1)))
    b = (FREQ > hi1) & (FREQ < hi2)
    w[b] = 0.5 * (1 + np.cos(np.pi * (FREQ[b] - hi1) / (hi2 - hi1)))
    return w


TAPER = whiten_taper()


def station_spectra(raw, day):
    """(48 x nfreq complex spectra of normalised windows, valid mask) or None."""
    from obspy import read, UTCDateTime
    st = read(io.BytesIO(raw))
    st.merge(method=0, fill_value=None)
    tr = st[0]
    t0 = UTCDateTime(day.isoformat())
    tr.trim(t0, t0 + 86400 - 1 / tr.stats.sampling_rate, pad=True, fill_value=None)
    data = tr.data
    mask = np.ma.getmaskarray(data)
    if (~mask).sum() < 20 * 3600 * tr.stats.sampling_rate:
        return None
    x = np.asarray(np.ma.filled(data.astype(float), np.nan))
    good = ~np.isnan(x)
    x[~good] = np.nanmean(x)
    tr.data = x - x.mean()
    tr.detrend("linear")
    sr = tr.stats.sampling_rate
    tr.filter("lowpass", freq=8.0, corners=4, zerophase=True)
    step = int(round(sr / FS))
    y = tr.data[::step][: int(86400 * FS)]
    g = good[::step][: int(86400 * FS)]
    if len(y) < int(86400 * FS):
        pad = int(86400 * FS) - len(y)
        y, g = np.concatenate([y, np.zeros(pad)]), np.concatenate([g, np.zeros(pad, bool)])
    from scipy.signal import butter, sosfiltfilt
    sos = butter(4, [0.3, 5.0], btype="band", fs=FS, output="sos")
    y = sosfiltfilt(sos, y)
    W = y.reshape(NWIN, NS)
    G = g.reshape(NWIN, NS).all(axis=1)
    rms = np.sqrt((W ** 2).mean(axis=1))
    med = np.median(rms[G]) if G.any() else np.inf
    valid = G & (rms <= 5 * med)
    spec = np.fft.rfft(W, n=NS, axis=1)
    spec = spec / np.maximum(np.abs(spec), 1e-20) * np.interp(np.fft.rfftfreq(NS, 1 / FS), FREQ, TAPER)
    Wt = np.fft.irfft(spec, n=NS, axis=1)
    k = int(2 * FS)
    ker = np.ones(k) / k
    ram = np.apply_along_axis(lambda r: np.convolve(np.abs(r), ker, mode="same"), 1, Wt)
    Wn = Wt / np.maximum(ram, 1e-20)
    return np.fft.rfft(Wn, n=NFFT, axis=1), valid


def process_day(day):
    out = OUT / str(day.year) / f"{day.isoformat()}.npz"
    if out.exists():
        return day, "exists"
    with ThreadPoolExecutor(len(STATIONS)) as ex:
        raws = list(ex.map(lambda s: fetch(day, s), STATIONS))
    specs = []
    for raw in raws:
        try:
            specs.append(station_spectra(raw, day) if raw else None)
        except Exception:
            specs.append(None)
    L = int(MAXLAG * FS)
    ccf = np.zeros((len(PAIRS), 2 * L + 1), np.float32)
    nwin = np.zeros(len(PAIRS), np.int16)
    for p, (i, j) in enumerate(PAIRS):
        if specs[i] is None or specs[j] is None:
            continue
        v = specs[i][1] & specs[j][1]
        if v.sum() < 24:
            continue
        c = np.fft.irfft(specs[i][0][v] * np.conj(specs[j][0][v]), n=NFFT, axis=1).mean(axis=0)
        c = np.concatenate([c[-L:], c[:L + 1]])                    # lags -L..+L
        ccf[p] = (c / NS).astype(np.float32)
        nwin[p] = int(v.sum())
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, ccf=ccf, nwin=nwin, stations=np.array(STATIONS),
                        have=np.array([s is not None for s in specs]))
    return day, f"{int((nwin > 0).sum())} pairs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode"); ap.add_argument("date", nargs="?")
    ap.add_argument("--start", default="2013-01-01"); ap.add_argument("--end", default="2026-09-30")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.mode == "test":
        t = time.time()
        print(process_day(date.fromisoformat(a.date)), f"{time.time() - t:.0f} s")
        return
    d0, d1 = date.fromisoformat(a.start), date.fromisoformat(a.end)
    days = [d0 + timedelta(n) for n in range((d1 - d0).days + 1)]
    days = [d for d in days if not (OUT / str(d.year) / f"{d.isoformat()}.npz").exists()]
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        for k, (d, msg) in enumerate(ex.map(process_day, days), 1):
            if k % 10 == 0 or k == len(days):
                print(f"{k}/{len(days)} {d} {msg} {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
