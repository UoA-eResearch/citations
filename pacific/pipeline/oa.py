"""Small OpenAlex API client with an on-disk response cache.

The API key is read from ~/.config/openalex/api_key (or $OPENALEX_API_KEY) and is never
written to the cache, logs or outputs. Every GET is cached by its URL-without-key, so
re-running the pipeline costs nothing once a response has been fetched.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

BASE = "https://api.openalex.org"
CACHE = Path(os.environ.get("PACIFIC_CACHE", "/mnt/data/ubuntu/pacific-cache"))
MAILTO = "nick.young@auckland.ac.nz"


def _key():
    k = os.environ.get("OPENALEX_API_KEY")
    if k:
        return k.strip()
    p = Path.home() / ".config/openalex/api_key"
    return p.read_text().strip() if p.exists() else None


_session = requests.Session()
_session.headers["User-Agent"] = f"va-atlas (mailto:{MAILTO})"
_spent = {"usd": 0.0, "calls": 0}


def get(path, params=None, *, use_cache=True):
    """GET BASE+path with params; returns parsed JSON. Cached on disk by URL (without key)."""
    params = dict(params or {})
    public = BASE + path + ("?" + urlencode(sorted(params.items())) if params else "")
    h = hashlib.sha1(public.encode()).hexdigest()
    f = CACHE / h[:2] / (h + ".json")
    if use_cache and f.exists():
        return json.loads(f.read_text())
    key = _key()
    if key:
        params["api_key"] = key
    else:
        params["mailto"] = MAILTO
    for attempt in range(7):
        try:
            r = _session.get(BASE + path, params=params, timeout=60)
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 200:
            data = r.json()
            _spent["calls"] += 1
            _spent["usd"] += float((data.get("meta") or {}).get("cost_usd") or 0)
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(json.dumps(data))
            return data
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(min(60, 2 ** attempt))
            continue
        if r.status_code == 404:
            return None
        raise RuntimeError(f"OpenAlex {r.status_code} for {public}: {r.text[:300]}")
    raise RuntimeError(f"OpenAlex: retries exhausted for {public}")


def paginate(path, params, *, cap=100000):
    """Cursor-paginate a list endpoint; yields result dicts."""
    params = dict(params)
    params["per_page"] = 100
    cursor, n = "*", 0
    while cursor and n < cap:
        params["cursor"] = cursor
        page = get(path, params)
        if not page:
            return
        for r in page["results"]:
            yield r
            n += 1
            if n >= cap:
                return
        cursor = page["meta"].get("next_cursor")
        if not page["results"]:
            return


def spent():
    return dict(_spent)


def short(oid):
    return str(oid or "").rsplit("/", 1)[-1]
