# Deviations log

Every departure from the lead and from plan.md, timestamped with `date` when it was made.

## D1 — 2026-10-17 08:08 NZDT — before any generation: three real arms are impossible; a within-record experiment instead

1. **Design.** 48,332 of the 48,353 DataCite records with a Local Contexts URI are Neotoma's, all with one element
   ("TK Open to Collaboration (TK CB)"); 21 are elsewhere. The lead's stratified real arm A (no publisher > 50%) and
   its arm-A-versus-arm-B comparison of different repositories cannot be built. Each record is instead shown with
   every condition swapped into the same rightsList slot (plan 1.2). Real arm-B records are not used.
2. **Element types** beyond Neotoma's are inserted using Local Contexts' own published names and URIs (BC Notice,
   TK Notice, TK Non-Commercial, TK Community Use Only), with matched conventional clauses.
3. **No LLM judge; agent adjudication of a pilot instead of 300 human-coded responses** (plan section 5). The lab
   has no human coder, and a judge model adds its own blind spots and would need care to stay local.
4. **Sample sizes:** 221 base records (200 Neotoma + 21 others) x 10 conditions rather than 3 x 400 records.
5. Neotoma's element pairs a TK *Label* name with the Open to Collaborate *Notice* URI - a data-quality point worth
   reporting to Neotoma and Local Contexts.
6. The Mistral snapshot's duplicate consolidated.safetensors (47 GB, a re-packaging of the sharded weights) was
   deleted so vLLM loads only the sharded set.

## D2 — 2026-10-17 08:29 NZDT — the Qwen3-32B server missed run_gpu.sh's 20-minute start timeout

Loading Qwen3-32B's 62 GB from the HDD took about 20 minutes; the server had just finished warming up when the
script's timeout stopped it, and the script moved on to OLMo-2 and Mistral. No Qwen output was generated. Qwen
runs afterwards in its own GPU window (code/run_gpu_qwen.sh: identical except for the model list and a 60-minute
timeout). Generation settings, prompts and corpus are unchanged.

Then OLMo-2's server crashed at start-up, started seconds after the Qwen container was stopped mid-warmup; the
container was removed (--rm) before its log could be read, so the cause is inferred, not seen: most likely Qwen's
GPU memory was not yet released. The second window (run_gpu_qwen.sh) now runs OLMo-2 and then Qwen3, waits for the
GPU to be free before each server starts, and captures each container's log to logs/lc-gen-<model>.log. Mistral
ran in the first window with its log captured.
