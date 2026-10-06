"""Download the two generators added in deviation D2 (Gemma 4 31B-it as the closest open relative of Gemini;
gpt-oss-120b as an OpenAI-style generator) and append their exact revisions to generator_revisions.json."""
import json
import os
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

RUN = Path(__file__).resolve().parents[1]
token = (Path.home() / ".config" / "hf" / "token").read_text().strip()
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
f = RUN / "results" / "tables" / "generator_revisions.json"
revs = json.load(open(f))
for repo, pats in [("google/gemma-4-31B-it", ["*.json", "*.safetensors", "*.txt", "*.model", "tokenizer*", "*.jinja"]),
                   ("openai/gpt-oss-120b", ["*.json", "model-*.safetensors", "*.txt", "tokenizer*", "*.jinja", "chat_template*"])]:
    info = HfApi().model_info(repo, token=token)
    snapshot_download(repo, revision=info.sha, local_dir=RUN / "data" / "models" / repo.split("/")[1], token=token, allow_patterns=pats)
    revs[repo] = info.sha
    json.dump(revs, open(f, "w"), indent=1)
    print(repo, info.sha, flush=True)
