#!/usr/bin/env python3

import pandas as pd
import json
import requests
import sys

id = sys.argv[1]

def req(query):
    r = requests.post("https://api.labs.cognitive.microsoft.com/academic/v1.0/evaluate", json={
        "expr": query,
        "model": "latest",
        "count": 10000,
        "attributes": "Id,DN,D,CC,ECC,DOI,AA.DAuN,AA.AuId,AA.DAfN,AA.AfId,F.DFN,F.FId,J.JN,J.JId,RId,S",
    }, headers={
        "Ocp-Apim-Subscription-Key": "2e889aa457224e7c94b9517d890f29ae",
        "Content-Type": "application/json"
    })
    return r.json()

main = req(f"Id={id}")["entities"]
print(main)

citations = req(f"RId={id}")["entities"]
print(len(citations))

known_ids = set([node["Id"] for node in citations])
print(len(known_ids))
nodes = {}
for e in main + citations:
    nodes[e["Id"]] = {
        "id": e["Id"],
        "date_published": e["D"],
        "citation_count": e["CC"],
        "estimated_citation_count": e["ECC"],
        "title": e["DN"],
        "authors": e["AA"],
        "fields": e.get("F"),
        "journal": e.get("J"),
        "DOI": e.get("DOI"),
        "source": e.get("S"),
        "references": [rid for rid in e.get("RId",[]) if rid in known_ids]
    }
nodes = list(nodes.values())

with open("data.json", "w") as f:
    json.dump(nodes, f)
