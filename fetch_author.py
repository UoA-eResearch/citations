#!/usr/bin/env python3

import pandas as pd
import json
import requests
from pprint import pprint
import sys
from tqdm.auto import tqdm

id = sys.argv[1]

params = {
    "per-page": 200,
    "mailto": "nick.young@auckland.ac.nz"
}

response = requests.get("https://api.openalex.org/works?filter=author.id:" + id, params=params).json()
pprint(response["meta"])
seed_works = response["results"]
print(len(seed_works))

citing_works = []

for w in tqdm(seed_works):
    response = requests.get(w["cited_by_api_url"], params=params).json()
    pprint(response["meta"])
    citing_works.extend(response["results"])

works = seed_works + citing_works
print(len(works))

with open("data.json", "w") as f:
    json.dump(works, f)