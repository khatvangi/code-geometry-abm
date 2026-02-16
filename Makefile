.PHONY: setup figures validate reproduce clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
CONFIRM := results/v2.5_corrected_three_regime_confirm
FIGURES := $(CONFIRM)/figures_publication

setup:
	python3 -m venv $(VENV)
	$(PIP) install -q -r requirements.txt

figures: setup
	$(PYTHON) scripts/build_v2_5_publication_figures.py \
		--root $(CONFIRM) --outdir $(FIGURES)

validate:
	$(PYTHON) scripts/validate_figures_from_csv.py

reproduce: figures validate
	@echo "=== reproduction complete ==="

clean:
	rm -f $(FIGURES)/fig*.png $(FIGURES)/fig*.pdf $(FIGURES)/FIGURE_CAPTIONS.md
