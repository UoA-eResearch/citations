"""Accent-aware mixed-precision allocation (plan section 4), from the FP16 model and the validation split.

  mp_alloc.py MODEL   -> results/tables/mp_allocation_<MODEL>.json
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decode  # noqa: E402
import manifest  # noqa: E402
import quant  # noqa: E402

RUN = Path(__file__).resolve().parents[1]
TAB = RUN / "results" / "tables"


def main(model):
    wer = json.loads((TAB / f"fp16_validation_group_wer_{model}.json").read_text())
    by = {}
    for w in manifest.windows(manifest.segments()):
        by.setdefault(w["accent"], []).append(w)
    groups = sorted((a for a in by if a != "Don't know"), key=lambda a: wer[a])
    best, worst = groups[:3], groups[-3:]
    rng = random.Random(0)
    pick = {a: rng.sample(by[a], 8) for a in best + worst}
    proc, m = decode.load(model)
    cal_w = decode.batches(model, proc, m, [w for a in worst for w in pick[a]])
    cal_b = decode.batches(model, proc, m, [w for a in best for w in pick[a]])
    ew, eb = quant.layer_error(m, cal_w), quant.layer_error(m, cal_b)
    bits, score, ratio = quant.mixed_allocation(m, ew, eb)
    assert 0.99 <= ratio <= 1.01, ratio
    mods = quant.block_linears(m)
    tot = sum(x.weight.numel() for x in mods.values())
    out = {"worst_validation_groups": worst, "best_validation_groups": best, "size_ratio_vs_w4": round(ratio, 5),
           "share_w8": round(sum(mods[k].weight.numel() for k in bits if bits[k] == 8) / tot, 4),
           "share_w3": round(sum(mods[k].weight.numel() for k in bits if bits[k] == 3) / tot, 4),
           "bits": bits, "score": score, "err_worst": ew, "err_best": eb}
    (TAB / f"mp_allocation_{model}.json").write_text(json.dumps(out, indent=1))
    print({k: v for k, v in out.items() if k not in ("bits", "score", "err_worst", "err_best")})


if __name__ == "__main__":
    main(sys.argv[1])
