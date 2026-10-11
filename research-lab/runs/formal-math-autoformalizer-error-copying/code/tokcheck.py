"""D2 item 6: tokenizer round-trip check inside the vLLM image (run before sampling)."""
from transformers import AutoTokenizer
S = "theorem my_favorite_theorem (x : ℝ) (h₀ : 0 < x) : ∑ k ∈ Finset.Icc 1 12, x ^ k ≤ √2 * π := by sorry"
for d in ["Kimina-Autoformalizer-7B", "Goedel-Formalizer-V2-8B", "Herald_translator", "Qwen2.5-7B-Instruct", "DeepSeek-Prover-V2-7B"]:
    try:
        t = AutoTokenizer.from_pretrained(f"/models/{d}", trust_remote_code=True)
        ids = t.encode(S, add_special_tokens=False)
        back = t.decode(ids)
        print(d, type(t).__name__, "ROUNDTRIP_OK" if back == S else f"MISMATCH: {back[:120]!r}", len(ids))
    except Exception as e:
        print(d, "ERROR", repr(e)[:200])
