"""Minimal Lean REPL client with wall-clock timeouts and periodic restarts (each command's env is kept in memory by the
REPL, so the process is restarted every `max_cmds` commands). Uses the DeepSeek/STP REPL on the STP mathlib build."""
import json
import os
import select
import signal
import subprocess
import time
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
# VAC_TOOLCHAIN=v49 (default; STP/Goedel/DeepSeek environment) or v415 (NuminaMath-LEAN, mathlib v4.15.0)
TOOLCHAIN = os.environ.get("VAC_TOOLCHAIN", "v49")
WS = RUN / "lean" / ("mathlib4_v415" if TOOLCHAIN == "v415" else "mathlib4")
REPL_BIN = RUN / "lean" / ("repl_v415" if TOOLCHAIN == "v415" else "repl") / ".lake" / "build" / "bin" / "repl"
LAKE = Path.home() / ".elan" / "bin" / "lake"
HEADER = "import Mathlib\nimport Aesop"


class Repl:
    def __init__(self, max_cmds=250):
        self.p, self.buf, self.n, self.max_cmds = None, b"", 0, max_cmds

    def start(self):
        env = dict(os.environ, PATH=f"{LAKE.parent}:{os.environ['PATH']}")
        self.p = subprocess.Popen([str(LAKE), "env", str(REPL_BIN)], cwd=WS, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, start_new_session=True, env=env)
        self.buf, self.n = b"", 0
        r = self._send({"cmd": HEADER}, 600)
        if not isinstance(r, dict) or r.get("env") != 0:
            raise RuntimeError(f"REPL failed to start: {r}")

    def kill(self):
        if self.p is not None:
            try:
                os.killpg(self.p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self.p.wait()
            self.p = None

    def restart(self):
        self.kill()
        self.start()

    def ensure(self, k):
        """Make sure k more commands fit before the next restart (so dependent envs stay valid)."""
        if self.p is None or self.n + k > self.max_cmds:
            self.restart()

    def _send(self, obj, timeout):
        try:
            self.p.stdin.write((json.dumps(obj, ensure_ascii=False) + "\n\n").encode())
            self.p.stdin.flush()
        except BrokenPipeError:
            return "dead"
        fd = self.p.stdout.fileno()
        deadline = time.time() + timeout
        while b"\n\n" not in self.buf.lstrip():
            rem = deadline - time.time()
            if rem <= 0:
                return None
            r, _, _ = select.select([fd], [], [], rem)
            if not r:
                return None
            chunk = os.read(fd, 1 << 20)
            if not chunk:
                return "dead"
            self.buf += chunk
        msg, _, self.buf = self.buf.lstrip().partition(b"\n\n")
        return json.loads(msg)

    def run(self, cmd, env=0, timeout=100):
        """Returns the REPL response dict, or {'timeout': True} / {'dead': True} (the REPL is then restarted)."""
        if self.p is None:
            self.start()
        t0 = time.time()
        r = self._send({"cmd": cmd, "env": env}, timeout)
        self.n += 1
        if not isinstance(r, dict):
            kind = "timeout" if r is None else "dead"
            self.restart()
            return {kind: True, "seconds": time.time() - t0}
        r["seconds"] = time.time() - t0
        return r


def errors(r):
    return [m for m in r.get("messages", []) if m.get("severity") == "error"]


def axioms(r, name):
    """Axioms listed by `#print axioms name`, or None if the message is missing (declaration not added)."""
    for m in r.get("messages", []):
        d = m.get("data", "")
        if d.startswith(f"'{name}' depends on axioms:"):
            return [a.strip() for a in d.split("[", 1)[1].rsplit("]", 1)[0].split(",") if a.strip()]
        if d.startswith(f"'{name}' does not depend on any axioms"):
            return []
    return None


def uses_sorry(r):
    return bool(r.get("sorries")) or any("declaration uses 'sorry'" in m.get("data", "") for m in r.get("messages", []))
