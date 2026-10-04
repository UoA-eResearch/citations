"""Structural statistics of the peaked circuits (no attack, no answers): CZ count, distinct pairs, CZ per qubit,
interaction-graph degree, and similarity of the two halves' interaction graphs (degree-sequence correlation)."""
import re
from collections import Counter
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

RUN = Path(__file__).resolve().parents[1]
FILES = {"P9": "peaked_circuit_P9_Hqap_56x1917.qasm", "P11": "peaked_circuit_P11_Hqap_98x1999.qasm",
         "P12": "peaked_circuit_P12_Hqap_98x2457.qasm"}
rows = []
for inst, f in FILES.items():
    txt = (RUN / "data" / "raw" / f).read_text()
    n = int(re.search(r"qreg q\[(\d+)\]", txt).group(1))
    cz = [tuple(sorted(map(int, m))) for m in re.findall(r"(?:cz|rzz\([^)]*\))\s+q\[(\d+)\]\s*,\s*q\[(\d+)\]", txt)]
    pairs = Counter(cz)
    half = len(cz) // 2
    g1, g2 = nx.Graph(), nx.Graph()
    g1.add_edges_from(cz[:half]); g2.add_edges_from(cz[half:])
    d1 = sorted(dict(g1.degree()).values()); d2 = sorted(dict(g2.degree()).values())
    m = min(len(d1), len(d2))
    rows.append(dict(instance=inst, qubits=n, cz=len(cz), distinct_pairs=len(pairs), cz_per_qubit=2 * len(cz) / n,
                     max_repeat_pair=max(pairs.values()), repeated_pairs=sum(v > 1 for v in pairs.values()),
                     mean_degree=np.mean(list(dict(nx.Graph(list(pairs)).degree()).values())),
                     halves_degree_corr=float(np.corrcoef(d1[:m], d2[:m])[0, 1]),
                     halves_shared_pairs=len(set(cz[:half]) & set(cz[half:]))))
df = pd.DataFrame(rows)
df.to_csv(RUN / "results" / "tables" / "structure.csv", index=False)
print(df.round(3).to_string(index=False))
