"""GPU / docker protocol (see README "GPU protocol").

The A100 is normally occupied by the user's vLLM server (docker container
`vllm`). The user authorized stopping it for GPU-heavy stages. GPUSession:
  * decides the JAX platform BEFORE jax is imported (env JAX_PLATFORMS),
  * stops the container only when the GPU is needed and not free,
  * ALWAYS restarts it on exit (normal, exception, SIGINT/SIGTERM).
Use as:   with GPUSession(cfg, backend) as gs:  <import jax-using modules>
"""
from __future__ import annotations

import logging
import os
import signal
import subprocess
import time

logger = logging.getLogger("q_chieff_copula")


def gpu_free_mib() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20)
        if out.returncode != 0:
            return None
        return int(out.stdout.strip().splitlines()[0])
    except Exception:  # noqa: BLE001
        return None


def gpu_total_mib() -> int | None:
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=20)
        return int(out.stdout.strip().splitlines()[0]) if out.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


def docker(cmd: str, name: str = "vllm") -> bool:
    try:
        r = subprocess.run(["docker", cmd, name], capture_output=True, text=True, timeout=300)
        logger.info("docker %s %s -> rc=%d %s", cmd, name, r.returncode, (r.stdout + r.stderr).strip()[:200])
        return r.returncode == 0
    except Exception as e:  # noqa: BLE001
        logger.error("docker %s %s failed: %s", cmd, name, e)
        return False


def docker_running(name: str = "vllm") -> bool | None:
    try:
        r = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", name],
                           capture_output=True, text=True, timeout=30)
        return r.stdout.strip() == "true" if r.returncode == 0 else None
    except Exception:  # noqa: BLE001
        return None


class GPUSession:
    def __init__(self, cfg, backend: str | None = None):
        run = cfg.raw["run"]
        self.backend = backend or cfg.backend   # mode-level override, else run.backend
        self.manage = bool(run.get("manage_vllm", True))
        self.min_free = int(run.get("gpu_min_free_mib", 20000))
        self.stopped = False
        self.platform = "cpu"
        self._old_handlers = {}

    def _restore(self, *_):
        if self.stopped:
            logger.info("restarting vllm container")
            docker("start")
            self.stopped = False

    def _signal(self, signum, frame):
        self._restore()
        raise SystemExit(128 + signum)

    def __enter__(self):
        if self.backend == "cpu":
            self.platform = "cpu"
        else:
            free = gpu_free_mib()
            # A running vllm container is stopped whenever this session manages the GPU, regardless of the
            # instantaneous free memory: right after a (re)start the container has not yet claimed its memory,
            # so a free-memory test races against it (2026-09-11 19:10, D16 note). After the stop, wait until the
            # GPU is essentially empty so that JAX's 85% preallocation cannot collide with a dying server.
            if self.manage and docker_running():
                logger.info("GPU has %s MiB free; vllm container is running -> stopping it for this stage", free)
                if docker("stop"):
                    self.stopped = True
                    for sig in (signal.SIGINT, signal.SIGTERM):
                        self._old_handlers[sig] = signal.signal(sig, self._signal)
                    total = gpu_total_mib() or 81920
                    for _ in range(90):
                        time.sleep(2)
                        free = gpu_free_mib()
                        if free is not None and free >= 0.8 * total:
                            break
                    logger.info("GPU has %s MiB free after stopping vllm", free)
            if free is not None and free >= self.min_free:
                self.platform = "cuda"
            elif self.backend == "gpu":
                self._restore()
                raise RuntimeError(f"GPU requested but only {free} MiB free")
            else:
                logger.warning("GPU not available (%s MiB free); falling back to CPU", free)
                self.platform = "cpu"
        os.environ["JAX_PLATFORMS"] = self.platform
        os.environ.setdefault("XLA_PYTHON_CLIENT_MEM_FRACTION", "0.85")
        logger.info("JAX platform: %s", self.platform)
        return self

    def __exit__(self, exc_type, exc, tb):
        self._restore()
        for sig, h in self._old_handlers.items():
            signal.signal(sig, h)
        return False

    @property
    def chunk_key(self):
        return "likelihood_chunk_gpu" if self.platform == "cuda" else "likelihood_chunk_cpu"
