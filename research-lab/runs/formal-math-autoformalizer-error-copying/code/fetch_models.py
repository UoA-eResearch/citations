"""Download the autoformalizer weights (ungated; no token). Records the resolved commit of each repo in
data/models/REVISIONS.tsv. Preparation only: no sampling."""
import sys
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

RUN = Path(__file__).resolve().parents[1]
REPOS = ["AI-MO/Kimina-Autoformalizer-7B", "Goedel-LM/Goedel-Formalizer-V2-8B", "FrenzyMath/Herald_translator",
         "Qwen/Qwen2.5-7B-Instruct"]
api = HfApi()
out = RUN / "data" / "models"
for repo in (sys.argv[1:] or REPOS):
    sha = api.model_info(repo).sha
    p = snapshot_download(repo, revision=sha, local_dir=out / repo.split("/")[1], token=False,
                          allow_patterns=["*.json", "*.safetensors", "*.model", "*.txt", "*.py", "*.jinja", "tokenizer*"])
    with open(out / "REVISIONS.tsv", "a") as f:
        f.write(f"{repo}\t{sha}\t{p}\n")
    print(repo, sha, flush=True)
print("MODELS DONE")
