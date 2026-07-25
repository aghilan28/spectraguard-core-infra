.PHONY: setup install lint format test smoke clean

VENV = .venv
PYTHON = $(VENV)/Scripts/python
PIP = $(VENV)/Scripts/pip

setup:
python -m venv $(VENV)
$(PIP) install --upgrade pip
$(PIP) install -r requirements.txt
$(VENV)/Scripts/pre-commit install

install:
$(PIP) install -r requirements.txt

lint:
$(VENV)/Scripts/ruff check .
$(VENV)/Scripts/mypy .

format:
$(VENV)/Scripts/black .
$(VENV)/Scripts/ruff check --fix .

test:
$(VENV)/Scripts/pytest

smoke:
$(PYTHON) smoke_test.py

clean:
if exist $(VENV) rmdir /s /q $(VENV)
if exist __pycache__ rmdir /s /q __pycache__
if exist .pytest_cache rmdir /s /q .pytest_cache
