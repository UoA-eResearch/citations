"""Assign each site's sector from its EARLIEST eligible pre-period snapshot, by fixed multilingual marker rules
(plan section 5). Markers are searched in the page's visible text and in href / class / id attribute values.

  in scope (the European Accessibility Act's consumer services):
    ecommerce  shopping-cart / basket / checkout markers in links or attributes, in 14 EU languages and English
    banking    online-banking markers, or a bank name in the domain
    transport  passenger-transport markers (timetables, flights, train / bus tickets)
    telecom    mobile / broadband tariff markers, e-book markers
  A site is in scope if any one sector has >= 2 distinct markers (or a bank-name domain); out of scope if no sector
  has any marker; otherwise ambiguous and excluded. Sectors themselves are reported, not used separately.
  Public bodies (government, parliament, municipality, university, police), identified from the domain labels or the
  page title, are "public" and excluded first: the Web Accessibility Directive has covered them since 2018-2020, and
  the frame's label filter misses names such as bundestag.de or uni-hamburg.de (deviations D2).
Writes data/sector.csv.

D9 (after review): a site is labelled from its earliest pre-period snapshot with at least MIN_VISIBLE visible
characters, not simply its earliest snapshot. The draft labelled any page with no marker "out of scope", including
redirect stubs, language choosers and empty captures, which put treated firms (drei.at, vodafone.nl, csob.cz) in the
control group. A site with no such snapshot is "unclassifiable" and excluded. Two marker leaks are also closed:
"basket" now needs word boundaries (it matched "Basketball"), and "spar" is dropped from the bank-domain pattern (it
matched valsparpaint.co.uk); "sparkasse" still matches.
"""
import gzip
import json
import re
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
MIN_VISIBLE = 300          # visible characters a snapshot needs before its markers are trusted (D9)
PRE_END = "20250628"       # the Act applied from 28 June 2025; labelling snapshots must predate it
M = {
    "ecommerce": [r"\bcart\b", r"\bbaskets?\b", r"checkout", r"warenkorb", r"\bkasse\b", r"panier", r"carrello", r"carrito",
                  r"winkelwagen", r"winkelmand", r"koszyk", r"varukorg", r"ostoskori", r"indk[øo]bskurv", r"carrinho",
                  r"ko[šs][íi]k", r"add[-_ ]to[-_ ]cart", r"in den warenkorb", r"ajouter au panier", r"aggiungi al carrello",
                  r"a[ñn]adir al carrito", r"dodaj do koszyka", r"l[äa]gg i varukorgen"],
    "banking": [r"online[- ]?banking", r"net ?bank", r"internet ?banking", r"e-banking", r"home ?banking",
                r"banque en ligne", r"banca online", r"banca en l[íi]nea", r"bankowo[śs][ćc] internetowa", r"n[äa]tbank",
                r"verkkopankki", r"internetov[ée] bankovnictv[íi]", r"\biban\b", r"girokonto", r"compte courant",
                r"conto corrente", r"cuenta corriente", r"rachunek osobisty"],
    "transport": [r"timetable", r"fahrplan", r"horaires", r"\borari[oa]", r"horarios?", r"dienstregeling",
                  r"rozk[łl]ad jazdy", r"tidtabell", r"aikataulu", r"k[øo]replan", r"j[íi]zdn[íi] [řr][áa]d",
                  r"\bflights?\b", r"fl[üu]ge", r"\bvols\b", r"\bvoli\b", r"vuelos", r"vluchten", r"\bloty\b",
                  r"train tickets?", r"bus tickets?", r"fahrkarten?", r"billets? de train", r"biglietti"],
    "telecom": [r"mobile plans?", r"handytarif", r"tarif[ea]?s? mobil", r"forfait", r"abbonamento", r"tarifa m[óo]vil",
                r"\bprepaid\b", r"sim[- ]?kart", r"carte sim", r"broadband", r"glasfaser", r"\bfibr[ea]\b", r"\be-?books?\b",
                r"h[öo]rb[üu]ch"],
}
BANK_DOMAIN = re.compile(r"bank|banque|banca|banco|sparkasse|volksbank|raiffeisen|kasa", re.I)
RX = {s: [re.compile(p, re.I) for p in ps] for s, ps in M.items()}
PUBLIC_DOMAIN = re.compile(r"(^|[.-])(gov|govt|bund|bundes\w*|landtag|uni|univ|tu|stadt|gemeente|kommune|gmina|polizei|"
                           r"politie|policja)([.-]|$)", re.I)
PUBLIC_TITLE = re.compile(r"ministeri|minist[eè]re|bundes(amt|ministerium|tag|rat|regierung|agentur|anstalt)|landtag|"
                          r"landesregierung|regierung|gouvernement|governo|gobierno|rijksoverheid|overheid|parlament|"
                          r"parliament|assembl[ée]e nationale|senato|senado|\bsejm\b|riksdag|eduskunta|folketing|"
                          r"gemeinde|kommune|municipality|ayuntamiento|comune di|\bgmina\b|kommun\b|\bkunta\b|mairie|"
                          r"ville de|city council|county council|universit|hochschule|yliopisto|uniwersytet|politechnika|"
                          r"polytechnic|polizei|politie|policja|gendarmerie|\bpolice\b", re.I)


def text_and_attrs(html):
    attrs = " ".join(re.findall(r'(?:href|class|id)\s*=\s*"([^"]{0,300})"', html))
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", text)[:200000] + " " + attrs


def visible_chars(html):
    body = re.sub(r"<script.*?</script>|<style.*?</style>|<noscript.*?</noscript>", " ", html, flags=re.S | re.I)
    return len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip())


def classify(domain, html):
    t = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if PUBLIC_DOMAIN.search(domain.rsplit(".", 2 if domain.count(".") >= 2 and domain.split(".")[-2] in ("co", "com") else 1)[0]) \
            or (t and PUBLIC_TITLE.search(t.group(1))):
        return "public", None, {}
    s = text_and_attrs(html)
    hits = {k: sum(bool(r.search(s)) for r in rx) for k, rx in RX.items()}
    if BANK_DOMAIN.search(domain.split(".")[0]):
        hits["banking"] = max(hits["banking"], 2)
    strong = [k for k, v in hits.items() if v >= 2]
    if strong:
        return "in_scope", max(strong, key=lambda k: hits[k]), hits
    if not any(hits.values()):
        return "out_of_scope", None, hits
    return "ambiguous", None, hits


def main():
    rows = [json.loads(l) for l in open(RUN / "data" / "cdx" / "eligible.jsonl")]
    out = []
    for r in rows:
        chosen, html, seen_any = None, None, False
        for ts in sorted(r["snapshots"]):
            if ts >= PRE_END:
                break
            f = RUN / "data" / "html" / r["domain"] / f"{ts}.html.gz"
            if not f.exists():
                continue
            seen_any = True
            h = gzip.decompress(f.read_bytes()).decode("utf-8", "ignore")
            if visible_chars(h) >= MIN_VISIBLE:
                chosen, html = ts, h
                break
        if chosen is None:
            out.append(dict(domain=r["domain"], status="unclassifiable" if seen_any else "no_html"))
            continue
        cls, sec, hits = classify(r["domain"], html)
        out.append(dict(domain=r["domain"], status=cls, sector=sec, first=chosen, visible=visible_chars(html),
                        **{f"m_{k}": v for k, v in hits.items()}))
    import pandas as pd
    pd.DataFrame(out).to_csv(RUN / "data" / "sector.csv", index=False)
    print(pd.DataFrame(out).status.value_counts().to_dict())


if __name__ == "__main__":
    sys.exit(main())
