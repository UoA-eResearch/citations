#!/usr/bin/env python3

import pandas as pd
import json
import requests
from pprint import pprint
import sys
from tqdm.auto import tqdm
import time

authors = {
    "Dan": "a5055846959",
    "Mark": "A4341954224",
    "Giovanni": "A4358613644",
    "Quinn": "A2899969917"
}

author = sys.argv[1]
id = authors[author]

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
    while True:
        try:
            response = requests.get(w["cited_by_api_url"], params=params).json()
        except Exception as e:
            print(f'Got {e} when requesting {w["cited_by_api_url"]}, retrying')
            time.sleep(1)
        break
    pprint(response["meta"])
    citing_works.extend(response["results"])

works = seed_works + citing_works
print(len(works))

with open(f"data/{author}.json", "w") as f:
    json.dump(works, f)
