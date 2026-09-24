"""Central config loader + run-dir path resolution + deterministic seeding.

Every pipeline script starts with:

    from config import load_config, add_common_args
    cfg = load_config(mode=args.mode)

and then uses `cfg.path("processed_dir")`, `cfg.mode_value("nlive")`,
`cfg.rng("stage-name")`, etc.

Mode blocks (`modes.smoke`, `modes.full`) hold every runtime-cost knob. A
handful of otherwise-global settings may also be overridden per mode:
`backend`, `max_variance`, `rho_true_grid`, `map_injection_subsample`,
`grid_overrides` (see config.yaml comments).
"""
from __future__ import annotations

import hashlib
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

CODE_DIR = Path(__file__).resolve().parent.parent
RUN_DIR = CODE_DIR.parent
_MISSING = object()


@dataclass
class Config:
    raw: dict
    mode: str
    run_dir: Path = RUN_DIR

    def path(self, key: str) -> Path:
        p = self.run_dir / self.raw["paths"][key]
        p.mkdir(parents=True, exist_ok=True)
        return p

    def mode_value(self, key: str, default=_MISSING):
        """Look up a mode-dependent knob from modes.<mode>.<key>."""
        block = self.raw["modes"][self.mode]
        if key in block:
            return block[key]
        if default is _MISSING:
            raise KeyError(f"modes.{self.mode}.{key} not set in config.yaml")
        return default

    @property
    def seed(self) -> int:
        return int(self.raw["run"]["seed"])

    @property
    def far_threshold(self) -> float:
        return float(self.raw["sample"]["far_threshold_per_yr"])

    @property
    def chi_eff_column(self) -> str:
        return self.raw["sample"]["chi_eff_column"]

    @property
    def grids(self) -> dict:
        g = dict(self.raw["grids"])
        g.update(self.mode_value("grid_overrides", {}) or {})
        return g

    @property
    def backend(self) -> str:
        return str(self.mode_value("backend", self.raw["run"].get("backend", "auto")))

    @property
    def max_variance(self) -> float:
        return float(self.mode_value("max_variance", self.raw["likelihood"]["max_variance"]))

    @property
    def rho_true_grid(self) -> list[float]:
        return [float(r) for r in self.mode_value("rho_true_grid", self.raw["mocks"]["rho_true_grid"])]

    def prior_bounds(self, name: str) -> tuple[float, float]:
        lo, hi = self.raw["priors"][name]
        return float(lo), float(hi)

    def seed_for(self, salt: str) -> int:
        """Deterministic per-stage integer seed derived from the top-level seed
        (hash-based so it does not depend on Python's per-process hash salt)."""
        h = hashlib.sha256(f"{self.seed}:{salt}".encode()).digest()
        return int.from_bytes(h[:4], "little") % (2**31 - 1)

    def rng(self, salt: str) -> np.random.Generator:
        return np.random.default_rng(self.seed_for(salt))

    def sample_table_path(self) -> Path:
        return self.path("processed_dir") / f"sample_table_{self.mode}.h5"

    def injection_table_path(self) -> Path:
        return self.path("processed_dir") / f"injection_table_{self.mode}.h5"

    def manifest_path(self) -> Path:
        return self.path("processed_dir") / f"event_manifest_{self.mode}.json"

    def fit_dir(self, model_name: str) -> Path:
        p = self.path("fits_dir") / self.mode / model_name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def mocks_path(self, rho: float) -> Path:
        return self.path("mocks_dir") / f"mocks_{self.mode}_rho{rho:+.2f}.h5"


def load_config(mode: str | None = None, config_path: str | Path | None = None) -> Config:
    cfg_path = Path(config_path) if config_path else CODE_DIR / "config.yaml"
    with open(cfg_path) as f:
        raw = yaml.safe_load(f)
    resolved_mode = mode or raw["run"]["mode"]
    assert resolved_mode in ("smoke", "full"), f"unknown mode {resolved_mode!r}"
    return Config(raw=raw, mode=resolved_mode)


def add_common_args(parser):
    parser.add_argument("--mode", choices=["smoke", "full"], default=None,
                        help="Override config.yaml's run.mode for this invocation.")
    parser.add_argument("--force", action="store_true",
                        help="Recompute even if this stage's outputs already exist.")
    parser.add_argument("--backend", choices=["auto", "cpu", "gpu"], default=None,
                        help="Override the configured jax backend (run.backend / modes.<mode>.backend).")
    return parser


def setup_logging(cfg: Config, stage: str) -> logging.Logger:
    log_dir = cfg.path("logs_dir")
    fmt = "%(asctime)s %(levelname)s %(message)s"
    handlers = [logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_dir / f"{stage}_{cfg.mode}.log")]
    logging.basicConfig(level=getattr(logging, cfg.raw["logging"]["level"]), format=fmt,
                        handlers=handlers, force=True)
    logger = logging.getLogger("q_chieff_copula")
    logger.info("stage=%s mode=%s seed=%d run_dir=%s", stage, cfg.mode, cfg.seed, cfg.run_dir)
    return logger


def outputs_exist(paths, force: bool, logger: logging.Logger, stage: str) -> bool:
    paths = [Path(p) for p in paths]
    if force:
        return False
    if all(p.exists() for p in paths):
        logger.info("%s: outputs already exist, skipping (use --force to redo): %s", stage,
                    ", ".join(str(p) for p in paths))
        return True
    return False
