"""Attack A2: low-bond MPS simulation (quimb CircuitPermMPS on GPU) + per-bit majority vote over samples, as in the
Kremer & Dupuis distillation notebook. Usage: attack_distill.py <P9|P11|P12> <max_bond> [n_samples] [seed]
Writes results/<instance>_A2_chi<max_bond>.json with the voted string, per-bit probabilities and the mean margin
|p - 0.5| (the attack's confidence). For P11/P12 the voted string is not compared with any answer here (blinding)."""
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import quimb
import torch
from qiskit import QuantumCircuit
from qiskit_quimb import quimb_circuit

warnings.filterwarnings("ignore")
RUN = Path(__file__).resolve().parents[1]
FILES = {"P9": "peaked_circuit_P9_Hqap_56x1917.qasm", "P11": "peaked_circuit_P11_Hqap_98x1999.qasm",
         "P12": "peaked_circuit_P12_Hqap_98x2457.qasm"}
P9_PUBLISHED = "01101110111001100000100000001010011100101101010111110111"


def to_backend(x):
    return torch.tensor(x, dtype=torch.complex128, device="cuda")   # complex64 gave NaN sampling probabilities on P9 (D1)


def main(inst, max_bond, n_samples=1000, seed=1234):
    max_bond, n_samples, seed = int(max_bond), int(n_samples), int(seed)
    t0 = time.perf_counter()
    circ = QuantumCircuit.from_qasm_file(str(RUN / "data" / "raw" / FILES[inst]))
    qc = quimb_circuit(circ, quimb_circuit_class=quimb.tensor.CircuitPermMPS, to_backend=to_backend,
                       max_bond=max_bond, cutoff=1e-12, progbar=False)
    mapping = [qc.qubits.index(q) for q in range(qc.N)]
    mapping = [mapping[q] for q in mapping]
    samples = ["".join(bs[q] for q in mapping) for bs in qc.sample(n_samples, seed=seed)]
    probs = np.array([[int(s) for s in ss] for ss in samples]).mean(axis=0)
    voted = "".join(str(int(p > 0.5)) for p in probs)
    out = dict(instance=inst, attack="A2", max_bond=max_bond, n_samples=n_samples, seed=seed, candidate=voted,
               mean_margin=float(np.mean(np.abs(probs - 0.5))), min_margin=float(np.min(np.abs(probs - 0.5))),
               bit_probs=probs.tolist(), seconds=time.perf_counter() - t0, peak_gpu_mem_gb=torch.cuda.max_memory_allocated() / 1e9)
    if inst == "P9":
        out["hamming_to_published_P9"] = sum(a != b for a, b in zip(voted, P9_PUBLISHED))
    json.dump(out, open(RUN / "results" / f"{inst}_A2_chi{max_bond}_s{seed}.json", "w"), indent=1)
    print({k: v for k, v in out.items() if k not in ("bit_probs",) and (inst == "P9" or k != "candidate")})


if __name__ == "__main__":
    main(*sys.argv[1:])
