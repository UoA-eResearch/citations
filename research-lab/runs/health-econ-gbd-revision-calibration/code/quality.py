"""Country-level data-quality covariates (plan section 4). Uses documents only, never GBD estimates.

1. WHO GHE 2021 methods, Table 4.1 (pages 9-14): quality class of each country's vital registration (VR) data (high,
   medium, low, very low), completeness and usability ranges, years in the WHO Mortality Database. Countries not in the
   table are classed `none` ("not assessed in WHO Table 4.1"). Table 4.1 covers only WHO's GHE scope (Member States
   over 90,000 people, plus Puerto Rico, Taiwan and Palestine), so `none` includes some countries that do have death
   registration (erratum, deviations.md D3; see code/review_checks.py).
2. GBD 2021 causes-of-death appendix 1, pages 76-78: percentage of VR deaths redistributed from garbage codes, by
   country-year (1980-2021). Covariate: mean over 2010-2021 of the years present; countries not listed have no VR.

Writes data/quality.parquet (one row per GBD country, 204 rows) and data/quality_crosswalk.csv (name matching)."""
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pdfplumber
from pypdf import PdfReader

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"

# WHO / GBD-appendix name -> GBD location_name (only where they differ)
ALIAS = {
    "Bolivia": "Bolivia (Plurinational State of)", "Iran": "Iran (Islamic Republic of)",
    "Venezuela": "Venezuela (Bolivarian Republic of)", "Syria": "Syrian Arab Republic", "Russia": "Russian Federation",
    "Moldova": "Republic of Moldova", "South Korea": "Republic of Korea", "Korea": "Republic of Korea",
    "Taiwan (province of China)": "Taiwan (Province of China)", "Taiwan": "Taiwan (Province of China)",
    "Turkey": "Türkiye", "Virgin Islands": "United States Virgin Islands", "The Bahamas": "Bahamas",
    "The Gambia": "Gambia", "Gambia (The)": "Gambia", "Brunei": "Brunei Darussalam", "Laos": "Lao People's Democratic Republic",
    "Vietnam": "Viet Nam", "Macedonia": "North Macedonia", "Czech Republic": "Czechia", "Swaziland": "Eswatini",
    "Cape Verde": "Cabo Verde", "Federated States of Micronesia": "Micronesia (Federated States of)",
    "Micronesia": "Micronesia (Federated States of)", "Tanzania": "United Republic of Tanzania",
    "United States": "United States of America", "USA": "United States of America", "UK": "United Kingdom",
    "Ivory Coast": "Côte d'Ivoire", "Cote d'Ivoire": "Côte d'Ivoire", "Palestine": "Palestine",
    "Occupied Palestinian Territory": "Palestine", "Netherlands (Kingdom of the)": "Netherlands",
    "Puerto Rico": "Puerto Rico", "Saint Vincent and the Grenadines": "Saint Vincent and the Grenadines",
    "Republic of Moldova": "Republic of Moldova", "Kyrgyz Republic": "Kyrgyzstan", "Cyprusf": "Cyprus", "São Tomé and Príncipe": "Sao Tome and Principe",
    "The former Yugoslav Republic of Macedonia": "North Macedonia",
}


def gbd_countries():
    z = zipfile.ZipFile(RAW / "ihme" / "IHME-GBD_2021_DATA-920e22ab-1.zip")
    p = pd.read_csv(z.open("IHME-GBD_2021_DATA-920e22ab-1.csv"))
    return p[["location_id", "location_name"]].drop_duplicates().reset_index(drop=True)


def norm(s):
    return re.sub(r"\s+", " ", str(s).replace("\n", " ")).strip()


def match(name, gbd_names):
    n = norm(name)
    n = ALIAS.get(n, n)
    if n in gbd_names:
        return n
    low = {g.lower(): g for g in gbd_names}
    return low.get(n.lower())


def who_table():
    rows = []
    with pdfplumber.open(RAW / "who" / "ghe2021_cod_methods.pdf") as pdf:
        for i in range(8, 14):
            for tb in pdf.pages[i].extract_tables():
                for r in tb:
                    if not r or not r[0] or r[3] not in ("high", "medium", "low", "very low"):
                        continue
                    pct = lambda s: float(s.rstrip("%")) / 100 if s and s.strip().endswith("%") else np.nan  # noqa: E731
                    rows.append(dict(who_name=norm(r[0]), years_in_mdb=norm(r[1]), years_used=norm(r[2]), who_quality=r[3],
                                     completeness_min=pct(r[4]), completeness_max=pct(r[5]), usability_min=pct(r[6]),
                                     usability_max=pct(r[7]), used_for_ghe=norm(r[8]), excluded_reason=norm(r[9])))
    return pd.DataFrame(rows)


def garbage_table():
    """Appendix 1 pages 76-78 (Appendix table of the percentage of VR deaths redistributed from garbage codes). Blank
    cells collapse in plain text, so word positions are used: the year header is rotated text (read reversed, e.g.
    '0891' = 1980); each value is assigned to the nearest year column by x, and to the nearest country-name row above
    it by y (values sit about 2 pt below the name's top)."""
    out = []
    cols = None
    with pdfplumber.open(RAW / "appendix" / "gbd2021_cod_appendix1_mmc1.pdf") as pdf:
        for i in (75, 76, 77):
            words = pdf.pages[i].extract_words(keep_blank_chars=False, use_text_flow=False)
            hdr = [w for w in words if re.fullmatch(r"\d{4}", w["text"]) and re.fullmatch(r"(19[89]\d|20[012]\d)", w["text"][::-1])]
            if len(hdr) > 30:
                cols = {int(w["text"][::-1]): (w["x0"] + w["x1"]) / 2 for w in hdr}
            hdr_ids = {id(w) for w in hdr}
            x_first = min(cols.values()) - 6
            name_words = [w for w in words if w["x1"] <= x_first and id(w) not in hdr_ids]
            rows = {}
            for w in name_words:
                rows.setdefault(round(w["top"], 0), []).append(w)
            row_tops = sorted(rows)
            names = {t: " ".join(w["text"] for w in sorted(rows[t], key=lambda w: w["x0"])) for t in row_tops}
            yc = np.array(list(cols.keys()))
            xc = np.array(list(cols.values()))
            for v in words:
                if v["x0"] < x_first or id(v) in hdr_ids or not re.fullmatch(r"\d{1,3}", v["text"]):
                    continue
                above = [t for t in row_tops if 0 <= v["top"] - t <= 5]
                if not above:
                    continue
                name = names[max(above)]
                if name.startswith(("Country", "Cells", "Color", "mortality", "cells")):
                    continue
                x = (v["x0"] + v["x1"]) / 2
                out.append(dict(gbd_app_name=name, year=int(yc[np.argmin(np.abs(xc - x))]), garbage_pct=float(v["text"]), page=i + 1))
    return pd.DataFrame(out), cols


def main():
    g = gbd_countries()
    names = set(g.location_name)
    w = who_table()
    w["location_name"] = [match(n, names) for n in w.who_name]
    gb, cols = garbage_table()
    gb["location_name"] = [match(n, names) for n in gb.gbd_app_name]
    xw = pd.concat([w[["who_name", "location_name"]].rename(columns={"who_name": "source_name"}).assign(source="WHO GHE Table 4.1"),
                    gb[["gbd_app_name", "location_name"]].drop_duplicates().rename(columns={"gbd_app_name": "source_name"})
                    .assign(source="GBD 2021 appendix garbage table")])
    xw.to_csv(RUN / "data" / "quality_crosswalk.csv", index=False)
    unmatched = xw[xw.location_name.isna()]
    print("WHO rows:", len(w), "| unmatched WHO:", list(w[w.location_name.isna()].who_name))
    print("garbage rows:", len(gb), "countries:", gb.gbd_app_name.nunique(), "| unmatched:", sorted(unmatched[unmatched.source.str.startswith("GBD")].source_name))
    print("year columns found:", min(cols), "-", max(cols), len(cols))
    gm = gb[gb.year.between(2010, 2021) & gb.location_name.notna()].groupby("location_name").garbage_pct.agg(["mean", "size"])
    q = g.merge(w.dropna(subset=["location_name"]).drop_duplicates("location_name"), on="location_name", how="left")
    q["who_quality"] = q.who_quality.fillna("none")
    q["usability_mid"] = (q.usability_min + q.usability_max) / 2
    q = q.merge(gm.rename(columns={"mean": "garbage_pct_2010_21", "size": "garbage_years_2010_21"}), left_on="location_name",
                right_index=True, how="left")
    q["quality_group"] = q.who_quality.map({"high": "high", "medium": "medium", "low": "low", "very low": "low", "none": "low"})
    q.to_parquet(RUN / "data" / "quality.parquet", index=False)
    print(q.who_quality.value_counts().to_dict(), "| quality_group:", q.quality_group.value_counts().to_dict())
    print("countries with GBD garbage data 2010-21:", int(q.garbage_pct_2010_21.notna().sum()))


if __name__ == "__main__":
    main()
