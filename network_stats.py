#!/usr/bin/env python3

from glob import glob
import json

files = sorted(glob("data/*.json"))

for f in files:
    network = json.load(open(f))
    known_ids = set(n["id"] for n in network)
    edges = sum(sum(r in known_ids for r in n["referenced_works"]) for n in network)
    print(f"{f}: {len(network)} nodes, {edges} edges")