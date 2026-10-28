"""List every bacterial organism group's latest metadata file on the Pathogen Detection FTP (plan section 1).

  list_groups.py -> data/groups.csv (group, file, size_label, url)
"""
import re
import urllib.request
from pathlib import Path

import pandas as pd

RUN = Path(__file__).resolve().parents[1]
BASE = "https://ftp.ncbi.nlm.nih.gov/pathogen/Results/"
SKIP = {"BioProject_Hierarchy", "Candidozyma_auris"}       # not a bacterial organism group
get = lambda u: urllib.request.urlopen(u, timeout=120).read().decode("utf-8", "replace")
groups = [g.strip("/") for g in re.findall(r'href="([A-Za-z0-9_]+/)"', get(BASE)) if g.strip("/") not in SKIP]
rows = []
for g in groups:
    try:
        x = get(f"{BASE}{g}/latest_snps/Metadata/")
    except Exception as e:
        rows.append((g, None, None, None)); continue
    m = re.search(r'href="(PDG[0-9.]+\.metadata\.tsv)">[^<]*</a>\s+\S+\s+\S+\s+(\S+)', x)
    rows.append((g, m.group(1), m.group(2), f"{BASE}{g}/latest_snps/Metadata/{m.group(1)}") if m else (g, None, None, None))
d = pd.DataFrame(rows, columns=["group", "file", "size_label", "url"])
d.to_csv(RUN / "data" / "groups.csv", index=False)
print(len(d), "groups;", d.file.notna().sum(), "with metadata"); print(d.dropna().size_label.value_counts().head(3).to_dict())
print(d[d.file.notna()].sort_values("size_label").tail(8).to_string(index=False))
