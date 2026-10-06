"""Download the benchmarks, the training corpora not already on disk, and the three prover models, recording exact
revisions in results/tables/revisions.json. Corpora already downloaded for the vacuity study are symlinked."""
import json
import os
import subprocess
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
VAC = RUN.parent / "formal-math-selfplay-vacuity-drift" / "data" / "raw"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
token = (Path.home() / ".config" / "hf" / "token").read_text().strip()
api = HfApi()
DATASETS = {
    "minif2f_test": "AI-MO/minif2f_test",
    "miniF2F_v2": "roozbeh-yz/miniF2F_v2",
    "ProofNetSharp": "PAug/ProofNetSharp",
    "Lean-Workbook": "internlm/Lean-Workbook",
    "Goedel-Pset-v1": "Goedel-LM/Goedel-Pset-v1",
}
MODELS = {"DeepSeek-Prover-V2-7B": "deepseek-ai/DeepSeek-Prover-V2-7B", "Goedel-Prover-V2-8B": "Goedel-LM/Goedel-Prover-V2-8B",
          "Kimina-Prover-Distill-8B": "AI-MO/Kimina-Prover-Distill-8B"}


def main():
    revs = {}
    for name in ("DeepSeek-Prover-V1", "Lean-workbook-proofs", "NuminaMath-LEAN", "SFT_dataset_v2", "STP_Lean_0320"):
        link = RAW / name
        if not link.exists():
            link.symlink_to(VAC / name)
    for name, repo in DATASETS.items():
        info = api.dataset_info(repo, token=token)
        snapshot_download(repo, repo_type="dataset", revision=info.sha, local_dir=RAW / name, token=token)
        revs[repo] = info.sha
        print(name, info.sha, flush=True)
    if not (RAW / "PutnamBench").exists():
        subprocess.run(["git", "clone", "-q", "https://github.com/trishullab/PutnamBench", str(RAW / "PutnamBench")], check=True)
    revs["trishullab/PutnamBench"] = subprocess.run(["git", "-C", str(RAW / "PutnamBench"), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    json.dump(revs, open(RUN / "results" / "tables" / "revisions.json", "w"), indent=1)
    for name, repo in MODELS.items():
        info = api.model_info(repo, token=token)
        snapshot_download(repo, revision=info.sha, local_dir=RUN / "data" / "models" / name, token=token,
                          allow_patterns=["*.json", "*.safetensors", "*.txt", "tokenizer*", "*.model", "*.jinja", "*.py"])
        revs[repo] = info.sha
        json.dump(revs, open(RUN / "results" / "tables" / "revisions.json", "w"), indent=1)
        print(name, info.sha, flush=True)


if __name__ == "__main__":
    main()
