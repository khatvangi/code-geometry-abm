.PHONY: setup build-canonical figures validate validate-v3 reproduce clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
CANONICAL := results/v2.5_methodology_paper_canonical
FIGURES := figures

setup:
	python3 -m venv $(VENV)
	$(PIP) install -q -r requirements.txt

build-canonical: setup
	$(PYTHON) scripts/build_methodology_paper_canonical.py

figures: build-canonical
	$(PYTHON) scripts/build_methodology_paper_figures.py

validate:
	$(PYTHON) scripts/validate_methodology_figures.py

# foolproof checks for the v3.x consolidated + episodic models
validate-v3:
	$(PYTHON) scripts/validate_v3.py

reproduce: figures validate
	@echo "=== reproduction complete ==="

clean:
	rm -rf $(CANONICAL)
	rm -f $(FIGURES)/figure4_trajectories.pdf
	rm -f $(FIGURES)/submission/fig2_phase_map.pdf
	rm -f $(FIGURES)/submission/fig3_concentration.pdf
	rm -f $(FIGURES)/submission/fig6_regime_counts.pdf
	rm -f $(FIGURES)/submission/table6_regime_metrics.tex
