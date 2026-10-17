"""RxNorm normalisation via RxNav (open API; gentle: about 4 requests/s, cached in data/rxnav_cache.json).
ingredients(name) -> list of ingredient names (IN) for a drug string; brands(ingredient) -> brand names (BN)."""
import json
import re
import time
from pathlib import Path

import requests

RUN = Path(__file__).resolve().parents[1]
CACHE_F = RUN / "data" / "rxnav_cache.json"
CACHE = json.load(open(CACHE_F)) if CACHE_F.exists() else {}
S = requests.Session(); S.headers["User-Agent"] = "research-lab pharmacovigilance study (mailto:noreply@anthropic.com)"


def _get(url, **params):
    key = url + "?" + json.dumps(params, sort_keys=True)
    if key in CACHE:
        return CACHE[key]
    for k in range(4):
        try:
            r = S.get(url, params=params, timeout=60)
            if r.status_code == 200:
                CACHE[key] = r.json(); time.sleep(0.25); return CACHE[key]
        except Exception:  # noqa: BLE001
            pass
        time.sleep(5 * (k + 1))
    return None


def save():
    json.dump(CACHE, open(CACHE_F, "w"))


def clean(name):
    s = re.sub(r"\([^)]*\)", " ", name or "")           # drop parenthesised abbreviations
    return re.sub(r"\s+", " ", s).strip()


def ingredients(name):
    """Ingredient names for a drug string, or [] if it cannot be mapped."""
    s = clean(name)
    if not s:
        return []
    j = _get("https://rxnav.nlm.nih.gov/REST/rxcui.json", name=s, search=2)
    ids = (j or {}).get("idGroup", {}).get("rxnormId") or []
    if not ids:
        j = _get("https://rxnav.nlm.nih.gov/REST/approximateTerm.json", term=s, maxEntries=1)
        cands = (j or {}).get("approximateGroup", {}).get("candidate") or []
        ids = [cands[0]["rxcui"]] if cands and float(cands[0].get("score", 0)) >= 60 else []
    if not ids:
        return []
    j = _get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{ids[0]}/related.json", tty="IN")
    groups = (j or {}).get("relatedGroup", {}).get("conceptGroup") or []
    return sorted({c["name"].lower() for g in groups for c in g.get("conceptProperties") or []})


def brands(ingredient):
    j = _get("https://rxnav.nlm.nih.gov/REST/rxcui.json", name=ingredient, search=0)
    ids = (j or {}).get("idGroup", {}).get("rxnormId") or []
    if not ids:
        return []
    j = _get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{ids[0]}/related.json", tty="BN")
    groups = (j or {}).get("relatedGroup", {}).get("conceptGroup") or []
    return sorted({c["name"].lower() for g in groups for c in g.get("conceptProperties") or []})
