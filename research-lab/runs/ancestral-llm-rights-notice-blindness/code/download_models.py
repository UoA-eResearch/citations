"""Download the three audited models at pinned revisions (safetensors, configs, tokenizer only)."""
import sys
from pathlib import Path

from huggingface_hub import snapshot_download

RUN = Path(__file__).resolve().parents[1]
MODELS = {
    "Qwen/Qwen3-32B": "9216db5781bf21249d130ec9da846c4624c16137",
    "allenai/OLMo-2-1124-13B-Instruct": "3a5c85baefbb1896a54d56fe2e76c0395627ddf4",
    "mistralai/Mistral-Small-24B-Instruct-2501": "9527884be6e5616bdd54de542f9ae13384489724",
}

if __name__ == "__main__":
    for repo, rev in MODELS.items():
        p = snapshot_download(repo, revision=rev, local_dir=RUN / "data" / "models" / repo.split("/")[1],
                              allow_patterns=["*.safetensors", "*.json", "tokenizer*", "*.model", "*.txt", "*.jinja"],
                              max_workers=8)
        print("done", repo, rev, p, flush=True)
    sys.exit(0)
