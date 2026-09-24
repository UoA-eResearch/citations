# q-chi_eff copula stress test -- pipeline targets
# Usage: make smoke | make full | make fit MODE=full | make clean-raw
MODE ?= smoke
PY := ../venv/bin/python
EXTRA ?=

.PHONY: smoke full fetch build test fit mocks mockstats diagnostics figures gpucheck vllm-start clean-raw clean-results

smoke:
	$(PY) run_all.py --mode smoke $(EXTRA)

full:
	$(PY) run_all.py --mode full $(EXTRA)

fetch build test fit mocks mockstats diagnostics figures:
	$(PY) run_all.py --mode $(MODE) --stages $@ $(EXTRA)

# optional: time the compiled likelihood on the A100 (stops/restarts the vllm container for a few minutes)
gpucheck:
	$(PY) run_all.py --mode $(MODE) --stages gpucheck $(EXTRA)

# safety net: every GPU stage restarts the vllm container itself (also on Ctrl-C / errors);
# only needed if a GPU stage was SIGKILLed or the machine rebooted mid-stage
vllm-start:
	docker start vllm; nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# delete raw PE downloads once the standardized tables exist (be a good citizen)
clean-raw:
	rm -rf ../data/raw/pe_samples/*.h5 ../data/raw/pe_samples/*.part

clean-results:
	rm -rf ../results/fits/$(MODE) ../results/tables/*_$(MODE).* ../results/figures/$(MODE)_* ../data/mocks/mocks_$(MODE)_*
