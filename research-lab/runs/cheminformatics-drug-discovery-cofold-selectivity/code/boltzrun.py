"""Boltz-2 plumbing: fetch one MSA per protein from the public ColabFold server, write one YAML per
complex, run `boltz predict` over a directory of YAMLs, and collect the affinity outputs.

MSAs are fetched once per protein and reused by every complex that protein appears in (the alternative,
letting `boltz --use_msa_server` fetch per complex, would hit the public server a thousand times for the
same 32 sequences). Everything is keyed by a short pair id so a crash can be resumed: YAMLs that already
have an affinity JSON in the output directory are skipped by boltz itself unless --override is passed.

Usage:
  python code/boltzrun.py msa   <name=seq-file.json>      fetch missing MSAs into data/msa/
  python code/boltzrun.py yaml  <spec.json> <indir>       write one YAML per complex
  python code/boltzrun.py run   <indir> <outdir> [flags]  run boltz predict over the directory
  python code/boltzrun.py collect <outdir> <arm> <jsonl>  append the affinity outputs to a jsonl
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
MSA = RUN / "data" / "msa"
VENV = RUN / "venv" / "bin"
SEED = 20261013


def msa_path(name):
    return MSA / f"{name}.a3m"


def fetch_msa(seqs, tries=3):
    """seqs: {name: sequence}. Writes data/msa/<name>.a3m for the ones that are missing.

    One sequence per request: a batched request to the public server came back missing one query's
    alignment (KeyError in boltz's own parser), and one-at-a-time is both robust and resumable.
    """
    from boltz.data.msa.mmseqs2 import run_mmseqs2
    MSA.mkdir(parents=True, exist_ok=True)
    (RUN / "data" / "msa_tmp").mkdir(parents=True, exist_ok=True)  # run_mmseqs2 mkdirs only the leaf
    todo = {n: s for n, s in seqs.items() if not msa_path(n).exists()}
    print(f"{len(seqs)} proteins, {len(todo)} MSAs to fetch", flush=True)
    failed = []
    for i, n in enumerate(sorted(todo), 1):
        t0 = time.time()
        for attempt in range(1, tries + 1):
            try:
                out = run_mmseqs2([todo[n]], prefix=str(RUN / "data" / "msa_tmp" / f"{n}_a{attempt}"),
                                  use_env=True, use_filter=True)
                a3ms = out[0] if isinstance(out, tuple) else out
                msa_path(n).write_text(a3ms[0])
                print(f"  [{i}/{len(todo)}] {n} {len(a3ms[0])}B in {time.time() - t0:.0f}s", flush=True)
                break
            except Exception as e:  # noqa: BLE001 - server-side flakiness, retry then record
                print(f"  [{i}/{len(todo)}] {n} attempt {attempt} failed: {type(e).__name__} {e}",
                      flush=True)
                time.sleep(20)
        else:
            failed.append(n)
    if failed:
        print("FAILED MSAs:", failed, flush=True)
    return failed


def write_yaml(indir, pair_id, protein, seq, smiles):
    """One complex: protein chain A with its cached MSA, ligand chain B from SMILES, affinity on B."""
    p = Path(indir) / f"{pair_id}.yaml"
    p.write_text(
        "version: 1\nsequences:\n"
        f"  - protein:\n      id: A\n      sequence: {seq}\n      msa: {msa_path(protein)}\n"
        f"  - ligand:\n      id: B\n      smiles: '{smiles}'\n"
        "properties:\n  - affinity:\n      binder: B\n")
    return p


def run(indir, outdir, extra=()):
    cmd = [str(VENV / "boltz"), "predict", str(indir), "--out_dir", str(outdir), "--seed", str(SEED),
           "--output_format", "mmcif", "--num_workers", "2", "--preprocessing-threads", "4", *extra]
    print(" ".join(cmd), flush=True)
    t0 = time.time()
    r = subprocess.run(cmd)
    print(f"exit {r.returncode} after {time.time() - t0:.0f}s", flush=True)
    return r.returncode


def collect(outdir, arm, jsonl):
    """Read affinity_*.json and confidence_*.json from a boltz output tree into one jsonl."""
    base = Path(outdir)
    pred = next(p for p in [base / "predictions", base] if p.exists())
    rows = []
    for d in sorted(pred.iterdir()):
        if not d.is_dir():
            continue
        aff = d / f"affinity_{d.name}.json"
        if not aff.exists():
            continue
        r = dict(arm=arm, pair_id=d.name, **json.load(open(aff)))
        conf = sorted(d.glob("confidence_*.json"))
        if conf:
            c = json.load(open(conf[0]))
            r.update(confidence_score=c.get("confidence_score"), ptm=c.get("ptm"),
                     iptm=c.get("iptm"), complex_plddt=c.get("complex_plddt"),
                     ligand_iptm=c.get("ligand_iptm"), protein_iptm=c.get("protein_iptm"))
        rows.append(r)
    with open(jsonl, "a") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"collected {len(rows)} predictions from {pred} -> {jsonl}")
    return rows


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "msa":
        fetch_msa(json.load(open(sys.argv[2])))
    elif cmd == "yaml":
        spec = json.load(open(sys.argv[2]))
        d = Path(sys.argv[3])
        d.mkdir(parents=True, exist_ok=True)
        for c in spec:
            write_yaml(d, c["pair_id"], c["protein"], c["seq"], c["smiles"])
        print(f"wrote {len(spec)} yaml files to {d}")
    elif cmd == "run":
        sys.exit(run(sys.argv[2], sys.argv[3], sys.argv[4:]))
    elif cmd == "collect":
        collect(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit(__doc__)
