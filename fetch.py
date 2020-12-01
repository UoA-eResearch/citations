#!/usr/bin/env python3

import pandas as pd
import json
import requests
from pprint import pprint

def req(query):
    r = requests.post("https://api.labs.cognitive.microsoft.com/academic/v1.0/evaluate", json={
        "expr": query,
        "model": "latest",
        "count": 10000,
        "attributes": "Id,Ty,DN,Y,D,CC,ECC,DOI,AA.DAuN,AA.AuId,AA.DAfN,AA.AfId,F.DFN,F.FId,J.JN,J.JId,Pt,RId",
    }, headers={
        "Ocp-Apim-Subscription-Key": "2e889aa457224e7c94b9517d890f29ae",
        "Content-Type": "application/json"
    })
    return r.json()

papers = req(f"Composite(AA.AuId=2172299206)")["entities"] # Fetch all of Giovanni's papers
print(len(papers))
ids = [node["Id"] for node in papers] # Extract just paper ids
ids = ",".join([f"RId={id}" for id in ids]) # Create a query referencing each paper id

citations = req(f"Or({ids})")["entities"] # Request all papers citing any of these 181 ids
print(len(citations))

known_ids = set([node["Id"] for node in papers + citations])
print(len(known_ids))
nodes = {}
for e in papers + citations:
    nodes[e["Id"]] = {
        "id": e["Id"],
        "date_published": e["D"],
        "citation_count": e["CC"],
        "estimated_citation_count": e["ECC"],
        "title": e["DN"],
        "authors": e["AA"],
        "fields": e.get("F"),
        "references": [rid for rid in e.get("RId",[]) if rid in known_ids]
    }
nodes = list(nodes.values())

with open("data.json", "w") as f:
    json.dump(nodes, f)