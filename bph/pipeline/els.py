"""Small Elsevier (Scopus + SciVal) API client with an on-disk response cache.

The API key is read from ~/.config/elsevier/api_key (or $ELSEVIER_API_KEY) and is sent only in the
X-ELS-APIKey header: it never appears in cached URLs, files or logs. Access depends on the
University's Scopus/SciVal subscription (calls are entitled from the University network).

Quotas are weekly and per API (SciVal 5,000; Scopus Search 20,000; Abstract Retrieval 10,000 at the
time of writing). Every GET is cached by its URL, so re-running the pipeline costs nothing once a
response has been fetched. Data from these APIs is for University-internal use under the
subscription: do not publish it openly.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

BASE = "https://api.elsevier.com"
CACHE = Path(os.environ.get("BPH_CACHE", "/mnt/data/ubuntu/bph-cache")) / "els"
UOA_SCIVAL = 212005      # SciVal institution ID, The University of Auckland
UOA_SCOPUS = 60005686    # Scopus affiliation ID, The University of Auckland


def _key():
    k = os.environ.get("ELSEVIER_API_KEY")
    if k:
        return k.strip()
    return (Path.home() / ".config/elsevier/api_key").read_text().strip()


def _strip_links(x):
    """Drop the 'link' / 'prism:url' navigation fields (they repeat request URLs)."""
    if isinstance(x, dict):
        return {k: _strip_links(v) for k, v in x.items() if k not in ("link", "prism:url")}
    if isinstance(x, list):
        return [_strip_links(v) for v in x]
    return x


_session = requests.Session()
_session.headers["Accept"] = "application/json"
_stats = {"calls": 0, "cached": 0, "remaining": {}}


def get(path, params=None, *, use_cache=True):
    """GET BASE+path with params; returns parsed JSON (None on 404). Cached on disk by URL."""
    params = dict(params or {})
    public = BASE + path + ("?" + urlencode(sorted(params.items())) if params else "")
    h = hashlib.sha1(public.encode()).hexdigest()
    f = CACHE / h[:2] / (h + ".json")
    if use_cache and f.exists():
        _stats["cached"] += 1
        return json.loads(f.read_text())
    key = _key()
    for attempt in range(7):
        try:
            r = _session.get(BASE + path, params=params, headers={"X-ELS-APIKey": key}, timeout=90)
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        api = path.split("/")[2] if path.startswith("/analytics") else path.split("/")[2] + "/" + path.split("/")[3]
        if r.headers.get("X-RateLimit-Remaining"):
            _stats["remaining"][api] = int(r.headers["X-RateLimit-Remaining"])
        if r.status_code == 200:
            # SciVal echoes the key inside its "link" URLs: scrub it before anything is parsed or cached.
            data = _strip_links(json.loads(r.text.replace(key, "")))
            _stats["calls"] += 1
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(data))
            return data
        if r.status_code == 404:
            return None
        if r.status_code == 429 and r.headers.get("X-RateLimit-Remaining") == "0":
            raise RuntimeError(f"Elsevier weekly quota exhausted for {api}; resets at {r.headers.get('X-RateLimit-Reset')}")
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(60, 2 ** attempt))
            continue
        raise RuntimeError(f"Elsevier {r.status_code} for {public}: {r.text[:300].replace(key, '<key>')}")
    raise RuntimeError(f"Elsevier: retries exhausted for {public}")


def stats():
    return json.loads(json.dumps(_stats))
