"""Thin client for the GWOSC eventapi (multi-catalog): event lists, FAR /
BBH pre-filters, resolving the preferred-PE Zenodo download URL, and
(parallel, resumable) downloads."""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

logger = logging.getLogger("q_chieff_copula")
UA = {"User-Agent": "q-chieff-copula-stress-test/0.2 (research pipeline; contact nyou045@aucklanduni.ac.nz)"}


def _get_json(url: str, timeout=60, retries=4) -> dict:
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=UA, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            logger.warning("GET %s failed (%d/%d): %s", url, attempt, retries, e)
            time.sleep(min(2**attempt, 20))
    raise RuntimeError(f"could not fetch {url}")


def fetch_event_list(eventapi_url: str) -> dict:
    return _get_json(eventapi_url)["events"]


def fetch_event_detail(summary: dict) -> dict:
    """The detail endpoint returns a single event keyed by its *full* name
    (e.g. GW190412_053044-v4 even when commonName is GW190412)."""
    events = _get_json(summary["jsonurl"])["events"]
    key = f"{summary['commonName']}-v{summary['version']}"
    return events[key] if key in events else next(iter(events.values()))


def prefilter_candidates(events: dict, far_threshold: float, mass2_floor: float,
                         far_fallback: dict | None = None) -> list[dict]:
    """FAR < threshold and eventapi point-estimate m2_source > floor (the
    point-estimate cut only avoids downloading obvious BNS/NSBH files; the
    real BBH cut is applied on the posterior in build_sample.py).

    `far_fallback` maps commonName -> FAR for events whose entry carries no
    FAR (the O1/O2 events re-released in GWTC-2.1-confident have far=None on
    the eventapi; their FARs come from GWTC-1-confident)."""
    out = []
    for ev in events.values():
        far = ev.get("far")
        if far is None and far_fallback and ev.get("commonName") in far_fallback:
            ev = dict(ev, far=float(far_fallback[ev["commonName"]]), far_source="fallback catalog")
            far = ev["far"]
        if far is None or far >= far_threshold:
            continue
        m2 = ev.get("mass_2_source")
        if m2 is not None and m2 <= mass2_floor:
            continue
        out.append(ev)
    out.sort(key=lambda e: (e["far"], e["commonName"]))
    return out


def resolve_preferred_pe(detail: dict, preferred_group: str) -> dict | None:
    """Find the parameters entry with pipeline_type == 'pe', matching
    waveform_family and is_preferred == True. Falls back to any preferred PE
    entry, then to any entry of the requested family."""
    params = detail.get("parameters", {})
    pe = [v for v in params.values() if v.get("pipeline_type") == "pe" and v.get("data_url")]
    for cond in (
        lambda v: v.get("waveform_family") == preferred_group and v.get("is_preferred"),
        lambda v: v.get("is_preferred"),
        lambda v: v.get("waveform_family") == preferred_group,
    ):
        for v in pe:
            if cond(v):
                return {"data_url": v["data_url"], "waveform_family": v.get("waveform_family")}
    return None


def remote_size(url: str, timeout=30) -> int | None:
    try:
        r = requests.head(url, headers=UA, timeout=timeout, allow_redirects=True)
        if r.ok and r.headers.get("Content-Length"):
            return int(r.headers["Content-Length"])
        r = requests.get(url, headers=UA, timeout=timeout, stream=True)
        r.close()
        return int(r.headers["Content-Length"]) if r.headers.get("Content-Length") else None
    except Exception:  # noqa: BLE001
        return None


def download_file(url: str, dest: Path, chunk_size=1 << 20, max_retries=5, timeout=180,
                  expected_size: int | None = None) -> Path:
    """Resumable download (HTTP Range on the .part file); skips if dest exists."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        if expected_size is None or dest.stat().st_size == expected_size:
            return dest
        logger.warning("%s has unexpected size %d != %d; re-downloading", dest, dest.stat().st_size, expected_size)
        dest.unlink()
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, max_retries + 1):
        try:
            have = tmp.stat().st_size if tmp.exists() else 0
            headers = dict(UA)
            if have > 0:
                headers["Range"] = f"bytes={have}-"
            with requests.get(url, headers=headers, stream=True, timeout=timeout) as r:
                if r.status_code == 416:  # already complete
                    pass
                else:
                    r.raise_for_status()
                    mode = "ab" if (have > 0 and r.status_code == 206) else "wb"
                    with open(tmp, mode) as f:
                        for chunk in r.iter_content(chunk_size=chunk_size):
                            if chunk:
                                f.write(chunk)
            size = tmp.stat().st_size
            if expected_size is not None and size != expected_size:
                raise IOError(f"size mismatch {size} != {expected_size}")
            tmp.rename(dest)
            logger.info("downloaded %s (%.1f MB)", dest.name, size / 1e6)
            return dest
        except Exception as e:  # noqa: BLE001
            logger.warning("download attempt %d/%d failed for %s: %s", attempt, max_retries, url, e)
            time.sleep(min(3**attempt, 60))
    raise RuntimeError(f"failed to download {url} after {max_retries} attempts")


def download_many(jobs: list[tuple[str, Path, int | None]], threads: int = 4) -> dict[Path, bool]:
    """jobs: [(url, dest, expected_size)]. Returns {dest: success}."""
    results = {}
    with ThreadPoolExecutor(max_workers=max(1, threads)) as ex:
        futs = {ex.submit(download_file, url, dest, expected_size=size): dest for url, dest, size in jobs}
        for fut in as_completed(futs):
            dest = futs[fut]
            try:
                fut.result()
                results[dest] = True
            except Exception as e:  # noqa: BLE001
                logger.error("giving up on %s: %s", dest, e)
                results[dest] = False
    return results
