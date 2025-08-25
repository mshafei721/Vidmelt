VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: help venv install run test fmt clean

help:
	@echo "Common commands:"
	@echo "  make venv      # create virtualenv"
	@echo "  make install   # install dependencies into venv"
	@echo "  make run       # run Flask app"
	@echo "  make test      # run pytest"
	@echo "  make fmt       # format with black/isort if available"
	@echo "  make clean     # remove caches"

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install -r requirements.txt

run:
	$(PY) app.py

test:
	$(VENV)/bin/pytest -q

fmt:
	@command -v $(VENV)/bin/black >/dev/null 2>&1 && $(VENV)/bin/black . || echo "black not installed"
	@command -v $(VENV)/bin/isort >/dev/null 2>&1 && $(VENV)/bin/isort . || echo "isort not installed"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
