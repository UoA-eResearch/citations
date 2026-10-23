"""Reviewer check: does the in-house GPTQ (code/quant.py) beat RTN on layer reconstruction, and is it a faithful GPTQ?

CPU only (the GPU is shared and busy). Whisper-small is run in float32 on a few calibration windows with the study's
own Collector hooks to get real Hessians for a handful of block linears; GPTQ and RTN weights are then compared on
held-out windows by relative output error ||X(W-Q)^T||^2 / ||XW^T||^2, at W4 and W3. Also: GPTQ with an identity
Hessian must reduce exactly to RTN; the damping path is instrumented; the size formula is recomputed.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
import numpy as np  # noqa: E402
import torch  # noqa: E402
from transformers import WhisperForConditionalGeneration, WhisperProcessor  # noqa: E402

torch.set_num_threads(int(os.environ.get("REV_THREADS", "4")))
RUN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RUN / "code"))
import quant  # noqa: E402
from audio import Audio  # noqa: E402

MAN = RUN / "data" / "manifest"
LAYERS = ["encoder.0.fc1", "encoder.5.self_attn.q_proj", "encoder.11.fc2", "decoder.0.self_attn.k_proj",
          "decoder.3.encoder_attn.v_proj", "decoder.6.fc1", "decoder.8.encoder_attn.out_proj", "decoder.11.fc2"]
N_CAL, N_HELD = int(os.environ.get("REV_NCAL", "8")), int(os.environ.get("REV_NHELD", "4"))


def wkey(w):
    return f"{w['speaker']}|{w['segs'][0][0]}|{w['segs'][0][1]}"


def make_batches(proc, windows, texts, aud):
    tok = proc.tokenizer
    tok.set_prefix_tokens(language="en", task="transcribe", predict_timestamps=False)
    out = []
    for w in windows:
        a = np.concatenate([aud.get(s, r) for s, r in w["segs"]])
        f = proc.feature_extractor([a], sampling_rate=16000, return_tensors="pt").input_features
        ids = tok(texts[wkey(w)]).input_ids[:-1][:448]
        out.append((f.float(), torch.tensor([ids])))
    return out


def main():
    proc = WhisperProcessor.from_pretrained("openai/whisper-small")
    m = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small", torch_dtype=torch.float32).eval()
    texts = json.loads((RUN / "data" / "calib_text" / "small.json").read_text())
    cal_w = json.loads((MAN / "calib_us_s0.json").read_text())[:N_CAL]
    held_w = json.loads((MAN / "calib_balanced_s0.json").read_text())[:N_HELD]
    aud = Audio("validation")
    cal, held = make_batches(proc, cal_w, texts, aud), make_batches(proc, held_w, texts, aud)
    mods = {k: v for k, v in quant.block_linears(m).items() if k in LAYERS}
    assert len(mods) == len(LAYERS), set(LAYERS) - set(mods)
    c = quant.Collector(mods)                       # Hessians 2XX^T/n from the FP32 model (the study uses FP16)
    quant.run_calibration(m, cal, c)
    h = quant.Collector(mods, hessian=False, sample_rows=1 << 30)   # every held-out row
    quant.run_calibration(m, held, h)
    res = {"n_cal_windows": N_CAL, "n_heldout_windows": N_HELD, "layers": {}}
    for k, mod in mods.items():
        W = mod.weight.data.float()
        H = c.H[k]
        X = torch.cat(h.rows[k]).float()
        Y = X @ W.T
        # damping path: does the first attempt (1% of mean diag) factorise?
        damp_ok = True
        try:
            torch.linalg.cholesky(H + 0.01 * torch.mean(torch.diag(H)) * torch.eye(H.shape[0]))
        except torch.linalg.LinAlgError:
            damp_ok = False
        r = {"in": int(W.shape[1]), "out": int(W.shape[0]), "dead_cols": int((torch.diag(H) == 0).sum()),
             "first_damping_factorises": damp_ok, "heldout_rows": int(X.shape[0])}
        for bits in (4, 3):
            Qr = quant.rtn_weight(W, bits)
            Qg = quant.gptq_weight(W, H, bits)
            er = ((X @ Qr.T - Y) ** 2).sum().item() / (Y ** 2).sum().item()
            eg = ((X @ Qg.T - Y) ** 2).sum().item() / (Y ** 2).sum().item()
            # in-sample proxy objective tr(D H D^T)
            Dr, Dg = W - Qr, W - Qg
            hr = torch.einsum("ij,jk,ik->", Dr, H, Dr).item()
            hg = torch.einsum("ij,jk,ik->", Dg, H, Dg).item()
            r[f"w{bits}"] = {"rel_err_rtn_heldout": er, "rel_err_gptq_heldout": eg, "gptq_over_rtn_heldout": eg / er,
                             "hessian_obj_gptq_over_rtn": hg / hr}
        # identity Hessian => GPTQ must equal RTN exactly
        Qi = quant.gptq_weight(W, torch.eye(W.shape[1]), 4)
        r["identity_hessian_equals_rtn"] = bool(torch.equal(Qi, quant.rtn_weight(W, 4)))
        res["layers"][k] = r
        print(k, json.dumps({kk: vv for kk, vv in r.items() if kk in ("w4", "w3", "identity_hessian_equals_rtn")}), flush=True)
    # size formula recomputed independently
    n = sum(v.weight.numel() for v in quant.block_linears(m).values())
    res["size"] = {"block_linear_weights": n, "n_layers": len(quant.block_linears(m)),
                   "w4_bits_formula": n * 4 + (n // 128) * 32, "study_w4_bits": quant.size_bits(m, {k: 4 for k in quant.block_linears(m)}),
                   "fp16_bits": quant.size_bits(m, {}), "all_in_features_multiple_of_128": all(v.in_features % 128 == 0 for v in quant.block_linears(m).values()),
                   "modules_with_bias_not_counted": sum(1 for v in quant.block_linears(m).values() if v.bias is not None)}
    # what is NOT quantized (plan: conv front end, embeddings, layer norms, tied output projection)
    quantised = set(id(v.weight) for v in quant.block_linears(m).values())
    other = {n_: tuple(p.shape) for n_, p in m.named_parameters() if id(p) not in quantised and p.dim() == 2}
    res["unquantised_2d_params"] = other
    Path(__file__).with_name("gptq_check.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["size"], indent=1))
    print("unquantised 2-D params:", list(other))


if __name__ == "__main__":
    main()
