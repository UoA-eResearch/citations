"""Build the country x cause x year panel (plan section 3). Joins and labels only; no coverage is computed here.

Inputs (data/raw/ihme, see SOURCES.tsv):
  GBD 2021 deaths, level-3 causes, 2019 and 2021        IHME-GBD_2021_DATA-30d8ecb1-1.zip
  GBD 2021 population, 2019 and 2021                     IHME-GBD_2021_DATA-920e22ab-1.zip
  GBD 2023 deaths, level-3 causes, 2019                  IHME-GBD_2023_DATA-297c3461-1.zip
  GBD 2023 deaths, all causes, 2021                      IHME-GBD_2023_DATA-2b7b6033-1.zip
  GBD 2023 population, 2019 and 2021                     IHME-GBD_2023_DATA-798d936a-1.zip
All: deaths (number), all ages, both sexes, 204 countries and territories.

Panel: the 137 level-3 causes whose cause_id is present in both releases' level-3 lists, x 204 countries x 2 years.
Writes data/panel.parquet and data/cause_map.csv (cause, level-1 and level-2 parents, in which release)."""
import json
import zipfile
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
IHME = RUN / "data" / "raw" / "ihme"
META = RUN / "data" / "raw" / "meta"
FILES = {
    "d21": "IHME-GBD_2021_DATA-30d8ecb1-1.zip", "pop21": "IHME-GBD_2021_DATA-920e22ab-1.zip",
    "d23_2019": "IHME-GBD_2023_DATA-297c3461-1.zip", "d23_2021": "IHME-GBD_2023_DATA-2b7b6033-1.zip",
    "pop23": "IHME-GBD_2023_DATA-798d936a-1.zip",
}
KEY = ["location_id", "cause_id", "year"]


def read(k):
    f = IHME / FILES[k]
    return pd.read_csv(zipfile.ZipFile(f).open(f.name.replace(".zip", ".csv")))


def hierarchy(rnd):
    """cause_id -> (level, level-1 parent, level-2 parent) from the Results tool's public hierarchy (data/raw/meta)."""
    h = json.load(open(META / f"hierarchy_{rnd}.json"))["data"]["causes"]
    m = json.load(open(META / f"metadata_{rnd}.json"))["data"]["cause"]
    out = {}

    def walk(n, path):
        path = path + [n["id"]]
        out[n["id"]] = dict(level=len(path) - 1, l1=path[1] if len(path) > 1 else None, l2=path[2] if len(path) > 2 else None)
        for c in n["children"]:
            walk(c, path)
    for n in h:
        walk(n, [])
    names = {int(k): v["name"] for k, v in m.items()}
    return out, names


def main():
    d21 = read("d21")
    d23 = pd.concat([read("d23_2019"), read("d23_2021")])
    h21, n21 = hierarchy(2021)
    h23, n23 = hierarchy(2023)
    l3_21 = {c for c in d21.cause_id.unique() if h21.get(c, {}).get("level") == 3}
    l3_23 = {c for c in read("d23_2019").cause_id.unique() if h23.get(c, {}).get("level") == 3}
    shared = sorted(l3_21 & l3_23)
    cm = pd.DataFrame([dict(cause_id=c, cause_name=n21.get(c, n23.get(c)), in_2021=c in l3_21, in_2023=c in l3_23,
                            l1=(h21.get(c) or h23.get(c))["l1"], l2=(h21.get(c) or h23.get(c))["l2"]) for c in sorted(l3_21 | l3_23)])
    cm["l1_name"] = cm.l1.map(lambda c: n21.get(c, n23.get(c)))
    cm["l2_name"] = cm.l2.map(lambda c: n21.get(c, n23.get(c)))
    cm.to_csv(RUN / "data" / "cause_map.csv", index=False)
    a = d21[d21.cause_id.isin(shared)][KEY + ["location_name", "cause_name", "val", "lower", "upper"]]
    b = d23[d23.cause_id.isin(shared) & d23.year.isin([2019, 2021])][KEY + ["val", "lower", "upper"]]
    p = a.rename(columns={"val": "p21", "lower": "L21", "upper": "U21"}).merge(
        b.rename(columns={"val": "p23", "lower": "L23", "upper": "U23"}), on=KEY, how="inner", validate="one_to_one")
    pops = []
    for k, r in (("pop21", "21"), ("pop23", "23")):
        x = read(k)[["location_id", "year", "val"]].rename(columns={"val": f"pop{r}"})
        pops.append(x)
    p = p.merge(pops[0], on=["location_id", "year"], how="left").merge(pops[1], on=["location_id", "year"], how="left")
    p = p.merge(cm[["cause_id", "l1_name", "l2_name"]], on="cause_id", how="left")
    p.to_parquet(RUN / "data" / "panel.parquet", index=False)
    print(f"{len(p)} cells = {p.location_id.nunique()} countries x {p.cause_id.nunique()} causes x {p.year.nunique()} years;",
          "missing:", int(p[["p21", "L21", "U21", "p23", "L23", "U23", "pop21", "pop23"]].isna().sum().sum()))
    print("level-3 causes only in 2021:", list(cm[cm.in_2021 & ~cm.in_2023].cause_name), "| only in 2023:", list(cm[~cm.in_2021 & cm.in_2023].cause_name))


if __name__ == "__main__":
    main()
