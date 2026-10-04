"""Attack A1: MPO middle-out cancellation with greedy unswapping (Kremer & Dupuis code, unchanged), as in their
unswapping notebook. Usage: attack_unswap.py <instance P9|P11|P12> [max_bond] [cutoff] [seed]
Writes results/<instance>_A1_mb<max_bond>_c<cutoff>.json (candidate, top samples, runtime) and the stats CSV.
For P11/P12 the candidate is NOT compared with any answer here (blinding; see plan.md)."""
import json
import sys
import time
import warnings
from collections import Counter
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
KD = RUN / "data" / "raw" / "peaked-circuit-simulation"
sys.path.insert(0, str(KD))
warnings.filterwarnings("ignore")

import pandas as pd  # noqa: E402
import torch  # noqa: E402
from qiskit import QuantumCircuit  # noqa: E402
from qiskit.transpiler import PassManager  # noqa: E402
from qiskit.transpiler.passes import Collect2qBlocks, ConsolidateBlocks  # noqa: E402
from unswap import mpo_compress_unswap, mpo_to_mps  # noqa: E402
from utils import to_backend_cuda  # noqa: E402

FILES = {"P9": "peaked_circuit_P9_Hqap_56x1917.qasm", "P11": "peaked_circuit_P11_Hqap_98x1999.qasm",
         "P12": "peaked_circuit_P12_Hqap_98x2457.qasm"}
P9_PUBLISHED = "01101110111001100000100000001010011100101101010111110111"   # from the Kremer & Dupuis notebook


def main(inst, max_bond=8192, cutoff=0.002, seed=123):
    max_bond, cutoff, seed = int(max_bond), float(cutoff), int(seed)
    tag = f"{inst}_A1_mb{max_bond}_c{cutoff}_s{seed}"
    t0 = time.perf_counter()
    circuit = QuantumCircuit.from_qasm_file(str(RUN / "data" / "raw" / FILES[inst]))
    circuit = PassManager([Collect2qBlocks(), ConsolidateBlocks(force_consolidate=True)]).run(circuit)
    mpo, layers_left, layers_right, stats = mpo_compress_unswap(
        circuit, seed=seed, to_backend=to_backend_cuda, cutoff=cutoff, max_bond=max_bond, unswap_threshold=1e6,
        center_ratio=0.5, equal=False, flip_freq=None, max_its=20, early_stopping_gates=0, hows=("both", "left", "right"))
    t_core = time.perf_counter() - t0
    pd.DataFrame(stats).to_csv(RUN / "results" / "tables" / f"{tag}_stats.csv", index=False)
    mps, perm = mpo_to_mps(mpo, layers_left[:-2], layers_right, cutoff=cutoff, to_backend=to_backend_cuda)
    raw = [p for p, _ in list(mps.sample(1000))]
    samples = ["".join(str(b) for b in bs) for bs in raw]
    c = Counter(samples)
    perm_top = [("".join(s[i] for i in perm), n) for s, n in c.most_common(20)]
    out = dict(instance=inst, attack="A1", max_bond=max_bond, cutoff=cutoff, seed=seed, candidate=perm_top[0][0],
               top_frequency=perm_top[0][1] / 1000, top20=perm_top, seconds_core=t_core, seconds_total=time.perf_counter() - t0,
               peak_gpu_mem_gb=torch.cuda.max_memory_allocated() / 1e9, mpo_max_bond=int(mpo.max_bond()))
    if inst == "P9":
        out["matches_published_P9"] = out["candidate"] == P9_PUBLISHED
    json.dump(out, open(RUN / "results" / f"{tag}.json", "w"), indent=1)
    print({k: v for k, v in out.items() if k not in ("top20",) and (inst == "P9" or k != "candidate")})


if __name__ == "__main__":
    main(*sys.argv[1:])
