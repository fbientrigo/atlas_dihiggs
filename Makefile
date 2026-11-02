# make setup: root .venv with all Python deps + dhb, 2HDMC, evaluate_point, DihiggsPointV2Evaluator, HB/HS dataset check.
# make smoke: dihiggs autoresearch end-to-end smoke with that venv.
PYTHON ?= python3
PY := $(CURDIR)/.venv/bin/python

.PHONY: setup smoke
setup:
	$(PYTHON) -m venv .venv
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r requirements.txt -r dihiggs/requirements.txt -e dihiggs_boundary/python
	bash dihiggs_boundary/scripts/build_evaluator.sh

smoke:
	$(MAKE) -C dihiggs autoresearch-smoke PY=$(PY)
