"""Attack A3: Heisenberg-picture back-propagation of each Z_i with Pauli truncation (qiskit-addon-obp), then
<Z_i> = sum of coefficients of I/Z-only terms on |0...0>; bit_i = 1 if <Z_i> < 0. Confidence = mean |<Z_i>|.
Usage: attack_pauli.py <P9|P11|P12> <max_paulis> <trunc_budget> [qubits: all|i,j,...]
Writes results/<instance>_A3_mp<max_paulis>_tb<trunc_budget>.json. P11/P12 candidates are not compared with any answer
here (blinding)."""
import json
import sys
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp
from qiskit_addon_obp import backpropagate
from qiskit_addon_obp.utils.simplify import OperatorBudget
from qiskit_addon_obp.utils.truncating import setup_budget
from qiskit_addon_utils.slicing import slice_by_depth

RUN = Path(__file__).resolve().parents[1]
FILES = {"P9": "peaked_circuit_P9_Hqap_56x1917.qasm", "P11": "peaked_circuit_P11_Hqap_98x1999.qasm",
         "P12": "peaked_circuit_P12_Hqap_98x2457.qasm"}
P9_PUBLISHED = "01101110111001100000100000001010011100101101010111110111"


def expval_zero(op):
    tot = 0.0
    for lbl, c in zip(op.paulis.to_labels(), op.coeffs):
        if all(ch in "IZ" for ch in lbl):
            tot += c.real
    return tot


def one(slices, n, q, max_paulis, tb):
    obs = SparsePauliOp.from_sparse_list([("Z", [q], 1.0)], num_qubits=n)
    budget = OperatorBudget(max_paulis=max_paulis)
    trunc = setup_budget(max_error_total=tb, num_slices=len(slices), p_norm=1)
    t0 = time.perf_counter()
    bp, remaining, meta = backpropagate(obs, slices, operator_budget=budget, truncation_error_budget=trunc)
    ok = len(remaining) == 0
    return q, expval_zero(bp) if ok else float("nan"), len(remaining), time.perf_counter() - t0, len(bp)


def main(inst, max_paulis, tb, qubits="all", n_jobs=24):
    max_paulis, tb = int(max_paulis), float(tb)
    qc = QuantumCircuit.from_qasm_file(str(RUN / "data" / "raw" / FILES[inst]))
    qc = transpile(qc, basis_gates=["rz", "sx", "x", "cz", "rzz", "u"], optimization_level=0)
    slices = slice_by_depth(qc, 1)
    n = qc.num_qubits
    qs = range(n) if qubits == "all" else [int(x) for x in qubits.split(",")]
    res = Parallel(n_jobs=int(n_jobs))(delayed(one)(slices, n, q, max_paulis, tb) for q in qs)
    z = {q: v for q, v, *_ in res}
    bits = "".join("1" if (z.get(q, 0) < 0) else "0" for q in range(n))
    out = dict(instance=inst, attack="A3", max_paulis=max_paulis, trunc_budget=tb, n_slices=len(slices),
               z={int(q): float(v) for q, v in z.items()}, unfinished_slices={int(q): int(r) for q, _, r, _, _ in res},
               seconds={int(q): s for q, _, _, s, _ in res}, final_terms={int(q): int(t) for q, *_, t in res},
               candidate=bits, mean_abs_z=float(np.nanmean([abs(v) for v in z.values()])))
    if inst == "P9":
        out["hamming_to_published_P9"] = sum(a != b for a, b in zip(bits, P9_PUBLISHED))
        out["hamming_reversed"] = sum(a != b for a, b in zip(bits[::-1], P9_PUBLISHED))
    tag = f"{inst}_A3_mp{max_paulis}_tb{tb}" + ("" if qubits == "all" else "_subset")
    json.dump(out, open(RUN / "results" / f"{tag}.json", "w"), indent=1)
    print({k: v for k, v in out.items() if k in ("instance", "n_slices", "mean_abs_z", "hamming_to_published_P9", "hamming_reversed")})
    print("per-qubit:", [(q, round(v, 3), r, round(s, 1)) for q, v, r, s, _ in res][:12])


if __name__ == "__main__":
    main(*sys.argv[1:])
