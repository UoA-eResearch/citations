"""Instances and exact values (plan sections 1-2).

  instances.py lattice          parse the tracker's 74q Floquet QASM -> data/instances/lattice.json (edges with colour)
  instances.py make NAME N SEED write N instances (families F and K, stratified) -> data/instances/NAME.json
  instances.py exact NAME       qiskit-aer statevector magnetization (D1) -> data/results/exact_NAME.json
  instances.py crosscheck NAME  numpy statevector on a subset of n=20 instances vs the aer values
  instances.py test             tiny-system checks of the statevector code

Gate conventions (qiskit): RX(t) = exp(-i t X / 2), RZ(t) = exp(-i t Z / 2), RZZ(t) = exp(-i t Z Z / 2).
"""
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

RUN = Path(__file__).resolve().parents[1]
INS, RES = RUN / "data" / "instances", RUN / "data" / "results"
INS.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)
QASM = ("https://raw.githubusercontent.com/quantum-advantage-tracker/quantum-advantage-tracker.github.io/main/data/"
        "observable-estimations/circuit-models/floquet_mixed_field_ising/floquet_mixed_field_ising_mag_74qx27c.qasm")
TX, TZ, TZZ = 1.56567, 0.33879, np.pi / 3
SIZES, DEPTH_F, DEPTH_K = [20, 22, 24, 26], [4, 8, 12, 16], [5, 10, 15, 20]


def lattice():
    txt = urllib.request.urlopen(QASM, timeout=120).read().decode()
    body = txt.split("qubit[74] q;")[1]
    colour, edges, seen = 0, [], set()
    prev = None
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("rx"):
            if prev == "rzz":
                colour += 1
            prev = "rx"
        m = re.match(r"rzz\(([^)]+)\) q\[(\d+)\], ?q\[(\d+)\];", line)
        if m:
            a, b = sorted((int(m.group(2)), int(m.group(3))))
            if (a, b) not in seen:
                seen.add((a, b))
                edges.append([a, b, colour % 3])
            prev = "rzz"
        if len(seen) and colour >= 3:
            break
    (INS / "lattice.json").write_text(json.dumps({"n": 74, "edges": edges}))
    print(len(edges), "edges; colours", sorted({e[2] for e in edges}))


def hexagons(adj):
    """The lattice's 12-cycles: the shortest cycle through each edge, deduplicated."""
    out = set()
    for u in adj:
        for v in adj[u]:
            if u > v:
                continue
            prev, queue = {u: None}, [u]
            while queue and v not in prev:
                nxt = []
                for x in queue:
                    for w in adj[x]:
                        if w not in prev and not (x == u and w == v):
                            prev[w] = x; nxt.append(w)
                queue = nxt
            if v in prev:
                cyc, x = [], v
                while x is not None:
                    cyc.append(x); x = prev[x]
                if len(cyc) == 12:
                    out.add(frozenset(cyc))
    return sorted(out, key=sorted)


def patch(edges, n, rng, compact=False):
    """Connected n-qubit patch. Random: grown from a random seed qubit with random tie-breaking.
    compact=True (D1): start from a random hexagon, add adjacent hexagons while they fit, then grow at random."""
    adj = {}
    for a, b, _ in edges:
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    if compact:
        H = hexagons(adj)
        sel = list(H[int(rng.integers(len(H)))])
        while True:
            cand = [h for h in H if h & set(sel) and not h <= set(sel) and len(set(sel) | h) <= n]
            if not cand:
                break
            sel += sorted(cand[int(rng.integers(len(cand)))] - set(sel))
    else:
        sel = [int(rng.choice(sorted(adj)))]
    frontier = [w for v in sel for w in adj[v] if w not in sel]
    while len(sel) < n and frontier:
        v = frontier.pop(int(rng.integers(len(frontier))))
        if v in sel:
            continue
        sel.append(v)
        frontier += [w for w in adj[v] if w not in sel]
    if len(sel) < n:
        return None
    idx = {q: i for i, q in enumerate(sorted(sel))}
    pe = [[idx[a], idx[b], c] for a, b, c in edges if a in idx and b in idx]
    return pe


def make(name, count, seed):
    L = json.loads((INS / "lattice.json").read_text())
    rng = np.random.default_rng(int(seed))
    out = []
    per = int(count) // 2
    for fam in ("F", "K"):
        cells = [(n, d) for n in SIZES for d in (DEPTH_F if fam == "F" else DEPTH_K)]
        for k in range(per):
            n, d = cells[k % len(cells)]
            pe = None
            compact = k % 2 == 1                                   # D1: alternate random and loop-preferring patches
            while pe is None:
                pe = patch(L["edges"], n, rng, compact)
            if fam == "F":
                f = rng.uniform(0.7, 1.3, 3)
                params = {"tx": TX * f[0], "tz": TZ * f[1], "tzz": TZZ * f[2], "cycles": d}
            else:
                params = {"theta": float(rng.uniform(0, np.pi / 2)), "layers": d}
            out.append({"id": f"{name}_{fam}{k:03d}", "family": fam, "n": n, "depth": d, "edges": pe, "params": params,
                        "compact": compact, "loops": len(pe) - n + 1})
    (INS / f"{name}.json").write_text(json.dumps(out))
    print(len(out), "instances")


def gates(ins):
    """Ordered gate list [(name, qubits, angle)], name in RX, RZ, RZZ (Schrodinger order)."""
    n, e, p = ins["n"], ins["edges"], ins["params"]
    g = []
    if ins["family"] == "F":
        for _ in range(p["cycles"]):
            for m in range(3):
                g += [("RX", [q], p["tx"] / 3) for q in range(n)]
                g += [("RZ", [q], p["tz"] / 3) for q in range(n)]
                g += [("RZZ", [a, b], p["tzz"]) for a, b, c in e if c == m]
    else:
        for _ in range(p["layers"]):
            g += [("RX", [q], p["theta"]) for q in range(n)]
            for m in range(3):
                g += [("RZZ", [a, b], -np.pi / 2) for a, b, c in e if c == m]
    return g


def statevector_mag(ins):
    n = ins["n"]
    psi = np.zeros(2 ** n, dtype=np.complex128)
    psi[0] = 1.0
    idx = np.arange(2 ** n, dtype=np.int64)

    def z(q):
        return 1 - 2 * ((idx >> q) & 1).astype(np.int8)

    block, cache = [], {}                              # diagonal blocks repeat every cycle: cache exp(-i/2 * phase)
    for name, qs, t in gates(ins) + [("END", [], 0)]:
        if name in ("RZ", "RZZ"):
            block.append((name, tuple(qs), t))
            continue
        if block:
            key = tuple(block)
            if key not in cache:
                phase = np.zeros(2 ** n)
                for bn, bq, bt in block:
                    phase += bt * (z(bq[0]) if bn == "RZ" else z(bq[0]) * z(bq[1]))
                cache[key] = np.exp(-0.5j * phase)
                del phase
            psi *= cache[key]
            block = []
        if name == "RX":
            q = qs[0]
            c, s = np.cos(t / 2), np.sin(t / 2)
            v = psi.reshape(2 ** (n - q - 1), 2, 2 ** q)
            a0, a1 = v[:, 0, :].copy(), v[:, 1, :].copy()
            v[:, 0, :] = c * a0 - 1j * s * a1
            v[:, 1, :] = -1j * s * a0 + c * a1
    pr = np.abs(psi) ** 2
    mag = sum(float(pr @ z(q)) for q in range(n)) / n
    return ins["id"], mag


def aer_mag(ins, threads=None):
    """D1: qiskit-aer statevector (complex128, multithreaded); same gate list and conventions as statevector_mag."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_aer import AerSimulator
    n = ins["n"]
    qc = QuantumCircuit(n)
    for name, qs, t in gates(ins):
        {"RX": qc.rx, "RZ": qc.rz, "RZZ": qc.rzz}[name](t, *qs)
    op = SparsePauliOp.from_sparse_list([("Z", [q], 1.0 / n) for q in range(n)], num_qubits=n)
    qc.save_expectation_value(op, list(range(n)), label="m")
    sim = AerSimulator(method="statevector", precision="double", max_parallel_threads=threads or 0)
    return ins["id"], float(np.real(sim.run(qc).result().data()["m"]))


def exact(name):
    I = json.loads((INS / f"{name}.json").read_text())
    I.sort(key=lambda x: -x["n"])
    res, out = {}, RES / f"exact_{name}.json"
    if out.exists():
        res = json.loads(out.read_text())
    for k, ins in enumerate(I, 1):
        if ins["id"] in res:
            continue
        res[ins["id"]] = aer_mag(ins, int(os.environ.get("THREADS", "12")))[1]
        out.write_text(json.dumps(res, indent=0))
        if k % 10 == 0:
            print(k, "of", len(I), flush=True)
    print("exact done", len(res))


def crosscheck(name, frac=0.05):
    """Numpy statevector on a 5% random subset of the n=20 instances, against the aer values."""
    I = [x for x in json.loads((INS / f"{name}.json").read_text()) if x["n"] == 20]
    sub = [I[i] for i in sorted(np.random.default_rng(1).choice(len(I), max(2, int(len(I) * frac * 4)), replace=False))]
    ex = json.loads((RES / f"exact_{name}.json").read_text())
    with ProcessPoolExecutor(4) as pool:
        d = {i: abs(m - ex[i]) for i, m in pool.map(statevector_mag, sub)}
    print("numpy vs aer max |diff|", max(d.values()), "over", len(d))
    assert max(d.values()) < 1e-10


def test():
    # one qubit: RX(t) on |0> gives <Z> = cos t
    ins = {"id": "t", "family": "K", "n": 1, "edges": [], "params": {"theta": 0.7, "layers": 1}}
    assert abs(statevector_mag(ins)[1] - np.cos(0.7)) < 1e-12
    # two qubits, one edge: RX(t) both then RZZ(-pi/2): <Z_i> unchanged by the diagonal -> cos t
    ins = {"id": "t2", "family": "K", "n": 2, "edges": [[0, 1, 0]], "params": {"theta": 0.4, "layers": 1}}
    assert abs(statevector_mag(ins)[1] - np.cos(0.4)) < 1e-12
    # two layers: compare with a dense-matrix simulation
    ins = {"id": "t3", "family": "F", "n": 3, "edges": [[0, 1, 0], [1, 2, 1]], "params": {"tx": 1.1, "tz": 0.3, "tzz": 0.9, "cycles": 2}}
    X = np.array([[0, 1], [1, 0]]); Z = np.diag([1, -1]); I2 = np.eye(2)

    def op(single, q, n):
        mats = [single if k == q else I2 for k in range(n)][::-1]       # qubit 0 is the least significant bit
        out = mats[0]
        for m in mats[1:]:
            out = np.kron(out, m)
        return out
    from scipy.linalg import expm
    n = 3; psi = np.zeros(8, complex); psi[0] = 1
    for name, qs, t in gates(ins):
        if name == "RX":
            psi = expm(-0.5j * t * op(X, qs[0], n)) @ psi
        elif name == "RZ":
            psi = expm(-0.5j * t * op(Z, qs[0], n)) @ psi
        else:
            psi = expm(-0.5j * t * op(Z, qs[0], n) @ op(Z, qs[1], n)) @ psi
    mag = np.mean([np.real(psi.conj() @ op(Z, q, n) @ psi) for q in range(n)])
    assert abs(statevector_mag(ins)[1] - mag) < 1e-10, (statevector_mag(ins)[1], mag)
    assert abs(aer_mag(ins)[1] - mag) < 1e-10, (aer_mag(ins)[1], mag)
    print("statevector + aer tests pass", round(mag, 6))


if __name__ == "__main__":
    a = sys.argv
    {"lattice": lattice, "make": lambda: make(a[2], a[3], a[4]), "exact": lambda: exact(a[2]), "test": test,
     "crosscheck": lambda: crosscheck(a[2])}[a[1]]()
