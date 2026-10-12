"""Download the inputs (no analysis):

- the 16 Pythia-160M variants at their final checkpoint (step143000): the original (seed 0), seeds 1-9, and the
  PolyPythia decoupled variants weight-seed1..3 (only the parameter initialisation differs) and data-seed1..3 (only
  the data order differs);
- the step-0 checkpoints of the original and the six decoupled variants, to check which initialisations are shared;
- monology/pile-uncopyrighted val.jsonl.zst (SAE training stream) and test.jsonl.zst (held-out matching set);
- EleutherAI/sae-pythia-160m-32k at the two study layers (recipe sanity check).

The HF read token is read from ~/.config/hf/token and never printed. Usage: fetch.py models|step0|pile|ref"""
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download, snapshot_download

RUN = Path(__file__).resolve().parents[1]
RAW = RUN / "data" / "raw"
TOKEN = (Path.home() / ".config" / "hf" / "token").read_text().strip()
MODELS = (["EleutherAI/pythia-160m"] + [f"EleutherAI/pythia-160m-seed{i}" for i in range(1, 10)]
          + [f"EleutherAI/pythia-160m-weight-seed{i}" for i in range(1, 4)]
          + [f"EleutherAI/pythia-160m-data-seed{i}" for i in range(1, 4)])
PILE, PILE_SHA = "monology/pile-uncopyrighted", "3be90335b66f24456a5d6659d9c8d208c0357119"
REF, REF_SHA = "EleutherAI/sae-pythia-160m-32k", "2046768ae0c8cb69a2e8ed64f2eafb9f8c5fa294"
LAYERS = [4, 8]
PATTERNS = ["config.json", "pytorch_model.bin", "tokenizer*", "special_tokens_map.json"]  # fp16 checkpoints in every repo


def short(name):
    return name.split("/")[1].replace("pythia-160m", "p160m") or "p160m"


def main(what):
    if what == "models":
        for m in MODELS:
            p = snapshot_download(m, revision="step143000", allow_patterns=PATTERNS, local_dir=RAW / "models" / short(m), token=TOKEN)
            print(m, "->", p, flush=True)
    elif what == "step0":
        for m in [MODELS[0]] + MODELS[10:]:
            p = snapshot_download(m, revision="step0", allow_patterns=["config.json", "pytorch_model.bin"],
                                  local_dir=RAW / "step0" / short(m), token=TOKEN)
            print(m, "step0 ->", p, flush=True)
    elif what == "pile":
        for f in ["val.jsonl.zst", "test.jsonl.zst"]:
            p = hf_hub_download(PILE, f, repo_type="dataset", revision=PILE_SHA, local_dir=RAW / "pile", token=TOKEN)
            print(f, "->", p, flush=True)
    elif what == "ref":
        for L in LAYERS:
            for f in ["cfg.json", "sae.safetensors"]:
                hf_hub_download(REF, f"layers.{L}/{f}", revision=REF_SHA, local_dir=RAW / "eai_sae_ref", token=TOKEN)
        print("reference SAEs ok", flush=True)
    print(what.upper(), "DONE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
